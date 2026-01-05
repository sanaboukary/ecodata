# -*- coding: utf-8 -*-
"""
Système de permissions par rôle pour la plateforme BRVM
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect

# Définition des rôles et leurs permissions
ROLE_PERMISSIONS = {
    'ADMIN': {
        'name': 'Administrateur',
        'permissions': [
            # Accès total à tout
            'view_dashboard',
            'view_actions',
            'view_recommendations',
            'view_alerts',
            'view_publications',
            'view_macro',
            'view_analytics',
            'manage_users',
            'manage_data',
            'manage_system',
            'export_data',
            'api_access',
        ]
    },
    'ANALYST': {
        'name': 'Ingénieur Financier / Analyste',
        'permissions': [
            # Accès complet aux données et analyses
            'view_dashboard',
            'view_actions',
            'view_recommendations',
            'view_alerts',
            'view_publications',
            'view_macro',
            'view_analytics',
            'export_data',
            'api_access',
        ]
    },
    'INVESTOR': {
        'name': 'Investisseur',
        'permissions': [
            # Accès aux recommandations et outils de décision
            'view_dashboard',
            'view_actions',
            'view_recommendations',
            'view_alerts',
            'view_publications',
            'view_macro',
        ]
    },
    'READER': {
        'name': 'Lecteur',
        'permissions': [
            # Consultation simple uniquement
            'view_dashboard',
            'view_actions',
            'view_publications',
        ]
    },
}

# Matrice d'accès par page
PAGE_ACCESS = {
    # Pages publiques (accessible à tous les connectés)
    '/': ['ADMIN', 'ANALYST', 'INVESTOR', 'READER'],
    '/dashboard/': ['ADMIN', 'ANALYST', 'INVESTOR', 'READER'],
    
    # Actions BRVM
    '/actions/': ['ADMIN', 'ANALYST', 'INVESTOR', 'READER'],
    '/actions/detail/<symbol>/': ['ADMIN', 'ANALYST', 'INVESTOR', 'READER'],
    
    # Recommandations (Investisseurs et plus)
    '/recommendations/': ['ADMIN', 'ANALYST', 'INVESTOR'],
    '/recommendations/premium/': ['ADMIN', 'ANALYST', 'INVESTOR'],
    
    # Alertes (Investisseurs et plus)
    '/alerts/': ['ADMIN', 'ANALYST', 'INVESTOR'],
    '/alerts/configure/': ['ADMIN', 'ANALYST', 'INVESTOR'],
    
    # Publications financières
    '/publications/': ['ADMIN', 'ANALYST', 'INVESTOR', 'READER'],
    '/publications/<id>/': ['ADMIN', 'ANALYST', 'INVESTOR', 'READER'],
    
    # Contexte macroéconomique (Investisseurs et plus)
    '/macro/': ['ADMIN', 'ANALYST', 'INVESTOR'],
    '/macro/correlations/': ['ADMIN', 'ANALYST', 'INVESTOR'],
    
    # Analytics avancés (Analystes et Admin uniquement)
    '/analytics/': ['ADMIN', 'ANALYST'],
    '/analytics/backtest/': ['ADMIN', 'ANALYST'],
    '/analytics/technical/': ['ADMIN', 'ANALYST'],
    '/analytics/sentiment/': ['ADMIN', 'ANALYST'],
    
    # Export de données (Analystes et Admin)
    '/export/': ['ADMIN', 'ANALYST'],
    '/export/csv/': ['ADMIN', 'ANALYST'],
    '/export/excel/': ['ADMIN', 'ANALYST'],
    
    # API REST (Analystes et Admin)
    '/api/': ['ADMIN', 'ANALYST'],
    '/api/actions/': ['ADMIN', 'ANALYST'],
    '/api/recommendations/': ['ADMIN', 'ANALYST'],
    '/api/macro/': ['ADMIN', 'ANALYST'],
    
    # Administration (Admin uniquement)
    '/admin/': ['ADMIN'],
    '/users/': ['ADMIN'],
    '/system/': ['ADMIN'],
    '/ingestion/': ['ADMIN'],
}


def get_user_role(user):
    """Récupère le rôle d'un utilisateur"""
    if not user.is_authenticated:
        return None
    
    # Vérifier si admin Django
    if user.is_superuser or user.is_staff:
        return 'ADMIN'
    
    # Récupérer le rôle depuis le profil utilisateur
    try:
        return user.profile.role
    except:
        return 'READER'  # Rôle par défaut


def has_permission(user, permission):
    """Vérifie si un utilisateur a une permission spécifique"""
    role = get_user_role(user)
    if not role:
        return False
    
    permissions = ROLE_PERMISSIONS.get(role, {}).get('permissions', [])
    return permission in permissions


def can_access_page(user, page_path):
    """Vérifie si un utilisateur peut accéder à une page"""
    role = get_user_role(user)
    if not role:
        return False
    
    # Chercher la page exacte ou une correspondance partielle
    for path, allowed_roles in PAGE_ACCESS.items():
        if page_path.startswith(path.replace('<symbol>', '').replace('<id>', '')):
            return role in allowed_roles
    
    # Par défaut, refuser l'accès
    return False


# Decorateurs pour protéger les vues
def role_required(*roles):
    """Decorator pour restreindre l'accès à certains rôles"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user_role = get_user_role(request.user)
            
            if user_role not in roles:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({
                        'error': 'Accès refusé',
                        'message': f'Cette page est réservée aux rôles: {", ".join(roles)}',
                        'required_role': roles,
                        'your_role': user_role
                    }, status=403)
                else:
                    return redirect('access_denied')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission):
    """Decorator pour restreindre l'accès selon une permission"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, permission):
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({
                        'error': 'Permission refusée',
                        'message': f'Vous n\'avez pas la permission: {permission}',
                        'required_permission': permission
                    }, status=403)
                else:
                    return redirect('access_denied')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Exemples d'utilisation dans les vues
"""
# Vue accessible uniquement aux investisseurs, analystes et admin
@role_required('INVESTOR', 'ANALYST', 'ADMIN')
def recommendations_view(request):
    ...

# Vue accessible uniquement aux analystes et admin
@role_required('ANALYST', 'ADMIN')
def analytics_view(request):
    ...

# Vue accessible uniquement à l'admin
@role_required('ADMIN')
def manage_users_view(request):
    ...

# Vue avec permission spécifique
@permission_required('export_data')
def export_csv_view(request):
    ...
"""
