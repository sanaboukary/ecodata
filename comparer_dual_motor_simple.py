#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPARAISON DUAL MOTOR - VERSION SIMPLE
Comparaison WOS STABLE vs EXPLOSION 7-10 JOURS
"""

from pymongo import MongoClient
from datetime import datetime

db = MongoClient('localhost', 27017)['centralisation_db']

week_str = datetime.now().strftime("%Y-W%V")

print("\n" + "="*100)
print("📊 COMPARAISON DUAL MOTOR - SYSTÈME BRVM")
print("="*100)
print(f"Semaine: {week_str}")
print("="*100 + "\n")

# ============================================================================
# MOTEUR 1: WOS STABLE
# ============================================================================

print("┌" + "─"*98 + "┐")
print("│" + " "*29 + "MOTEUR 1: WOS STABLE (2-8 semaines)" + " "*34 + "│")
print("└" + "─"*98 + "┘\n")

wos_recos = list(db.decisions_finales_brvm.find(
    {},
    {'symbol': 1, 'decision': 1, 'wos_score': 1, 'close': 1, 
     'target_price': 1, 'stop_price': 1, 'week': 1, '_id': 0}
).sort([('created_at', -1), ('_id', -1)]).limit(6))

if wos_recos:
    # Grouper par semaine
    by_week = {}
    for r in wos_recos:
        w = r.get('week', 'N/A')
        if w not in by_week:
            by_week[w] = []
        by_week[w].append(r)
    
    # Afficher dernière semaine
    for week in sorted(by_week.keys(), reverse=True)[:1]:
        positions = by_week[week]
        print(f"📅 Semaine: {week}")
        print(f"🎯 Positions: {len(positions)}/6 MAX")
        print(f"💰 Allocation: {len(positions) * 10}% capital ({len(positions)} × 10%)")
        print(f"\n{'Rang':<6}{'Symbol':<8}{'Prix':<10}{'Target':<10}{'Stop':<10}{'Score WOS':<12}")
        print("─"*60)
        
        for i, r in enumerate(positions, 1):
            symbol = r.get('symbol', 'N/A')
            close = r.get('close', 0)
            target = r.get('target_price', 0)
            stop = r.get('stop_price', 0)
            wos = r.get('wos_score', r.get('score', 'N/A'))
            
            print(f"#{i:<5}{symbol:<8}{close:<10.0f}{target:<10.0f}{stop:<10.0f}{wos}")
        
        print(f"\n💡 Stratégie: Qualité > Quantité | Patience 2-8 semaines")
        print(f"🎯 Objectif: +15-25% par position | Winrate 55-65%")
else:
    print("⚠️  Aucune décision WOS STABLE trouvée")
    print("\n💡 Générer avec:")
    print("   python analyse_ia_simple.py")
    print("   python decision_finale_brvm.py")

print()

# ============================================================================
# MOTEUR 2: EXPLOSION 7-10 JOURS
# ============================================================================

print("┌" + "─"*98 + "┐")
print("│" + " "*26 + "MOTEUR 2: EXPLOSION 7-10 JOURS (Opportuniste)" + " "*28 + "│")
print("└" + "─"*98 + "┘\n")

explosion_recos = list(db.decisions_explosion_7j.find(
    {},
    {'symbol': 1, 'week': 1, 'explosion_score': 1, 'close': 1,
     'stop_pct': 1, 'target_pct': 1, 'risk_reward': 1,
     'breakout_score': 1, 'volume_zscore': 1, 'acceleration': 1,
     'prob_top5': 1, 'rank': 1, '_id': 0}
).sort('generated_at', -1).limit(2))

if explosion_recos:
    # Grouper par semaine
    by_week = {}
    for r in explosion_recos:
        w = r.get('week', 'N/A')
        if w not in by_week:
            by_week[w] = []
        by_week[w].append(r)
    
    # Afficher dernière semaine
    for week in sorted(by_week.keys(), reverse=True)[:1]:
        positions = by_week[week]
        print(f"📅 Semaine: {week}")
        print(f"🔥 Positions: {len(positions)}/2 MAX")
        print(f"💰 Allocation: {len(positions) * 15}% capital ({len(positions)} × 15%)")
        print(f"\n{'Rang':<6}{'Symbol':<8}{'Prix':<10}{'Target':<10}{'Stop':<10}{'Score EXP':<12}{'Breakout':<10}")
        print("─"*70)
        
        for r in positions:
            rank = r.get('rank', 0)
            symbol = r.get('symbol', 'N/A')
            close = r.get('close', 0)
            target_pct = r.get('target_pct', 0)
            stop_pct = r.get('stop_pct', 0)
            score = r.get('explosion_score', 0)
            breakout = r.get('breakout_score', 0)
            
            target_price = close * (1 + target_pct/100)
            stop_price = close * (1 - stop_pct/100)
            
            print(f"#{rank:<5}{symbol:<8}{close:<10.0f}{target_price:<10.0f}{stop_price:<10.0f}{score:<12.1f}{breakout}/100")
        
        print(f"\n💡 Stratégie: Timing > Scoring | Rotation rapide 7-10 jours")
        print(f"🎯 Objectif: TOP 5 hausses hebdo (+8-15%) | Winrate 45-55%")
else:
    print("⚠️  Aucune décision EXPLOSION 7J trouvée")
    print("\n💡 Générer avec:")
    print("   python explosion_simple.py 2026-W06")

print()

# ============================================================================
# ANALYSE CONVERGENCE
# ============================================================================

print("┌" + "─"*98 + "┐")
print("│" + " "*35 + "ANALYSE CONVERGENCE" + " "*44 + "│")
print("└" + "─"*98 + "┘\n")

if wos_recos and explosion_recos:
    wos_symbols = set(r.get('symbol') for r in wos_recos)
    exp_symbols = set(r.get('symbol') for r in explosion_recos)
    
    overlap = wos_symbols & exp_symbols
    
    if overlap:
        print(f"✅ {len(overlap)} ACTION(S) COMMUNE(S): {', '.join(overlap)}")
        print(f"   → HAUTE CONVICTION (les 2 moteurs convergent)")
        print(f"   → Allocation suggérée: 20% sur action commune (10% WOS + 10% EXPLOSION)")
    else:
        print("ℹ️  Aucune convergence")
        print("   → Les 2 moteurs ciblent des opportunités différentes (normal)")
        print("   → Diversification maximale")
else:
    print("⚠️  Impossible de calculer convergence (données insuffisantes)")

print()

# ============================================================================
# ALLOCATION CAPITAL SUGGÉRÉE
# ============================================================================

print("┌" + "─"*98 + "┐")
print("│" + " "*31 + "ALLOCATION CAPITAL SUGGÉRÉE" + " "*40 + "│")
print("└" + "─"*98 + "┘\n")

wos_count = len(wos_recos) if wos_recos else 0
exp_count = len(explosion_recos) if explosion_recos else 0

wos_alloc = min(wos_count * 10, 60)
exp_alloc = min(exp_count * 15, 30)
cash_alloc = 100 - wos_alloc - exp_alloc

print(f"60% WOS STABLE     → {wos_count} positions × 10% = {wos_alloc}% alloué")
print(f"30% EXPLOSION 7J   → {exp_count} positions × 15% = {exp_alloc}% alloué")
print(f"10% Cash réserve   → {cash_alloc}% disponible")
print("─"*60)
print(f"100% TOTAL         → {wos_alloc + exp_alloc + cash_alloc}% (dont {100 - cash_alloc}% investi)")

print()

# ============================================================================
# PROFIL RISQUE
# ============================================================================

print("┌" + "─"*98 + "┐")
print("│" + " "*38 + "PROFIL RISQUE" + " "*47 + "│")
print("└" + "─"*98 + "┘\n")

print("MOTEUR 1 (WOS):      Risque MODÉRÉ | Stop large (1.0× ATR) | Patient")
print("MOTEUR 2 (EXPLOSION): Risque ÉLEVÉ | Stop serré (0.8× ATR) | Actif")
print("\nPORTEFOLIO DUAL MOTOR: Risque ÉQUILIBRÉ (60% modéré + 30% élevé)")
print("Drawdown max attendu: 20-25%")

print("\n" + "="*100)
print("✅ COMPARAISON TERMINÉE")
print("="*100 + "\n")

print("💡 PROCHAINES ÉTAPES:")
print("   1. Valider les positions proposées")
print("   2. Ajuster allocation selon appétit risque")
print("   3. Suivre quotidiennement (EXPLOSION surtout)")
print("   4. Mettre à jour track record après 7-10 jours")
print()
