#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPARAISON DUAL MOTOR - WOS STABLE vs EXPLOSION 7J
===================================================

Compare les 2 systèmes côte à côte:
- MOTEUR 1 (STABLE): WOS 2-8 semaines, qualité > quantité
- MOTEUR 2 (OPPORTUNISTE): EXPLOSION 7-10 jours, timing > scoring

DIFFÉRENCES CLÉS:
               | WOS STABLE      | EXPLOSION 7J
----------------|-----------------|------------------
Horizon        | 2-8 semaines    | 7-10 jours
Positions      | 3-6 MAX         | 1-2 MAX
Stop/Target    | 1.0× / 2.6× ATR | 0.8× / 1.8× ATR
Score          | WOS (tendance)  | EXPLOSION (breakout)
Volume         | Ratio legacy    | Z-score anomalies
Philosophie    | Qualité setup   | Opportunisme timing
"""

import os, sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# RÉCUPÉRATION RECOMMANDATIONS
# ============================================================================

def get_wos_stable_recos(week_str=None):
    """Récupère recommandations WOS STABLE"""
    if not week_str:
        week_str = datetime.now().strftime("%Y-W%V")
    
    recos = list(db.decisions_finales_brvm.find(
        {'horizon': 'SEMAINE', 'decision': 'BUY'},
        {'symbol': 1, 'classe': 1, 'wos': 1, 'confidence': 1, 
         'gain_attendu': 1, 'rr': 1, 'prix_actuel': 1,
         'stop_pct': 1, 'target_pct': 1}
    ).sort('wos', -1).limit(6))
    
    return recos

def get_explosion_7j_recos(week_str=None):
    """Récupère recommandations EXPLOSION 7J"""
    if not week_str:
        week_str = datetime.now().strftime("%Y-W%V")
    
    recos = list(db.decisions_explosion_7j.find(
        {'week': week_str},
        {'symbol': 1, 'explosion_score': 1, 'close': 1,
         'stop_pct': 1, 'target_pct': 1, 'risk_reward': 1,
         'breakout_score': 1, 'volume_zscore': 1, 'acceleration': 1,
         'prob_top5': 1, 'rank': 1}
    ).sort('rank', 1))
    
    return recos

# ============================================================================
# AFFICHAGE COMPARATIF
# ============================================================================

def compare_dual_motor():
    """Comparaison côte à côte des 2 moteurs"""
    week_str = datetime.now().strftime("%Y-W%V")
    
    print("\n" + "="*100)
    print("COMPARAISON DUAL MOTOR - BRVM 30 ANS EXPERTISE")
    print("="*100)
    print(f"Semaine: {week_str}")
    print("="*100 + "\n")
    
    # ========================================================================
    # MOTEUR 1: WOS STABLE
    # ========================================================================
    
    wos_recos = get_wos_stable_recos(week_str)
    
    print("┌" + "─"*98 + "┐")
    print("│ MOTEUR 1: WOS STABLE (2-8 semaines)".ljust(99) + "│")
    print("│ Philosophie: Qualité setup > Quantité positions".ljust(99) + "│")
    print("│ Stop/Target: 1.0× / 2.6× ATR (conservateur)".ljust(99) + "│")
    print("└" + "─"*98 + "┘")
    print()
    
    if wos_recos:
        print(f"{'#':<3} {'SYMBOL':<8} {'CLASSE':<7} {'WOS':<6} {'CONF%':<6} {'GAIN%':<7} {'RR':<5} {'STOP%':<7} {'TARGET%':<8}")
        print("-"*100)
        
        for i, r in enumerate(wos_recos, 1):
            print(f"{i:<3} {r['symbol']:<8} {r.get('classe', 'C'):<7} "
                  f"{r.get('wos', 0):<6.1f} {r.get('confidence', 0):<6.1f} "
                  f"{r.get('gain_attendu', 0):<7.1f} {r.get('rr', 0):<5.2f} "
                  f"{r.get('stop_pct', 0):<7.1f} {r.get('target_pct', 0):<8.1f}")
        
        print("-"*100)
        print(f"Total: {len(wos_recos)} positions (MAX 6)")
        
        # Statistiques
        avg_wos = sum(r.get('wos', 0) for r in wos_recos) / len(wos_recos)
        avg_gain = sum(r.get('gain_attendu', 0) for r in wos_recos) / len(wos_recos)
        avg_rr = sum(r.get('rr', 0) for r in wos_recos) / len(wos_recos)
        
        print(f"\nMOYENNES: WOS {avg_wos:.1f} | Gain {avg_gain:.1f}% | RR {avg_rr:.2f}")
    else:
        print("⚠️  Aucune recommandation WOS cette semaine\n")
    
    print("\n" + "="*100 + "\n")
    
    # ========================================================================
    # MOTEUR 2: EXPLOSION 7J
    # ========================================================================
    
    explosion_recos = get_explosion_7j_recos(week_str)
    
    print("┌" + "─"*98 + "┐")
    print("│ MOTEUR 2: EXPLOSION 7-10 JOURS (Opportuniste)".ljust(99) + "│")
    print("│ Philosophie: Timing explosions > Scoring qualité".ljust(99) + "│")
    print("│ Stop/Target: 0.8× / 1.8× ATR (court terme)".ljust(99) + "│")
    print("└" + "─"*98 + "┘")
    print()
    
    if explosion_recos:
        print(f"{'#':<3} {'SYMBOL':<8} {'EXPL':<6} {'BREAK':<7} {'VOLZ':<7} {'ACCEL%':<8} {'TOP5%':<7} {'STOP%':<7} {'TARGET%':<8}")
        print("-"*100)
        
        for r in explosion_recos:
            print(f"{r.get('rank', 0):<3} {r['symbol']:<8} "
                  f"{r.get('explosion_score', 0):<6.1f} "
                  f"{r.get('breakout_score', 0):<7.1f} "
                  f"{r.get('volume_zscore', 0):<7.2f} "
                  f"{r.get('acceleration', 0):<8.1f} "
                  f"{r.get('prob_top5', 0):<7.1f} "
                  f"{r.get('stop_pct', 0):<7.1f} "
                  f"{r.get('target_pct', 0):<8.1f}")
        
        print("-"*100)
        print(f"Total: {len(explosion_recos)} position(s) (MAX 2)")
        
        # Statistiques
        avg_expl = sum(r.get('explosion_score', 0) for r in explosion_recos) / len(explosion_recos)
        avg_z = sum(r.get('volume_zscore', 0) for r in explosion_recos) / len(explosion_recos)
        avg_prob = sum(r.get('prob_top5', 0) for r in explosion_recos) / len(explosion_recos)
        
        print(f"\nMOYENNES: Explosion {avg_expl:.1f} | Vol Z-score {avg_z:.2f} | Prob TOP5 {avg_prob:.1f}%")
    else:
        print("⚠️  Aucune opportunité EXPLOSION détectée cette semaine")
        print("(Normal - Système très sélectif pour court terme)\n")
    
    print("\n" + "="*100 + "\n")
    
    # ========================================================================
    # ANALYSE COMPARATIVE
    # ========================================================================
    
    print("ANALYSE DUAL MOTOR:")
    print("-"*100)
    
    if wos_recos and explosion_recos:
        # Chevauchements
        wos_symbols = {r['symbol'] for r in wos_recos}
        expl_symbols = {r['symbol'] for r in explosion_recos}
        common = wos_symbols & expl_symbols
        
        if common:
            print(f"\n⚡ CONVERGENCE DÉTECTÉE: {', '.join(common)}")
            print("   → Actions validées par LES DEUX moteurs (haute conviction)")
        else:
            print("\n✓ DIVERSIFICATION: Aucun chevauchement entre moteurs")
            print("   → Capital réparti sur différentes stratégies")
        
        # Capital allocation suggérée
        print("\n💰 ALLOCATION CAPITAL SUGGÉRÉE:")
        print(f"   - WOS STABLE (60%):      {len(wos_recos)} positions × ~10% = {len(wos_recos)*10}%")
        print(f"   - EXPLOSION 7J (30%):    {len(explosion_recos)} positions × ~15% = {len(explosion_recos)*15}%")
        print(f"   - Cash réserve (10%):    Opportunités futures")
        
        # Profil risque
        print("\n📊 PROFIL RISQUE DUAL MOTOR:")
        
        wos_avg_target = sum(r.get('target_pct', 0) for r in wos_recos) / len(wos_recos)
        expl_avg_target = sum(r.get('target_pct', 0) for r in explosion_recos) / len(explosion_recos)
        
        print(f"   - WOS STABLE:    Target moy {wos_avg_target:.1f}% (conservative)")
        print(f"   - EXPLOSION 7J:  Target moy {expl_avg_target:.1f}% (agressive)")
        print(f"   - Rotation:      STABLE = lent, EXPLOSION = rapide (7-10j)")
        
    elif wos_recos:
        print("\n⚠️  MODE WOS STABLE UNIQUEMENT")
        print("   → Aucune explosion détectée, capital concentré sur WOS")
        
    elif explosion_recos:
        print("\n⚡ MODE EXPLOSION UNIQUEMENT")
        print("   → Pas de WOS qualité setup, focus opportunisme court terme")
        
    else:
        print("\n❌ AUCUN SIGNAL (WOS + EXPLOSION)")
        print("   → Marché BRVM inerte, attendre meilleures conditions")
    
    print("\n" + "="*100 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    compare_dual_motor()
    
    print("\n📌 RAPPELS DUAL MOTOR:")
    print("   1. WOS STABLE = Qualité setup, patience, RR élevé")
    print("   2. EXPLOSION 7J = Timing opportuniste, rotation rapide")
    print("   3. Les 2 moteurs sont COMPLÉMENTAIRES (pas concurrents)")
    print("   4. Allocation: 60% WOS + 30% EXPLOSION + 10% Cash")
    print("   5. Tolérance zéro = Stop obligatoire sur LES DEUX")
    print("\n")

if __name__ == "__main__":
    main()
