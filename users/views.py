# -*- coding: utf-8 -*-
"""
Vues simplifiées pour l'authentification - Système 4 rôles
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .permissions import get_user_role, ROLE_PERMISSIONS


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
            
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Identifiants incorrects')
    
    return render(request, 'users/login.html')


def quick_login_view(request):
    """Page de connexion rapide pour tester les 4 rôles"""
    if request.method == 'POST':
        role_code = request.POST.get('role')
        
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


@login_required
def profile_view(request):
    """Page de profil utilisateur"""
    role = get_user_role(request.user)
    permissions = ROLE_PERMISSIONS.get(role, {}).get('permissions', [])
    
    return render(request, 'users/profile.html', {
        'role': role,
        'role_name': ROLE_PERMISSIONS.get(role, {}).get('name', 'Inconnu'),
        'permissions': permissions
    })


# Redirections pour compatibilité avec l'ancien système
@login_required
def admin_dashboard(request):
    return redirect('dashboard:home')


@login_required
def engineer_dashboard(request):
    return redirect('dashboard:home')


def generate_api_token_view(request):
    return redirect('dashboard:home')


def enable_mfa_view(request):
    return redirect('dashboard:home')


def verify_mfa_setup_view(request):
    return redirect('dashboard:home')
