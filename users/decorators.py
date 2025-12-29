"""
Décorateurs pour contrôler l'accès basé sur les rôles et permissions
"""

from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from .models import User, AuditLog, Role


def role_required(*allowed_roles):
    """
    Décorateur pour restreindre l'accès à certains rôles
    
    Usage:
        @role_required(Role.ADMIN_PLATFORM, Role.DATA_ENGINEER)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not request.user.role:
                messages.error(request, "Vous n'avez aucun rôle assigné.")
                return HttpResponseForbidden("Accès refusé: Aucun rôle assigné")
            
            if request.user.role.code not in allowed_roles:
                messages.error(request, f"Accès refusé. Rôle requis: {', '.join(allowed_roles)}")
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.ACTION_DATA_ACCESS,
                    level=AuditLog.LEVEL_WARNING,
                    resource=view_func.__name__,
                    details={'reason': 'insufficient_role', 'required_roles': list(allowed_roles)},
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return HttpResponseForbidden("Accès refusé")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def permission_required(*permission_codes):
    """
    Décorateur pour vérifier les permissions spécifiques
    
    Usage:
        @permission_required('data.export', 'data.view')
        def export_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Vérifier chaque permission
            missing_permissions = []
            for perm_code in permission_codes:
                if not request.user.has_permission(perm_code):
                    missing_permissions.append(perm_code)
            
            if missing_permissions:
                messages.error(request, f"Permissions manquantes: {', '.join(missing_permissions)}")
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.ACTION_DATA_ACCESS,
                    level=AuditLog.LEVEL_WARNING,
                    resource=view_func.__name__,
                    details={'reason': 'missing_permissions', 'required': list(permission_codes)},
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return HttpResponseForbidden("Accès refusé: Permissions insuffisantes")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def api_token_required(view_func):
    """
    Décorateur pour les endpoints API nécessitant un token
    
    Usage:
        @api_token_required
        def api_endpoint(request):
            # request.api_user contient l'utilisateur authentifié par token
            ...
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Récupérer le token depuis le header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Token manquant ou format invalide'}, status=401)
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            user = User.objects.get(api_token=token, is_active=True)
            
            # Vérifier le rate limit (simple)
            # TODO: Implémenter un vrai rate limiting avec Redis
            
            # Ajouter l'utilisateur à la requête
            request.api_user = user
            
            # Log de l'appel API
            AuditLog.objects.create(
                user=user,
                action=AuditLog.ACTION_API_CALL,
                level=AuditLog.LEVEL_INFO,
                resource=view_func.__name__,
                details={'endpoint': request.path},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return view_func(request, *args, **kwargs)
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'Token invalide'}, status=401)
    
    return wrapped_view


def audit_action(action_type, resource_name=None):
    """
    Décorateur pour logger automatiquement une action
    
    Usage:
        @audit_action(AuditLog.ACTION_DATA_EXPORT, 'BRVM Data')
        def export_brvm_data(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            result = view_func(request, *args, **kwargs)
            
            # Déterminer le niveau en fonction du résultat
            if hasattr(result, 'status_code'):
                if result.status_code >= 500:
                    level = AuditLog.LEVEL_ERROR
                elif result.status_code >= 400:
                    level = AuditLog.LEVEL_WARNING
                else:
                    level = AuditLog.LEVEL_INFO
            else:
                level = AuditLog.LEVEL_INFO
            
            # Créer le log d'audit
            user = getattr(request, 'api_user', request.user if request.user.is_authenticated else None)
            
            AuditLog.objects.create(
                user=user,
                action=action_type,
                level=level,
                resource=resource_name or view_func.__name__,
                details={
                    'view': view_func.__name__,
                    'method': request.method,
                    'path': request.path
                },
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return result
        return wrapped_view
    return decorator


def source_access_required(source_code):
    """
    Décorateur pour vérifier l'accès à une source de données spécifique
    
    Usage:
        @source_access_required('BRVM')
        def brvm_data_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Vérifier l'accès à la source
            from .models import DataSourceAccess
            has_access = DataSourceAccess.objects.filter(
                user=request.user,
                source=source_code,
                can_read=True
            ).exists()
            
            if not has_access and not request.user.is_superuser:
                messages.error(request, f"Accès refusé à la source: {source_code}")
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.ACTION_DATA_ACCESS,
                    level=AuditLog.LEVEL_WARNING,
                    resource=f"Source: {source_code}",
                    details={'reason': 'source_access_denied'},
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return HttpResponseForbidden(f"Accès refusé à la source: {source_code}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def get_client_ip(request):
    """Utilitaire pour récupérer l'IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
