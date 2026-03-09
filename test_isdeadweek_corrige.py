"""
TEST is_dead_week() CORRIGÉ - Utilise RANGE au lieu de variation%
"""
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from pymongo import MongoClient
from brvm_pipeline.pipeline_weekly import is_dead_week, calculate_atr_pct

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("TEST is_dead_week() CORRIGÉ (RANGE au lieu de variation%)")
print("="*80)

# Test sur 2026-W06
recent = list(db.prices_weekly.find({'week': '2026-W06'}))

print(f"\nSemaine 2026-W06: {len(recent)} observations\n")

dead_count = 0
active_count = 0

print("ÉCHANTILLON (10 premières actions):")
for i, obs in enumerate(recent[:10], 1):
    sym = obs['symbol']
    o = obs.get('open', 0)
    h = obs.get('high', 0)
    l = obs.get('low', 0)
    c = obs.get('close', 0)
    vol = obs.get('volume', 0)
    var_pct = obs.get('variation_pct', 0)
    
    # Calculer range%
    range_pct = ((h - l) / c * 100) if c > 0 else 0
    
    # Tester is_dead_week
    is_dead = is_dead_week(obs)
    
    if is_dead:
        dead_count += 1
        status = "❌ DEAD"
    else:
        active_count += 1
        status = "✅ ACTIVE"
    
    print(f"{i}. {sym:8} | Vol={vol:>8,} Range={range_pct:>5.2f}% Var={var_pct:>5.2f}% | {status}")

# Compter sur toute la semaine
total_dead = sum(1 for obs in recent if is_dead_week(obs))
total_active = len(recent) - total_dead

print(f"\nSTATS GLOBALES:")
print(f"  Total: {len(recent)}")
print(f"  ACTIVE: {total_active} ({total_active/len(recent)*100:.1f}%)")
print(f"  DEAD: {total_dead} ({total_dead/len(recent)*100:.1f}%)")

# Test calcul ATR sur une action active
print("\n" + "="*80)
print("TEST CALCUL ATR (action avec historique)")
print("="*80)

# Trouver une action avec données
test_actions = ['SNTS', 'UNLC', 'SIVC', 'ETIT', 'NEIC']

for test_sym in test_actions:
    hist = list(db.prices_weekly.find(
        {'symbol': test_sym}
    ).sort('week', -1).limit(10))
    
    if len(hist) < 6:
        continue
    
    # Inverser pour ordre chronologique
    hist = sorted(hist, key=lambda x: x['week'])
    
    print(f"\nAction: {test_sym} ({len(hist)} semaines)")
    
    # Filtrer semaines actives
    active = [w for w in hist if not is_dead_week(w)]
    
    print(f"Semaines actives: {len(active)}/{len(hist)}\n")
    
    # Afficher historique
    for i, w in enumerate(hist, 1):
        h = w.get('high', 0)
        l = w.get('low', 0)
        c = w.get('close', 0)
        vol = w.get('volume', 0)
        range_pct = ((h-l) / c * 100) if c > 0 else 0
        
        dead = "DEAD" if is_dead_week(w) else "ACTIVE"
        
        print(f"  {i}. {w['week']} | C={c:>6.0f} Range={range_pct:>5.2f}% Vol={vol:>8,} | {dead}")
    
    # Calcul ATR
    if len(active) >= 6:
        atr = calculate_atr_pct(active, period=5)
        print(f"\nATR(5): {atr}%")
        
        if atr and 6 <= atr <= 25:
            print(f"✅ ATR TRADABLE (6-25%)")
            
            # Stop/Target
            stop = max(atr * 1.0, 4.0)
            target = atr * 2.6
            rr = target / stop
            
            print(f"Stop: {stop:.2f}% | Target: {target:.2f}% | RR: {rr:.2f}")
        elif atr:
            print(f"⚠️ ATR hors range: {atr:.2f}% (attendu 6-25%)")
        else:
            print("❌ ATR = None")
    else:
        print(f"❌ Seulement {len(active)} semaines actives (besoin 6)")
    
    break  # Tester seulement la première action trouvée

print("\n" + "="*80)
