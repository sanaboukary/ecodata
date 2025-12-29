#!/usr/bin/env python
"""
Guide interactif pour visualiser les publications BRVM
"""
print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   PUBLICATIONS BRVM - GUIDE D'ACCÈS                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ DONNÉES ENREGISTRÉES EN BASE : 164 publications

📊 DISTRIBUTION :
   • 98 Communiqués (divers types)
   • 30 Rapports Sociétés
   • 26 Bulletins Officiels
   • 10 Autres

═══════════════════════════════════════════════════════════════════════════════

🌐 ACCÈS WEB - 3 FAÇONS :

1️⃣  PAGE COMPLÈTE (Interface visuelle)
   ═══════════════════════════════════════════════════════════════════════════
   URL: http://localhost:8000/dashboard/brvm/publications/
   
   Affiche toutes les publications avec :
   • Filtrage par type (communiqués, rapports, bulletins)
   • Filtrage par date
   • Export CSV/JSON
   • Téléchargement PDF direct
   
   Filtres disponibles :
   • Tous les communiqués: ?type=COMMUNIQUE
   • Rapports sociétés: ?type=RAPPORT_SOCIETE
   • Bulletins officiels: ?type=BULLETIN_OFFICIEL
   • Résultats financiers: ?type=COMMUNIQUE_RESULTATS
   • Nominations: ?type=COMMUNIQUE_NOMINATION
   
   Exemple complet :
   http://localhost:8000/dashboard/brvm/publications/?type=COMMUNIQUE&limit=200

═══════════════════════════════════════════════════════════════════════════════

2️⃣  API JSON (Pour développeurs)
   ═══════════════════════════════════════════════════════════════════════════
   URL: http://localhost:8000/api/brvm/publications/
   
   Retourne JSON :
   {
     "results": [
       {
         "title": "NSIA BANQUE CI : Communiqué...",
         "date": "2025-12-04T13:04:37Z",
         "url": "https://www.brvm.org/fr/...",
         "type": "COMMUNIQUE",
         "category": "Communiqué",
         "emetteur": "BRVM"
       },
       ...
     ],
     "total": 98
   }
   
   Paramètres :
   • ?limit=100 (nombre de résultats)
   • ?type=COMMUNIQUE (filtre par type)
   • ?since=2025-12-01 (depuis une date)
   
   Exemple :
   http://localhost:8000/api/brvm/publications/?type=COMMUNIQUE&limit=50

═══════════════════════════════════════════════════════════════════════════════

3️⃣  EXPORT DONNÉES (CSV/JSON)
   ═══════════════════════════════════════════════════════════════════════════
   CSV : http://localhost:8000/api/brvm/publications/export/?format=csv
   JSON: http://localhost:8000/api/brvm/publications/export/?format=json
   
   Avec filtres :
   http://localhost:8000/api/brvm/publications/export/?format=csv&type=COMMUNIQUE

═══════════════════════════════════════════════════════════════════════════════

🔧 VÉRIFICATIONS :

1. Serveur Django en cours ? 
   Test : curl http://localhost:8000/api/brvm/publications/?limit=1
   
2. Voir les logs :
   Terminal où vous avez lancé : python manage.py runserver
   
3. Rafraîchir la page :
   Ctrl + F5 (rafraîchissement forcé)

═══════════════════════════════════════════════════════════════════════════════

📱 LIENS RAPIDES :

🏠 Page principale publications :
   http://localhost:8000/dashboard/brvm/publications/

📣 Tous les communiqués (98) :
   http://localhost:8000/dashboard/brvm/publications/?type=COMMUNIQUE&limit=200

🏢 Rapports sociétés (30) :
   http://localhost:8000/dashboard/brvm/publications/?type=RAPPORT_SOCIETE

📄 Bulletins officiels (26) :
   http://localhost:8000/dashboard/brvm/publications/?type=BULLETIN_OFFICIEL

💼 Résultats financiers (43) :
   http://localhost:8000/dashboard/brvm/publications/?type=COMMUNIQUE_RESULTATS

👔 Nominations (9) :
   http://localhost:8000/dashboard/brvm/publications/?type=COMMUNIQUE_NOMINATION

🎯 Assemblées générales (5) :
   http://localhost:8000/dashboard/brvm/publications/?type=COMMUNIQUE_AG

═══════════════════════════════════════════════════════════════════════════════

✅ TOUT EST PRÊT !

Les 98 communiqués et 30 rapports sont dans la base et accessibles via l'interface web.

Ouvrez simplement : http://localhost:8000/dashboard/brvm/publications/

╚══════════════════════════════════════════════════════════════════════════════╝
""")

# Test automatique
import subprocess
import sys

print("\n🧪 Test automatique de connexion...")
print("=" * 80)

try:
    result = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:8000/api/brvm/publications/?limit=1'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    status = result.stdout.strip()
    
    if status == '200':
        print("✅ Serveur Django ACTIF et API fonctionnelle")
        print()
        print("🎯 Ouvrez maintenant:")
        print("   http://localhost:8000/dashboard/brvm/publications/")
    else:
        print(f"⚠️  Status: {status}")
        print()
        print("💡 Démarrer le serveur:")
        print("   python manage.py runserver")
except Exception as e:
    print("⚠️  Impossible de tester (curl non disponible ou serveur éteint)")
    print()
    print("💡 Pour démarrer le serveur:")
    print("   python manage.py runserver")

print("=" * 80)
