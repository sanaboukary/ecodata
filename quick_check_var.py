from pymongo import MongoClient

c = MongoClient('mongodb://localhost:27017/')
db = c['centralisation_db']

obs = db.prices_weekly.find_one({'week': '2026-W06'})

print("Symbol:", obs['symbol'])
print("OHLC:")
print("  Open:", obs.get('open'))
print("  High:", obs.get('high'))
print("  Low:", obs.get('low'))
print("  Close:", obs.get('close'))
print("\nVariations:")
print("  variation:", obs.get('variation', 'N/A'))
print("  variation_pct:", obs.get('variation_pct', 'N/A'))

print("\nTous les champs:", list(obs.keys()))

# Recalculer
o = obs.get('open', 0)
c_price = obs.get('close', 0)
if o > 0:
    var_calc = ((c_price - o) / o) * 100
    print(f"\nVariation recalculée: {var_calc:.2f}%")
