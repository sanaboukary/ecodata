from pymongo import MongoClient

client = MongoClient()

# Vérifier brvm_db
print("=== BRVM_DB.top5_weekly_brvm ===")
top5_old = list(client['brvm_db'].top5_weekly_brvm.find().sort("rank", 1))
for t in top5_old:
    print(f"#{t.get('rank')} {t.get('symbol')} | Prix: {t.get('prix_entree')} FCFA")

# Vérifier centralisation_db
print("\n=== CENTRALISATION_DB.top5_weekly_brvm ===")
top5_new = list(client['centralisation_db'].top5_weekly_brvm.find().sort("rank", 1))
for t in top5_new:
    print(f"#{t.get('rank')} {t.get('symbol')} | Prix: {t.get('prix_entree')} FCFA")

# Vérifier decisions_finales_brvm
print("\n=== CENTRALISATION_DB.decisions_finales_brvm ===")
dec = client['centralisation_db'].decisions_finales_brvm.find_one(sort=[('date_decision', -1)])
if dec:
    print(f"Date: {dec.get('date_decision')}")
    for r in dec.get('recommandations', []):
        print(f"  {r.get('symbol')} | Prix: {r.get('prix_entree')} FCFA")
else:
    print("Aucune décision")
