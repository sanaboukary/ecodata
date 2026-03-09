#!/usr/bin/env python3
"""
📊 LISTE DES INDICATEURS BANQUE MONDIALE
Affiche tous les indicateurs World Bank collectés
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def lister_indicateurs_worldbank():
    """Lister tous les indicateurs World Bank"""
    _, db = get_mongo_db()
    
    print("=" * 100)
    print("📊 INDICATEURS BANQUE MONDIALE")
    print("=" * 100)
    
    # Compter total observations
    total = db.curated_observations.count_documents({'source': 'WorldBank'})
    print(f"\n📈 Total observations WorldBank: {total:,}")
    
    # Lister les indicateurs (datasets)
    pipeline = [
        {'$match': {'source': 'WorldBank'}},
        {'$group': {
            '_id': '$dataset',
            'count': {'$sum': 1},
            'pays': {'$addToSet': '$key'},
            'sample_value': {'$first': '$value'},
            'latest_date': {'$max': '$ts'}
        }},
        {'$sort': {'count': -1}}
    ]
    
    indicateurs = list(db.curated_observations.aggregate(pipeline))
    
    print(f"\n📋 {len(indicateurs)} indicateurs trouvés:\n")
    print(f"{'CODE':<15} {'OBSERVATIONS':>12} {'PAYS':>6} {'DERNIÈRE DATE':<15} {'EXEMPLE VALEUR':>15}")
    print(f"{'-'*15} {'-'*12} {'-'*6} {'-'*15} {'-'*15}")
    
    for ind in indicateurs:
        code = ind['_id']
        count = ind['count']
        nb_pays = len(ind['pays'])
        latest = ind['latest_date'][:10] if ind['latest_date'] else 'N/A'
        sample = ind['sample_value']
        
        # Formater la valeur
        if isinstance(sample, (int, float)):
            if sample > 1_000_000:
                sample_str = f"{sample/1_000_000:.1f}M"
            elif sample > 1000:
                sample_str = f"{sample/1000:.1f}K"
            else:
                sample_str = f"{sample:.2f}"
        else:
            sample_str = str(sample)[:15]
        
        print(f"{code:<15} {count:>12,} {nb_pays:>6} {latest:<15} {sample_str:>15}")
    
    # Détail par pays pour quelques indicateurs clés
    print("\n" + "=" * 100)
    print("🌍 DÉTAIL PAR PAYS (Indicateurs clés)")
    print("=" * 100)
    
    indicateurs_cles = ['SP.POP.TOTL', 'NY.GDP.MKTP.CD', 'FP.CPI.TOTL.ZG', 'SE.PRM.ENRR']
    noms_indicateurs = {
        'SP.POP.TOTL': 'Population totale',
        'NY.GDP.MKTP.CD': 'PIB ($ US courants)',
        'FP.CPI.TOTL.ZG': 'Inflation (IPC %)',
        'SE.PRM.ENRR': 'Taux scolarisation primaire'
    }
    
    for ind_code in indicateurs_cles:
        obs = list(db.curated_observations.find({
            'source': 'WorldBank',
            'dataset': ind_code
        }).sort('ts', -1).limit(8))
        
        if obs:
            nom = noms_indicateurs.get(ind_code, ind_code)
            print(f"\n📊 {ind_code} - {nom}")
            print(f"   {len(obs)} observations récentes:")
            
            for o in obs[:8]:
                pays = o['key']
                date = o['ts'][:10]
                value = o['value']
                
                if isinstance(value, (int, float)):
                    if value > 1_000_000_000:
                        value_str = f"{value/1_000_000_000:.2f} Mds"
                    elif value > 1_000_000:
                        value_str = f"{value/1_000_000:.2f} M"
                    else:
                        value_str = f"{value:,.2f}"
                else:
                    value_str = str(value)
                
                print(f"   - {pays:<3} | {date} | {value_str}")
    
    print("\n" + "=" * 100)

if __name__ == '__main__':
    lister_indicateurs_worldbank()
