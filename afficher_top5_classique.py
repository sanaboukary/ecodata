#!/usr/bin/env python3
"""
TOP5 classique : décisions de decision_finale_brvm.py
uniquement (hors injections MF synthétiques).
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ─── 1. Toutes décisions BUY hebdo non-archivées ─────────────────────────────
all_buys = list(db.decisions_finales_brvm.find(
    {"decision": "BUY", "horizon": "SEMAINE", "archived": {"$ne": True}}
))

# ─── 2. Séparer classique vs MF-injecté ──────────────────────────────────────
classique = [d for d in all_buys if d.get("generated_by") != "multi_factor_engine"]
mf_inject = [d for d in all_buys if d.get("generated_by") == "multi_factor_engine"]

print(f"Total BUY hebdo actifs : {len(all_buys)}")
print(f"  Système classique    : {len(classique)}")
print(f"  Injections MF        : {len(mf_inject)}")
print()

# ─── 3. Trier classique par confidence décroissant ───────────────────────────
classique_sorted = sorted(classique, key=lambda x: x.get("confidence", 0), reverse=True)

print("=" * 72)
print(f"  {'#':<3} {'Symbol':<8} {'Cl.':<5} {'Conf':>5} {'Gain':>8}  "
      f"{'RS P':>5}  {'Entrée':>8}  {'Stop':>8}  {'TP1':>8}")
print("=" * 72)

for i, d in enumerate(classique_sorted[:10], 1):
    sym    = d.get("symbol", "?")
    cl     = d.get("classe", "?")
    conf   = d.get("confidence", 0)
    gain   = d.get("gain_attendu") or d.get("expected_return") or 0
    rs_p   = d.get("rs_percentile") or 0
    prix   = d.get("prix_entree") or 0
    stop   = d.get("stop") or 0
    tp1    = round(prix * 1.075) if prix else 0
    mf     = d.get("score_total_mf")
    mf_str = f"  MF={mf:.0f}" if mf else ""
    marker = " << TOP5" if i <= 5 else ""
    print(f"  {i:<3} {sym:<8} {cl:<5} {conf:>5.0f}% {gain:>7.1f}%  "
          f"RS P{rs_p:>2.0f}  {prix:>8,.0f}  {stop:>8,.0f}  {tp1:>8,.0f}"
          f"{mf_str}{marker}")

print()
print("─" * 72)
print("TOP 5 CLASSIQUE — Détail complet")
print("─" * 72)

for i, d in enumerate(classique_sorted[:5], 1):
    sym    = d.get("symbol", "?")
    cl     = d.get("classe", "?")
    conf   = d.get("confidence", 0)
    gain   = d.get("gain_attendu") or d.get("expected_return") or 0
    rr     = d.get("rr") or 0
    prix   = d.get("prix_entree") or 0
    stop   = d.get("stop") or 0
    atr    = d.get("atr_pct") or 0
    rs_p   = d.get("rs_percentile") or 0
    mf     = d.get("score_total_mf")
    mf_lbl = d.get("mf_label", "")
    stype  = d.get("setup_type", "N/D")
    wos    = d.get("wos") or 0

    if prix > 0:
        tp1    = round(prix * 1.075)
        tp2    = round(prix * 1.150)
        runner = round(prix * 1.275)
        stop_pct = round((prix - stop) / prix * 100, 1) if stop else 0
    else:
        tp1 = tp2 = runner = stop_pct = 0

    print(f"\n#{i}  {sym} — Classe {cl} | Conf {conf:.0f}% | Gain cible {gain:.1f}% | RR {rr:.1f}")
    if mf:
        print(f"    MF Score   : {mf:.1f}/100  {mf_lbl}  | Setup : {stype}")
    print(f"    RS Pctile  : P{rs_p:.0f}")
    print(f"    WOS        : {wos} semaines horizon")
    print(f"    ATR%       : {atr:.1f}%")
    print()
    if prix > 0:
        print(f"    Entrée     : {prix:,.0f} FCFA")
        print(f"    Stop       : {stop:,.0f} FCFA  (-{stop_pct:.1f}%  ATR×1.5)")
        print(f"    TP1        : {tp1:,.0f} FCFA  (+7.5%  → vendre 50%)")
        print(f"    TP2        : {tp2:,.0f} FCFA  (+15%   → vendre 30%)")
        print(f"    Runner     : {runner:,.0f} FCFA  (+27.5% → trailing)")
    print(f"    Invalide   : clôture < {stop:,.0f} FCFA")

print()
print("─" * 72)
print("INJECTIONS MF (hors classique)")
print("─" * 72)
for d in sorted(mf_inject, key=lambda x: x.get("score_total_mf", 0), reverse=True):
    print(f"  {d.get('symbol'):<8} MF={d.get('score_total_mf'):.1f}  "
          f"{d.get('mf_label')}  entrée={d.get('prix_entree'):,.0f}  "
          f"stop={d.get('stop'):,.0f}")
