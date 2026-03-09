#!/usr/bin/env python3
"""
CORRIGER les outliers BRVM au lieu de les supprimer
- Identifier les valeurs aberrantes
- Les CORRIGER en utilisant médiane, interpolation, ou plafonnement
- CONSERVER toutes les observations en les réparant
"""

import pymongo
from datetime import datetime
import statistics

def corriger_outliers_brvm():
    """
    Corriger les outliers en utilisant des techniques statistiques
    plutôt que de supprimer les observations
    """
    
    print(f"[CORRECTION INTELLIGENTE OUTLIERS BRVM]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    stats = {
        'prix_corriges': 0,
        'variations_corrigees': 0,
        'volumes_corriges': 0,
        'total_observations': 0
    }
    
    # Récupérer toutes les observations STOCK_PRICE
    observations = list(db.curated_observations.find({'dataset': 'STOCK_PRICE'}))
    stats['total_observations'] = len(observations)
    
    print(f"[ANALYSE] {stats['total_observations']} observations STOCK_PRICE")
    
    if stats['total_observations'] == 0:
        print(f"[ERREUR] Aucune observation à traiter")
        return stats
    
    # Grouper par ticker pour analyser les outliers par action
    par_ticker = {}
    for obs in observations:
        ticker = obs.get('ticker')
        if ticker:
            if ticker not in par_ticker:
                par_ticker[ticker] = []
            par_ticker[ticker].append(obs)
    
    print(f"[ACTIONS] {len(par_ticker)} tickers différents\n")
    
    # Traiter chaque ticker séparément
    for ticker, obs_list in par_ticker.items():
        if len(obs_list) < 3:
            continue  # Besoin de minimum 3 points pour statistiques
        
        # Extraire les prix
        prix = [obs.get('value') for obs in obs_list if obs.get('value') is not None]
        
        if not prix:
            continue
        
        # Calculer statistiques
        prix_median = statistics.median(prix)
        prix_mean = statistics.mean(prix)
        prix_min = min(prix)
        prix_max = max(prix)
        
        # IQR pour détecter outliers
        prix_sorted = sorted(prix)
        q1 = prix_sorted[len(prix_sorted)//4]
        q3 = prix_sorted[3*len(prix_sorted)//4]
        iqr = q3 - q1
        
        # Bornes outliers (1.5x IQR est standard, 3x pour extrêmes)
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Compter outliers
        outliers_count = sum(1 for p in prix if p < lower_bound or p > upper_bound)
        
        if outliers_count > 0:
            print(f"[{ticker}] {len(obs_list)} obs, prix médian {prix_median:.0f} FCFA")
            print(f"  Range: {prix_min:.0f} - {prix_max:.0f} FCFA")
            print(f"  IQR: [{q1:.0f}, {q3:.0f}], Outliers: {outliers_count}")
            
            # Corriger les outliers
            for obs in obs_list:
                prix_obs = obs.get('value')
                
                if prix_obs is None:
                    continue
                
                # Si outlier, corriger
                if prix_obs < lower_bound:
                    # Prix trop bas : remplacer par Q1 (conservateur)
                    nouveau_prix = q1
                    
                    db.curated_observations.update_one(
                        {'_id': obs['_id']},
                        {'$set': {
                            'value': nouveau_prix,
                            'original_value': prix_obs,
                            'corrected': True,
                            'correction_type': 'outlier_low'
                        }}
                    )
                    
                    print(f"    ✓ Corrigé {prix_obs:.0f} → {nouveau_prix:.0f} FCFA (trop bas)")
                    stats['prix_corriges'] += 1
                
                elif prix_obs > upper_bound:
                    # Prix trop haut : remplacer par Q3 (conservateur)
                    nouveau_prix = q3
                    
                    db.curated_observations.update_one(
                        {'_id': obs['_id']},
                        {'$set': {
                            'value': nouveau_prix,
                            'original_value': prix_obs,
                            'corrected': True,
                            'correction_type': 'outlier_high'
                        }}
                    )
                    
                    print(f"    ✓ Corrigé {prix_obs:.0f} → {nouveau_prix:.0f} FCFA (trop haut)")
                    stats['prix_corriges'] += 1
                
                # Corriger volumes si présents
                if 'attrs' in obs and 'volume' in obs['attrs']:
                    volume = obs['attrs']['volume']
                    
                    # Volume négatif → 0
                    if volume < 0:
                        db.curated_observations.update_one(
                            {'_id': obs['_id']},
                            {'$set': {
                                'attrs.volume': 0,
                                'attrs.volume_original': volume,
                                'corrected': True
                            }}
                        )
                        stats['volumes_corriges'] += 1
                    
                    # Volume excessif (>10M actions peu probable BRVM)
                    elif volume > 10_000_000:
                        db.curated_observations.update_one(
                            {'_id': obs['_id']},
                            {'$set': {
                                'attrs.volume': 10_000_000,
                                'attrs.volume_original': volume,
                                'corrected': True
                            }}
                        )
                        stats['volumes_corriges'] += 1
            
            print()
    
    # Résumé
    print(f"[RÉSUMÉ CORRECTIONS]")
    print(f"  Prix corrigés:        {stats['prix_corriges']}")
    print(f"  Volumes corrigés:     {stats['volumes_corriges']}")
    print(f"  Variations corrigées: {stats['variations_corrigees']}")
    print(f"  Total observations:   {stats['total_observations']}")
    
    # Vérifier qualité finale
    corrected_count = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'corrected': True
    })
    
    print(f"\n[QUALITÉ]")
    print(f"  Observations corrigées: {corrected_count}")
    print(f"  Observations intactes:  {stats['total_observations'] - corrected_count}")
    print(f"  Taux correction:        {corrected_count/stats['total_observations']*100:.1f}%")
    
    print(f"\n✓ Toutes les observations conservées et corrigées")
    
    client.close()
    
    return stats

if __name__ == "__main__":
    try:
        stats = corriger_outliers_brvm()
        print(f"\n[OK] Correction terminée - 0 observations supprimées")
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
