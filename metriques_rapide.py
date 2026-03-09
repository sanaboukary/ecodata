#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
METRIQUES PERFORMANCE SIMPLE - Calcul direct
"""

import os
import sys
import django
from datetime import datetime

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    print("\n" + "="*80)
    print(" METRIQUES PERFORMANCE BRVM - ANALYSE RAPIDE")
    print("="*80 + "\n")
    
    _, db = get_mongo_db()
    
    # Récupérer toutes décisions SEMAINE avec week
    decisions = list(db.decisions_finales_brvm.find({
        "horizon": "SEMAINE",
        "week": {"$exists": True, "$ne": None}
    }))
    
    print(f"Decisions trouvees: {len(decisions)}")
    
    if len(decisions) == 0:
        print("\n[INFO] Aucune decision hebdomadaire avec champ 'week'")
        print("       Lancer decision_finale_brvm.py avec MODE_INSTITUTIONAL=True\n")
        return
    
    # Grouper par semaine
    from collections import defaultdict
    by_week = defaultdict(list)
    
    for dec in decisions:
        week = dec.get("week")
        if week:
            by_week[week].append(dec)
    
    print(f"Semaines uniques: {len(by_week)}")
    print(f"Semaines: {', '.join(sorted(by_week.keys())[:10])}")
    
    # Calculer métriques par semaine
    print("\n" + "-"*80)
    print(" ANALYSE SEMAINE PAR SEMAINE")
    print("-"*80)
    print(f"{'Semaine':<12} {'Trades':>7} {'BUY':>5} {'SELL':>5} {'ALPHA moy':>10}")
    print("-"*80)
    
    total_buy = 0
    total_sell = 0
    all_alphas = []
    
    for week in sorted(by_week.keys()):
        decs = by_week[week]
        nb_buy = sum(1 for d in decs if d.get("decision") == "BUY")
        nb_sell = sum(1 for d in decs if d.get("decision") == "SELL")
        
        alphas = [d.get("alpha_score") or d.get("wos", 50) for d in decs if d.get("alpha_score") or d.get("wos")]
        avg_alpha = sum(alphas) / len(alphas) if alphas else 0
        
        print(f"{week:<12} {len(decs):>7} {nb_buy:>5} {nb_sell:>5} {avg_alpha:>9.1f}")
        
        total_buy += nb_buy
        total_sell += nb_sell
        all_alphas.extend(alphas)
    
    print("-"*80)
    print(f"{'TOTAL':<12} {len(decisions):>7} {total_buy:>5} {total_sell:>5} {sum(all_alphas)/len(all_alphas) if all_alphas else 0:>9.1f}")
    print("="*80)
    
    # Statistiques globales
    print("\n" + "-"*80)
    print(" STATISTIQUES GLOBALES")
    print("-"*80)
    print(f"Nombre total de trades:     {len(decisions)}")
    print(f"Nombre de semaines:         {len(by_week)}")
    print(f"Trades BUY:                 {total_buy} ({total_buy/len(decisions)*100:.1f}%)")
    print(f"Trades SELL:                {total_sell} ({total_sell/len(decisions)*100:.1f}%)")
    print(f"ALPHA_SCORE moyen:          {sum(all_alphas)/len(all_alphas) if all_alphas else 0:.1f}/100")
    
    # Trouver best/worst weeks par nombre de trades
    best_week = max(by_week.items(), key=lambda x: len(x[1]))
    worst_week = min(by_week.items(), key=lambda x: len(x[1]))
    
    print(f"\nSemaine la plus active:     {best_week[0]} ({len(best_week[1])} trades)")
    print(f"Semaine la moins active:    {worst_week[0]} ({len(worst_week[1])} trades)")
    
    # Top symboles
    from collections import Counter
    symbols = [d.get("symbol") for d in decisions if d.get("symbol")]
    top_symbols = Counter(symbols).most_common(10)
    
    print("\n" + "-"*80)
    print(" TOP 10 SYMBOLES RECOMMANDES")
    print("-"*80)
    for symbol, count in top_symbols:
        print(f"{symbol:<8} {count:>3} fois")
    
    print("\n" +  "="*80)
    
    # Note sur métriques complètes  
    print("\n[NOTE] Pour metriques completes (win rate, gain/perte reels):")
    print("       - Besoin de prix de sortie (Vendredi) pour chaque trade")
    print("       - Actuellement: statistiques descriptives uniquement")
    print("       - Prochaine etape: Tracker performance reelle chaque semaine\n")
    
    # Calcul win rate si prix sortie disponibles
    decisions_with_exit = [d for d in decisions if d.get("prix_sortie")]
    
    if len(decisions_with_exit) > 0:
        print("\n" + "-"*80)
        print(f" PERFORMANCE REELLE ({len(decisions_with_exit)} trades complets)")
        print("-"*80)
        
        wins = 0
        losses = 0
        gains = []
        
        for d in decisions_with_exit:
            prix_entree = d.get("prix_entree")
            prix_sortie = d.get("prix_sortie")
            
            if prix_entree and prix_sortie:
                perf = (prix_sortie - prix_entree) / prix_entree * 100
                
                if perf > 0:
                    wins += 1
                    gains.append(perf)
                else:
                    losses += 1
                    gains.append(perf)
        
        if wins + losses > 0:
            win_rate = wins / (wins + losses) * 100
            avg_gain = sum(g for g in gains if g > 0) / wins if wins > 0 else 0
            avg_loss = sum(g for g in gains if g < 0) / losses if losses > 0 else 0
            
            print(f"Win Rate:           {win_rate:.1f}% ({wins} wins / {losses} losses)")
            print(f"Gain moyen:         +{avg_gain:.2f}%")
            print(f"Perte moyenne:      {avg_loss:.2f}%")
            print(f"Performance totale: {sum(gains):.2f}%")
            print("="*80)


if __name__ == "__main__":
    main()
