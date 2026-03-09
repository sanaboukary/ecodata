"""
AUDIT EXPERT BRUTAL - Sans complaisance
Vérifie pourquoi la plateforme ne produit AUCUNE recommandation
"""
import sys
from pymongo import MongoClient
from datetime import datetime, timedelta

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("AUDIT BRUTAL PLATEFORME BRVM")
print("="*80)

# 1. DONNÉES WEEKLY
print("\n1️⃣ DONNÉES HEBDOMADAIRES")
weekly = list(db.prices_weekly.find().sort("week", -1).limit(500))
print(f"Total observations weekly: {len(weekly)}")

if len(weekly) == 0:
    print("❌ PROBLÈME FATAL: AUCUNE DONNÉE WEEKLY")
    sys.exit(1)

# 2. ANALYSE SEMAINE RÉCENTE
latest_week = weekly[0]['week']
print(f"\nSemaine la plus récente: {latest_week}")

recent = [w for w in weekly if w['week'] == latest_week]
print(f"Observations pour {latest_week}: {len(recent)}")

# 3. QUALITÉ DES DONNÉES
print("\n2️⃣ QUALITÉ DES DONNÉES (ÉCHANTILLON 5 ACTIONS)")
for obs in recent[:5]:
    symbol = obs.get('symbol', 'UNKNOWN')
    print(f"\n{symbol}:")
    print(f"  Prix: O={obs.get('open', 0)} H={obs.get('high', 0)} L={obs.get('low', 0)} C={obs.get('close', 0)}")
    print(f"  Volume: {obs.get('volume', 0)}")
    print(f"  Variation: {obs.get('variation', 0):.2f}%")
    
    # Test is_dead_week
    is_dead = False
    if obs.get('volume', 0) == 0:
        is_dead = True
        print("  ⚠️ DEAD: volume = 0")
    elif obs.get('high', 0) == obs.get('low', 0) == obs.get('close', 0):
        is_dead = True
        print("  ⚠️ DEAD: prix bloqués (H=L=C)")
    elif abs(obs.get('variation', 0)) < 0.1:
        is_dead = True
        print("  ⚠️ DEAD: variation < 0.1%")
    
    if not is_dead:
        print("  ✅ SEMAINE ACTIVE")

# 4. TEST CALCUL ATR MANUEL
print("\n3️⃣ TEST CALCUL ATR (5 SEMAINES)")

# Prendre une action avec données
test_symbol = recent[0]['symbol']
print(f"\nAction test: {test_symbol}")

# Récupérer historique 10 semaines
hist = list(db.prices_weekly.find(
    {"symbol": test_symbol}
).sort("week", -1).limit(10))

print(f"Semaines disponibles: {len(hist)}")

if len(hist) >= 6:
    # Inverser pour avoir ordre chronologique
    hist = sorted(hist, key=lambda x: x['week'])
    
    print("\nHistorique:")
    for i, w in enumerate(hist):
        vol = w.get('volume', 0)
        var = w.get('variation', 0)
        h = w.get('high', 0)
        l = w.get('low', 0)
        c = w.get('close', 0)
        
        dead = ""
        if vol == 0:
            dead = "DEAD(vol=0)"
        elif h == l == c:
            dead = "DEAD(bloqué)"
        elif abs(var) < 0.1:
            dead = "DEAD(var<0.1)"
        
        print(f"  {i}: {w['week']} | C={c} H={h} L={l} Vol={vol:,} Var={var:.2f}% {dead}")
    
    # Filtrer semaines actives
    active = [w for w in hist if not (
        w.get('volume', 0) == 0 or
        (w.get('high', 0) == w.get('low', 0) == w.get('close', 0)) or
        abs(w.get('variation', 0)) < 0.1
    )]
    
    print(f"\nSemaines ACTIVES: {len(active)}/{len(hist)}")
    
    if len(active) >= 6:
        print("\nCalcul ATR manuel:")
        
        true_ranges = []
        for i in range(1, len(active)):
            h = active[i].get('high', 0)
            l = active[i].get('low', 0)
            prev_c = active[i-1].get('close', 0)
            
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            true_ranges.append(tr)
            print(f"  TR[{i}]: {tr:.2f} (H={h} L={l} PrevC={prev_c})")
        
        if len(true_ranges) >= 5:
            atr_5 = sum(true_ranges[-5:]) / 5
            current_price = active[-1].get('close', 0)
            atr_pct = (atr_5 / current_price) * 100
            
            print(f"\n  ATR(5): {atr_5:.2f}")
            print(f"  Prix actuel: {current_price}")
            print(f"  ATR%: {atr_pct:.2f}%")
            
            if 6 <= atr_pct <= 25:
                print(f"  ✅ ATR TRADABLE (6-25%)")
                
                # Calcul stop/target
                stop = max(atr_pct * 1.0, 4.0)
                target = atr_pct * 2.6
                rr = target / stop
                
                print(f"\n  Stop: {stop:.2f}%")
                print(f"  Target: {target:.2f}%")
                print(f"  RR: {rr:.2f}")
            else:
                print(f"  ❌ ATR HORS RANGE (attendu 6-25%)")
        else:
            print(f"\n❌ Seulement {len(true_ranges)} TR calculés (besoin 5)")
    else:
        print(f"\n❌ Seulement {len(active)} semaines actives (besoin 6)")
else:
    print(f"❌ Seulement {len(hist)} semaines (besoin 6 minimum)")

# 5. COMPTAGE ATR DANS DB
print("\n4️⃣ ATR ACTUELS DANS LA BASE")
with_atr = db.prices_weekly.count_documents({"atr_pct": {"$gt": 0}})
total = db.prices_weekly.count_documents({})
print(f"Observations avec ATR > 0: {with_atr}/{total} ({with_atr/total*100:.1f}%)")

if with_atr > 0:
    atr_sample = list(db.prices_weekly.find(
        {"atr_pct": {"$gt": 0}}
    ).limit(5))
    
    print("\nÉchantillon ATR existants:")
    for obs in atr_sample:
        print(f"  {obs['symbol']}: ATR={obs.get('atr_pct', 0):.2f}%")
else:
    print("❌ AUCUN ATR CALCULÉ DANS LA BASE")

# 6. DÉCISIONS EXPERT
print("\n5️⃣ RECOMMANDATIONS GÉNÉRÉES")
decisions = list(db.decisions_brvm_weekly.find().sort("week", -1).limit(10))
print(f"Décisions EXPERT dans DB: {len(decisions)}")

if len(decisions) > 0:
    print("\nDernières recommandations:")
    for d in decisions[:5]:
        print(f"  {d.get('week')} | {d.get('symbol')} | Classe {d.get('classe')} | WOS={d.get('wos', 0):.1f} RR={d.get('risk_reward', 0):.2f}")
else:
    print("❌ AUCUNE RECOMMANDATION GÉNÉRÉE")

# DIAGNOSTIC FINAL
print("\n"+"="*80)
print("DIAGNOSTIC FINAL")
print("="*80)

problems = []
if total == 0:
    problems.append("FATAL: Aucune donnée weekly")
elif with_atr == 0:
    problems.append("CRITIQUE: ATR = 0 pour toutes les observations")
    problems.append("Cause probable: is_dead_week() filtre TOUT ou données manquantes")
elif len(decisions) == 0:
    problems.append("BLOQUANT: Moteur expert ne produit aucune recommandation")

if problems:
    print("\n❌ PROBLÈMES IDENTIFIÉS:")
    for i, p in enumerate(problems, 1):
        print(f"  {i}. {p}")
else:
    print("\n✅ PLATEFORME OPÉRATIONNELLE")
    
print("\n" + "="*80)
