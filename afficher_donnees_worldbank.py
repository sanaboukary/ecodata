#!/usr/bin/env python3
"""
Affichage des donnees World Bank en base
"""
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from plateforme_centralisation.mongo import get_mongo_db

def afficher_donnees_worldbank():
    """Afficher toutes les donnees World Bank"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("DONNEES WORLD BANK EN BASE DE DONNEES")
    print("="*80)
    
    # Compter total
    total = db.curated_observations.count_documents({'source': 'WorldBank'})
    print(f"\nTotal observations World Bank: {total:,}")
    
    if total == 0:
        print("\nAucune donnee World Bank trouvee.")
        print("\nPour collecter les donnees World Bank:")
        print("  python manage.py ingest_source --source worldbank --indicator SP.POP.TOTL --country CI")
        return
    
    # Statistiques par indicateur
    print("\n" + "-"*80)
    print("REPARTITION PAR INDICATEUR:")
    print("-"*80)
    
    pipeline = [
        {'$match': {'source': 'WorldBank'}},
        {'$group': {
            '_id': '$dataset',
            'count': {'$sum': 1},
            'pays': {'$addToSet': '$key'}
        }},
        {'$sort': {'count': -1}}
    ]
    
    for result in db.curated_observations.aggregate(pipeline):
        indicateur = result['_id']
        count = result['count']
        pays = result['pays']
        print(f"{indicateur:40} : {count:>6,} obs ({len(pays)} pays)")
    
    # Statistiques par pays
    print("\n" + "-"*80)
    print("REPARTITION PAR PAYS:")
    print("-"*80)
    
    pipeline = [
        {'$match': {'source': 'WorldBank'}},
        {'$group': {
            '_id': '$key',
            'count': {'$sum': 1},
            'indicateurs': {'$addToSet': '$dataset'}
        }},
        {'$sort': {'count': -1}}
    ]
    
    for result in db.curated_observations.aggregate(pipeline):
        pays = result['_id']
        count = result['count']
        nb_indicateurs = len(result['indicateurs'])
        print(f"{pays:15} : {count:>6,} obs ({nb_indicateurs} indicateurs)")
    
    # Echantillon de donnees recentes
    print("\n" + "-"*80)
    print("ECHANTILLON - 10 DERNIERES OBSERVATIONS:")
    print("-"*80)
    print(f"{'PAYS':<8} {'INDICATEUR':<40} {'ANNEE':<6} {'VALEUR':>15}")
    print("-"*80)
    
    for obs in db.curated_observations.find(
        {'source': 'WorldBank'}
    ).sort('ts', -1).limit(10):
        pays = obs.get('key', 'N/A')
        indicateur = obs.get('dataset', 'N/A')
        annee = obs.get('ts', 'N/A')
        valeur = obs.get('value', 0)
        
        # Formater la valeur
        if isinstance(valeur, (int, float)):
            if valeur > 1_000_000_000:
                valeur_str = f"{valeur/1_000_000_000:.2f}B"
            elif valeur > 1_000_000:
                valeur_str = f"{valeur/1_000_000:.2f}M"
            else:
                valeur_str = f"{valeur:,.2f}"
        else:
            valeur_str = str(valeur)
        
        print(f"{pays:<8} {indicateur:<40} {annee:<6} {valeur_str:>15}")
    
    # Details complets pour quelques observations
    print("\n" + "-"*80)
    print("DETAILS COMPLETS (3 exemples):")
    print("-"*80)
    
    for i, obs in enumerate(db.curated_observations.find(
        {'source': 'WorldBank'}
    ).limit(3), 1):
        print(f"\n[{i}] {obs.get('dataset', 'N/A')} - {obs.get('key', 'N/A')} ({obs.get('ts', 'N/A')})")
        print(f"    Valeur: {obs.get('value', 'N/A')}")
        if 'attrs' in obs and obs['attrs']:
            print(f"    Attributs: {obs['attrs']}")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    afficher_donnees_worldbank()
