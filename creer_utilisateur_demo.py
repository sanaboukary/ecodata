#!/usr/bin/env python
"""
Script pour créer un utilisateur de démonstration
Utilisateur: demo
Mot de passe: brvm2025
"""
import os
import sys
import django

# Configuration Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from users.models import User

def create_demo_user():
    """Créer l'utilisateur de démonstration"""
    username = 'demo'
    password = 'brvm2025'
    email = 'demo@brvm.org'
    
    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username=username).exists():
        print(f"✅ L'utilisateur '{username}' existe déjà")
        user = User.objects.get(username=username)
        # Mettre à jour le mot de passe au cas où
        user.set_password(password)
        user.save()
        print(f"🔄 Mot de passe mis à jour")
    else:
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Démo',
            last_name='BRVM'
        )
        print(f"✅ Utilisateur '{username}' créé avec succès")
    
    print(f"""
╔══════════════════════════════════════════╗
║   COMPTE DE DÉMONSTRATION BRVM           ║
╠══════════════════════════════════════════╣
║  Nom d'utilisateur : {username:<20s} ║
║  Mot de passe      : {password:<20s} ║
║  Email             : {email:<20s} ║
╚══════════════════════════════════════════╝
""")

if __name__ == '__main__':
    create_demo_user()
