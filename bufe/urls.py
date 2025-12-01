from django.urls import path
from . import views

app_name = 'bufe'

urlpatterns = [
    # Web interface - Student views
    path('', views.index, name='index'),
    path('rendeles/', views.create_order, name='create_order'),
    path('rendeles/<int:order_id>/', views.order_detail, name='order_detail'),
    path('rendeleseim/', views.my_orders, name='my_orders'),
    path('rendeles/<int:order_id>/visszavonas/', views.cancel_order, name='cancel_order'),
    
    # Bufeadmin interface
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/menu/', views.admin_menu_management, name='admin_menu_management'),
    path('admin/opening-hours/', views.admin_opening_hours, name='admin_opening_hours'),
    
    # API endpoints - Public
    path('api/check-access/', views.api_check_access, name='api_check_access'),
    path('api/opening-hours/', views.api_opening_hours, name='api_opening_hours'),
    
    # API endpoints - Bufeadmin only
    path('admin/api/orders/', views.api_get_orders, name='api_get_orders'),
    path('admin/api/update-order/', views.api_update_order_status, name='api_update_order'),
    path('admin/api/archive-order/', views.api_archive_order, name='api_archive_order'),
    path('admin/api/archive-all-done/', views.api_archive_all_done, name='api_archive_all_done'),
    path('admin/api/update-product/', views.api_update_product, name='api_update_product'),
    path('admin/api/add-product/', views.api_add_product, name='api_add_product'),
    path('admin/api/categories/', views.api_get_categories, name='api_get_categories'),
    path('admin/api/update-bufe/', views.api_update_bufe, name='api_update_bufe'),
    path('admin/api/update-opening-hours/', views.api_update_opening_hours, name='api_update_opening_hours'),
]