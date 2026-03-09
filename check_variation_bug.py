"""
Vérifier pourquoi variation_pct = 0.00% pour toutes les observations
"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("VÉRIFICATION VARIATION_PCT BUG\n")

# Prendre 10 observations au hasard
sample = list(db.prices_weekly.find({'week': '2026-W06'}).limit(10))

print(f"Échantillon de {len(sample)} observations (2026-W06):\n")

for obs in sample:
    sym = obs['symbol']
    o = obs.get('open', 0)
    h = obs.get('high', 0)
    l = obs.get('low', 0)
    c = obs.get('close', 0)
    var = obs.get('variation_pct', 0)
    
    # Recalculer variation
    if o > 0:
        var_calc = ((c - o) / o) * 100
    else:
        var_calc = 0
    
    print(f"{sym}:")
    print(f"  OHLC: O={o} H={h} L={l} C={c}")
    print(f"  Variation DB: {var:.2f}%")
    print(f"  Variation recalculée: {var_calc:.2f}%")
    print(f"  Match: {'✅' if abs(var - var_calc) < 0.01 else '❌'}")
    print()

# Vérifier si 'variation_pct' existe ou si c'est 'variation'
print("\nCHAMPS DISPONIBLES dans prices_weekly:")
if sample:
    print(list(sample[0].keys()))
