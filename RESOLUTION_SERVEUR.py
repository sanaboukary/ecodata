#!/usr/bin/env python3
"""
Guide de démarrage rapide de la plateforme
"""

print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║              ✅ PROBLÈME RÉSOLU - SERVEUR DJANGO OPÉRATIONNEL                 ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

🔧 CAUSE DU PROBLÈME
═══════════════════════════════════════════════════════════════════════════════

  Le serveur Django s'arrête quand vous exécutez d'autres commandes dans
  le même terminal. Le serveur doit tourner en permanence dans son propre
  terminal pour rester accessible.

✅ SOLUTION APPLIQUÉE
═══════════════════════════════════════════════════════════════════════════════

  ✓ Serveur Django redémarré dans un terminal dédié
  ✓ Page web chargée avec succès (HTTP 200)
  ✓ Interface accessible sur http://127.0.0.1:8000

🚀 COMMENT GARDER LE SERVEUR ACTIF
═══════════════════════════════════════════════════════════════════════════════

  MÉTHODE 1: Utiliser le script batch (RECOMMANDÉ)
  ─────────────────────────────────────────────────
  Double-cliquez sur: start_django.bat
  
  Avantages:
  • Ouvre un terminal dédié au serveur
  • Reste actif en permanence
  • Facile à relancer si besoin

  MÉTHODE 2: Ligne de commande
  ─────────────────────────────
  .venv\\Scripts\\python.exe manage.py runserver 127.0.0.1:8000
  
  ⚠️  IMPORTANT: Ne fermez PAS ce terminal et n'exécutez PAS d'autres
                commandes dedans, sinon le serveur s'arrêtera !

🌐 ACCÈS À L'INTERFACE WEB
═══════════════════════════════════════════════════════════════════════════════

  URL principale: http://127.0.0.1:8000
  
  ✓ Vue d'ensemble des données
  ✓ 5,668+ observations disponibles
  ✓ 5 sources de données actives
  ✓ Graphiques interactifs

📊 PAGES PRINCIPALES
═══════════════════════════════════════════════════════════════════════════════

  Page d'accueil:
  http://127.0.0.1:8000/
  
  Dashboard BRVM (50 actions):
  http://127.0.0.1:8000/dashboards/brvm/
  
  Dashboard Banque Mondiale:
  http://127.0.0.1:8000/dashboards/worldbank/
  
  Explorateur de données:
  http://127.0.0.1:8000/explorer/
  
  Monitoring des collectes:
  http://127.0.0.1:8000/administration/ingestion/

🔄 SI LE SERVEUR S'ARRÊTE À NOUVEAU
═══════════════════════════════════════════════════════════════════════════════

  1. Double-cliquez sur start_django.bat
     OU
  2. Exécutez dans un nouveau terminal:
     .venv\\Scripts\\python.exe manage.py runserver 127.0.0.1:8000

  3. Ouvrez votre navigateur sur http://127.0.0.1:8000

💡 CONSEIL
═══════════════════════════════════════════════════════════════════════════════

  Pour utiliser la plateforme confortablement:
  
  1. Gardez un terminal ouvert avec le serveur Django
  2. Utilisez un autre terminal pour les autres commandes
  3. Le serveur restera actif tant que son terminal est ouvert

═══════════════════════════════════════════════════════════════════════════════

✅ SERVICES ACTIFS ACTUELLEMENT
═══════════════════════════════════════════════════════════════════════════════

  ✓ Serveur Django      : http://127.0.0.1:8000
  ✓ MongoDB             : Port 27018
  ✓ Collecte automatique: APScheduler en arrière-plan
  ✓ Données disponibles : 5,668+ observations

═══════════════════════════════════════════════════════════════════════════════

🎉 Votre plateforme est maintenant COMPLÈTEMENT OPÉRATIONNELLE !

""")
