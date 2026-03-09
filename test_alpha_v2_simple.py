#!/usr/bin/env python3
"""Test simple ALPHA v2 - Une seule action"""

import os
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def test_one_action(db, symbol):
    """Test calcul ALPHA v2 pour une action"""
    
    print(f"\n{'='*60}")
    print(f"TEST ALPHA V2 - {symbol}")
    print(f"{'='*60}\n")
    
    # 1. Vérifier données disponibles
    print("1. Verification donnees techniques...")
    tech = db.curated_observations.find_one({
        "dataset": "ANALYSE_TECHNIQUE_SIMPLE",
        "key": symbol
    })
    
    if tech:
        rs = tech.get("attrs", {}).get("rs", 0)
        print(f"   ✓ RS: {rs:.1f}")
    else:
        print(f"   ✗ Pas de donnees techniques")
        return
    
    # 2. Vérifier prix
    print("\n2. Verification prix...")
    prices = list(db.prices_daily.find({
        "key": symbol
    }).sort("ts", -1).limit(5))
    
    if prices:
        print(f"   ✓ {len(prices)} jours de prix")
        latest = prices[0]
        close = latest.get("attrs", {}).get("Close", 0)
        volume = latest.get("attrs", {}).get("Volume", 0)
        print(f"   Dernier: Close={close} FCFA, Volume={volume}")
    else:
        print(f"   ✗ Pas de prix")
        return
    
    # 3. Vérifier agrégation sémantique
    print("\n3. Verification sentiment...")
    sentiment = db.curated_observations.find_one({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if sentiment:
        sent_value = sentiment.get("value", 0)
        print(f"   ✓ Sentiment: {sent_value:.1f}")
    else:
        print(f"   ⚠ Pas de sentiment (score = 50 par defaut)")
    
    # 4. Vérifier événements
    print("\n4. Verification evenements...")
    events = list(db.curated_observations.find({
        "dataset": "PUBLICATIONS_ENRICHIES_BRVM",
        "attrs.symboles_detectes": symbol
    }).sort("ts", -1).limit(3))
    
    if events:
        print(f"   ✓ {len(events)} evenements recents")
        for e in events[:2]:
            cat = e.get("attrs", {}).get("categorie_finale", "?")
            titre = e.get("attrs", {}).get("titre", "?")[:50]
            print(f"     - {cat}: {titre}")
    else:
        print(f"   ○ Pas d'evenements (normal)")
    
    print(f"\n{'='*60}")
    print(f"DONNEES SUFFISANTES pour calcul ALPHA v2")
    print(f"{'='*60}\n")

def main():
    _, db = get_mongo_db()
    
    # Tester avec BICC (généralement liquide)
    test_one_action(db, "BICC")

if __name__ == "__main__":
    main()
