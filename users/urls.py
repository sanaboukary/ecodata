from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Dashboards par rôle
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('engineer/dashboard/', views.engineer_dashboard, name='engineer_dashboard'),
    
    # API Token
    path('api/generate-token/', views.generate_api_token_view, name='generate_api_token'),
    
    # MFA
    path('mfa/enable/', views.enable_mfa_view, name='enable_mfa'),
    path('mfa/verify/', views.verify_mfa_setup_view, name='verify_mfa'),
]
