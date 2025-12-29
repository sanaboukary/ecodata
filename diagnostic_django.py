#!/usr/bin/env python
"""
Script de diagnostic Django - Vérifie pourquoi les URLs ne fonctionnent pas
"""
import os
import sys

# Configuration
os.chdir(r"E:\DISQUE C\Desktop\Implementation plateforme")
sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

print("=" * 80)
print("DIAGNOSTIC DJANGO - CONFIGURATION URLs")
print("=" * 80)
print()

# Import Django
try:
    import django
    django.setup()
    print("✅ Django importé et configuré")
except Exception as e:
    print(f"❌ Erreur import Django: {e}")
    sys.exit(1)

# Vérifier settings
from django.conf import settings
print(f"\n📋 SETTINGS MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"📋 ROOT_URLCONF: {settings.ROOT_URLCONF}")
print(f"📋 DEBUG: {settings.DEBUG}")
print(f"📋 ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

# Vérifier si le module URLs existe
print(f"\n🔍 Vérification du module URLs...")
try:
    import plateforme_centralisation.urls
    print(f"✅ Module {settings.ROOT_URLCONF} trouvé")
    print(f"   Fichier: {plateforme_centralisation.urls.__file__}")
except ImportError as e:
    print(f"❌ Impossible d'importer {settings.ROOT_URLCONF}: {e}")
    sys.exit(1)

# Lister les URLs
print(f"\n📍 URLs CONFIGURÉES:")
from django.urls import get_resolver
resolver = get_resolver()

def list_urls(lis, acc=''):
    for entry in lis:
        if hasattr(entry, 'url_patterns'):
            list_urls(entry.url_patterns, acc + str(entry.pattern))
        else:
            print(f"   {acc}{entry.pattern} → {entry.callback.__name__ if hasattr(entry.callback, '__name__') else entry.callback}")

list_urls(resolver.url_patterns)

# Vérifier la vue index
print(f"\n🎯 Vérification de la vue INDEX:")
try:
    from dashboard import views
    if hasattr(views, 'index'):
        print(f"✅ Fonction views.index trouvée")
        print(f"   Fichier: {views.__file__}")
        print(f"   Fonction: {views.index}")
    else:
        print(f"❌ Fonction views.index NOT FOUND")
except Exception as e:
    print(f"❌ Erreur import dashboard.views: {e}")

# Test de résolution d'URL
print(f"\n🧪 TEST DE RÉSOLUTION D'URL '/':")
try:
    from django.urls import resolve
    match = resolve('/')
    print(f"✅ URL '/' résolue:")
    print(f"   Vue: {match.func}")
    print(f"   Nom: {match.url_name}")
    print(f"   App: {match.app_name}")
except Exception as e:
    print(f"❌ Impossible de résoudre URL '/': {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC TERMINÉ")
print("=" * 80)
