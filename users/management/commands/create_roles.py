# -*- coding: utf-8 -*-
"""
Commande pour créer les rôles et utilisateurs de test
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile


class Command(BaseCommand):
    help = 'Crée les rôles et utilisateurs de test pour la plateforme BRVM'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("CRÉATION DES UTILISATEURS DE TEST")
        self.stdout.write("="*60 + "\n")
        
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@brvm-platform.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'Système',
                'role': 'ADMIN',
                'is_superuser': True,
                'is_staff': True,
            },
            {
                'username': 'analyste',
                'email': 'analyste@brvm-platform.com',
                'password': 'analyste123',
                'first_name': 'Jean',
                'last_name': 'Kouassi',
                'role': 'ANALYST',
                'company': 'SGI Afrique',
                'position': 'Ingénieur Financier',
            },
            {
                'username': 'investisseur',
                'email': 'investisseur@brvm-platform.com',
                'password': 'investisseur123',
                'first_name': 'Fatou',
                'last_name': 'Diallo',
                'role': 'INVESTOR',
                'company': 'Fonds Capital CI',
                'position': 'Gestionnaire de Portefeuille',
            },
            {
                'username': 'lecteur',
                'email': 'lecteur@brvm-platform.com',
                'password': 'lecteur123',
                'first_name': 'Ahmed',
                'last_name': 'Traoré',
                'role': 'READER',
                'company': 'Particulier',
                'position': 'Étudiant Finance',
            },
        ]
        
        for user_data in users_data:
            username = user_data['username']
            
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Utilisateur '{username}' existe déjà")
                )
                continue
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_superuser=user_data.get('is_superuser', False),
                is_staff=user_data.get('is_staff', False),
            )
            
            # Configurer le profil
            profile = user.profile
            profile.role = user_data['role']
            profile.company = user_data.get('company', '')
            profile.position = user_data.get('position', '')
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ {username} créé ({user_data['role']}) - "
                    f"Mot de passe: {user_data['password']}"
                )
            )
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("RÉSUMÉ DES ACCÈS PAR RÔLE")
        self.stdout.write("="*60 + "\n")
        
        from users.permissions import ROLE_PERMISSIONS
        
        for role, config in ROLE_PERMISSIONS.items():
            self.stdout.write(f"\n{config['name']} ({role}):")
            permissions = config['permissions']
            for perm in permissions:
                self.stdout.write(f"  • {perm}")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("CONNEXION")
        self.stdout.write("="*60)
        self.stdout.write("\nUtilisez ces identifiants pour vous connecter:")
        self.stdout.write("\n• Admin:        admin / admin123")
        self.stdout.write("• Analyste:     analyste / analyste123")
        self.stdout.write("• Investisseur: investisseur / investisseur123")
        self.stdout.write("• Lecteur:      lecteur / lecteur123\n")
