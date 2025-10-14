"""
Domain verification utilities for the Büfé app.
"""
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.template.response import TemplateResponse
from functools import wraps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


# Allowed email domains for Büfé access
ALLOWED_DOMAINS = ['szlgbp.hu', 'botond.eu']


def is_email_domain_allowed(email):
    """
    Check if the user's email domain is in the allowed list.
    
    Args:
        email (str): User's email address
        
    Returns:
        bool: True if domain is allowed, False otherwise
    """
    if not email:
        return False
    
    domain = email.split('@')[-1].lower()
    return domain in ALLOWED_DOMAINS


def get_user_domain(user):
    """
    Get the domain part of a user's email.
    
    Args:
        user: Django User object
        
    Returns:
        str: Domain part of email or empty string
    """
    if not user or not user.email:
        return ""
    
    return user.email.split('@')[-1].lower()


def domain_required(allowed_domains=None):
    """
    Decorator that restricts access to users with specific email domains.
    Also requires user to be authenticated and active.
    
    Args:
        allowed_domains (list): List of allowed domains. Defaults to ALLOWED_DOMAINS.
    """
    if allowed_domains is None:
        allowed_domains = ALLOWED_DOMAINS
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Check if user is active (which means email is verified)
            if not user.is_active:
                messages.error(
                    request, 
                    'Fiókja nincs aktiválva. Kérjük, ellenőrizze e-mail fiókját a megerősítő linkért.'
                )
                return redirect('authentication:login')
            
            # Check if user has valid email domain
            if not is_email_domain_allowed(user.email):
                context = {
                    'user_domain': get_user_domain(user),
                    'allowed_domains': allowed_domains,
                    'user_email': user.email
                }
                return TemplateResponse(
                    request, 
                    'bufe/domain_restricted.html', 
                    context, 
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


def check_domain_access(user):
    """
    Check if a user has domain access to the Büfé app.
    
    Args:
        user: Django User object
        
    Returns:
        tuple: (has_access: bool, reason: str)
    """
    if not user.is_authenticated:
        return False, "not_authenticated"
    
    if not user.is_active:
        return False, "not_active"
    
    if not is_email_domain_allowed(user.email):
        return False, "invalid_domain"
    
    return True, "access_granted"


class DomainPermissionMixin:
    """
    Mixin for class-based views to check domain permissions.
    """
    allowed_domains = ALLOWED_DOMAINS
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        
        has_access, reason = check_domain_access(request.user)
        
        if not has_access:
            if reason == "not_active":
                messages.error(
                    request, 
                    'Fiókja nincs aktiválva. Kérjük, ellenőrizze e-mail fiókját a megerősítő linkért.'
                )
                return redirect('authentication:login')
            elif reason == "invalid_domain":
                context = {
                    'user_domain': get_user_domain(request.user),
                    'allowed_domains': self.allowed_domains,
                    'user_email': request.user.email
                }
                return TemplateResponse(
                    request, 
                    'bufe/domain_restricted.html', 
                    context, 
                    status=403
                )
        
        return super().dispatch(request, *args, **kwargs)


def is_bufeadmin(user):
    """
    Check if a user is a bufeadmin.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is a bufeadmin, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    from .models import Bufe
    try:
        bufe = Bufe.objects.first()
        if not bufe:
            return False
        return bufe.bufeadmin.filter(id=user.id).exists()
    except Exception:
        return False


def bufeadmin_required(view_func):
    """
    Decorator that restricts access to bufeadmin users only.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not is_bufeadmin(request.user):
            messages.error(request, 'Nincs jogosultsága a büfé adminisztrációs felület eléréséhez.')
            return redirect('bufe:index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def broadcast_order_update(order_data, action='new'):
    """
    Broadcast order update to all connected bufeadmin WebSocket clients.
    
    Args:
        order_data (dict): Order data to broadcast
        action (str): Action type - 'new', 'update', 'delete'
    """
    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                'bufe_orders',
                {
                    'type': 'order_update',
                    'action': action,
                    'order': order_data
                }
            )
        except Exception as e:
            print(f"Error broadcasting order update: {e}")