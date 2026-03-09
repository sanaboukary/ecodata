#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AFFICHER METRICS PRELIMINARY - Dashboard métriques performance
==============================================================

Affiche métriques préliminaires depuis MongoDB.

Usage:
    python afficher_metrics_preliminary.py

Auteur: Expert BRVM 30 ans
Date: 17 Février 2026
"""

import os
import sys
from datetime import datetime

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


def display_weekly_details(weekly_metrics):
    """
    Affiche détails semaine par semaine
    """
    print("\n" + "="*80)
    print(" PERFORMANCE SEMAINE PAR SEMAINE")
    print("="*80 + "\n")
    
    print(f"{'Semaine':<12} {'Portfolio':>10} {'BRVM':>10} {'Alpha':>10} {'Win Rate':>10} {'Pos':>6}")
    print("-" * 80)
    
    for w in weekly_metrics:
        print(f"{w['week']:<12} "
              f"{w['portfolio_return']:>+9.2f}% "
              f"{w['brvm_return']:>+9.2f}% "
              f"{w['alpha']:>+9.2f}% "
              f"{w['win_rate']:>9.1f}% "
              f"{w['winners']}/{w['nb_positions']:>1}")
    
    print()


def display_top_performers(weekly_metrics):
    """
    Affiche top 5 meilleures/pires positions
    """
    # Extraire toutes positions
    all_positions = []
    for w in weekly_metrics:
        for p in w["positions"]:
            p_copy = p.copy()
            p_copy["week"] = w["week"]
            all_positions.append(p_copy)
    
    if len(all_positions) == 0:
        return
    
    # Tri par performance
    all_positions.sort(key=lambda x: x["return_pct"], reverse=True)
    
    print("\n" + "="*80)
    print(" TOP 5 MEILLEURES POSITIONS")
    print("="*80 + "\n")
    
    print(f"{'Semaine':<12} {'Symbol':>8} {'Return':>10} {'Alpha':>8} {'Classe':>8}")
    print("-" * 80)
    
    for p in all_positions[:5]:
        print(f"{p['week']:<12} "
              f"{p['symbol']:>8} "
              f"{p['return_pct']:>+9.2f}% "
              f"{p.get('alpha_score', 0):>7.1f} "
              f"{p.get('classe', 'N/A'):>8}")
    
    print("\n" + "="*80)
    print(" TOP 5 PIRES POSITIONS")
    print("="*80 + "\n")
    
    print(f"{'Semaine':<12} {'Symbol':>8} {'Return':>10} {'Alpha':>8} {'Classe':>8}")
    print("-" * 80)
    
    for p in all_positions[-5:]:
        print(f"{p['week']:<12} "
              f"{p['symbol']:>8} "
              f"{p['return_pct']:>+9.2f}% "
              f"{p.get('alpha_score', 0):>7.1f} "
              f"{p.get('classe', 'N/A'):>8}")
    
    print()


def main():
    """
    Main entry point
    """
    _, db = get_mongo_db()
    
    # Récupérer métriques
    metrics = db.preliminary_metrics.find_one()
    
    if not metrics:
        print("\n[ERROR] Aucune metrique disponible.")
        print("        Lancez d'abord: python performance_preliminary.py\n")
        return
    
    print("\n" + "="*80)
    print(" DASHBOARD PERFORMANCE PRELIMINARY")
    print("="*80 + "\n")
    
    print(f"Derniere mise a jour: {metrics.get('timestamp', 'N/A')}")
    print(f"Periode analysee:     {metrics['period']}")
    print(f"Nombre semaines:      {metrics['nb_weeks']}\n")
    
    print("-" * 80)
    print(" PERFORMANCE CUMULEE")
    print("-" * 80)
    print(f"  Portfolio:   {metrics['cumul_portfolio_pct']:+7.2f}%")
    print(f"  BRVM:        {metrics['cumul_brvm_pct']:+7.2f}%")
    print(f"  ALPHA:       {metrics['cumul_alpha_pct']:+7.2f}%")
    print()
    
    print("-" * 80)
    print(" PERFORMANCE HEBDOMADAIRE MOYENNE")
    print("-" * 80)
    print(f"  Portfolio:   {metrics['avg_weekly_return']:+7.2f}%")
    print(f"  BRVM:        {metrics['avg_weekly_brvm']:+7.2f}%")
    print(f"  ALPHA:       {metrics['avg_weekly_alpha']:+7.2f}%")
    print()
    
    print("-" * 80)
    print(" RISQUE")
    print("-" * 80)
    print(f"  Volatilite hebdo:  {metrics['volatility_weekly']:7.2f}%")
    print(f"  Max Drawdown:      {metrics['max_drawdown_pct']:7.2f}%")
    print(f"  Sharpe Ratio:      {metrics['sharpe_ratio']:7.2f}")
    print()
    
    print("-" * 80)
    print(" WIN RATE")
    print("-" * 80)
    print(f"  Win Rate Global:     {metrics['global_win_rate_pct']:7.2f}%")
    print(f"  Positions gagnantes: {metrics['total_winners']}")
    print(f"  Positions perdantes: {metrics['total_losers']}")
    print(f"  Total positions:     {metrics['total_positions']}")
    print()
    
    print("-" * 80)
    print(" GAINS / PERTES")
    print("-" * 80)
    print(f"  Gain moyen:    {metrics['avg_gain_pct']:+7.2f}%")
    print(f"  Perte moyenne: {metrics['avg_loss_pct']:+7.2f}%")
    print(f"  Profit Factor: {metrics['profit_factor']:7.2f}")
    print()
    
    # Validation seuils
    print("-" * 80)
    print(" VALIDATION SEUILS (Cibles apres 8+ semaines)")
    print("-" * 80)
    
    alpha_ok = metrics['cumul_alpha_pct'] > 4.0
    dd_ok = metrics['max_drawdown_pct'] > -12.0
    wr_ok = metrics['global_win_rate_pct'] > 60.0
    
    print(f"  Alpha cumule > +4%:      {'OK' if alpha_ok else 'NON'}  ({metrics['cumul_alpha_pct']:+.2f}%)")
    print(f"  Drawdown < -12%:         {'OK' if dd_ok else 'NON'}  ({metrics['max_drawdown_pct']:.2f}%)")
    print(f"  Win rate > 60%:          {'OK' if wr_ok else 'NON'}  ({metrics['global_win_rate_pct']:.2f}%)")
    
    if metrics['nb_weeks'] >= 8:
        if alpha_ok and dd_ok and wr_ok:
            print("\n  >> SYSTEME VALIDE - Peut optimiser stops/allocation")
        else:
            print("\n  >> SYSTEME EN OBSERVATION - Accumuler + donnees")
    else:
        print(f"\n  >> DONNEES INSUFFISANTES - Besoin {8 - metrics['nb_weeks']} semaines sup")
    
    print()
    
    # Détails semaine par semaine
    if "weekly_metrics" in metrics:
        display_weekly_details(metrics["weekly_metrics"])
        display_top_performers(metrics["weekly_metrics"])


if __name__ == "__main__":
    main()
