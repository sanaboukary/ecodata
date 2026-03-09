from pymongo import MongoClient

print("="*70)
print("TEST RAPIDE is_dead_week() CORRIGÉ")
print("="*70)

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    db = client['centralisation_db']
    
    # Prendre UNE observation
    obs = db.prices_weekly.find_one({'week': '2026-W06', 'symbol': 'SNTS'})
    
    if not obs:
        print("Aucune obs SNTS trouvée, essai autre action...")
        obs = db.prices_weekly.find_one({'week': '2026-W06'})
    
    print(f"\nAction: {obs['symbol']}")
    print(f"Week: {obs['week']}")
    
    h = obs.get('high', 0)
    l = obs.get('low', 0)
    c = obs.get('close', 0)
    vol = obs.get('volume', 0)
    
    print(f"\nDonnées:")
    print(f"  High: {h}")
    print(f"  Low: {l}")
    print(f"  Close: {c}")
    print(f"  Volume: {vol}")
    
    # Test nouveau filtre
    print(f"\nTest filtre:")
    
    if vol == 0:
        print("  ❌ DEAD - Volume = 0")
    elif h == l:
        print("  ❌ DEAD - Range = 0 (high == low)")
    elif c > 0:
        range_pct = ((h - l) / c) * 100
        print(f"  Range%: {range_pct:.2f}%")
        
        if range_pct < 0.5:
            print("  ❌ DEAD - Range < 0.5%")
        else:
            print("  ✅ ACTIVE - Range >= 0.5%")
    
    # Stats globales
    print("\n" + "-"*70)
    print("STATS 2026-W06")
    print("-"*70)
    
    all_obs = list(db.prices_weekly.find({'week': '2026-W06'}))
    print(f"\nTotal: {len(all_obs)} observations")
    
    active = 0
    dead_vol0 = 0
    dead_range0 = 0
    dead_range_low = 0
    
    for o in all_obs:
        v = o.get('volume', 0)
        high = o.get('high', 0)
        low = o.get('low', 0)
        close = o.get('close', 0)
        
        if v == 0:
            dead_vol0 += 1
        elif high == low:
            dead_range0 += 1
        elif close > 0:
            rng_pct = ((high - low) / close) * 100
            if rng_pct < 0.5:
                dead_range_low += 1
            else:
                active += 1
    
    print(f"\nRésultats:")
    print(f"  ✅ ACTIVE (range ≥ 0.5%): {active} ({active/len(all_obs)*100:.1f}%)")
    print(f"  ❌ DEAD - Volume=0: {dead_vol0}")
    print(f"  ❌ DEAD - Range=0: {dead_range0}")
    print(f"  ❌ DEAD - Range<0.5%: {dead_range_low}")
    print(f"  ❌ DEAD TOTAL: {dead_vol0+dead_range0+dead_range_low} ({(dead_vol0+dead_range0+dead_range_low)/len(all_obs)*100:.1f}%)")
    
    print("\n" + "="*70)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
