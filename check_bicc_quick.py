from pymongo import MongoClient

db = MongoClient()['centralisation_db']

print("\n=== PRIX BICC ===")
bicc = list(db.prices_weekly.find({'symbol': 'BICC'}).sort('week', -1).limit(3))
for d in bicc:
    print(f"{d.get('week')} | Close: {d.get('close', 0)} FCFA")

dec = db.decisions_finales_brvm.find_one(sort=[('date_decision', -1)])
if dec:
    print(f"\nDate dernière décision: {dec.get('date_decision')}")
    recos = dec.get('recommandations', [])
    bicc_r = next((r for r in recos if r.get('symbol') == 'BICC'), None)
    if bicc_r:
        print(f"BICC prix_entree: {bicc_r.get('prix_entree')} FCFA")
