from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .utils import domain_required, check_domain_access, get_user_domain


@domain_required()
def index(request):
    """
    Büfé app main view.
    Requires authentication and valid email domain (@szlgbp.hu or @botond.eu).
    """
    user = request.user
    user_domain = get_user_domain(user)
    
    context = {
        'user': user,
        'user_domain': user_domain,
        'user_full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
        'welcome_message': f"Üdvözöljük a Büfé alkalmazásban, {user.first_name}!"
    }
    
    return render(request, 'bufe/index.html', context)


@csrf_exempt
@require_http_methods(["GET"])
def api_check_access(request):
    """
    API endpoint to check if current user has access to Büfé app.
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'has_access': False,
            'reason': 'not_authenticated',
            'message': 'Felhasználó nincs bejelentkezve'
        }, status=401)
    
    has_access, reason = check_domain_access(request.user)
    user_domain = get_user_domain(request.user)
    
    if has_access:
        return JsonResponse({
            'has_access': True,
            'reason': reason,
            'message': 'Hozzáférés engedélyezve',
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'domain': user_domain,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_active': request.user.is_active
            }
        })
    else:
        status_codes = {
            'not_authenticated': 401,
            'not_active': 403,
            'invalid_domain': 403
        }
        
        messages = {
            'not_authenticated': 'Felhasználó nincs bejelentkezve',
            'not_active': 'Felhasználó fiókja nincs aktiválva',
            'invalid_domain': f'Érvénytelen e-mail domain: @{user_domain}'
        }
        
        return JsonResponse({
            'has_access': False,
            'reason': reason,
            'message': messages.get(reason, 'Hozzáférés megtagadva'),
            'user_domain': user_domain,
            'allowed_domains': ['szlgbp.hu', 'botond.eu']
        }, status=status_codes.get(reason, 403))
