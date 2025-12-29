#!/usr/bin/env python3
"""
📤 EXPORTER LES DONNÉES RÉELLES EXISTANTES
Extrait les 317 observations REAL_MANUAL + REAL_SCRAPER de MongoDB vers CSV
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def exporter_donnees_reelles():
    """Exporte données RÉELLES de MongoDB vers CSV"""
    
    print("\n" + "="*80)
    print("EXPORT DONNEES REELLES BRVM")
    print("="*80 + "\n")
    
    client, db = get_mongo_db()
    
    # Récupérer toutes les données RÉELLES
    cursor = db.curated_observations.find({
        'source': 'BRVM',
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    }).sort('ts', 1)
    
    observations = list(cursor)
    
    print(f"Observations RÉELLES trouvées: {len(observations)}")
    
    if not observations:
        print("❌ Aucune donnée réelle à exporter")
        return
    
    # Grouper par date
    dates = {}
    for obs in observations:
        date = obs['ts']
        if date not in dates:
            dates[date] = []
        dates[date].append(obs)
    
    print(f"Jours avec données: {len(dates)}")
    print(f"Première date: {min(dates.keys())}")
    print(f"Dernière date: {max(dates.keys())}")
    print()
    
    # Générer CSV
    filename = f'donnees_reelles_brvm_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('DATE,SYMBOL,CLOSE,VOLUME,VARIATION\n')
        
        for obs in observations:
            symbol = obs['key']
            date = obs['ts']
            close = obs['value']
            
            attrs = obs.get('attrs', {})
            volume = attrs.get('volume', 0)
            variation = attrs.get('variation', 0)
            
            f.write(f'{date},{symbol},{close},{volume},{variation}\n')
    
    print(f"✅ Export réussi: {filename}")
    print(f"   {len(observations)} lignes exportées")
    print()
    
    # Statistiques par action
    print("Actions présentes:")
    actions = {}
    for obs in observations:
        symbol = obs['key']
        actions[symbol] = actions.get(symbol, 0) + 1
    
    for symbol in sorted(actions.keys()):
        count = actions[symbol]
        print(f"  {symbol:<12} {count:>3} observations")
    
    print()
    print("="*80)
    print("UTILISATION")
    print("="*80)
    print()
    print("Ce fichier contient vos données RÉELLES existantes.")
    print("Vous pouvez:")
    print()
    print("1. Le compléter avec nouvelles données")
    print("2. Le fusionner avec un template 60 jours")
    print("3. Le réimporter après nettoyage:")
    print(f"   python collecter_csv_automatique.py --dossier .")
    print()

if __name__ == '__main__':
    exporter_donnees_reelles()
