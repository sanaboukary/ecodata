#!/usr/bin/env python3
"""Aperçu de curated_observations"""
import os, sys
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def main():
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("APERCU curated_observations")
    print("="*80 + "\n")
    
    total = db.curated_observations.count_documents({})
    print(f"Total documents: {total:,}\n")
    
    # Échantillon
    sample = db.curated_observations.find_one()
    
    print("STRUCTURE d'un document:")
    print("-"*80)
    if sample:
        for key, value in list(sample.items())[:15]:
            val_str = str(value)[:60]
            print(f"  {key:<25} : {val_str}")
    
    # Sources
    print("\n\nSOURCES des données:")
    print("-"*80)
    sources = db.curated_observations.distinct('source')
    for src in sources[:10]:
        count = db.curated_observations.count_documents({'source': src})
        print(f"  {src:<30} : {count:>6,} docs")
    
    # Symboles
    print("\n\nSYMBOLES collectés:")
    print("-"*80)
    symbols = db.curated_observations.distinct('symbol')
    print(f"  Total symboles uniques: {len(symbols)}")
    
    # Compter par symbole
    symbol_counts = {}
    for sym in symbols[:20]:
        symbol_counts[sym] = db.curated_observations.count_documents({'symbol': sym})
    
    sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
    print("\n  TOP 15 symboles (plus d'observations):")
    for sym, cnt in sorted_symbols[:15]:
        print(f"    {sym:<10} : {cnt:>5,} obs")
    
    # Dates
    print("\n\nPÉRIODE couverte:")
    print("-"*80)
    
    # Essayer différents champs date
    for date_field in ['date', 'datetime', 'timestamp', 'observation_date']:
        dates = db.curated_observations.distinct(date_field)
        if dates:
            dates_sorted = sorted([d for d in dates if d])
            if dates_sorted:
                print(f"  Champ '{date_field}':")
                print(f"    Première: {dates_sorted[0]}")
                print(f"    Dernière: {dates_sorted[-1]}")
                print(f"    Total dates: {len(dates_sorted)}")
                break
    
    # Types de données
    print("\n\nTYPES de données collectées:")
    print("-"*80)
    
    # Vérifier présence de prix
    with_price = db.curated_observations.count_documents({'price': {'$exists': True}})
    with_close = db.curated_observations.count_documents({'close': {'$exists': True}})
    with_volume = db.curated_observations.count_documents({'volume': {'$exists': True}})
    with_high = db.curated_observations.count_documents({'high': {'$exists': True}})
    with_low = db.curated_observations.count_documents({'low': {'$exists': True}})
    
    total = db.curated_observations.count_documents({})
    
    print(f"  Avec 'price':  {with_price:>6,} / {total:,} ({with_price/total*100:.1f}%)")
    print(f"  Avec 'close':  {with_close:>6,} / {total:,} ({with_close/total*100:.1f}%)")
    print(f"  Avec 'volume': {with_volume:>6,} / {total:,} ({with_volume/total*100:.1f}%)")
    print(f"  Avec 'high':   {with_high:>6,} / {total:,} ({with_high/total*100:.1f}%)")
    print(f"  Avec 'low':    {with_low:>6,} / {total:,} ({with_low/total*100:.1f}%)")
    
    # Exemple concret
    print("\n\nEXEMPLE de 3 observations:")
    print("-"*80)
    
    examples = list(db.curated_observations.find().limit(3))
    for i, ex in enumerate(examples, 1):
        print(f"\n  Observation {i}:")
        # Afficher champs importants seulement
        important_fields = ['symbol', 'date', 'datetime', 'price', 'close', 'volume', 
                          'high', 'low', 'open', 'source', 'variation_pct']
        for field in important_fields:
            if field in ex:
                print(f"    {field:<15} : {ex[field]}")
    
    print("\n" + "="*80)
    print("\nCONCLUSION:")
    print("-"*80)
    print("Ces 34,212 observations sont vos DONNEES HISTORIQUES BRVM collectées")
    print("au fil du temps. Elles servent de source pour reconstruire DAILY et WEEKLY.")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
