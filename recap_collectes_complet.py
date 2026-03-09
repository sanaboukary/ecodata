#!/usr/bin/env python3
"""Récapitulatif complet de toutes les collectes"""
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017')
db = client['centralisation_db']

print("\n" + "="*100)
print(f"RÉCAPITULATIF COMPLET DES COLLECTES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# Total par source
print("\n📊 OBSERVATIONS PAR SOURCE")
print("-" * 100)

sources = ['BRVM', 'BRVM_PUBLICATION', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG']
total_general = 0

for source in sources:
    count = db.curated_observations.count_documents({'source': source})
    total_general += count
    
    # Pour BRVM, vérifier data_quality
    if source == 'BRVM':
        reel = db.curated_observations.count_documents({
            'source': source,
            'attrs.data_quality': {'$in': ['REAL_SCRAPER', 'REAL_MANUAL']}
        })
        simule = count - reel
        print(f"  {source:20s}: {count:6d}  (REEL: {reel:6d}, SIMULÉ: {simule:6d})")
    else:
        print(f"  {source:20s}: {count:6d}")

print(f"  {'-'*20}   {'-'*6}")
print(f"  {'TOTAL':20s}: {total_general:6d}")

# BRVM - Dernières collectes
print("\n" + "-" * 100)
print("📈 BRVM - COURS ACTIONS (10 dernières)")
print("-" * 100)

brvm_recent = db.curated_observations.find({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
}).sort('attrs.collecte_datetime', -1).limit(10)

print(f"{'DATE':<12} {'HEURE':<10} {'SYMBOLE':<8} {'PRIX':>10} {'VOLUME':>10} {'VAR%':>8} {'QUALITY':<15}")
print("-" * 100)

for obs in brvm_recent:
    attrs = obs.get('attrs', {})
    print(
        f"{obs['ts']:<12} "
        f"{attrs.get('collecte_heure', 'N/A'):<10} "
        f"{obs['key']:<8} "
        f"{obs['value']:>10,.0f} "
        f"{attrs.get('volume', 0):>10,} "
        f"{attrs.get('variation', 0):>+7.2f}% "
        f"{attrs.get('data_quality', 'UNKNOWN'):<15}"
    )

# Publications BRVM
print("\n" + "-" * 100)
print("📰 PUBLICATIONS BRVM (10 dernières)")
print("-" * 100)

pubs_count = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATION'})

if pubs_count > 0:
    # Par type
    types = db.curated_observations.aggregate([
        {'$match': {'source': 'BRVM_PUBLICATION'}},
        {'$group': {'_id': '$dataset', 'count': {'$sum': 1}}}
    ])
    
    print("\nPar type:")
    for t in types:
        print(f"  {t['_id']:25s}: {t['count']:4d}")
    
    # Dernières publications
    print(f"\nExemples récents:")
    print(f"{'TYPE':<25} {'TITRE':<75}")
    print("-" * 100)
    
    pubs = db.curated_observations.find({
        'source': 'BRVM_PUBLICATION'
    }).sort('attrs.collecte_datetime', -1).limit(10)
    
    for pub in pubs:
        attrs = pub.get('attrs', {})
        titre = attrs.get('titre', 'N/A')[:72]
        type_doc = pub.get('dataset', 'N/A')[:22]
        print(f"{type_doc:<25} {titre:<75}")
else:
    print("  Aucune publication collectée")

# WorldBank
print("\n" + "-" * 100)
print("🌍 WORLD BANK (10 dernières observations)")
print("-" * 100)

wb_count = db.curated_observations.count_documents({'source': 'WorldBank'})
print(f"Total: {wb_count}")

if wb_count > 0:
    wb_recent = db.curated_observations.find({
        'source': 'WorldBank'
    }).sort('ts', -1).limit(10)
    
    print(f"\n{'PAYS':<4} {'INDICATEUR':<25} {'DATE':<12} {'VALEUR':>15}")
    print("-" * 100)
    
    for obs in wb_recent:
        attrs = obs.get('attrs', {})
        pays = attrs.get('country', 'N/A')[:3]
        indicateur = obs['dataset'][:22]
        print(f"{pays:<4} {indicateur:<25} {obs['ts']:<12} {obs['value']:>15,.2f}")

print("\n" + "="*100)
print("FIN DU RÉCAPITULATIF")
print("="*100)

client.close()
