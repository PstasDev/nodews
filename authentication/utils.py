"""
Utility functions for email verification and JWT token handling.
"""
import jwt as PyJWT
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from .models import EmailVerificationToken


def generate_verification_jwt(user, token_uuid):
    """
    Generate a JWT token for email verification containing:
    - user_id: User's ID
    - username: User's username for second verification
    - token_uuid: UUID from EmailVerificationToken
    - iat: Token issued at timestamp
    - exp: Token expires at timestamp
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=settings.EMAIL_VERIFICATION_TOKEN_LIFETIME)
    
    payload = {
        'user_id': user.id,
        'username': user.username,
        'token_uuid': str(token_uuid),
        'iat': now,
        'exp': expires_at,
        'purpose': 'email_verification'
    }
    
    return PyJWT.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def decode_verification_jwt(token):
    """
    Decode and validate a JWT verification token.
    Returns the payload if valid, None if invalid.
    """
    try:
        payload = PyJWT.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=['HS256']
        )
        
        # Verify this is an email verification token
        if payload.get('purpose') != 'email_verification':
            return None
            
        return payload
    except PyJWT.ExpiredSignatureError:
        return None
    except PyJWT.InvalidTokenError:
        return None


def send_verification_email(user, verification_token):
    """
    Send email verification email to the user.
    """
    # Generate JWT token
    jwt_token = generate_verification_jwt(user, verification_token.token)
    
    # Create verification URL
    verification_url = f"{settings.FRONTEND_URL}{reverse('authentication:email_confirmation', kwargs={'token': jwt_token})}"
    
    # Email context
    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': 'NodeWS',
        'school_name': 'Kőbányai Szent László Gimnázium'
    }
    
    # Render email templates
    html_message = render_to_string('authentication/emails/verification_email.html', context)
    plain_message = strip_tags(html_message)
    
    # Send email
    subject = 'NodeWS - E-mail cím megerősítése'
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False


def verify_user_email(jwt_token):
    """
    Verify user email using JWT token.
    Returns (success: bool, message: str, user: User|None)
    """
    # Decode JWT token
    payload = decode_verification_jwt(jwt_token)
    if not payload:
        return False, "Érvénytelen vagy lejárt token.", None
    
    try:
        from django.contrib.auth.models import User
        
        # Get user and verify username matches
        user = User.objects.get(
            id=payload['user_id'],
            username=payload['username']
        )
        
        # Get verification token
        verification_token = EmailVerificationToken.objects.get(
            user=user,
            token=payload['token_uuid']
        )
        
        # Check if token is valid
        if not verification_token.is_valid():
            return False, "A token érvénytelen vagy már felhasználásra került.", None
        
        # Activate user and mark token as used
        user.is_active = True
        user.save()
        
        verification_token.mark_as_used()
        
        return True, "E-mail cím sikeresen megerősítve! Most már bejelentkezhet.", user
        
    except User.DoesNotExist:
        return False, "Felhasználó nem található.", None
    except EmailVerificationToken.DoesNotExist:
        return False, "Érvénytelen token.", None
    except Exception as e:
        return False, f"Hiba történt: {str(e)}", None