from pymongo import MongoClient
db = MongoClient('mongodb://localhost:27017').centralisation_db

print("\n" + "="*95)
print("                              DONNÉES BRVM COLLECTÉES")
print("="*95 + "\n")

# Total
total = db.curated_observations.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
print(f"📊 Total observations BRVM : {total}\n")

# Actions uniques (sans les clés avec timestamp)
actions_seen = set()
resultats = []

for obs in db.curated_observations.find({'source': 'BRVM', 'dataset': 'STOCK_PRICE'}).sort('timestamp', -1).limit(100):
    key = obs.get('key', '')
    
    # Skip anciennes clés avec timestamp
    if '_2026' in key or '_2025' in key or len(key) > 10:
        continue
    
    if key not in actions_seen and len(actions_seen) < 60:
        actions_seen.add(key)
        attrs = obs.get('attrs', {})
        resultats.append({
            'symbole': key,
            'nom': (attrs.get('nom', 'N/A') or 'N/A')[:22],
            'cours': attrs.get('cours', obs.get('value', 0)) or 0,
            'variation': attrs.get('variation_pct', 0) or 0,
            'volume': attrs.get('volume', 0) or 0,
            'ouverture': attrs.get('ouverture', 0) or 0,
            'haut': attrs.get('haut', 0) or 0,
            'bas': attrs.get('bas', 0) or 0,
            'precedent': attrs.get('precedent', 0) or 0
        })

print(f"📈 Actions collectées : {len(resultats)}\n")
print(f"{'SYM':<8} {'NOM':<24} {'COURS':>10} {'VAR%':>8} {'VOLUME':>10} {'OUV':>10} {'HAUT':>10} {'BAS':>10}")
print("-"*95)

for r in sorted(resultats, key=lambda x: x['symbole']):
    print(f"{r['symbole']:<8} {r['nom']:<24} {r['cours']:>10,.2f} {r['variation']:>7.2f}% "
          f"{r['volume']:>10,} {r['ouverture']:>10,.2f} {r['haut']:>10,.2f} {r['bas']:>10,.2f}")

print("\n" + "="*95 + "\n")
