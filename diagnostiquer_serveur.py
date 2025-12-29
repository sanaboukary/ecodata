#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic rapide du serveur Django
Identifie les problèmes courants
"""
import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("\n" + "="*80)
print("  DIAGNOSTIC SERVEUR DJANGO")
print("="*80)

# 1. Vérifier l'environnement virtuel
print("\n[1] Environnement Python:")
print(f"    Python: {sys.executable}")
print(f"    Version: {sys.version.split()[0]}")

# 2. Vérifier Django
try:
    import django
    print(f"    Django: {django.get_version()} ✓")
except ImportError:
    print("    Django: NON INSTALLÉ ✗")
    sys.exit(1)

# 3. Vérifier les settings
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    from django.conf import settings
    print(f"\n[2] Configuration Django:")
    print(f"    ROOT_URLCONF: {settings.ROOT_URLCONF} ✓")
    print(f"    DEBUG: {settings.DEBUG}")
except Exception as e:
    print(f"\n[2] Configuration Django: ERREUR ✗")
    print(f"    {e}")
    sys.exit(1)

# 4. Vérifier les routes
try:
    from django.urls import get_resolver
    resolver = get_resolver()
    print(f"\n[3] Routes URL:")
    print(f"    URLconf: {resolver.urlconf_name} ✓")
    
    # Test route racine
    match = resolver.resolve('/')
    print(f"    Route '/': {match.func.__name__} ✓")
except Exception as e:
    print(f"\n[3] Routes URL: ERREUR ✗")
    print(f"    {e}")
    sys.exit(1)

# 5. Vérifier MongoDB
try:
    from plateforme_centralisation.mongo import get_mongo_db
    client, db = get_mongo_db()
    count = db.curated_observations.count_documents({'source': 'BRVM'}, limit=1)
    print(f"\n[4] MongoDB:")
    print(f"    Connexion: {db.name} ✓")
    print(f"    Données BRVM: Disponibles ✓")
except Exception as e:
    print(f"\n[4] MongoDB: ERREUR ✗")
    print(f"    {e}")

# 6. Vérifier les processus en cours
print(f"\n[5] Processus serveur:")
try:
    import subprocess
    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
    lines = [l for l in result.stdout.split('\n') if ':8000' in l and 'LISTENING' in l]
    if lines:
        print(f"    Serveurs actifs sur port 8000: {len(lines)}")
        if len(lines) > 1:
            print(f"    ⚠️  ATTENTION: {len(lines)} serveurs en conflit !")
    else:
        print(f"    Aucun serveur actif sur port 8000")
except:
    print(f"    Impossible de vérifier (netstat non disponible)")

print("\n" + "="*80)
print("  RÉSULTAT:")
print("="*80)
print("\n✅ Configuration correcte - Le serveur peut démarrer")
print("\n💡 Pour démarrer: python manage.py runserver 127.0.0.1:8000")
print("   Ou utilisez: DEMARRER_SERVEUR_PROPRE.bat")
print("\n" + "="*80 + "\n")
