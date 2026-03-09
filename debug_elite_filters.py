"""
Debug ELITE filters - Voir pourquoi aucune action n'a passé
"""
from pymongo import MongoClient
import numpy as np
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Semaine précédente (comme decision_finale_brvm.py)
week_ago = datetime.now() - timedelta(days=7)
semaine = week_ago.strftime("%Y-W%V")
print(f"=== DEBUG FILTRES ELITE - {semaine} ===\n")

# Charger prices_weekly
prices = list(db.prices_weekly.find({'week': semaine}))
print(f"📊 {len(prices)} actions disponibles\n")

if not prices:
    print("❌ Aucune donnée prices_weekly pour cette semaine")
    exit()

# Calculer percentiles
rs_values = [p.get('rs_4_weeks', 0) for p in prices if p.get('rs_4_weeks') is not None]
vol_values = [p.get('volume_spike', 0) for p in prices if p.get('volume_spike') is not None]
accel_values = [p.get('acceleration', 0) for p in prices if p.get('acceleration') is not None]
atr_values = [p.get('atr_pct', 0) for p in prices if p.get('atr_pct') is not None]

rs_p75 = np.percentile(rs_values, 75) if rs_values else 0
vol_p30 = np.percentile(vol_values, 30) if vol_values else 0

print("🎯 SEUILS CALCULÉS:")
print(f"   RS P75: {rs_p75:.2f}%")
print(f"   Volume Spike P30: {vol_p30:.2f}%")
print(f"   Acceleration: 2.0% (seuil fixe)")
print(f"   ATR: 8-30% (seuil fixe)")
print()

# Compter combien passent chaque filtre
rs_pass = sum(1 for p in prices if p.get('rs_4_weeks', 0) >= rs_p75)
vol_pass = sum(1 for p in prices if p.get('volume_spike', 0) >= vol_p30)
accel_pass = sum(1 for p in prices if p.get('acceleration', 0) >= 2.0)
atr_pass = sum(1 for p in prices if 8 <= p.get('atr_pct', 0) <= 30)

print("📈 COMBIEN PASSENT CHAQUE FILTRE:")
print(f"   Filtre 1 - RS≥{rs_p75:.1f}%: {rs_pass}/{len(prices)} actions")
print(f"   Filtre 2 - Vol≥{vol_p30:.1f}%: {vol_pass}/{len(prices)} actions")
print(f"   Filtre 3 - Accel≥2%: {accel_pass}/{len(prices)} actions")
print(f"   Filtre 4 - ATR 8-30%: {atr_pass}/{len(prices)} actions")
print()

# Trouver actions qui passent le plus de filtres
actions_scores = []
for p in prices:
    score = 0
    details = []
    
    if p.get('rs_4_weeks', 0) >= rs_p75:
        score += 1
        details.append("RS✓")
    else:
        details.append(f"RS✗{p.get('rs_4_weeks', 0):.1f}")
    
    if p.get('volume_spike', 0) >= vol_p30:
        score += 1
        details.append("Vol✓")
    else:
        details.append(f"Vol✗{p.get('volume_spike', 0):.1f}")
    
    if p.get('acceleration', 0) >= 2.0:
        score += 1
        details.append("Acc✓")
    else:
        details.append(f"Acc✗{p.get('acceleration', 0):.1f}")
    
    if 8 <= p.get('atr_pct', 0) <= 30:
        score += 1
        details.append("ATR✓")
    else:
        details.append(f"ATR✗{p.get('atr_pct', 0):.1f}")
    
    actions_scores.append((p['symbol'], score, details, p.get('rs_4_weeks', 0)))

# Trier par nombre de filtres passés
actions_scores.sort(key=lambda x: (x[1], x[3]), reverse=True)

print("🏆 TOP 10 ACTIONS (par nombre de filtres passés):")
print()
for symbol, score, details, rs in actions_scores[:10]:
    status = "✅ PASSE TOUT" if score == 4 else f"❌ {score}/4 filtres"
    print(f"{symbol:8} {status:20} RS={rs:6.1f}%  {' '.join(details)}")

print()
print("💡 ANALYSE:")
if actions_scores[0][1] == 4:
    print(f"   ✅ {sum(1 for a in actions_scores if a[1] == 4)} action(s) passent les 4 filtres de base")
    print("   ⚠️  Peut-être que les filtres 5-6 (breakout, autre) sont trop stricts")
else:
    print(f"   ❌ Aucune action ne passe les 4 filtres de base")
    print(f"   📊 Meilleur score: {actions_scores[0][1]}/4 filtres ({actions_scores[0][0]})")
    print()
    print("   🔍 Suggestion: MODE_ELITE_MINIMALISTE peut être trop strict pour ce marché")
    print("      → Considérer System 1 (TOP5 ENGINE) qui utilise seulement RS ranking")
    print("      → Ou V2 (formule simple 4 facteurs)")
