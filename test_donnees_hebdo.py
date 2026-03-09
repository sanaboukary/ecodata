from pymongo import MongoClient

c = MongoClient('mongodb://localhost:27017/')
db = c.centralisation_db

actions = ['BICC', 'SGBC', 'SLBC', 'ABJC', 'BOAM', 'ETIT', 'NTLC', 'BOAS']

print("="*70)
print("TEST DONNÉES HEBDOMADAIRES PAR ACTION")
print("="*70)
print()

for a in actions:
    count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'granularite': 'WEEKLY',
        'ticker': a
    })
    
    weeks = sorted(db.curated_observations.distinct('week', {
        'dataset': 'STOCK_PRICE',
        'granularite': 'WEEKLY',
        'ticker': a
    }))
    
    if weeks:
        print(f"{a:6s}: {count:2d} semaines - {weeks[0]} à {weeks[-1]}")
    else:
        print(f"{a:6s}: {count:2d} semaines - AUCUNE DONNÉE")

print()
print("MINIMUM REQUIS POUR ANALYSE TECHNIQUE: 14 semaines")
print()

# Compter combien d'actions ont >= 14 semaines
ready = 0
for a in db.curated_observations.distinct('ticker', {'granularite': 'WEEKLY'}):
    count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'granularite': 'WEEKLY',
        'ticker': a
    })
    if count >= 14:
        ready += 1

print(f"Actions prêtes pour analyse (>= 14 sem): {ready}")

c.close()
