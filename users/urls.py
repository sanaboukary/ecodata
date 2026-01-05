from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('quick-login/', views.quick_login_view, name='quick_login'),
    path('profile/', views.profile_view, name='profile'),
    
    # Accès refusé
    path('access-denied/', views.access_denied_view, name='access_denied'),
    
    # Ancien système (conservé pour compatibilité)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('engineer/dashboard/', views.engineer_dashboard, name='engineer_dashboard'),
    path('api/generate-token/', views.generate_api_token_view, name='generate_api_token'),
    path('mfa/enable/', views.enable_mfa_view, name='enable_mfa'),
    path('mfa/verify/', views.verify_mfa_setup_view, name='verify_mfa'),
]
