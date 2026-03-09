"""Test ultra-simple des données hebdomadaires"""
from pymongo import MongoClient

c = MongoClient('mongodb://localhost:27017/')
db = c.centralisation_db

print("="*70)
print("TEST RAPIDE DONNÉES HEBDOMADAIRES")
print("="*70)
print()

test_actions = ['BICC', 'SGBC', 'ABJC']

for ticker in test_actions:
    # Vérifier données hebdomadaires
    weekly = list(db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        'granularite': 'WEEKLY',
        'ticker': ticker
    }).sort('timestamp', 1))
    
    print(f"{ticker}: {len(weekly)} semaines")
    
    if len(weekly) >= 5:
        # Afficher quelques exemples
        for i, w in enumerate(weekly[:3]):
            close = w.get('close', 0)
            week = w.get('week', 'N/A')
            print(f"  Semaine {i+1}: {week}, Close={close:.0f} FCFA")
        
        # Extraire tous les prix
        prices = [w.get('close') or w.get('prix') for w in weekly]
        prices = [p for p in prices if p and p > 0]
        
        if prices:
            print(f"  → Total prix valides: {len(prices)}")
            print(f"  → Premier: {prices[0]:.0f}, Dernier: {prices[-1]:.0f}")
            var = ((prices[-1] - prices[0]) / prices[0]) * 100
            print(f"  → Variation totale: {var:+.1f}%")
        else:
            print(f"  ✗ Aucun prix valide trouvé")
    else:
        print(f"  ✗ Pas assez de semaines")
    print()

c.close()
