"""
Vues pour l'authentification et la gestion des utilisateurs
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta

from .models import User, AuditLog, Role
from .decorators import get_client_ip, role_required
from .permissions import get_user_role, ROLE_PERMISSIONS


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Page de connexion simplifiée"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            role = get_user_role(user)
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
            
            # Redirection selon le rôle
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Identifiants incorrects')
    
    return render(request, 'users/login.html')


def quick_login_view(request):
    """Page de connexion rapide pour tester les 4 rôles"""
    if request.method == 'POST':
        role_code = request.POST.get('role')
        
        # Mapping rôle → username
        role_mapping = {
            'ADMIN': 'admin',
            'ANALYST': 'analyste',
            'INVESTOR': 'investisseur',
            'READER': 'lecteur',
        }
        
        username = role_mapping.get(role_code)
        if username:
            user = authenticate(request, username=username, password=f'{username}123')
            if user:
                login(request, user)
                messages.success(request, f'Connecté en tant que {ROLE_PERMISSIONS[role_code]["name"]}')
                return redirect('dashboard:home')
    
    return render(request, 'users/quick_login.html', {
        'roles': ROLE_PERMISSIONS
    })


def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, 'Vous êtes déconnecté')
    return redirect('users:login')


def access_denied_view(request):
    """Page d'accès refusé"""
    role = get_user_role(request.user) if request.user.is_authenticated else None
    return render(request, 'users/access_denied.html', {
        'role': role,
        'role_name': ROLE_PERMISSIONS.get(role, {}).get('name', 'Inconnu') if role else None
    })


# ANCIENNES VUES (conservées pour compatibilité)
@require_http_methods(["GET", "POST"])
def OLD_login_view(request):
    """ANCIENNE Page de connexion avec support MFA"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        mfa_token = request.POST.get('mfa_token', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Vérifier si le compte est verrouillé
            if user.is_account_locked():
                messages.error(request, 'Compte temporairement verrouillé. Réessayez plus tard.')
                return render(request, 'users/login.html')
            
            # Vérifier MFA si activé
            if user.mfa_enabled:
                if not mfa_token:
                    # Afficher le formulaire MFA
                    request.session['mfa_user_id'] = user.id
                    return render(request, 'users/login.html', {'show_mfa': True, 'username': username})
                
                # Vérifier le token MFA
                if not user.verify_mfa_token(mfa_token):
                    messages.error(request, 'Code MFA invalide')
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        user.lock_account(30)  # Verrouiller pour 30 minutes
                    user.save()
                    return render(request, 'users/login.html', {'show_mfa': True, 'username': username})
            
            # Connexion réussie
            user.failed_login_attempts = 0
            user.last_login_ip = get_client_ip(request)
            user.save()
            
            login(request, user)
            
            # Log d'audit
            AuditLog.objects.create(
                user=user,
                action=AuditLog.ACTION_LOGIN,
                level=AuditLog.LEVEL_INFO,
                details={'success': True},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Bienvenue, {user.get_full_name() or user.username}!')
            
            # Rediriger selon le rôle
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            if user.role:
                if user.role.code == Role.ADMIN_PLATFORM:
                    return redirect('users:admin_dashboard')
                elif user.role.code == Role.DATA_ENGINEER:
                    return redirect('users:engineer_dashboard')
                elif user.role.code == Role.ANALYST_ECONOMIST:
                    return redirect('dashboard:index')
                else:
                    return redirect('dashboard:index')
            
            return redirect('dashboard:index')
        else:
            # Authentification échouée
            try:
                user = User.objects.get(username=username)
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.lock_account(30)
                    messages.error(request, 'Trop de tentatives échouées. Compte verrouillé pour 30 minutes.')
                user.save()
            except User.DoesNotExist:
                pass
            
            # Log d'audit (désactivé temporairement - problème Djongo)
            # AuditLog.objects.create(
            #     action=AuditLog.ACTION_LOGIN,
            #     level=AuditLog.LEVEL_WARNING,
            #     details={'success': False, 'username': username},
            #     ip_address=get_client_ip(request),
            #     user_agent=request.META.get('HTTP_USER_AGENT', '')
            # )
            
            messages.error(request, 'Nom d\'utilisateur ou mot de passe invalide')
    
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    """Déconnexion de l'utilisateur"""
    # Log d'audit (désactivé temporairement - problème Djongo)
    # AuditLog.objects.create(
    #     user=request.user,
    #     action=AuditLog.ACTION_LOGOUT,
    #     level=AuditLog.LEVEL_INFO,
    #     ip_address=get_client_ip(request),
    #     user_agent=request.META.get('HTTP_USER_AGENT', '')
    # )
    
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès')
    return redirect('users:login')


@login_required
def profile_view(request):
    """Profil de l'utilisateur"""
    # Désactiver temporairement les logs récents (problème Djongo)
    # recent_logs = AuditLog.objects.filter(user=request.user)[:20]
    return render(request, 'users/profile.html', {
        'user': request.user,
        'permissions': request.user.get_permissions(),
        # 'recent_logs': recent_logs
    })


@login_required
@role_required(Role.ADMIN_PLATFORM)
def admin_dashboard(request):
    """Dashboard pour les administrateurs"""
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    # Statistiques utilisateurs
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    users_by_role = User.objects.values('role__name').annotate(count=Count('id'))
    
    # Activité récente (7 derniers jours)
    week_ago = timezone.now() - timedelta(days=7)
    recent_logins = AuditLog.objects.filter(
        action=AuditLog.ACTION_LOGIN,
        timestamp__gte=week_ago
    ).count()
    
    # Logs d'audit récents
    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:50]
    
    # Alertes de sécurité
    security_alerts = AuditLog.objects.filter(
        level__in=[AuditLog.LEVEL_WARNING, AuditLog.LEVEL_ERROR, AuditLog.LEVEL_CRITICAL],
        timestamp__gte=week_ago
    ).order_by('-timestamp')[:20]
    
    return render(request, 'users/admin_dashboard.html', {
        'total_users': total_users,
        'active_users': active_users,
        'users_by_role': users_by_role,
        'recent_logins': recent_logins,
        'recent_logs': recent_logs,
        'security_alerts': security_alerts,
    })


@login_required
@role_required(Role.DATA_ENGINEER)
def engineer_dashboard(request):
    """Dashboard pour les ingénieurs Data/ETL"""
    from plateforme_centralisation.mongo import get_mongo_db
    
    _, db = get_mongo_db()
    
    # Statistiques des ingestions
    recent_runs = list(db.ingestion_runs.find().sort('started_at', -1).limit(20))
    
    # Sources configurées
    sources = ['BRVM', 'WorldBank', 'IMF', 'UN_SDG', 'AfDB']
    source_stats = {}
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        source_stats[source] = count
    
    return render(request, 'users/engineer_dashboard.html', {
        'recent_runs': recent_runs,
        'source_stats': source_stats,
    })


@login_required
def generate_api_token_view(request):
    """Générer un nouveau token API"""
    if request.method == 'POST':
        if request.user.role and request.user.role.code == Role.API_CLIENT:
            token = request.user.generate_api_token()
            messages.success(request, 'Nouveau token API généré!')
            return render(request, 'users/api_token.html', {'token': token})
        else:
            messages.error(request, 'Seuls les clients API peuvent générer des tokens')
    
    return redirect('users:profile')


@login_required
def enable_mfa_view(request):
    """Activer l'authentification multi-facteurs"""
    if request.method == 'POST':
        if not request.user.mfa_enabled:
            import pyotp
            secret = request.user.regenerate_mfa_secret()
            totp = pyotp.TOTP(secret)
            qr_uri = totp.provisioning_uri(
                name=request.user.email,
                issuer_name='Plateforme Centralisation'
            )
            
            # Générer des codes de secours
            import secrets
            backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
            request.user.mfa_backup_codes = backup_codes
            request.user.save()
            
            return render(request, 'users/mfa_setup.html', {
                'secret': secret,
                'qr_uri': qr_uri,
                'backup_codes': backup_codes
            })
    
    return render(request, 'users/mfa_enable.html')


@login_required
def verify_mfa_setup_view(request):
    """Vérifier et finaliser l'activation MFA"""
    if request.method == 'POST':
        token = request.POST.get('token')
        if request.user.verify_mfa_token(token):
            request.user.mfa_enabled = True
            request.user.save()
            messages.success(request, 'MFA activé avec succès!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Code invalide. Veuillez réessayer.')
    
    return redirect('users:enable_mfa')
