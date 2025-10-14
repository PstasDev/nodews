from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import EmailVerificationToken
from .utils import send_verification_email, verify_user_email
import json


def index(request):
    """
    Index view that serves as the collection page for all nodews apps.
    """
    context = {
        'title': 'NodeWS',
        'apps': [
            {
                'name': 'Büfé',
                'description': 'Iskolai büfé rendelés',
                'url': '/bufe/',
                'status': 'Fejlesztés alatt'
            }
        ],
        'user': request.user
    }
    return render(request, 'authentication/index.html', context)


def user_login(request):
    """Login view with email verification check"""
    if request.user.is_authenticated:
        return redirect('authentication:index')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Üdvözöljük újra, {user.first_name or user.username}!')
            return redirect('authentication:index')
        else:
            # Add form errors to messages for better visibility
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomAuthenticationForm()
    
    context = {
        'form': form
    }
    return render(request, 'authentication/login.html', context)


def user_register(request):
    """Registration view with email verification"""
    if request.user.is_authenticated:
        return redirect('authentication:index')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create user as inactive
            user = form.save()
            
            # Create verification token
            verification_token = EmailVerificationToken.create_for_user(user)
            
            # Send verification email
            if send_verification_email(user, verification_token):
                messages.success(
                    request, 
                    f'Fiók létrehozva! Megerősítő e-mailt küldtünk a(z) {user.email} címre. '
                    'Kérjük, ellenőrizze a postafiókját és kattintson a megerősítő linkre.'
                )
            else:
                messages.warning(
                    request,
                    'Fiók létrehozva, de hiba történt a megerősítő e-mail küldése során. '
                    'Kérjük, használja az "E-mail újraküldése" funkciót.'
                )
            
            return redirect('authentication:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'authentication/register.html', {'form': form})


@login_required
def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('authentication:index')


# API Endpoints for secure authentication (future auth.szlg.info)

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """API endpoint for login with activation check"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'E-mail és jelszó megadása kötelező'}, status=400)
        
        # Find user by email and get username
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return JsonResponse({'error': 'Érvénytelen e-mail cím vagy jelszó'}, status=401)
        
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': 'Sikeres bejelentkezés',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_active': user.is_active,
                        'date_joined': user.date_joined.isoformat()
                    }
                })
            else:
                return JsonResponse({
                    'error': 'Fiókja nincs aktiválva. Kérjük, ellenőrizze e-mail fiókját a megerősítő linkért.'
                }, status=403)
        else:
            return JsonResponse({'error': 'Érvénytelen e-mail cím vagy jelszó'}, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    """API endpoint for registration with email verification"""
    try:
        data = json.loads(request.body)
        
        form = CustomUserCreationForm(data)
        if form.is_valid():
            # Create user as inactive
            user = form.save()
            
            # Create verification token
            verification_token = EmailVerificationToken.create_for_user(user)
            
            # Send verification email
            email_sent = send_verification_email(user, verification_token)
            
            return JsonResponse({
                'success': True,
                'message': 'Felhasználó sikeresen létrehozva. Kérjük, ellenőrizze e-mail fiókját a megerősítő linkért.',
                'email_sent': email_sent,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active
                }
            }, status=201)
        else:
            return JsonResponse({'error': form.errors}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def api_logout(request):
    """API endpoint for logout"""
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logout successful'})
    else:
        return JsonResponse({'error': 'Not authenticated'}, status=401)


@require_http_methods(["GET"])
def api_user_info(request):
    """API endpoint to get current user info"""
    if request.user.is_authenticated:
        return JsonResponse({
            'success': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
                'is_active': request.user.is_active,
                'date_joined': request.user.date_joined.isoformat(),
                'last_login': request.user.last_login.isoformat() if request.user.last_login else None
            }
        })
    else:
        return JsonResponse({'error': 'Not authenticated'}, status=401)


def email_confirmation(request, token):
    """
    Email confirmation view for activating user accounts.
    """
    success, message, user = verify_user_email(token)
    
    if success:
        messages.success(request, message)
        # Auto-login the user after successful verification
        if user:
            login(request, user)
        return redirect('authentication:index')
    else:
        messages.error(request, message)
        return redirect('authentication:login')


def resend_verification_email(request):
    """
    View to resend verification email for users who haven't activated their account.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'E-mail cím megadása kötelező.')
            return redirect('authentication:login')
        
        try:
            user = User.objects.get(email=email, is_active=False)
            
            # Create new verification token
            verification_token = EmailVerificationToken.create_for_user(user)
            
            # Send verification email
            if send_verification_email(user, verification_token):
                messages.success(request, 'Megerősítő e-mail újra elküldve. Kérjük, ellenőrizze postafiókját.')
            else:
                messages.error(request, 'Hiba történt az e-mail küldése során. Kérjük, próbálja meg később.')
                
        except User.DoesNotExist:
            messages.error(request, 'Nem található inaktív felhasználó ezzel az e-mail címmel.')
        
        return redirect('authentication:login')
    
    return redirect('authentication:login')
