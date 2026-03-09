"""Test rapide de l'analyse technique hebdomadaire"""
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("="*70)
print("TEST ANALYSE TECHNIQUE HEBDOMADAIRE")
print("="*70)
print()

_,db = get_mongo_db()

# Test sur quelques actions
test_actions = ['BICC', 'SGBC', 'ABJC', 'ETIT', 'BOAM']

for ticker in test_actions:
    # Vérifier données hebdomadaires
    weekly_data = list(db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        'granularite': 'WEEKLY',
        'ticker': ticker
    }).sort('timestamp', 1))
    
    print(f"{ticker:6s}: {len(weekly_data):2d} semaines")
    
    if len(weekly_data) >= 14:
        # Extraire les prix close
        prices = [d.get('close') or d.get('prix_cloture') or d.get('prix') for d in weekly_data]
        prices = [p for p in prices if p and p > 0]
        
        if len(prices) >= 14:
            print(f"  → Prix: {prices[0]:.0f} → {prices[-1]:.0f} FCFA")
            print(f"  → Variation: {((prices[-1]-prices[0])/prices[0]*100):.1f}%")
            print(f"  ✓ PRÊT pour analyse technique")
        else:
            print(f"  ✗ Pas assez de prix valides: {len(prices)}")
    else:
        print(f"  ✗ Pas assez de semaines: {len(weekly_data)}")
    print()

print("="*70)
print("RÉSUMÉ")
print("="*70)

# Compter total prêt
total_ready = 0
for ticker in db.curated_observations.distinct('ticker', {'granularite': 'WEEKLY'}):
    count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'granularite': 'WEEKLY',
        'ticker': ticker
    })
    if count >= 14:
        total_ready += 1

print(f"✓ {total_ready} actions prêtes pour analyse technique hebdomadaire")
print()
