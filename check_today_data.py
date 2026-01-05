#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Vérification rapide des données collectées aujourd'hui"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def check_today_brvm():
    client, db = get_mongo_db()
    
    today = "2026-01-05"
    
    # Compter observations BRVM aujourd'hui
    count_today = db.curated_observations.count_documents({
        "source": "BRVM",
        "ts": today
    })
    
    # Dernière date avec données BRVM
    last_obs = list(db.curated_observations.find({
        "source": "BRVM"
    }).sort("ts", -1).limit(1))
    
    print(f"\n{'='*60}")
    print(f"VERIFICATION COLLECTE BRVM - {today}")
    print(f"{'='*60}\n")
    
    print(f"Observations BRVM pour aujourd'hui ({today}): {count_today}")
    
    if last_obs:
        last_date = last_obs[0].get('ts', 'N/A')
        last_key = last_obs[0].get('key', 'N/A')
        last_value = last_obs[0].get('value', 'N/A')
        data_quality = last_obs[0].get('attrs', {}).get('data_quality', 'N/A')
        
        print(f"\nDerniere observation BRVM:")
        print(f"  - Date: {last_date}")
        print(f"  - Symbole: {last_key}")
        print(f"  - Valeur: {last_value}")
        print(f"  - Qualite: {data_quality}")
    else:
        print("\nAucune donnee BRVM trouvee dans la base")
    
    # Total observations BRVM
    total_brvm = db.curated_observations.count_documents({"source": "BRVM"})
    print(f"\nTotal observations BRVM dans la base: {total_brvm}")
    
    print(f"\n{'='*60}\n")
    
    # Verdict
    if count_today > 0:
        print(f"✅ COLLECTE EFFECTUEE AUJOURD'HUI ({count_today} observations)")
    else:
        print("❌ AUCUNE COLLECTE AUJOURD'HUI")
        if last_obs:
            print(f"   Derniere collecte: {last_obs[0].get('ts', 'N/A')}")

if __name__ == "__main__":
    check_today_brvm()
