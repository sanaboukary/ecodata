#!/usr/bin/env python
"""Script pour démarrer le serveur Django"""
import os
import sys

# Ajouter le répertoire du projet au path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

# Démarrer le serveur
if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    print("=" * 60)
    print("🚀 Démarrage du serveur Django - Marketplace BRVM")
    print("=" * 60)
    print("📍 URL: http://127.0.0.1:8000/")
    print("📊 Marketplace: http://127.0.0.1:8000/marketplace/")
    print("=" * 60)
    execute_from_command_line(['manage.py', 'runserver'])
