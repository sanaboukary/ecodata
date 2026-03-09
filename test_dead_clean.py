from pymongo import MongoClient

print("="*70)
print("TEST is_dead_week() CORRIGE - Sans emojis")
print("="*70)

client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
db = client['centralisation_db']

# Stats 2026-W06
all_obs = list(db.prices_weekly.find({'week': '2026-W06'}))

print(f"\n2026-W06: {len(all_obs)} observations")

active = 0
dead_vol0 = 0
dead_range0 = 0
dead_range_low = 0

print("\nEchantillon (premiere 10):")
for i, o in enumerate(all_obs[:10], 1):
    sym = o['symbol']
    v = o.get('volume', 0)
    high = o.get('high', 0)
    low = o.get('low', 0)
    close = o.get('close', 0)
    
    rng_pct = ((high - low) / close) * 100 if close > 0 else 0
    
    status = ""
    if v == 0:
        status = "DEAD(vol=0)"
        dead_vol0 += 1
    elif high == low:
        status = "DEAD(range=0)"
        dead_range0 += 1
    elif rng_pct < 0.5:
        status = "DEAD(range<0.5)"
        dead_range_low += 1
    else:
        status = "ACTIVE"
        active += 1
    
    print(f"  {i:2}. {sym:8} Vol={v:>8,} Range={rng_pct:>5.2f}% {status}")

# Compter sur tout
total_active = 0
total_dead_vol = 0
total_dead_range = 0
total_dead_low = 0

for o in all_obs:
    v = o.get('volume', 0)
    high = o.get('high', 0)
    low = o.get('low', 0)
    close = o.get('close', 0)
    
    if v == 0:
        total_dead_vol += 1
    elif high == low:
        total_dead_range += 1
    elif close > 0:
        rng_pct = ((high - low) / close) * 100
        if rng_pct < 0.5:
            total_dead_low += 1
        else:
            total_active += 1

print(f"\nRESULTATS COMPLETS:")
print(f"  ACTIVE (range >= 0.5%): {total_active}/{len(all_obs)} ({total_active/len(all_obs)*100:.1f}%)")
print(f"  DEAD - Volume=0: {total_dead_vol} ({total_dead_vol/len(all_obs)*100:.1f}%)")
print(f"  DEAD - Range=0: {total_dead_range}")
print(f"  DEAD - Range<0.5%: {total_dead_low}")
print(f"  DEAD TOTAL: {total_dead_vol+total_dead_range+total_dead_low} ({(total_dead_vol+total_dead_range+total_dead_low)/len(all_obs)*100:.1f}%)")

# Test ATR sur SNTS
print("\n" + "="*70)
print("TEST ATR - SNTS")
print("="*70)

snts_hist = list(db.prices_weekly.find({'symbol': 'SNTS'}).sort('week', 1))
print(f"\nHistorique: {len(snts_hist)} semaines\n")

active_weeks = []
for i, w in enumerate(snts_hist, 1):
    h = w.get('high', 0)
    l = w.get('low', 0)
    c = w.get('close', 0)
    v = w.get('volume', 0)
    
    rng_pct = ((h - l) / c * 100) if c > 0 else 0
    
    is_dead = (v == 0) or (h == l) or (rng_pct < 0.5)
    status = "DEAD" if is_dead else "ACTIVE"
    
    print(f"  {i:2}. {w['week']} C={c:>6.0f} Range={rng_pct:>5.2f}% Vol={v:>8,} {status}")
    
    if not is_dead:
        active_weeks.append(w)

print(f"\nSemaines actives: {len(active_weeks)}/{len(snts_hist)}")

if len(active_weeks) >= 6:
    print("\nCalcul ATR(5) manuel:")
    
    trs = []
    for i in range(1, len(active_weeks)):
        h = active_weeks[i]['high']
        l = active_weeks[i]['low']
        prev_c = active_weeks[i-1]['close']
        
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    
    if len(trs) >= 5:
        atr5 = sum(trs[-5:]) / 5
        price = active_weeks[-1]['close']
        atr_pct = (atr5 / price) * 100
        
        print(f"  ATR(5): {atr5:.2f} FCFA")
        print(f"  Prix: {price:.0f} FCFA")
        print(f"  ATR%: {atr_pct:.2f}%")
        
        if 6 <= atr_pct <= 25:
            print(f"\n  >> ATR TRADABLE (6-25%)")
            stop = max(atr_pct, 4.0)
            target = atr_pct * 2.6
            rr = target / stop
            print(f"  Stop: {stop:.2f}% | Target: {target:.2f}% | RR: {rr:.2f}")
        else:
            print(f"\n  >> ATR hors range")
else:
    print(f"\nPas assez de semaines actives ({len(active_weeks)}/6)")

print("\n" + "="*70)
