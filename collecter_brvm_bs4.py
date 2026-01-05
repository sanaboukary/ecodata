#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COLLECTEUR BRVM - Alternative BeautifulSoup avec retry et contournement
Collecte les 47 actions avec TOUTES les données disponibles
"""

import sys
import io
import re
import time
import random
from datetime import datetime
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pymongo import MongoClient
MONGO_URI = 'mongodb://localhost:27017'
DB_NAME = 'centralisation_db'

# 47 Actions BRVM
ACTIONS_BRVM_47 = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAS',
    'CABC', 'CFAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'NTLC', 'NSBC',
    'ONTBF', 'ORAC', 'ORGT', 'PALC', 'PRSC', 'SAFC', 'SAGC', 'SCRC',
    'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICC', 'SICB',
    'SLBC', 'SMBC', 'SNTS', 'SOGB', 'SPHC', 'STAC', 'STBC', 'SVOC',
    'TTLC', 'TTRC', 'TUBC', 'UNLC', 'UNXC', 'NEIC', 'TOTAL'
]

def log(msg, level='INFO'):
    symbols = {'INFO': '📊', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbols.get(level, 'ℹ️')} {msg}")

def parse_french_number(x):
    """Parse nombre français."""
    if pd.isna(x) or x == '' or x == '-':
        return None
    s = str(x).strip().replace('\xa0', ' ').replace(' ', '').replace(',', '.')
    try:
        return float(re.match(r'-?\d*\.?\d+', s).group())
    except:
        return None

def scraper_brvm_robuste():
    """Scraper avec retry et user-agents multiples."""
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    # URLs à essayer (incluant page alternative)
    urls = [
        "https://www.brvm.org/fr/investir/cours-et-cotations",
        "https://www.brvm.org/fr/cours-actions/0",
        "https://www.brvm.org/en/cours-actions/0",
    ]
    
    for url in urls:
        for attempt in range(3):
            try:
                log(f"Tentative {attempt+1}/3: {url}")
                
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                session = requests.Session()
                session.headers.update(headers)
                
                # Requête avec timeout
                response = session.get(url, timeout=15, verify=True)
                
                if response.status_code == 200:
                    log(f"✅ Connexion réussie ({len(response.content)} bytes)", 'SUCCESS')
                    
                    # Parser HTML
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Chercher toutes les tables
                    tables = soup.find_all('table')
                    log(f"Tables trouvées: {len(tables)}")
                    
                    if tables:
                        # Essayer pandas.read_html
                        dfs = pd.read_html(str(response.content), thousands=" ", decimal=",")
                        
                        if dfs:
                            log(f"DataFrames extraits: {len(dfs)}")
                            
                            # Trouver la table principale (plus de 10 lignes)
                            for idx, df in enumerate(dfs):
                                log(f"  Table {idx+1}: {len(df)} lignes × {len(df.columns)} colonnes")
                                if len(df) >= 10:
                                    log(f"  Colonnes: {list(df.columns)}")
                                    return df
                        
                        # Fallback: Parser manuellement
                        return parser_table_manuelle(tables[0])
                    
                else:
                    log(f"Erreur HTTP {response.status_code}", 'WARNING')
                
                time.sleep(random.uniform(2, 4))
                
            except requests.exceptions.SSLError:
                log(f"Erreur SSL - Retry sans vérification", 'WARNING')
                try:
                    response = session.get(url, timeout=15, verify=False)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        tables = soup.find_all('table')
                        if tables:
                            dfs = pd.read_html(str(response.content), thousands=" ", decimal=",")
                            if dfs:
                                return dfs[0] if len(dfs[0]) >= 10 else dfs[-1]
                except:
                    pass
                    
            except Exception as e:
                log(f"Erreur: {type(e).__name__}: {str(e)[:100]}", 'ERROR')
                time.sleep(random.uniform(3, 6))
    
    return pd.DataFrame()

def parser_table_manuelle(table):
    """Parse table HTML manuellement."""
    data = []
    headers = []
    
    # Headers
    for th in table.find_all('th'):
        headers.append(th.text.strip())
    
    # Lignes
    for tr in table.find_all('tr')[1:]:  # Skip header
        cells = tr.find_all('td')
        if cells:
            row = [cell.text.strip() for cell in cells]
            if len(row) == len(headers):
                data.append(row)
    
    return pd.DataFrame(data, columns=headers)

def collecter_action_individuelle(ticker):
    """Collecte données pour UNE action (fallback)."""
    url = f"https://www.brvm.org/fr/cours-action/{ticker}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Chercher prix
            prix_elem = soup.find(text=re.compile(r'Dernier|Last|Cours'))
            if prix_elem:
                parent = prix_elem.parent
                # Trouver valeur à côté
                for sibling in parent.next_siblings:
                    if sibling.name:
                        prix_text = sibling.text.strip()
                        prix = parse_french_number(prix_text)
                        if prix:
                            return {'Ticker': ticker, 'Cours': prix}
        
        return None
    except:
        return None

def main():
    print("=" * 100)
    print("🚀 COLLECTEUR BRVM ALTERNATIF - BeautifulSoup + Retry")
    print("=" * 100)
    print()
    
    # Connexion MongoDB
    log("Connexion MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        client.server_info()
        log("MongoDB connecté", 'SUCCESS')
    except Exception as e:
        log(f"Erreur MongoDB: {e}", 'ERROR')
        return 1
    
    # Scraping
    df = scraper_brvm_robuste()
    
    if df.empty:
        log("Échec scraping global - Tentative individuelle...", 'WARNING')
        
        # Fallback: collecter action par action
        actions_data = []
        for ticker in ACTIONS_BRVM_47[:10]:  # Tester sur 10 premières
            log(f"Collecte {ticker}...")
            data = collecter_action_individuelle(ticker)
            if data:
                actions_data.append(data)
            time.sleep(random.uniform(1, 2))
        
        if actions_data:
            df = pd.DataFrame(actions_data)
            log(f"✅ {len(df)} actions collectées individuellement", 'SUCCESS')
        else:
            log("Échec total", 'ERROR')
            client.close()
            return 1
    
    # Normaliser colonnes
    rename_map = {
        'Symbole': 'Ticker', 'Symbol': 'Ticker',
        'Dernier': 'Cours', 'Last': 'Cours', 'Close': 'Cours',
        'Variation (%)': 'Variation_%', 'Change (%)': 'Variation_%',
        'Volume': 'Volume', 'Quantité': 'Volume',
    }
    
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})
    
    # Nettoyer
    if 'Ticker' in df.columns:
        df['Ticker'] = df['Ticker'].astype(str).str.strip().str.upper()
        df = df[df['Ticker'].isin(ACTIONS_BRVM_47)]
    
    numeric_cols = ['Cours', 'Variation_%', 'Volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_french_number)
    
    log(f"Données finales: {len(df)} actions")
    
    # Sauvegarder
    date_str = datetime.now().strftime('%Y-%m-%d')
    saved = 0
    
    for _, row in df.iterrows():
        ticker = row.get('Ticker')
        cours = row.get('Cours')
        
        if pd.notna(ticker) and pd.notna(cours):
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': str(ticker),
                'ts': date_str,
                'value': float(cours),
                'attrs': {
                    'data_quality': 'REAL_SCRAPER',
                    'variation_pct': float(row['Variation_%']) if pd.notna(row.get('Variation_%')) else None,
                    'volume': float(row['Volume']) if pd.notna(row.get('Volume')) else None,
                }
            }
            
            db.curated_observations.update_one(
                {'source': 'BRVM', 'key': ticker, 'ts': date_str},
                {'$set': obs},
                upsert=True
            )
            saved += 1
    
    # Export CSV
    import os
    os.makedirs('out_brvm', exist_ok=True)
    csv_path = f"out_brvm/brvm_bs4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 100)
    log(f"TERMINÉ: {saved}/{len(ACTIONS_BRVM_47)} actions sauvegardées", 'SUCCESS')
    log(f"CSV: {csv_path}", 'SUCCESS')
    print("=" * 100)
    
    client.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
