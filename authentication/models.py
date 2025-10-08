from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class EmailVerificationToken(models.Model):
    """
    Model to store email verification tokens for user account activation.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='email_verification_token'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique token for email verification"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification token for {self.user.username}"
    
    def is_expired(self):
        """Check if the token has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save()

    @classmethod
    def create_for_user(cls, user, expires_in_seconds=24*60*60):
        """
        Create a new verification token for a user.
        Deletes any existing token for the user.
        """
        # Delete any existing tokens for this user
        cls.objects.filter(user=user).delete()
        
        # Create new token
        expires_at = timezone.now() + timezone.timedelta(seconds=expires_in_seconds)
        return cls.objects.create(
            user=user,
            expires_at=expires_at
        )
