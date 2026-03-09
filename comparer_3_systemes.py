"""
Comparaison des 3 systèmes de recommandations
"""
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

print("\n" + "="*120)
print("COMPARAISON DES 3 SYSTÈMES DE RECOMMANDATIONS BRVM")
print("="*120 + "\n")

# SYSTÈME 1: TOP5 ENGINE
print("📊 SYSTÈME 1 : TOP5 ENGINE (Classement Surperformance)")
print("─" * 120)
top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))
if top5:
    regime_s1 = top5[0].get('market_regime', 'N/A')
    print(f"Régime détecté: {regime_s1}")
    print(f"Recommandations: {len(top5)}\n")
    for t in top5:
        print(f"  #{t['rank']}  {t['symbol']:6s}  RS: {t.get('rs_4sem', 0):+6.1f}%  Secteur: {t.get('secteur', 'N/A')}")
else:
    print("❌ Pas de recommandations\n")

print()

# SYSTÈME 2: DECISION FINALE (INSTITUTIONAL + ELITE)
print("📊 SYSTÈME 2 : DECISION FINALE (MODE INSTITUTIONAL + ELITE MINIMALISTE)")
print("─" * 120)
decisions = list(db.decisions_finales_brvm.find({"horizon": "SEMAINE"}).sort("alpha_score", -1))
if decisions:
    regime_s2 = decisions[0].get('regime_marche', 'N/A')
    mode_elite = decisions[0].get('mode_elite', False)
    print(f"Régime détecté: {regime_s2}")
    print(f"Mode ELITE: {'✅ Activé' if mode_elite else '❌ Désactivé'}")
    print(f"Recommandations: {len(decisions)}\n")
    for idx, d in enumerate(decisions, 1):
        print(f"  #{idx}  {d['symbol']:6s}  ALPHA: {d.get('alpha_score', 0):5.1f}  RS: {d.get('rs_4sem', 0):+6.1f}%  Secteur: {d.get('secteur', 'N/A')}")
else:
    print("❌ Pas de recommandations\n")

print()

# V2 SHADOW
print("📊 V2 SHADOW (Formule 4 facteurs)")
print("─" * 120)
v2_data = list(db.curated_observations.find(
    {"dataset": "ALPHA_V2_SHADOW"}
).sort("alpha_v2_score", -1).limit(10))

if v2_data:
    print(f"TOP 10 actions par ALPHA V2:")
    print(f"Formule: 35% Early Momentum + 25% Volume Spike + 20% Event + 20% Sentiment\n")
    for idx, v in enumerate(v2_data, 1):
        symbol = v.get('symbol', 'N/A')
        alpha = v.get('alpha_v2_score', 0)
        em = v.get('early_momentum_pct', 0)
        vs = v.get('volume_spike_pct', 0)
        print(f"  #{idx:<2}  {symbol:6s}  ALPHA: {alpha:5.1f}  EM: {em:+5.1f}%  VS: {vs:+5.1f}%")
else:
    print("❌ Pas de données V2\n")

print()

# ANALYSE DE CONVERGENCE
print("="*120)
print("📈 ANALYSE DE CONVERGENCE")
print("="*120 + "\n")

# Actions communes
top5_symbols = set(t['symbol'] for t in top5)
s2_symbols = set(d['symbol'] for d in decisions)
v2_symbols = set(v.get('symbol', 'N/A') for v in v2_data if v.get('symbol'))

print("Actions recommandées par chaque système:")
print(f"  Système 1 (TOP5):      {sorted(top5_symbols)}")
print(f"  Système 2 (DECISION):  {sorted(s2_symbols)}")
if v2_symbols:
    print(f"  V2 Shadow (TOP 10):    {sorted(list(v2_symbols)[:5])} (+ {max(0, len(v2_symbols)-5)} autres)")
else:
    print(f"  V2 Shadow (TOP 10):    Pas de symboles valides")

print()

# Convergence S1 vs S2
convergence_s1_s2 = top5_symbols & s2_symbols
if top5_symbols and s2_symbols:
    taux_conv_s1_s2 = len(convergence_s1_s2) / max(len(top5_symbols), len(s2_symbols)) * 100
    print(f"Convergence S1 ∩ S2: {len(convergence_s1_s2)}/{max(len(top5_symbols), len(s2_symbols))} = {taux_conv_s1_s2:.0f}%")
    if convergence_s1_s2:
        print(f"  ✅ Actions communes: {sorted(convergence_s1_s2)}")
    else:
        print(f"  ❌ Aucune action commune")
else:
    print("Convergence S1 ∩ S2: N/A")

print()

# Convergence S1 vs V2
if v2_symbols:
    convergence_s1_v2 = top5_symbols & v2_symbols
    if top5_symbols and v2_symbols:
        taux_conv_s1_v2 = len(convergence_s1_v2) / max(len(top5_symbols), len(v2_symbols)) * 100
        print(f"Convergence S1 ∩ V2: {len(convergence_s1_v2)}/{max(len(top5_symbols), len(v2_symbols))} = {taux_conv_s1_v2:.0f}%")
        if convergence_s1_v2:
            print(f"  ✅ Actions communes: {sorted(convergence_s1_v2)}")
        else:
            print(f"  ❌ Aucune action commune")
    else:
        print("Convergence S1 ∩ V2: N/A")
else:
    print("Convergence S1 ∩ V2: N/A (V2 sans symboles valides)")
    convergence_s1_v2 = set()

print()

# Convergence S2 vs V2
if v2_symbols:
    convergence_s2_v2 = s2_symbols & v2_symbols
    if s2_symbols and v2_symbols:
        taux_conv_s2_v2 = len(convergence_s2_v2) / max(len(s2_symbols), len(v2_symbols)) * 100
        print(f"Convergence S2 ∩ V2: {len(convergence_s2_v2)}/{max(len(s2_symbols), len(v2_symbols))} = {taux_conv_s2_v2:.0f}%")
        if convergence_s2_v2:
            print(f"  ✅ Actions communes: {sorted(convergence_s2_v2)}")
        else:
            print(f"  ❌ Aucune action commune")
    else:
        print("Convergence S2 ∩ V2: N/A")
else:
    print("Convergence S2 ∩ V2: N/A (V2 sans symboles valides)")
    convergence_s2_v2 = set()

print()

# Actions dans les 3 systèmes
triple_convergence = top5_symbols & s2_symbols & v2_symbols
if triple_convergence:
    print(f"🎯 CONVERGENCE TRIPLE (S1 ∩ S2 ∩ V2): {sorted(triple_convergence)}")
    print("   → Ces actions ont le consensus le plus fort !")
else:
    double_conv_s1_s2 = top5_symbols & s2_symbols
    if double_conv_s1_s2:
        print(f"🎯 CONVERGENCE DOUBLE (S1 ∩ S2): {sorted(double_conv_s1_s2)}")
        print("   → Ces actions ont le consensus des 2 systèmes principaux !")
    else:
        print("🎯 CONVERGENCE TRIPLE: Aucune action commune aux 3 systèmes")

print()

# Recommandation
print("="*120)
print("💡 RECOMMANDATION")
print("="*120)
print()

double_conv_s1_s2 = top5_symbols & s2_symbols
if len(double_conv_s1_s2) == len(top5_symbols) == len(s2_symbols):
    print("🏆 CONVERGENCE PARFAITE 100% S1-S2 !")
    print(f"   Les deux systèmes recommandent EXACTEMENT les mêmes actions: {sorted(double_conv_s1_s2)}")
    print()
    print("   ✅ HAUTE CONFIANCE → Les deux approches (RS simple + ALPHA institutionnel) convergent")
    print("   ✅ FORTE CRÉDIBILITÉ → Consensus entre méthodes indépendantes")
elif len(double_conv_s1_s2) >= 2:
    print("✅ FORTE CONVERGENCE S1-S2 → Les deux systèmes s'accordent")
    print(f"   Actions consensuelles: {sorted(double_conv_s1_s2)}")
elif v2_symbols and len(convergence_s1_v2) >= 2:
    print("✅ FORTE CONVERGENCE S1-V2 → TOP5 ENGINE et V2 s'accordent")
    print(f"   Actions consensuelles: {sorted(convergence_s1_v2)}")
else:
    print("⚠️  DIVERGENCE entre systèmes")
    print("   → Privilégier les actions présentes dans au moins 2 systèmes")
    print("   → Ou choisir le système le mieux adapté:")
    print("      • S1 (TOP5 ENGINE): Simple, basé RS momentum")
    print("      • S2 (INSTITUTIONAL): Sophistiqué, filtres stricts, scoring ALPHA")
    if v2_symbols:
        print("      • V2 (Shadow): Formule équilibrée 4 facteurs")

print()
print("="*120 + "\n")
