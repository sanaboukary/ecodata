#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COLLECTEUR COMPLET BRVM - Toutes métriques pour Analyse IA
Collecte: Prix, Variations, Volatilité, Liquidité pour 47 actions BRVM

Métriques collectées:
- Prix: Ouverture, Clôture, Plus haut, Plus bas
- Variations: Jour, Semaine, Mois, Année
- Volatilité: Écart-type 5j, 20j, 60j
- Liquidité: Volume, Valeur échangée, Ratio volume/cap
"""

import sys
import os
import io
import time
import re
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd
import numpy as np

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
DB_NAME = 'centralisation_db'

# 47 actions BRVM
SYMBOLES_BRVM = [
    'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAS', 'CABC', 'CFAC',
    'CIEC', 'ECOC', 'ETIT', 'FTSC', 'NTLC', 'NSBC', 'ONTBF', 'ORAC', 'ORGT',
    'PALC', 'PRSC', 'SAFC', 'SAGC', 'SCRC', 'SDCC', 'SDSC', 'SEMC', 'SGBC',
    'SHEC', 'SIBC', 'SICC', 'SICB', 'SLBC', 'SMBC', 'SNTS', 'SOGB', 'SPHC',
    'STAC', 'STBC', 'SVOC', 'TTLC', 'TTRC', 'TUBC', 'UNLC', 'UNXC', 'ABJC',
    'BOAC', 'TOTAL'
]

def log(message, level='INFO'):
    """Log avec timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    symbols = {'INFO': '📊', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'DATA': '💾'}
    print(f"[{timestamp}] {symbols.get(level, 'ℹ️')} {message}")

def get_mongo():
    """Connexion MongoDB."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    client.server_info()
    return client, db

def parse_fr_number(x):
    """Parse nombre français."""
    if pd.isna(x):
        return None
    s = str(x).strip().replace("\xa0", " ").replace(" ", "").replace(",", ".")
    m = re.match(r"^-?\d*\.?\d+$", s)
    if not m:
        return None
    try:
        return float(s)
    except:
        return None

def collecter_selenium_avance():
    """Collecte avec Selenium avancé - toutes les métriques."""
    log("Collecte Selenium avancée - TOUTES métriques")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait as Wait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Configuration Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        log("Démarrage ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Collecter cours et cotations
        url = "https://www.brvm.org/fr/cours-actions/0"
        log(f"Connexion: {url}")
        driver.get(url)
        
        # Attendre tables
        Wait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(2)
        
        # Lire tables
        dfs = pd.read_html(driver.page_source, thousands=" ", decimal=",")
        log(f"{len(dfs)} table(s) trouvée(s)")
        
        driver.quit()
        
        if not dfs:
            return None
        
        # Concaténer toutes les tables
        df = pd.concat(dfs, ignore_index=True).dropna(how='all')
        
        # Normaliser colonnes
        rename_map = {
            'Symbole': 'ticker', 'Libellé': 'libelle', 'Libelle': 'libelle',
            'Dernier': 'prix', 'Dernier cours': 'prix',
            'Ouverture': 'ouverture', 'Plus Haut': 'plus_haut', 'Plus Bas': 'plus_bas',
            'Variation': 'variation', 'Variation (%)': 'variation_pct',
            'Volume': 'volume', 'Valeur': 'valeur',
            'Secteur': 'secteur', 'Sector': 'secteur'
        }
        
        df = df.rename(columns={c: rename_map.get(c, c.lower()) for c in df.columns})
        
        # Nettoyer numériques
        num_cols = ['prix', 'ouverture', 'plus_haut', 'plus_bas', 'variation', 'variation_pct', 'volume', 'valeur']
        for col in num_cols:
            if col in df.columns:
                df[col] = df[col].apply(parse_fr_number)
        
        # Nettoyer ticker
        if 'ticker' in df.columns:
            df['ticker'] = df['ticker'].astype(str).str.strip().str.upper()
        
        # Filtrer uniquement les 47 actions BRVM
        df = df[df['ticker'].isin(SYMBOLES_BRVM)]
        
        log(f"Actions collectées: {len(df)}")
        return df
        
    except Exception as e:
        log(f"Erreur Selenium: {e}", 'ERROR')
        return None

def calculer_volatilite(db, ticker, periodes=[5, 20, 60]):
    """Calcule la volatilité sur différentes périodes."""
    volatilites = {}
    
    for periode in periodes:
        date_debut = (datetime.now() - timedelta(days=periode)).strftime('%Y-%m-%d')
        
        # Récupérer prix historiques
        obs = list(db.curated_observations.find({
            'source': 'BRVM',
            'key': ticker,
            'ts': {'$gte': date_debut}
        }).sort('ts', 1))
        
        if len(obs) >= 5:
            prix = [o['value'] for o in obs]
            # Calculer rendements quotidiens
            rendements = [((prix[i] - prix[i-1]) / prix[i-1]) * 100 for i in range(1, len(prix))]
            volatilite = np.std(rendements) if rendements else 0
            volatilites[f'volatilite_{periode}j'] = round(volatilite, 2)
        else:
            volatilites[f'volatilite_{periode}j'] = None
    
    return volatilites

def calculer_liquidite(prix, volume, valeur):
    """Calcule les métriques de liquidité."""
    liquidite = {}
    
    # Volume relatif (volume / prix = nombre de titres échangés)
    if prix and prix > 0:
        liquidite['titres_echanges'] = round(volume / prix) if volume else 0
    else:
        liquidite['titres_echanges'] = 0
    
    # Valeur échangée
    liquidite['valeur_echangee'] = valeur if valeur else 0
    
    # Score de liquidité (0-100)
    # Basé sur volume et valeur
    if volume and valeur:
        score = min(100, (volume / 10000) * 50 + (valeur / 1000000) * 50)
        liquidite['score_liquidite'] = round(score, 1)
    else:
        liquidite['score_liquidite'] = 0
    
    return liquidite

def enrichir_avec_metriques(df, db):
    """Enrichit les données avec volatilité et liquidité."""
    log("Enrichissement avec volatilité et liquidité...")
    
    enriched = []
    
    for _, row in df.iterrows():
        ticker = row.get('ticker')
        if not ticker or ticker not in SYMBOLES_BRVM:
            continue
        
        # Données de base
        data = {
            'ticker': ticker,
            'libelle': row.get('libelle', ''),
            'secteur': row.get('secteur', ''),
            'prix': row.get('prix'),
            'ouverture': row.get('ouverture'),
            'plus_haut': row.get('plus_haut'),
            'plus_bas': row.get('plus_bas'),
            'variation': row.get('variation'),
            'variation_pct': row.get('variation_pct'),
            'volume': row.get('volume', 0),
            'valeur': row.get('valeur', 0)
        }
        
        # Calculer volatilité
        try:
            volatilites = calculer_volatilite(db, ticker, [5, 20, 60])
            data.update(volatilites)
        except Exception as e:
            log(f"Erreur volatilité {ticker}: {e}", 'WARNING')
            data.update({'volatilite_5j': None, 'volatilite_20j': None, 'volatilite_60j': None})
        
        # Calculer liquidité
        try:
            liquidite = calculer_liquidite(
                data['prix'],
                data['volume'],
                data['valeur']
            )
            data.update(liquidite)
        except Exception as e:
            log(f"Erreur liquidité {ticker}: {e}", 'WARNING')
            data.update({'titres_echanges': 0, 'valeur_echangee': 0, 'score_liquidite': 0})
        
        enriched.append(data)
    
    return pd.DataFrame(enriched)

def sauvegarder_mongodb(df, db):
    """Sauvegarde dans MongoDB avec toutes les métriques."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    saved = 0
    
    for _, row in df.iterrows():
        obs = {
            'source': 'BRVM',
            'dataset': 'STOCK_COMPLETE',
            'key': row['ticker'],
            'ts': date_str,
            'value': float(row['prix']) if pd.notna(row['prix']) else None,
            'attrs': {
                'data_quality': 'REAL_SCRAPER',
                'collecte_complete': True,
                
                # Prix
                'ouverture': float(row['ouverture']) if pd.notna(row['ouverture']) else None,
                'plus_haut': float(row['plus_haut']) if pd.notna(row['plus_haut']) else None,
                'plus_bas': float(row['plus_bas']) if pd.notna(row['plus_bas']) else None,
                
                # Variations
                'variation': float(row['variation']) if pd.notna(row['variation']) else None,
                'variation_pct': float(row['variation_pct']) if pd.notna(row['variation_pct']) else None,
                
                # Volume/Valeur
                'volume': float(row['volume']) if pd.notna(row['volume']) else 0,
                'valeur': float(row['valeur']) if pd.notna(row['valeur']) else 0,
                
                # Volatilité
                'volatilite_5j': float(row['volatilite_5j']) if pd.notna(row['volatilite_5j']) else None,
                'volatilite_20j': float(row['volatilite_20j']) if pd.notna(row['volatilite_20j']) else None,
                'volatilite_60j': float(row['volatilite_60j']) if pd.notna(row['volatilite_60j']) else None,
                
                # Liquidité
                'titres_echanges': int(row['titres_echanges']) if pd.notna(row['titres_echanges']) else 0,
                'valeur_echangee': float(row['valeur_echangee']) if pd.notna(row['valeur_echangee']) else 0,
                'score_liquidite': float(row['score_liquidite']) if pd.notna(row['score_liquidite']) else 0,
                
                # Infos
                'libelle': str(row['libelle']) if pd.notna(row['libelle']) else '',
                'secteur': str(row['secteur']) if pd.notna(row['secteur']) else ''
            }
        }
        
        try:
            db.curated_observations.update_one(
                {
                    'source': obs['source'],
                    'dataset': obs['dataset'],
                    'key': obs['key'],
                    'ts': obs['ts']
                },
                {'$set': obs},
                upsert=True
            )
            saved += 1
        except Exception as e:
            log(f"Erreur sauvegarde {row['ticker']}: {e}", 'WARNING')
    
    return saved

def exporter_csv(df, dossier='out_brvm_ia'):
    """Exporte CSV pour analyse IA."""
    os.makedirs(dossier, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV complet
    csv_path = os.path.join(dossier, f"brvm_complete_ia_{timestamp}.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    # CSV simplifié pour ML
    cols_ml = ['ticker', 'prix', 'variation_pct', 'volume', 'volatilite_20j', 'score_liquidite']
    df_ml = df[[c for c in cols_ml if c in df.columns]]
    csv_ml_path = os.path.join(dossier, f"brvm_ml_{timestamp}.csv")
    df_ml.to_csv(csv_ml_path, index=False, encoding='utf-8')
    
    return csv_path, csv_ml_path

def main():
    print("=" * 80)
    print("🚀 COLLECTEUR COMPLET BRVM - Pour Analyse IA")
    print("=" * 80)
    print()
    print("Métriques collectées pour les 47 actions:")
    print("  ✅ Prix (ouverture, clôture, haut, bas)")
    print("  ✅ Variations (absolue, pourcentage)")
    print("  ✅ Volatilité (5j, 20j, 60j)")
    print("  ✅ Liquidité (volume, valeur, score)")
    print()
    print("=" * 80)
    print()
    
    try:
        # Connexion MongoDB
        log("Connexion MongoDB...")
        client, db = get_mongo()
        log("MongoDB connecté", 'SUCCESS')
        
        # Collecte Selenium
        log("Collecte des cours BRVM...")
        df = collecter_selenium_avance()
        
        if df is None or df.empty:
            log("Échec collecte Selenium", 'ERROR')
            return 1
        
        log(f"{len(df)} actions collectées", 'SUCCESS')
        
        # Enrichissement avec métriques
        df_enrichi = enrichir_avec_metriques(df, db)
        log(f"{len(df_enrichi)} actions enrichies", 'SUCCESS')
        
        # Sauvegarde MongoDB
        log("Sauvegarde dans MongoDB...")
        saved = sauvegarder_mongodb(df_enrichi, db)
        log(f"{saved} observations sauvegardées", 'SUCCESS')
        
        # Export CSV
        log("Export CSV pour analyse IA...")
        csv_path, csv_ml_path = exporter_csv(df_enrichi)
        log(f"CSV complet: {csv_path}", 'DATA')
        log(f"CSV ML: {csv_ml_path}", 'DATA')
        
        # Statistiques
        print()
        print("=" * 80)
        print("📊 RÉSUMÉ DE LA COLLECTE")
        print("=" * 80)
        print()
        print(f"Actions collectées: {len(df_enrichi)}/47")
        print(f"Prix moyen: {df_enrichi['prix'].mean():.2f} FCFA")
        print(f"Volatilité moyenne (20j): {df_enrichi['volatilite_20j'].mean():.2f}%")
        print(f"Score liquidité moyen: {df_enrichi['score_liquidite'].mean():.1f}/100")
        print()
        
        # Top 5 plus liquides
        print("🔝 TOP 5 ACTIONS PLUS LIQUIDES:")
        top_liquides = df_enrichi.nlargest(5, 'score_liquidite')[['ticker', 'libelle', 'prix', 'volume', 'score_liquidite']]
        print(top_liquides.to_string(index=False))
        print()
        
        # Top 5 plus volatiles
        print("⚡ TOP 5 ACTIONS PLUS VOLATILES (20j):")
        top_volatiles = df_enrichi.nlargest(5, 'volatilite_20j')[['ticker', 'libelle', 'prix', 'volatilite_20j']]
        print(top_volatiles.to_string(index=False))
        print()
        
        print("=" * 80)
        print("✅ COLLECTE TERMINÉE - DONNÉES PRÊTES POUR ANALYSE IA")
        print("=" * 80)
        print()
        print("Utilisez les données dans:")
        print(f"  - MongoDB: collection 'curated_observations'")
        print(f"  - CSV complet: {csv_path}")
        print(f"  - CSV ML: {csv_ml_path}")
        print()
        
        client.close()
        return 0
        
    except Exception as e:
        log(f"ERREUR: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
