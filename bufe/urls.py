from django.urls import path
from . import views

app_name = 'bufe'

urlpatterns = [
    # Web interface
    path('', views.index, name='index'),
    
    # API endpoints
    path('api/check-access/', views.api_check_access, name='api_check_access'),
]