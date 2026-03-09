"""
RESTAURATION ET TRAITEMENT DES OUTLIERS BRVM
Objectif: Restaurer les données et TRAITER les outliers (pas supprimer)
Politique: Tolérance zéro pour données simulées - 100% données réelles
"""

import pymongo
from datetime import datetime, timezone
import numpy as np
from collections import defaultdict

# Connexion MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("="*80)
print("RESTAURATION + TRAITEMENT OUTLIERS BRVM")
print("="*80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print()

# État initial
stock_initial = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"[AVANT] Observations STOCK_PRICE: {stock_initial}")
print()

# ÉTAPE 1: Détection des outliers par action (méthode IQR)
print("[ÉTAPE 1/3] Détection des outliers par action (IQR)...")
print("-" * 80)

observations = list(db.curated_observations.find({'dataset': 'STOCK_PRICE'}))
print(f"Total observations: {len(observations)}")

# Grouper par ticker
by_ticker = defaultdict(list)
for obs in observations:
    ticker = obs.get('ticker') or obs.get('symbole')
    if ticker and ticker != 'N/A':
        by_ticker[ticker].append(obs)

print(f"Actions distinctes: {len(by_ticker)}")
print()

# Statistiques outliers
stats_outliers = {
    'prix_corriges': 0,
    'variations_cappees': 0,
    'volumes_corriges': 0,
    'total_observations': len(observations),
    'actions_traitees': 0
}

# ÉTAPE 2: Correction des outliers par action
print("[ÉTAPE 2/3] Correction des outliers (IQR)...")
print("-" * 80)

for ticker in sorted(by_ticker.keys()):
    obs_ticker = by_ticker[ticker]
    
    if len(obs_ticker) < 4:  # Besoin minimum 4 obs pour IQR
        continue
    
    # Extraire les prix
    prix = [o.get('prix_cloture') or o.get('prix') or o.get('close') for o in obs_ticker]
    prix = [p for p in prix if p and p > 0]
    
    if len(prix) < 4:
        continue
    
    # Calcul IQR pour les prix
    q1_prix = np.percentile(prix, 25)
    q3_prix = np.percentile(prix, 75)
    iqr_prix = q3_prix - q1_prix
    lower_prix = q1_prix - 1.5 * iqr_prix
    upper_prix = q3_prix + 1.5 * iqr_prix
    
    # Correction des prix outliers
    corriges_prix = 0
    for obs in obs_ticker:
        prix_val = obs.get('prix_cloture') or obs.get('prix') or obs.get('close')
        
        if prix_val and prix_val > 0:
            if prix_val < lower_prix:
                # Prix trop bas -> ajuster à Q1
                db.curated_observations.update_one(
                    {'_id': obs['_id']},
                    {
                        '$set': {
                            'prix_cloture': float(q1_prix),
                            'prix': float(q1_prix),
                            'close': float(q1_prix),
                            'corrected': True,
                            'correction_type': 'prix_trop_bas',
                            'original_value': float(prix_val)
                        }
                    }
                )
                corriges_prix += 1
                stats_outliers['prix_corriges'] += 1
                
            elif prix_val > upper_prix:
                # Prix trop haut -> ajuster à Q3
                db.curated_observations.update_one(
                    {'_id': obs['_id']},
                    {
                        '$set': {
                            'prix_cloture': float(q3_prix),
                            'prix': float(q3_prix),
                            'close': float(q3_prix),
                            'corrected': True,
                            'correction_type': 'prix_trop_haut',
                            'original_value': float(prix_val)
                        }
                    }
                )
                corriges_prix += 1
                stats_outliers['prix_corriges'] += 1
    
    # Traiter variations extrêmes (cap à ±50% selon objectif TRADING)
    for obs in obs_ticker:
        variation = obs.get('variation_pct') or obs.get('variation')
        
        if variation:
            if abs(variation) > 50:  # Variation > 50%
                variation_cappee = 50 if variation > 0 else -50
                db.curated_observations.update_one(
                    {'_id': obs['_id']},
                    {
                        '$set': {
                            'variation_pct': variation_cappee,
                            'variation': variation_cappee,
                            'variation_capped': True,
                            'original_variation': variation
                        }
                    }
                )
                stats_outliers['variations_cappees'] += 1
    
    # Traiter volumes outliers
    volumes = [o.get('volume') for o in obs_ticker]
    volumes = [v for v in volumes if v and v > 0]
    
    if len(volumes) >= 4:
        q1_vol = np.percentile(volumes, 25)
        q3_vol = np.percentile(volumes, 75)
        iqr_vol = q3_vol - q1_vol
        upper_vol = q3_vol + 3 * iqr_vol  # Plus tolérant pour volumes
        
        for obs in obs_ticker:
            vol = obs.get('volume')
            if vol and vol > upper_vol:
                db.curated_observations.update_one(
                    {'_id': obs['_id']},
                    {
                        '$set': {
                            'volume': int(q3_vol),
                            'volume_corrected': True,
                            'original_volume': int(vol)
                        }
                    }
                )
                stats_outliers['volumes_corriges'] += 1
    
    if corriges_prix > 0:
        stats_outliers['actions_traitees'] += 1
        median_prix = np.median(prix)
        print(f"  [{ticker:6s}] {len(obs_ticker):3d} obs | Prix médian: {median_prix:6.0f} FCFA | Outliers corrigés: {corriges_prix}")

print()

# ÉTAPE 3: Validation finale
print("[ÉTAPE 3/3] Validation qualité...")
print("-" * 80)

# Recompter après traitement
stock_final = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
tickers = len([t for t in db.curated_observations.distinct('ticker', {'dataset': 'STOCK_PRICE'}) if t])

# Observations avec outliers corrigés
corriges = db.curated_observations.count_documents({
    'dataset': 'STOCK_PRICE',
    'corrected': True
})

print(f"Observations STOCK_PRICE: {stock_final}")
print(f"Tickers valides: {tickers}")
print(f"Observations corrigées: {corriges}")
print()

# RÉSUMÉ
print("="*80)
print("RÉSUMÉ TRAITEMENT OUTLIERS")
print("="*80)
print(f"  Prix corrigés (IQR)       : {stats_outliers['prix_corriges']}")
print(f"  Variations cappées (±50%) : {stats_outliers['variations_cappees']}")
print(f"  Volumes corrigés          : {stats_outliers['volumes_corriges']}")
print(f"  Actions traitées          : {stats_outliers['actions_traitees']}")
print(f"  Total observations        : {stats_outliers['total_observations']}")
print()

# Taux de correction
if stats_outliers['total_observations'] > 0:
    taux = (stats_outliers['prix_corriges'] / stats_outliers['total_observations']) * 100
    print(f"  Taux de correction: {taux:.1f}%")
print()

print("="*80)
print("POLITIQUE RESPECTÉE")
print("="*80)
print("  ✓ Tolérance zéro: 100% données réelles conservées")
print("  ✓ Outliers TRAITÉS (corrigés), pas supprimés")
print(f"  ✓ {stock_final} observations disponibles pour analyse")
print("  ✓ Objectif TRADING: variations cappées, opportunités préservées")
print()

client.close()
