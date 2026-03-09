# Script pour vérifier la consécutivité des semaines et la validité des closes
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = client["centralisation_db"]

symbols = db.prices_weekly.distinct("symbol")

print("\n=== DIAGNOSTIC CONSÉCUTIVITÉ & CLOSES ===\n")
problèmes = []
for symbol in sorted(symbols):
    docs = list(db.prices_weekly.find({"symbol": symbol}).sort("week", -1).limit(9))
    if len(docs) < 9:
        print(f"⚠️  {symbol}: Moins de 9 semaines (trouvé {len(docs)})")
        problèmes.append(symbol)
        continue
    weeks = [d.get("week") for d in docs]
    closes = [d.get("close") for d in docs]
    # Vérifier closes
    invalid_close = [i for i, c in enumerate(closes) if c in (None, 0)]
    if invalid_close:
        print(f"⚠️  {symbol}: closes invalides aux positions {invalid_close} (valeurs: {[closes[i] for i in invalid_close]})")
        problèmes.append(symbol)
    # Vérifier consécutivité
    try:
        week_dates = [datetime.strptime(w, "%Y-W%V") for w in weeks if w]
        deltas = [(week_dates[i] - week_dates[i+1]).days for i in range(len(week_dates)-1)]
        if any(d != 7 for d in deltas):
            print(f"⚠️  {symbol}: semaines non consécutives (deltas: {deltas})")
            problèmes.append(symbol)
    except Exception as e:
        print(f"⚠️  {symbol}: erreur parsing semaine ({e})")
        problèmes.append(symbol)
    if not invalid_close and (not problèmes or symbol not in problèmes):
        print(f"✅ {symbol}: closes valides et semaines consécutives")

if not problèmes:
    print("\nAucun problème détecté : toutes les actions ont closes valides et semaines consécutives.")
else:
    print(f"\n{len(problèmes)} actions avec problème de closes ou de consécutivité.")
