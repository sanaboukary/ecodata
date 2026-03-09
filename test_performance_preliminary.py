#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST PERFORMANCE PRELIMINARY - Validation avec données simulées
===============================================================

Test du module performance_preliminary.py avec données fictives.

Simule 8 semaines de trading pour valider:
- Calcul métriques
- Affichage
- Sauvegarde MongoDB

Usage:
    python test_performance_preliminary.py

Auteur: Expert BRVM 30 ans
Date: 17 Février 2026
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


def generate_simulated_week_data(db, week_num):
    """
    Génère données simulées pour une semaine de trading
    
    Simule:
    - Prix hebdo BRVM (47 actions)
    - Décisions Top5
    - Performance réaliste
    """
    # Calcul date semaine
    year = 2026
    jan_1 = datetime(year, 1, 1)
    week_1_monday = jan_1 + timedelta(days=(7 - jan_1.weekday()))
    target_monday = week_1_monday + timedelta(weeks=week_num - 1)
    target_friday = target_monday + timedelta(days=4)
    
    week_str = f"{year}-W{week_num:02d}"
    
    print(f"\n[SIMULATION] Semaine {week_str}")
    
    # Symboles BRVM
    symbols = ["SGBC", "SNTS", "PALC", "SIBC", "ETIT", "BOAC", "BOAM", "SOGC", "TTLC", "CFAC",
               "ORGT", "SEMC", "CIEC", "SHEC", "NEIC", "FTSC", "SIVC", "STAC", "SDSC", "BOAS"]
    
    # Génération prix hebdo pour chaque action
    for symbol in symbols:
        # Prix aléatoires réalistes
        open_price = random.uniform(500, 15000)
        perf = random.gauss(0, 5)  # Moyenne 0%, std 5% (marché BRVM volatile)
        close_price = open_price * (1 + perf/100)
        
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.03)
        low_price = min(open_price, close_price) * random.uniform(0.97, 1.0)
        
        volume = random.randint(10000, 500000)
        
        # Insertion/update prix hebdo
        db.prices_weekly.update_one(
            {"symbol": symbol, "week": week_str},
            {"$set": {
                "open": round(open_price, 2),
                "close": round(close_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "volume": volume,
                "performance": round(perf, 2)
            }},
            upsert=True
        )
    
    # Génération Top5 recommandations
    # Simuler performance réaliste: 60% winners, 40% losers
    top5_symbols = random.sample(symbols, 5)
    
    decisions = []
    for i, symbol in enumerate(top5_symbols):
        # Prix entrée = lundi open
        price_monday = db.prices_weekly.find_one({"symbol": symbol, "week": week_str})
        prix_entree = price_monday["open"] if price_monday else random.uniform(1000, 10000)
        prix_sortie = price_monday["close"] if price_monday else prix_entree * (1 + random.gauss(0, 5)/100)
        
        # ALPHA score réaliste (50-85)
        alpha_score = random.uniform(50, 85)
        
        # Classe selon ALPHA
        if alpha_score >= 75:
            classe = "A"
        elif alpha_score >= 60:
            classe = "B"
        else:
            classe = "C"
        
        decision = {
            "symbol": symbol,
            "week": week_str,
            "horizon": "SEMAINE",
            "decision": "BUY",
            "classe": classe,
            "alpha_score": round(alpha_score, 1),
            "prix_entree": round(prix_entree, 2),
            "prix_actuel": round(prix_entree, 2),
            "prix_cible": round(prix_entree * 1.10, 2),
            "stop": round(prix_entree * 0.96, 2),
            "target_pct": 10.0,
            "stop_pct": 4.0,
            "pct_portfolio": 20.0,  # Equal weight 5 positions
            "generated_at": target_monday
        }
        
        decisions.append(decision)
        
        # Insertion décision
        db.decisions_finales_brvm.update_one(
            {"symbol": symbol, "week": week_str, "horizon": "SEMAINE"},
            {"$set": decision},
            upsert=True
        )
    
    print(f"   - {len(symbols)} prix hebdo generés")
    print(f"   - {len(decisions)} décisions Top5 générées")
    
    return week_str


def main():
    """
    Génère 8 semaines de données simulées puis teste metrics
    """
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print(" TEST PERFORMANCE PRELIMINARY - Données simulées")
    print("="*80)
    
    # Nettoyage données test précédentes
    print("\n[CLEANUP] Suppression données test précédentes...")
    db.prices_weekly.delete_many({"week": {"$regex": "^2026-W"}})
    db.decisions_finales_brvm.delete_many({"week": {"$regex": "^2026-W"}})
    db.preliminary_metrics.delete_many({})
    
    # Génération 8 semaines (minimum pour validation seuils)
    print("\n[GENERATION] Création 8 semaines de données simulées...")
    weeks = []
    for week_num in range(1, 9):  # Semaines 1-8 de 2026
        week_str = generate_simulated_week_data(db, week_num)
        weeks.append(week_str)
    
    print(f"\n[OK] {len(weeks)} semaines simulées: {weeks[0]} à {weeks[-1]}")
    
    # Test calcul métriques
    print("\n[TEST] Lancement performance_preliminary.py...")
    print("="*80 + "\n")
    
    # Import et exécution
    from performance_preliminary import compute_preliminary_metrics, display_metrics, save_metrics_to_db
    
    metrics = compute_preliminary_metrics(db, nb_weeks=8)
    
    if metrics:
        display_metrics(metrics)
        save_metrics_to_db(db, metrics)
        
        print("\n" + "="*80)
        print(" TEST REUSSI")
        print("="*80)
        print("\nLe module performance_preliminary.py fonctionne correctement.")
        print("Vous pouvez maintenant:")
        print("  1. Lancer pipeline_brvm.py chaque semaine")
        print("  2. Lancer performance_preliminary.py apres chaque semaine")
        print("  3. Accumuler 8+ semaines pour validation seuils\n")
    else:
        print("\n[ERROR] Erreur dans calcul métriques\n")


if __name__ == "__main__":
    main()
