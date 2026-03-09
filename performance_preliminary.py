#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PERFORMANCE PRELIMINARY - Métriques 14-week compatible
======================================================

Module institutionnel pour calcul métriques performance AVANT 52 semaines.

Calcule chaque semaine:
- Win rate
- Gain/Perte moyens
- Alpha vs BRVM
- Max drawdown
- Capture rate

Compatible avec données limitées (14+ semaines).

Usage:
    python performance_preliminary.py

Auteur: Expert BRVM 30 ans
Date: 17 Février 2026
"""

import os
import sys
from datetime import datetime, timedelta
from statistics import mean, stdev
from scipy.stats import gmean
import numpy as np

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def compute_brvm_weekly_return(db, week_str):
    """
    Calcule performance BRVM (indice proxy = moyenne géométrique 47 actions)
    
    Args:
        db: MongoDB database
        week_str: Format "2026-W07"
    
    Returns:
        float: Performance BRVM en % pour la semaine
    """
    # Récupérer toutes actions semaine
    prices_week = list(db.prices_weekly.find({"week": week_str}))
    
    if len(prices_week) < 20:  # Minimum 20 actions pour proxy valide
        print(f"  [WARN] Seulement {len(prices_week)} actions pour semaine {week_str}")
        return 0.0
    
    # Performance par action
    perfs = []
    for p in prices_week:
        if p.get("open") and p.get("close") and p["open"] > 0:
            perf = (p["close"] - p["open"]) / p["open"] * 100
            perfs.append(perf)
    
    if len(perfs) < 20:
        return 0.0
    
    # Moyenne géométrique (proxy indice BRVM)
    # Convertir % en ratios: +5% = 1.05
    ratios = [(1 + p/100) for p in perfs]
    geom_mean = gmean(ratios)
    brvm_return = (geom_mean - 1) * 100
    
    return brvm_return


def compute_portfolio_weekly_return(db, week_str):
    """
    Calcule performance portfolio Top5 pour la semaine
    
    Returns:
        dict: {
            'portfolio_return': float,
            'positions': [{symbol, entry, exit, return, size}],
            'win_rate': float,
            'winners': int,
            'losers': int
        }
    """
    # Récupérer Top5 de la semaine (decisions ou top5_weekly)
    top5 = list(db.decisions_finales_brvm.find({
        "horizon": "SEMAINE",
        "decision": "BUY",
        "week": week_str  # Si stocké
    }).limit(5))
    
    if len(top5) == 0:
        # Fallback: chercher dans top5_weekly_brvm
        top5 = list(db.top5_weekly_brvm.find({"week": week_str}))
    
    if len(top5) == 0:
        print(f"  [WARN] Aucune recommandation pour semaine {week_str}")
        return None
    
    positions = []
    winners = 0
    losers = 0
    
    for decision in top5:
        symbol = decision.get("symbol")
        prix_entree = decision.get("prix_entree") or decision.get("prix_actuel")
        
        if not prix_entree:
            continue
        
        # Chercher prix vendredi (clôture semaine)
        # Convertir week → date vendredi
        from datetime import datetime, timedelta
        year, week_num = map(int, week_str.split('-W'))
        # Premier jour de l'année
        jan_1 = datetime(year, 1, 1)
        # Premier lundi de l'année
        week_1_monday = jan_1 + timedelta(days=(7 - jan_1.weekday()))
        # Lundi de la semaine cible
        target_monday = week_1_monday + timedelta(weeks=week_num - 1)
        # Vendredi = Lundi + 4 jours
        target_friday = target_monday + timedelta(days=4)
        
        # Prix vendredi
        price_friday = db.prices_daily.find_one({
            "symbol": symbol,
            "date": target_friday.strftime("%Y-%m-%d")
        })
        
        if not price_friday:
            # Fallback: prix clôture semaine dans prices_weekly
            price_weekly = db.prices_weekly.find_one({
                "symbol": symbol,
                "week": week_str
            })
            prix_sortie = price_weekly.get("close") if price_weekly else prix_entree
        else:
            prix_sortie = price_friday.get("prix_actuel") or price_friday.get("close")
        
        # Calcul return
        position_return = (prix_sortie - prix_entree) / prix_entree * 100
        
        # Position size (equal weight par défaut, ou via decision.capital_alloue)
        position_size = decision.get("pct_portfolio", 1.0 / len(top5))
        
        positions.append({
            "symbol": symbol,
            "prix_entree": prix_entree,
            "prix_sortie": prix_sortie,
            "return_pct": position_return,
            "size": position_size,
            "alpha_score": decision.get("alpha_score"),
            "classe": decision.get("classe")
        })
        
        if position_return > 0:
            winners += 1
        else:
            losers += 1
    
    if len(positions) == 0:
        return None
    
    # Portfolio return (moyenne pondérée)
    portfolio_return = sum(p["return_pct"] * p["size"] for p in positions)
    
    # Win rate
    win_rate = winners / len(positions) * 100 if len(positions) > 0 else 0.0
    
    return {
        "portfolio_return": portfolio_return,
        "positions": positions,
        "win_rate": win_rate,
        "winners": winners,
        "losers": losers,
        "nb_positions": len(positions)
    }


def compute_preliminary_metrics(db, nb_weeks=14):
    """
    Calcule métriques préliminaires sur N dernières semaines
    
    Compatible avec données limitées (14+ semaines).
    
    Args:
        db: MongoDB database
        nb_weeks: Nombre semaines à analyser (14 par défaut)
    
    Returns:
        dict: Métriques agrégées
    """
    print("\n" + "="*80)
    print(" CALCUL METRIQUES PRELIMINAIRES (14-week compatible)")
    print("="*80 + "\n")
    
    # Récupérer dernières N semaines
    latest_weeks = list(db.prices_weekly.aggregate([
        {"$group": {"_id": "$week"}},
        {"$sort": {"_id": -1}},
        {"$limit": nb_weeks}
    ]))
    
    weeks = sorted([w["_id"] for w in latest_weeks])
    
    print(f"Analyse {len(weeks)} semaines: {weeks[0]} a {weeks[-1]}\n")
    
    # Métriques hebdomadaires
    weekly_metrics = []
    
    for week_str in weeks:
        print(f"[{week_str}] Calcul performance...")
        
        # Performance BRVM
        brvm_return = compute_brvm_weekly_return(db, week_str)
        
        # Performance portfolio
        portfolio_data = compute_portfolio_weekly_return(db, week_str)
        
        if portfolio_data is None:
            print(f"  [SKIP] Pas de donnees portfolio\n")
            continue
        
        portfolio_return = portfolio_data["portfolio_return"]
        alpha = portfolio_return - brvm_return
        
        weekly_metrics.append({
            "week": week_str,
            "portfolio_return": portfolio_return,
            "brvm_return": brvm_return,
            "alpha": alpha,
            "win_rate": portfolio_data["win_rate"],
            "nb_positions": portfolio_data["nb_positions"],
            "winners": portfolio_data["winners"],
            "losers": portfolio_data["losers"],
            "positions": portfolio_data["positions"]
        })
        
        print(f"  Portfolio: {portfolio_return:+.2f}%")
        print(f"  BRVM:      {brvm_return:+.2f}%")
        print(f"  ALPHA:     {alpha:+.2f}%")
        print(f"  Win Rate:  {portfolio_data['win_rate']:.1f}%")
        print(f"  Positions: {portfolio_data['winners']}W / {portfolio_data['losers']}L\n")
    
    # Métriques agrégées
    if len(weekly_metrics) == 0:
        print("\n[ERROR] Aucune donnee de performance disponible")
        print("        Le systeme doit tourner quelques semaines avant metriques.\n")
        return None
    
    # Cumul returns
    portfolio_returns = [w["portfolio_return"] for w in weekly_metrics]
    brvm_returns = [w["brvm_return"] for w in weekly_metrics]
    alphas = [w["alpha"] for w in weekly_metrics]
    
    # Win rate global
    total_winners = sum(w["winners"] for w in weekly_metrics)
    total_positions = sum(w["nb_positions"] for w in weekly_metrics)
    global_win_rate = total_winners / total_positions * 100 if total_positions > 0 else 0.0
    
    # Gains/Pertes moyens
    all_position_returns = []
    for w in weekly_metrics:
        all_position_returns.extend([p["return_pct"] for p in w["positions"]])
    
    gains = [r for r in all_position_returns if r > 0]
    losses = [r for r in all_position_returns if r < 0]
    
    avg_gain = mean(gains) if len(gains) > 0 else 0.0
    avg_loss = mean(losses) if len(losses) > 0 else 0.0
    
    # Profit factor
    total_gains = sum(gains) if len(gains) > 0 else 0.0
    total_losses = abs(sum(losses)) if len(losses) > 0 else 0.0
    profit_factor = total_gains / total_losses if total_losses > 0 else 0.0
    
    # Max drawdown (drawdown cumulatif portfolio)
    cumulative_returns = [1.0]  # Start at 100%
    for ret in portfolio_returns:
        cumulative_returns.append(cumulative_returns[-1] * (1 + ret/100))
    
    peak = cumulative_returns[0]
    max_drawdown = 0.0
    for value in cumulative_returns:
        if value > peak:
            peak = value
        drawdown = (value - peak) / peak * 100
        if drawdown < max_drawdown:
            max_drawdown = drawdown
    
    # Performance cumulée
    cumul_portfolio = (cumulative_returns[-1] - 1) * 100
    cumul_brvm = sum(brvm_returns)  # Approximation additive (petit biais)
    cumul_alpha = cumul_portfolio - cumul_brvm
    
    # Sharpe ratio (simplifié, sans risk-free)
    sharpe = mean(portfolio_returns) / stdev(portfolio_returns) if len(portfolio_returns) > 1 and stdev(portfolio_returns) > 0 else 0.0
    
    # Métriques finales
    metrics = {
        "nb_weeks": len(weekly_metrics),
        "period": f"{weeks[0]} a {weeks[-1]}",
        
        # Performance
        "cumul_portfolio_pct": cumul_portfolio,
        "cumul_brvm_pct": cumul_brvm,
        "cumul_alpha_pct": cumul_alpha,
        
        "avg_weekly_return": mean(portfolio_returns),
        "avg_weekly_brvm": mean(brvm_returns),
        "avg_weekly_alpha": mean(alphas),
        
        # Risk
        "volatility_weekly": stdev(portfolio_returns) if len(portfolio_returns) > 1 else 0.0,
        "max_drawdown_pct": max_drawdown,
        "sharpe_ratio": sharpe,
        
        # Win rate
        "global_win_rate_pct": global_win_rate,
        "total_positions": total_positions,
        "total_winners": total_winners,
        "total_losers": total_positions - total_winners,
        
        # Gains/Losses
        "avg_gain_pct": avg_gain,
        "avg_loss_pct": avg_loss,
        "profit_factor": profit_factor,
        
        # Details
        "weekly_metrics": weekly_metrics,
        "timestamp": datetime.now()
    }
    
    return metrics


def display_metrics(metrics):
    """
    Affiche métriques de manière lisible (terminal-safe)
    """
    if metrics is None:
        return
    
    print("\n" + "="*80)
    print(" RESULTATS METRIQUES PRELIMINAIRES")
    print("="*80 + "\n")
    
    print(f"Periode analysee: {metrics['period']}")
    print(f"Nombre semaines:  {metrics['nb_weeks']}\n")
    
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
    print(f"  Win Rate Global:   {metrics['global_win_rate_pct']:7.2f}%")
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
    
    # Seuils cibles (après 8 semaines)
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


def save_metrics_to_db(db, metrics):
    """
    Sauvegarde métriques dans MongoDB
    """
    if metrics is None:
        return
    
    # Collection dédiée
    collection = db["preliminary_metrics"]
    
    # Suppression métriques précédentes (on garde seulement dernière version)
    collection.delete_many({})
    
    # Insertion
    collection.insert_one(metrics)
    
    print(f"[SAVE] Metriques sauvegardes dans collection 'preliminary_metrics'\n")


def main():
    """
    Main entry point
    """
    _, db = get_mongo_db()
    
    # Calcul métriques 14 semaines
    metrics = compute_preliminary_metrics(db, nb_weeks=14)
    
    if metrics:
        # Affichage
        display_metrics(metrics)
        
        # Sauvegarde DB
        save_metrics_to_db(db, metrics)
    else:
        print("\n[INFO] Le systeme doit generer des recommandations pendant")
        print("       quelques semaines avant de calculer metriques.\n")
        print("       Lancez regulierement pipeline_brvm.py chaque semaine.\n")


if __name__ == "__main__":
    main()
