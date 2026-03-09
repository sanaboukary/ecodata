# Script de diagnostic : Vérifie l'historique de prix weekly pour chaque action
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["centralisation_db"]

symbols = db.prices_weekly.distinct("symbol")

print("\n=== DIAGNOSTIC HISTORIQUE PRICES_WEEKLY ===\n")
problèmes = []
for symbol in sorted(symbols):
    docs = list(db.prices_weekly.find({"symbol": symbol}).sort("week", -1))
    n = len(docs)
    n_valid = sum(1 for d in docs if d.get("close") not in (None, 0))
    if n < 9:
        print(f"⚠️  {symbol}: Seulement {n} semaines de données (besoin 9 min)")
        problèmes.append(symbol)
    elif n_valid < 9:
        print(f"⚠️  {symbol}: {n_valid}/9 semaines avec close valide (close manquant ou nul)")
        problèmes.append(symbol)
    else:
        print(f"✅ {symbol}: {n} semaines, {n_valid} closes valides")

if not problèmes:
    print("\nAucun problème détecté : toutes les actions ont un historique suffisant.")
else:
    print(f"\n{len(problèmes)} actions avec historique insuffisant ou données manquantes.")
