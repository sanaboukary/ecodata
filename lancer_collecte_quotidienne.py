#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplifié pour lancer la collecte quotidienne BRVM
Stratégies : Scraping → Saisie manuelle → AUCUNE COLLECTE
"""

import os
import sys
from datetime import datetime

print("=" * 80)
print("🚀 COLLECTE QUOTIDIENNE BRVM - DONNÉES RÉELLES UNIQUEMENT")
print("=" * 80)
print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

try:
    import django
    django.setup()
    print("✓ Django configuré")
except Exception as e:
    print(f"❌ Erreur Django : {e}")
    sys.exit(1)

try:
    from plateforme_centralisation.mongo import get_mongo_db
    client, db = get_mongo_db()
    print("✓ Connexion MongoDB établie")
except Exception as e:
    print(f"❌ Erreur MongoDB : {e}")
    sys.exit(1)

# === DIAGNOSTIC RAPIDE ===
print("\n" + "=" * 80)
print("📊 DIAGNOSTIC RAPIDE")
print("=" * 80)

date_aujourdhui = datetime.now().strftime('%Y-%m-%d')

# Compter observations BRVM du jour
obs_aujourdhui = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': date_aujourdhui,
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

# Compter total observations BRVM
obs_total = db.curated_observations.count_documents({'source': 'BRVM'})

# Compter observations réelles
obs_reelles = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

# Actions distinctes
actions_distinctes = len(db.curated_observations.distinct('key', {'source': 'BRVM'}))

print(f"  Observations aujourd'hui ({date_aujourdhui}): {obs_aujourdhui}")
print(f"  Observations BRVM totales: {obs_total:,}")
print(f"  Observations réelles: {obs_reelles:,} ({obs_reelles/max(obs_total, 1)*100:.1f}%)")
print(f"  Actions distinctes: {actions_distinctes}")

# Vérifier si collecte déjà faite
if obs_aujourdhui >= 40:
    print(f"\n✅ Collecte déjà effectuée aujourd'hui ({obs_aujourdhui} cours)")
    print("   Aucune action nécessaire.")
    sys.exit(0)

# === COLLECTE ===
print("\n" + "=" * 80)
print("🔄 LANCEMENT DE LA COLLECTE")
print("=" * 80)

collecte_reussie = False
methode_utilisee = None

# STRATÉGIE 1 : Scraping site BRVM
print("\n1️⃣ Tentative scraping site BRVM...")
try:
    from scripts.connectors.brvm_scraper_production import scraper_brvm_officiel
    
    cours_scrapes = scraper_brvm_officiel()
    
    if cours_scrapes and len(cours_scrapes) > 0:
        print(f"   ✅ Scraping réussi : {len(cours_scrapes)} cours récupérés")
        
        # Sauvegarder dans MongoDB
        from scripts.mongo_utils import upsert_observations
        
        observations = []
        for cours in cours_scrapes:
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': cours.get('symbol'),
                'ts': date_aujourdhui,
                'value': cours.get('last_price', 0),
                'attrs': {
                    **cours,
                    'data_quality': 'REAL_SCRAPER'
                }
            }
            observations.append(obs)
        
        # Connexion sans Django ORM
        count = upsert_observations(observations)
        
        print(f"   ✅ {count} observations sauvegardées dans MongoDB")
        collecte_reussie = True
        methode_utilisee = "SCRAPING"
    else:
        print("   ⚠️  Scraping n'a retourné aucune donnée")
        
except ImportError as e:
    print(f"   ⚠️  Module scraper non disponible : {e}")
except Exception as e:
    print(f"   ❌ Erreur scraping : {e}")

# STRATÉGIE 2 : Vérifier saisie manuelle
if not collecte_reussie:
    print("\n2️⃣ Vérification saisie manuelle...")
    
    obs_manuelles = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date_aujourdhui,
        'attrs.data_quality': 'REAL_MANUAL'
    })
    
    if obs_manuelles >= 40:
        print(f"   ✅ {obs_manuelles} cours saisis manuellement trouvés")
        collecte_reussie = True
        methode_utilisee = "SAISIE_MANUELLE"
    else:
        print(f"   ⚠️  Seulement {obs_manuelles} cours manuels en base")

# === RÉSULTAT ===
print("\n" + "=" * 80)
print("📋 RÉSULTAT DE LA COLLECTE")
print("=" * 80)

if collecte_reussie:
    # Recompter
    obs_finales = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date_aujourdhui,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    
    print(f"✅ COLLECTE RÉUSSIE")
    print(f"   Méthode : {methode_utilisee}")
    print(f"   Observations du jour : {obs_finales}")
    print(f"   Date : {date_aujourdhui}")
    
else:
    print("🔴 AUCUNE DONNÉE N'A ÉTÉ AJOUTÉE")
    print("\n💡 Actions possibles :")
    print("   1. Vérifier l'accès au site BRVM : https://www.brvm.org")
    print("   2. Exécuter manuellement : python mettre_a_jour_cours_brvm.py")
    print("   3. Importer depuis CSV : python collecter_csv_automatique.py")
    print("   4. Ré-essayer plus tard")
    print("\n⚠️  Le système n'ajoute JAMAIS de données estimées ou simulées")

print("\n" + "=" * 80)
print(f"Fin de la collecte : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
