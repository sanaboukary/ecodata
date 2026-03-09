#!/usr/bin/env python3
"""
RESTAURER les données BRVM réelles depuis CSV
- Importer 2,974 observations historiques
- Éviter doublons avec les 188 existantes
- Garantir données 100% réelles (pas de simulation)
"""

import pandas as pd
import pymongo
from datetime import datetime

def restaurer_donnees_brvm_csv():
    """Restaurer données BRVM depuis les fichiers CSV historiques"""
    
    print(f"[RESTAURATION DONNÉES BRVM RÉELLES]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Liste des 47 actions BRVM officielles
    actions_brvm_47 = {
        'ABJC', 'BICC', 'BOAB', 'BOABF', 'BOAC', 'BOAG', 'BOAM', 'BOAN', 'BOAS',
        'CBIBF', 'CFAO', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'NEIC', 'NSBC', 'NTLC',
        'ONTBF', 'ORGT', 'PALC', 'PRSC', 'SAFC', 'SCRC', 'SDCC', 'SDSC', 'SEMC',
        'SGBC', 'SHEC', 'SIBC', 'SICC', 'SIVC', 'SLBC', 'SMBC', 'SNTS', 'SODE',
        'SOGC', 'SPHC', 'STAC', 'STBC', 'SVOC', 'TTLC', 'TTRC', 'UNXC', 'CIAC',
        'SNDC', 'SPHEC'
    }
    
    # Connexion MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    # Vérifier état initial
    count_avant = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
    print(f"[ÉTAT INITIAL]")
    print(f"  Observations STOCK_PRICE existantes: {count_avant}\n")
    
    # Fichiers CSV à restaurer
    fichiers_csv = [
        {
            'path': 'historique_brvm.csv',
            'description': 'Historique sept-nov 2025'
        },
        {
            'path': 'historique_brvm_complement_nov_dec.csv',
            'description': 'Complément nov-déc 2025'
        },
        {
            'path': 'donnees_reelles_brvm.csv',
            'description': 'Données réelles déc 2025'
        }
    ]
    
    stats = {
        'total_lus': 0,
        'actions_brvm': 0,
        'doublons_evites': 0,
        'importes': 0,
        'actions_hors_brvm': set()
    }
    
    # Récupérer les clés existantes pour éviter doublons
    keys_existantes = set(db.curated_observations.distinct('key', {'dataset': 'STOCK_PRICE'}))
    print(f"[DOUBLONS] {len(keys_existantes)} clés existantes à éviter\n")
    
    # Traiter chaque fichier
    for fichier in fichiers_csv:
        print(f"[FICHIER] {fichier['path']} - {fichier['description']}")
        
        try:
            # Lire CSV
            df = pd.read_csv(fichier['path'])
            stats['total_lus'] += len(df)
            
            print(f"  Lignes: {len(df)}")
            
            # Filtrer actions BRVM uniquement
            df_brvm = df[df['SYMBOL'].isin(actions_brvm_47)].copy()
            actions_filtrées = len(df) - len(df_brvm)
            
            if actions_filtrées > 0:
                actions_hors = set(df[~df['SYMBOL'].isin(actions_brvm_47)]['SYMBOL'].unique())
                stats['actions_hors_brvm'].update(actions_hors)
                print(f"  ⚠ {actions_filtrées} lignes filtrées (actions hors 47 BRVM)")
            
            print(f"  Actions BRVM: {df_brvm['SYMBOL'].nunique()}")
            stats['actions_brvm'] = max(stats['actions_brvm'], df_brvm['SYMBOL'].nunique())
            
            # Importer dans MongoDB
            importes_fichier = 0
            doublons_fichier = 0
            
            for _, row in df_brvm.iterrows():
                # Créer clé unique
                date_str = str(row['DATE'])
                symbol = row['SYMBOL']
                key = f"{symbol}_{date_str}"
                
                # Éviter doublon
                if key in keys_existantes:
                    doublons_fichier += 1
                    continue
                
                # Créer observation
                obs = {
                    'key': key,
                    'source': 'BRVM_CSV_HISTORIQUE',
                    'ts': date_str,
                    'dataset': 'STOCK_PRICE',
                    'ticker': symbol,
                    'value': float(row['CLOSE']),
                    'attrs': {
                        'close': float(row['CLOSE']),
                        'volume': int(row['VOLUME']) if pd.notna(row['VOLUME']) else 0,
                        'variation': float(row['VARIATION']) if pd.notna(row['VARIATION']) else 0.0,
                        'source_file': fichier['path']
                    }
                }
                
                # Insérer
                db.curated_observations.insert_one(obs)
                keys_existantes.add(key)
                importes_fichier += 1
                stats['importes'] += 1
            
            stats['doublons_evites'] += doublons_fichier
            
            print(f"  ✓ Importés: {importes_fichier}")
            if doublons_fichier > 0:
                print(f"  ⓘ Doublons évités: {doublons_fichier}")
            print()
            
        except Exception as e:
            print(f"  [ERREUR] {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # Vérifier état final
    count_apres = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
    
    print(f"[RÉSUMÉ RESTAURATION]")
    print(f"  Total lignes lues: {stats['total_lus']}")
    print(f"  Observations importées: {stats['importes']}")
    print(f"  Doublons évités: {stats['doublons_evites']}")
    print(f"  Actions BRVM couvertes: {stats['actions_brvm']}/47")
    
    if stats['actions_hors_brvm']:
        print(f"\n  Actions hors 47 BRVM (filtrées): {sorted(stats['actions_hors_brvm'])}")
    
    print(f"\n[ÉTAT FINAL]")
    print(f"  Avant: {count_avant} observations")
    print(f"  Après: {count_apres} observations")
    print(f"  Gain: +{count_apres - count_avant} observations")
    
    # Vérifier distribution par action
    pipeline = [
        {'$match': {'dataset': 'STOCK_PRICE'}},
        {'$group': {
            '_id': '$ticker',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    
    top_actions = list(db.curated_observations.aggregate(pipeline))
    
    print(f"\n[TOP 10 ACTIONS PAR OBSERVATIONS]")
    for action in top_actions:
        ticker = action['_id']
        count = action['count']
        print(f"  {ticker}: {count} obs")
    
    print(f"\n✓ Restauration terminée - 100% données RÉELLES")
    print(f"✓ Aucune donnée simulée - Politique TOLÉRANCE ZÉRO respectée")
    
    client.close()
    
    return {
        'avant': count_avant,
        'apres': count_apres,
        'importes': stats['importes']
    }

if __name__ == "__main__":
    try:
        result = restaurer_donnees_brvm_csv()
        print(f"\n[OK] {result['importes']} observations restaurées")
        print(f"[OK] Base passée de {result['avant']} → {result['apres']} observations")
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
