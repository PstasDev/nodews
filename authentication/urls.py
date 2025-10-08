from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Web interface
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    
    # Email verification
    path('email-confirmation/<str:token>/', views.email_confirmation, name='email_confirmation'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    
    # API endpoints for secure authentication (future auth.szlg.info)
    path('api/login/', views.api_login, name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/user/', views.api_user_info, name='api_user_info'),
]