"""
Test direct is_dead_week() sans import du pipeline (évite setup Django)
"""
from pymongo import MongoClient

def is_dead_week_v2(week_data):
    """Version corrigée: filtre sur RANGE au lieu de variation%"""
    # Volume nul = marché fermé
    if week_data.get('volume', 0) == 0:
        return True
    
    # Prix complètement bloqués (zero range)
    high = week_data.get('high', 0)
    low = week_data.get('low', 0)
    close = week_data.get('close', 0)
    
    if high == low:  # Range = 0 → marché vraiment mort
        return True    
    # Range insignifiant (< 0.5% du prix)
    if close > 0:
        range_pct = ((high - low) / close) * 100
        if range_pct < 0.5:  # Moins de 0.5% de range
            return True
    
    return False

print("TEST is_dead_week() CORRIGÉ\n")

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Test sur 2026-W06
recent = list(db.prices_weekly.find({'week': '2026-W06'}))

print(f"Semaine 2026-W06: {len(recent)} observations\n")

active_count = 0
dead_count = 0

print("Échantillon (10 actions):\n")

for i, obs in enumerate(recent[:10], 1):
    sym = obs['symbol']
    h = obs.get('high', 0)
    l = obs.get('low', 0)
    c = obs.get('close', 0)
    vol = obs.get('volume', 0)
    
    range_pct = ((h - l) / c * 100) if c > 0 else 0
    
    is_dead = is_dead_week_v2(obs)
    
    if is_dead:
        dead_count += 1
        status = "❌ DEAD"
    else:
        active_count += 1
        status = "✅ ACTIVE"
    
    print(f"{i:2}. {sym:8} | Vol={vol:>8,} Range={range_pct:>5.2f}% | {status}")

# Stats totales
total_active = sum(1 for obs in recent if not is_dead_week_v2(obs))
total_dead = len(recent) - total_active

print(f"\nSTATS TOTALES (2026-W06):")
print(f"  Total: {len(recent)}")
print(f"  ACTIVE: {total_active} ({total_active/len(recent)*100:.1f}%)")
print(f"  DEAD: {total_dead} ({total_dead/len(recent)*100:.1f}%)")

# Test calcul ATR manuel sur SNTS
print("\n" + "="*70)
print("TEST CALCUL ATR MANUEL - SNTS")
print("="*70)

hist_snts = list(db.prices_weekly.find({'symbol': 'SNTS'}).sort('week', 1))

print(f"\nHistorique SNTS: {len(hist_snts)} semaines\n")

for i, w in enumerate(hist_snts, 1):
    h = w.get('high', 0)
    l = w.get('low', 0)
    c = w.get('close', 0)
    vol = w.get('volume', 0)
    
    range_pct = ((h - l) / c * 100) if c > 0 else 0
    
    is_dead = is_dead_week_v2(w)
    status = "DEAD" if is_dead else "ACTIVE"
    
    print(f"{i:2}. {w['week']} | C={c:>6.0f} H={h:>6.0f} L={l:>6.0f} Range={range_pct:>5.2f}% Vol={vol:>8,} | {status}")

# Filtrer actives
active_weeks = [w for w in hist_snts if not is_dead_week_v2(w)]

print(f"\nSemaines ACTIVES: {len(active_weeks)}/{len(hist_snts)}")

if len(active_weeks) >= 6:
    print("\n🔥 Calcul ATR(5) manuel:")
    
    # Calcul TR
    true_ranges = []
    for i in range(1, len(active_weeks)):
        h = active_weeks[i].get('high', 0)
        l = active_weeks[i].get('low', 0)
        prev_c = active_weeks[i-1].get('close', 0)
        
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        true_ranges.append(tr)
        print(f"  TR[{i}]: {tr:.2f}")
    
    if len(true_ranges) >= 5:
        atr_5 = sum(true_ranges[-5:]) / 5
        current_price = active_weeks[-1].get('close', 0)
        
        if current_price > 0:
            atr_pct = (atr_5 / current_price) * 100
            
            print(f"\n  ATR(5): {atr_5:.2f} FCFA")
            print(f"  Prix actuel: {current_price:.0f} FCFA")
            print(f"  ATR%: {atr_pct:.2f}%")
            
            if 6 <= atr_pct <= 25:
                print(f"\n  ✅ ATR TRADABLE (6-25%)")
                
                stop = max(atr_pct * 1.0, 4.0)
                target = atr_pct * 2.6
                rr = target / stop
                
                print(f"  Stop: {stop:.2f}%")
                print(f"  Target: {target:.2f}%")
                print(f"  Risk/Reward: {rr:.2f}")
            elif atr_pct < 6:
                print(f"\n  ⚠️ ATR trop faible (< 6%)")
            else:
                print(f"\n  ⚠️ ATR trop élevé (> 25%)")
    else:
        print(f"\n❌ Seulement {len(true_ranges)} TR (besoin 5)")
else:
    print(f"\n❌ Seulement {len(active_weeks)} semaines actives (besoin 6)")

print("\n" + "="*70)
