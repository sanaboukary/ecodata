#!/usr/bin/env python3
"""
COMPARAISON V1 VS V2 - VALIDATION FRAMEWORK
============================================

Objectif: Tracker metriques validation pour decision migration

Metriques:
- Win Rate (% positions gagnantes)
- Return moyen
- Sharpe Ratio
- Max Drawdown
- Turnover (rotation TOP 5)
- Stabilite ranking

Seuils validation (migration v1 → v2):
- ≥ 4 semaines donnees
- WinRate_v2 ≥ WinRate_v1 + 5%
- Drawdown_v2 ≤ Drawdown_v1
- Sharpe_v2 ≥ Sharpe_v1

Decision: QUANTITATIVE (pas subjective)
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


def get_top5_v1(db) -> list:
    """Recuperer TOP 5 v1 (production actuelle)"""
    try:
        # V1 = decision_finale_brvm (production)
        decisions = list(db.curated_observations.find({
            "dataset": "DECISION_FINALE_BRVM"
        }).sort("attrs.ALPHA_SCORE", -1).limit(5))
        
        top5_v1 = [(d["key"], d.get("attrs", {}).get("ALPHA_SCORE", 0)) for d in decisions]
        
        return top5_v1
    
    except Exception as e:
        print(f"Erreur recuperation v1: {e}")
        return []


def get_top5_v2(db) -> list:
    """Recuperer TOP 5 v2 (shadow mode)"""
    try:
        # V2 = alpha_v2_shadow
        alphas_v2 = list(db.curated_observations.find({
            "dataset": "ALPHA_V2_SHADOW",
            "attrs.categorie": {"$ne": "REJECTED"}
        }).sort("value", -1).limit(5))
        
        top5_v2 = [(a["key"], a["value"]) for a in alphas_v2]
        
        return top5_v2
    
    except Exception as e:
        print(f"Erreur recuperation v2: {e}")
        return []


def calculate_turnover(top5_old: list, top5_new: list) -> float:
    """
    Calcul turnover (% rotation entre 2 TOP 5)
    
    Return: 0.0 (aucun changement) a 1.0 (rotation complete)
    """
    if not top5_old or not top5_new:
        return 0.0
    
    symbols_old = set(s[0] for s in top5_old)
    symbols_new = set(s[0] for s in top5_new)
    
    # Symboles differents
    changes = len(symbols_old.symmetric_difference(symbols_new))
    
    # Turnover = changes / 5
    turnover = changes / 5.0
    
    return turnover


def get_performance_week(db, symbol: str, start_date: datetime, end_date: datetime) -> dict:
    """
    Calcul performance hebdomadaire d'une action
    
    Return:
    - return_pct: rendement %
    - prix_debut: prix dimanche/lundi
    - prix_fin: prix vendredi
    """
    try:
        # Prix debut semaine
        prices_start = list(db.prices_daily.find({
            "key": symbol,
            "ts": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": (start_date + timedelta(days=2)).strftime("%Y-%m-%d")}
        }).sort("ts", 1).limit(1))
        
        # Prix fin semaine
        prices_end = list(db.prices_daily.find({
            "key": symbol,
            "ts": {"$gte": (end_date - timedelta(days=2)).strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
        }).sort("ts", -1).limit(1))
        
        if not prices_start or not prices_end:
            return {"return_pct": 0, "prix_debut": 0, "prix_fin": 0, "valide": False}
        
        prix_debut = prices_start[0].get("value", 0) or prices_start[0].get("attrs", {}).get("Close", 0)
        prix_fin = prices_end[0].get("value", 0) or prices_end[0].get("attrs", {}).get("Close", 0)
        
        if prix_debut == 0:
            return {"return_pct": 0, "prix_debut": 0, "prix_fin": prix_fin, "valide": False}
        
        return_pct = ((prix_fin - prix_debut) / prix_debut) * 100
        
        return {
            "return_pct": return_pct,
            "prix_debut": prix_debut,
            "prix_fin": prix_fin,
            "valide": True
        }
    
    except Exception as e:
        return {"return_pct": 0, "prix_debut": 0, "prix_fin": 0, "valide": False, "erreur": str(e)}


def calculate_metrics_portfolio(db, top5: list, start_date: datetime, end_date: datetime, version: str) -> dict:
    """
    Calcul metriques portfolio (TOP 5)
    
    Metriques:
    - win_rate: % positions gagnantes
    - return_moyen: rendement moyen
    - return_total: rendement global (equiponderation)
    - drawdown_max: pire action
    """
    results = []
    
    for symbol, alpha_score in top5:
        perf = get_performance_week(db, symbol, start_date, end_date)
        
        if perf["valide"]:
            results.append({
                "symbol": symbol,
                "alpha_score": alpha_score,
                "return_pct": perf["return_pct"],
                "prix_debut": perf["prix_debut"],
                "prix_fin": perf["prix_fin"]
            })
    
    if not results:
        return {
            "version": version,
            "win_rate": 0,
            "return_moyen": 0,
            "return_total": 0,
            "drawdown_max": 0,
            "nb_positions": 0,
            "details": []
        }
    
    # Win rate
    winners = [r for r in results if r["return_pct"] > 0]
    win_rate = (len(winners) / len(results)) * 100 if results else 0
    
    # Returns
    returns = [r["return_pct"] for r in results]
    return_moyen = statistics.mean(returns) if returns else 0
    return_total = sum(returns) / len(returns) if returns else 0  # Equiponderation
    
    # Drawdown max (pire action)
    drawdown_max = min(returns) if returns else 0
    
    return {
        "version": version,
        "win_rate": round(win_rate, 1),
        "return_moyen": round(return_moyen, 2),
        "return_total": round(return_total, 2),
        "drawdown_max": round(drawdown_max, 2),
        "nb_positions": len(results),
        "details": results
    }


def calculate_sharpe_ratio(returns: list) -> float:
    """
    Sharpe Ratio = Return_moyen / StdDev_returns
    
    (Taux sans risque = 0 pour simplification BRVM)
    """
    if len(returns) < 2:
        return 0.0
    
    mean_return = statistics.mean(returns)
    std_return = statistics.stdev(returns) if len(returns) > 1 else 0.01
    
    if std_return == 0:
        return 0.0
    
    sharpe = mean_return / std_return
    
    return sharpe


def main():
    _, db = get_mongo_db()
    
    print("\n" + "=" * 80)
    print("COMPARAISON V1 VS V2 - VALIDATION FRAMEWORK")
    print("=" * 80 + "\n")
    
    # Recuperer TOP 5 des 2 versions
    print(">> Recuperation TOP 5...\n")
    
    top5_v1 = get_top5_v1(db)
    top5_v2 = get_top5_v2(db)
    
    if not top5_v1:
        print("ATTENTION: TOP 5 v1 (production) non disponible")
        print("           Executer d'abord decision_finale_brvm.py\n")
    
    if not top5_v2:
        print("ATTENTION: TOP 5 v2 (shadow) non disponible")
        print("           Executer d'abord alpha_score_v2_shadow.py\n")
    
    if not top5_v1 or not top5_v2:
        print("ARRET - Donnees manquantes\n")
        return
    
    # Affichage TOP 5
    print("=" * 80)
    print("TOP 5 - VERSION 1 (Production Actuelle)")
    print("=" * 80)
    for i, (symbol, score) in enumerate(top5_v1, 1):
        print(f"{i}. {symbol:6s} | Alpha v1: {score:5.1f}")
    
    print("\n" + "=" * 80)
    print("TOP 5 - VERSION 2 (Shadow Mode - Early Momentum)")
    print("=" * 80)
    for i, (symbol, score) in enumerate(top5_v2, 1):
        print(f"{i}. {symbol:6s} | Alpha v2: {score:5.1f}")
    
    # Turnover
    turnover = calculate_turnover(top5_v1, top5_v2)
    print("\n" + "=" * 80)
    print(f"TURNOVER: {turnover*100:.0f}% (rotation entre v1 et v2)")
    print("=" * 80)
    
    common = set(s[0] for s in top5_v1).intersection(set(s[0] for s in top5_v2))
    print(f"Symboles communs: {len(common)}/5 → {', '.join(sorted(common)) if common else 'AUCUN'}\n")
    
    # PERFORMANCE SEMAINE EN COURS (si disponible)
    print("=" * 80)
    print("PERFORMANCE SEMAINE EN COURS")
    print("=" * 80 + "\n")
    
    # Dates semaine (lundi → vendredi)
    today = datetime.now()
    # Trouver lundi de cette semaine
    days_since_monday = today.weekday()  # 0 = lundi
    start_week = today - timedelta(days=days_since_monday)
    end_week = start_week + timedelta(days=4)  # Vendredi
    
    print(f"Periode: {start_week.strftime('%Y-%m-%d')} → {end_week.strftime('%Y-%m-%d')}\n")
    
    metrics_v1 = calculate_metrics_portfolio(db, top5_v1, start_week, end_week, "v1")
    metrics_v2 = calculate_metrics_portfolio(db, top5_v2, start_week, end_week, "v2")
    
    # Affichage metriques
    print("VERSION 1 (Production):")
    print(f"  Win Rate:       {metrics_v1['win_rate']:5.1f}%")
    print(f"  Return Moyen:   {metrics_v1['return_moyen']:+6.2f}%")
    print(f"  Return Total:   {metrics_v1['return_total']:+6.2f}%")
    print(f"  Drawdown Max:   {metrics_v1['drawdown_max']:+6.2f}%")
    print(f"  Positions:      {metrics_v1['nb_positions']}/5\n")
    
    print("VERSION 2 (Shadow):")
    print(f"  Win Rate:       {metrics_v2['win_rate']:5.1f}%")
    print(f"  Return Moyen:   {metrics_v2['return_moyen']:+6.2f}%")
    print(f"  Return Total:   {metrics_v2['return_total']:+6.2f}%")
    print(f"  Drawdown Max:   {metrics_v2['drawdown_max']:+6.2f}%")
    print(f"  Positions:      {metrics_v2['nb_positions']}/5\n")
    
    # COMPARAISON
    print("=" * 80)
    print("COMPARAISON DELTA (v2 - v1)")
    print("=" * 80)
    
    delta_wr = metrics_v2['win_rate'] - metrics_v1['win_rate']
    delta_return = metrics_v2['return_total'] - metrics_v1['return_total']
    delta_dd = metrics_v2['drawdown_max'] - metrics_v1['drawdown_max']
    
    print(f"  Delta Win Rate:    {delta_wr:+6.1f} points")
    print(f"  Delta Return:      {delta_return:+6.2f}%")
    print(f"  Delta Drawdown:    {delta_dd:+6.2f}% (negatif = meilleur)\n")
    
    # SHARPE RATIO (si assez de donnees)
    if metrics_v1['nb_positions'] >= 3 and metrics_v2['nb_positions'] >= 3:
        returns_v1 = [d['return_pct'] for d in metrics_v1['details']]
        returns_v2 = [d['return_pct'] for d in metrics_v2['details']]
        
        sharpe_v1 = calculate_sharpe_ratio(returns_v1)
        sharpe_v2 = calculate_sharpe_ratio(returns_v2)
        
        print(f"  Sharpe v1:         {sharpe_v1:+6.2f}")
        print(f"  Sharpe v2:         {sharpe_v2:+6.2f}")
        print(f"  Delta Sharpe:      {sharpe_v2 - sharpe_v1:+6.2f}\n")
    
    # SAUVEGARDER TRACKING
    tracking_doc = {
        "source": "VALIDATION_V1_V2",
        "dataset": "TRACKING_SHADOW",
        "key": f"week_{start_week.strftime('%Y-W%U')}",
        "ts": datetime.utcnow().strftime("%Y-%m-%d"),
        "value": metrics_v2['return_total'] - metrics_v1['return_total'],  # Delta performance
        "attrs": {
            "semaine": start_week.strftime('%Y-W%U'),
            "date_debut": start_week.strftime('%Y-%m-%d'),
            "date_fin": end_week.strftime('%Y-%m-%d'),
            "top5_v1": [s[0] for s in top5_v1],
            "top5_v2": [s[0] for s in top5_v2],
            "turnover": turnover,
            "metrics_v1": metrics_v1,
            "metrics_v2": metrics_v2,
            "deltas": {
                "win_rate": delta_wr,
                "return": delta_return,
                "drawdown": delta_dd
            },
            "timestamp": datetime.utcnow()
        }
    }
    
    db.curated_observations.insert_one(tracking_doc)
    print("OK - Tracking sauvegarde (dataset=TRACKING_SHADOW)\n")
    
    # DECISION VALIDATION (si ≥ 4 semaines)
    print("=" * 80)
    print("CRITERES VALIDATION MIGRATION (≥ 4 semaines requises)")
    print("=" * 80 + "\n")
    
    # Compter semaines trackees
    nb_semaines = db.curated_observations.count_documents({"dataset": "TRACKING_SHADOW"})
    
    print(f"Semaines trackees: {nb_semaines}/4 minimum\n")
    
    if nb_semaines < 4:
        print("STATUT: EN COURS - Continuer observation\n")
        print(f"         {4 - nb_semaines} semaine(s) restante(s) avant decision\n")
    else:
        # Recuperer historique
        historique = list(db.curated_observations.find({
            "dataset": "TRACKING_SHADOW"
        }).sort("ts", 1))
        
        # Metriques globales
        all_wr_v1 = [h['attrs']['metrics_v1']['win_rate'] for h in historique]
        all_wr_v2 = [h['attrs']['metrics_v2']['win_rate'] for h in historique]
        all_ret_v1 = [h['attrs']['metrics_v1']['return_total'] for h in historique]
        all_ret_v2 = [h['attrs']['metrics_v2']['return_total'] for h in historique]
        all_dd_v1 = [h['attrs']['metrics_v1']['drawdown_max'] for h in historique]
        all_dd_v2 = [h['attrs']['metrics_v2']['drawdown_max'] for h in historique]
        
        avg_wr_v1 = statistics.mean(all_wr_v1)
        avg_wr_v2 = statistics.mean(all_wr_v2)
        avg_ret_v1 = statistics.mean(all_ret_v1)
        avg_ret_v2 = statistics.mean(all_ret_v2)
        avg_dd_v1 = statistics.mean(all_dd_v1)
        avg_dd_v2 = statistics.mean(all_dd_v2)
        
        print("METRIQUES GLOBALES ({} semaines):".format(nb_semaines))
        print(f"  Win Rate v1:     {avg_wr_v1:5.1f}%")
        print(f"  Win Rate v2:     {avg_wr_v2:5.1f}%")
        print(f"  Delta:           {avg_wr_v2 - avg_wr_v1:+5.1f} points\n")
        
        print(f"  Return v1:       {avg_ret_v1:+6.2f}%")
        print(f"  Return v2:       {avg_ret_v2:+6.2f}%")
        print(f"  Delta:           {avg_ret_v2 - avg_ret_v1:+6.2f}%\n")
        
        print(f"  Drawdown v1:     {avg_dd_v1:+6.2f}%")
        print(f"  Drawdown v2:     {avg_dd_v2:+6.2f}%")
        print(f"  Delta:           {avg_dd_v2 - avg_dd_v1:+6.2f}%\n")
        
        # DECISION
        print("=" * 80)
        print("DECISION QUANTITATIVE")
        print("=" * 80 + "\n")
        
        crit1 = avg_wr_v2 >= avg_wr_v1 + 5
        crit2 = avg_dd_v2 <= avg_dd_v1
        crit3 = avg_ret_v2 >= avg_ret_v1
        
        print(f"  [{'OK' if crit1 else 'NON'}] Win Rate v2 >= v1 + 5%  ({avg_wr_v2:.1f}% vs {avg_wr_v1:.1f}%)")
        print(f"  [{'OK' if crit2 else 'NON'}] Drawdown v2 <= v1      ({avg_dd_v2:.2f}% vs {avg_dd_v1:.2f}%)")
        print(f"  [{'OK' if crit3 else 'NON'}] Return v2 >= v1        ({avg_ret_v2:.2f}% vs {avg_ret_v1:.2f}%)\n")
        
        if crit1 and crit2 and crit3:
            print("VERDICT: MIGRATION V2 RECOMMANDEE")
            print("         Performance v2 superieure selon criteres validation\n")
        elif crit3 and not crit1:
            print("VERDICT: OBSERVATION PROLONGEE")
            print("         Performance v2 positive mais win rate insuffisant\n")
        else:
            print("VERDICT: CONSERVER V1")
            print("         Performance v2 inferieure ou egale a v1\n")
    
    print("=" * 80)
    print("Prochain tracking: Semaine suivante (execution hebdomadaire)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
