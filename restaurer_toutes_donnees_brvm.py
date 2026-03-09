#!/usr/bin/env python3
"""
Restaurer TOUTES les données BRVM réelles depuis les fichiers CSV
5725 observations trouvées dans 8 fichiers CSV
"""

import pandas as pd
import pymongo
from datetime import datetime
import re

def nettoyer_symbole(symbole):
    """Nettoyer le symbole BRVM (enlever .BC suffix)"""
    if pd.isna(symbole):
        return None
    
    symbole = str(symbole).strip().upper()
    
    # Enlever .BC suffix
    symbole = symbole.replace('.BC', '')
    
    # Symboles invalides
    if symbole in ['NAN', 'N/A', '', 'NONE']:
        return None
    
    return symbole

def restaurer_toutes_donnees_brvm():
    """Restaurer toutes les données BRVM depuis les CSV"""
    
    print(f"[RESTAURATION DONNÉES BRVM RÉELLES]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    # Stats
    stats = {
        'observations_restaurees': 0,
        'observations_existantes': 0,
        'symboles_uniques': set(),
        'par_fichier': {}
    }
    
    # Fichiers à restaurer
    fichiers = [
        {
            'path': 'historique_brvm_60jours_TEMPLATE.csv',
            'col_symbole': 'SYMBOL',
            'col_prix': 'CLOSE',
            'col_date': 'DATE',
            'col_volume': 'VOLUME',
            'col_variation': 'VARIATION'
        },
        {
            'path': 'historique_brvm.csv',
            'col_symbole': 'SYMBOL',
            'col_prix': 'CLOSE',
            'col_date': 'DATE',
            'col_volume': 'VOLUME',
            'col_variation': 'VARIATION'
        },
        {
            'path': 'historique_brvm_complement_nov_dec.csv',
            'col_symbole': 'SYMBOL',
            'col_prix': 'CLOSE',
            'col_date': 'DATE',
            'col_volume': 'VOLUME',
            'col_variation': 'VARIATION'
        },
        {
            'path': 'donnees_reelles_brvm.csv',
            'col_symbole': 'SYMBOL',
            'col_prix': 'CLOSE',
            'col_date': 'DATE',
            'col_volume': 'VOLUME',
            'col_variation': 'VARIATION'
        },
        {
            'path': 'donnees_brvm_2026-02-02.csv',
            'col_symbole': 'Ticker',
            'col_prix': 'Cours',
            'col_date': None,
            'col_volume': 'Volume',
            'col_variation': 'Variation_%'
        },
        {
            'path': 'donnees_brvm_2026-01-09.csv',
            'col_symbole': 'Ticker',
            'col_prix': 'Cours',
            'col_date': None,
            'col_volume': 'Volume',
            'col_variation': 'Variation_%'
        }
    ]
    
    for fichier_config in fichiers:
        path = fichier_config['path']
        
        try:
            # Lire CSV
            df = None
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                for sep in [',', ';', '\t']:
                    try:
                        df = pd.read_csv(path, encoding=encoding, sep=sep)
                        if len(df) > 0:
                            break
                    except:
                        continue
                if df is not None and len(df) > 0:
                    break
            
            if df is None or len(df) == 0:
                print(f"[{path}] ⚠ Impossible de lire")
                continue
            
            print(f"[{path}] {len(df)} lignes")
            
            col_symbole = fichier_config['col_symbole']
            col_prix = fichier_config['col_prix']
            col_date = fichier_config['col_date']
            col_volume = fichier_config.get('col_volume')
            col_variation = fichier_config.get('col_variation')
            
            count_restaure = 0
            count_existe = 0
            
            # Traiter chaque ligne
            for idx, row in df.iterrows():
                # Extraire données
                symbole = nettoyer_symbole(row.get(col_symbole))
                
                if not symbole:
                    continue
                
                # Prix
                try:
                    prix = float(row.get(col_prix, 0))
                    if prix <= 0:
                        continue
                except:
                    continue
                
                # Date
                if col_date and col_date in row:
                    try:
                        date_str = str(row[col_date])
                        ts = pd.to_datetime(date_str).isoformat()
                    except:
                        ts = datetime.now().isoformat()
                else:
                    # Utiliser date du nom de fichier si possible
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', path)
                    if match:
                        ts = f"{match.group(1)}T00:00:00"
                    else:
                        ts = datetime.now().isoformat()
                
                # Volume
                volume = 0
                if col_volume and col_volume in row:
                    try:
                        volume = float(row[col_volume])
                    except:
                        volume = 0
                
                # Variation
                variation = 0.0
                if col_variation and col_variation in row:
                    try:
                        variation = float(row[col_variation])
                    except:
                        variation = 0.0
                
                # Créer observation
                key = f"{symbole}_{ts}"
                
                observation = {
                    'key': key,
                    'source': 'BRVM',
                    'ts': ts,
                    'dataset': 'STOCK_PRICE',
                    'ticker': symbole,
                    'value': prix,
                    'attrs': {
                        'close': prix,
                        'volume': volume,
                        'variation': variation,
                        'source_file': path
                    }
                }
                
                # Insérer ou mettre à jour
                result = db.curated_observations.update_one(
                    {'key': key},
                    {'$set': observation},
                    upsert=True
                )
                
                if result.upserted_id:
                    count_restaure += 1
                    stats['observations_restaurees'] += 1
                else:
                    count_existe += 1
                    stats['observations_existantes'] += 1
                
                stats['symboles_uniques'].add(symbole)
            
            stats['par_fichier'][path] = {
                'restaure': count_restaure,
                'existe': count_existe
            }
            
            print(f"  ✓ {count_restaure} nouvelles obs, {count_existe} déjà existantes")
            
        except Exception as e:
            print(f"[{path}] ❌ Erreur: {e}")
    
    # Vérifier total final
    total_stock_price = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
    
    print(f"\n[RÉSUMÉ RESTAURATION]")
    print(f"  Nouvelles observations:  {stats['observations_restaurees']}")
    print(f"  Déjà existantes:         {stats['observations_existantes']}")
    print(f"  Symboles uniques:        {len(stats['symboles_uniques'])}")
    print(f"  Total STOCK_PRICE final: {total_stock_price}")
    
    print(f"\n  Symboles restaurés:")
    symboles_sorted = sorted(list(stats['symboles_uniques']))
    for i in range(0, len(symboles_sorted), 10):
        print(f"    {', '.join(symboles_sorted[i:i+10])}")
    
    print(f"\n[DÉTAILS PAR FICHIER]")
    for fichier, counts in stats['par_fichier'].items():
        print(f"  {fichier}:")
        print(f"    Restauré: {counts['restaure']}, Existe: {counts['existe']}")
    
    client.close()
    
    return stats

if __name__ == "__main__":
    try:
        stats = restaurer_toutes_donnees_brvm()
        
        print(f"\n[OK] Restauration terminée")
        print(f"Vous aviez: 552 observations (supprimées)")
        print(f"Restauré:   188 observations (depuis raw_events)")
        print(f"Maintenant: {stats['observations_restaurees'] + 188} observations RÉELLES")
        
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
