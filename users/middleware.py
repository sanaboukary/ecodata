# -*- coding: utf-8 -*-
"""
Middleware pour gérer les accès et logs
"""

from django.shortcuts import redirect
from django.urls import reverse
from .models import AccessLog
from .permissions import can_access_page


class RoleBasedAccessMiddleware:
    """Middleware pour contrôler l'accès basé sur les rôles"""
    
    # Pages exemptées de vérification
    EXEMPT_PATHS = [
        '/login/',
        '/logout/',
        '/register/',
        '/access-denied/',
        '/static/',
        '/media/',
        '/admin/login/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier si la page est exemptée
        path = request.path
        if any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS):
            return self.get_response(request)
        
        # Laisser passer si utilisateur non authentifié (géré par @login_required)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Vérifier l'accès
        if not can_access_page(request.user, path):
            # Logger l'accès refusé
            AccessLog.objects.create(
                user=request.user,
                page_path=path,
                method=request.method,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                access_granted=False
            )
            return redirect('access_denied')
        
        # Logger l'accès autorisé
        AccessLog.objects.create(
            user=request.user,
            page_path=path,
            method=request.method,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            access_granted=True
        )
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
