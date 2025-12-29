#!/usr/bin/env python3
"""Vérification rapide données BRVM"""

import os
import sys
import io
import django

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

print("\n" + "="*80)
print("🔍 DIAGNOSTIC DONNÉES BRVM 60 JOURS")
print("="*80)
print()

client, db = get_mongo_db()

# 1. Total BRVM
total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
print(f"📊 Total observations BRVM: {total_brvm:,}")

# 2. Par qualité
real_manual = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': 'REAL_MANUAL'
})

real_scraper = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': 'REAL_SCRAPER'
})

unknown = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': 'UNKNOWN'
})

print(f"   REAL_MANUAL:  {real_manual:,}")
print(f"   REAL_SCRAPER: {real_scraper:,}")
print(f"   UNKNOWN:      {unknown:,}")
print()

# 3. Actions distinctes
actions = db.curated_observations.distinct('key', {'source': 'BRVM'})
print(f"📈 Actions distinctes: {len(actions)}")
print(f"   Exemples: {', '.join(actions[:5])}")
print()

# 4. Plage de dates
pipeline = [
    {'$match': {'source': 'BRVM'}},
    {'$group': {
        '_id': None,
        'min_date': {'$min': '$ts'},
        'max_date': {'$max': '$ts'}
    }}
]

dates = list(db.curated_observations.aggregate(pipeline))

if dates and dates[0]['min_date']:
    print(f"📅 Plage dates:")
    print(f"   Première: {dates[0]['min_date']}")
    print(f"   Dernière: {dates[0]['max_date']}")
    
    # Calculer jours
    from datetime import datetime
    debut = datetime.fromisoformat(dates[0]['min_date'].replace('Z', '+00:00'))
    fin = datetime.fromisoformat(dates[0]['max_date'].replace('Z', '+00:00'))
    jours = (fin - debut).days
    print(f"   Durée: {jours} jours")
print()

# 5. Test ECOC
print("🔍 TEST ACTION ECOC.BC:")

ecoc = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': 'ECOC.BC'
}).sort('ts', -1).limit(5))

print(f"   Total points: {len(ecoc)}")

if ecoc:
    print(f"   5 derniers:")
    for obs in ecoc[:5]:
        quality = obs.get('attrs', {}).get('data_quality', 'N/A')
        print(f"     {obs['ts']}: {obs['value']:>10,.0f} FCFA ({quality})")
else:
    print(f"   ❌ AUCUNE DONNÉE ECOC.BC TROUVÉE !")
print()

# 6. Vérifier prix > 0
prix_zero = db.curated_observations.count_documents({
    'source': 'BRVM',
    'value': 0
})

prix_valides = db.curated_observations.count_documents({
    'source': 'BRVM',
    'value': {'$gt': 0}
})

print(f"💰 Validation prix:")
print(f"   Prix > 0: {prix_valides:,}")
print(f"   Prix = 0: {prix_zero:,}")
print()

# 7. Échantillon données
print("📋 ÉCHANTILLON (3 actions × 3 points):")
for action in actions[:3]:
    samples = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': action
    }).sort('ts', -1).limit(3))
    
    if samples:
        print(f"\n   {action}:")
        for s in samples:
            quality = s.get('attrs', {}).get('data_quality', 'N/A')
            print(f"     {s['ts']}: {s['value']:>10,.0f} FCFA ({quality})")

print()

# DIAGNOSTIC
print("="*80)
print("📊 DIAGNOSTIC")
print("="*80)
print()

if total_brvm == 0:
    print("❌ PROBLÈME MAJEUR: Aucune donnée BRVM dans MongoDB !")
    print()
    print("SOLUTION:")
    print("  1. Ré-importer CSV 60 jours:")
    print("     python collecter_csv_automatique.py")
    print()
    print("  2. Ou scraper site BRVM:")
    print("     python scripts/connectors/brvm_scraper_production.py")
    print()
    
elif prix_zero > total_brvm * 0.5:
    print("⚠️  PROBLÈME: Plus de 50% des prix sont à 0")
    print()
    print("CAUSE PROBABLE: Données mal importées ou corrompues")
    print()
    print("SOLUTION:")
    print("  1. Purger données invalides:")
    print("     python purger_prix_zero.py")
    print()
    print("  2. Ré-importer données valides:")
    print("     python collecter_csv_automatique.py")
    print()
    
elif len(actions) < 10:
    print("⚠️  ATTENTION: Seulement", len(actions), "actions trouvées (attendu: 40+)")
    print()
    print("SOLUTION: Importer plus d'actions")
    print()
    
elif real_manual + real_scraper < total_brvm * 0.5:
    print("⚠️  ATTENTION: Moins de 50% de données RÉELLES")
    print(f"   ({real_manual + real_scraper:,} / {total_brvm:,})")
    print()
    print("SOLUTION: Purger données UNKNOWN et ré-importer")
    print()
    
else:
    print("✅ DONNÉES BRVM DISPONIBLES")
    print()
    print(f"   {total_brvm:,} observations")
    print(f"   {len(actions)} actions")
    print(f"   {(real_manual + real_scraper) / total_brvm * 100:.1f}% données réelles")
    print()
    print("PROCHAINE ÉTAPE:")
    print("  python generer_recommandations_hebdo.py")
    print()

client.close()

print("="*80)
print()
