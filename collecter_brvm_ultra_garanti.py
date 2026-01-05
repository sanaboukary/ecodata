#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COLLECTEUR BRVM ULTRA-GARANTI - 47 Actions
Stratégies multiples en cascade jusqu'à succès complet
"""

import sys
import io
import re
import time
import random
import json
from datetime import datetime
import pandas as pd
import numpy as np

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pymongo import MongoClient

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
    symbols = {'INFO': '📊', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'WAIT': '⏳'}
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

def strategie_1_selenium_ultra_patient():
    """Selenium avec PATIENCE EXTRÊME - attend vraiment le chargement complet."""
    log("🎯 STRATÉGIE 1: Selenium Ultra-Patient (attente 60s)")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait as Wait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.action_chains import ActionChains
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Configuration anti-détection MAXIMALE
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Masquer webdriver
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR', 'fr', 'en-US', 'en']});
            '''
        })
        
        log("Chrome démarré - mode humain activé")
        
        # URL
        url = "https://www.brvm.org/fr/investir/cours-et-cotations"
        log(f"Navigation: {url}")
        driver.get(url)
        
        # PATIENCE: Attendre vraiment longtemps
        log("⏳ Attente chargement initial (15s)...", 'WAIT')
        time.sleep(15)
        
        # Cookies avec patience
        try:
            btns = driver.find_elements(By.TAG_NAME, "button")
            for b in btns:
                txt = (b.text or "").lower()
                if any(word in txt for word in ["accept", "accepter", "agree", "tout accepter"]):
                    time.sleep(1)
                    b.click()
                    log("Cookies fermés")
                    time.sleep(2)
                    break
        except:
            pass
        
        # Simuler VRAIMENT un humain
        log("🖱️ Simulation comportement humain...")
        actions = ActionChains(driver)
        
        # Mouvements souris aléatoires
        for i in range(3):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            actions.move_by_offset(x, y).perform()
            time.sleep(random.uniform(0.5, 1.5))
            actions.move_by_offset(-x, -y).perform()
        
        # Scroll TRÈS progressif pour déclencher lazy loading
        log("📜 Scroll progressif ultra-lent...")
        current_height = 0
        target_height = driver.execute_script("return document.body.scrollHeight")
        
        while current_height < target_height:
            # Scroll par petits incréments (simulation humaine)
            increment = random.randint(100, 300)
            current_height += increment
            
            driver.execute_script(f"window.scrollTo({{top: {current_height}, behavior: 'smooth'}});")
            time.sleep(random.uniform(0.8, 2.0))
            
            # Parfois scroll retour (humain)
            if random.random() < 0.15:
                back = random.randint(50, 150)
                driver.execute_script(f"window.scrollBy(0, -{back});")
                time.sleep(random.uniform(0.3, 0.8))
            
            # Mettre à jour hauteur (contenu peut charger)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height > target_height:
                target_height = new_height
                log(f"  Nouveau contenu détecté: {target_height}px")
        
        # Attendre encore que tout se stabilise
        log("⏳ Attente stabilisation (10s)...", 'WAIT')
        time.sleep(10)
        
        # Scroll final vers le haut
        driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
        time.sleep(3)
        
        # ATTENTE FINALE EXTRÊME pour lazy loading
        log("⏳ Attente finale lazy loading (20s)...", 'WAIT')
        time.sleep(20)
        
        # Parser toutes les tables
        log("📋 Extraction tables HTML...")
        dfs = pd.read_html(driver.page_source, thousands=" ", decimal=",")
        
        driver.quit()
        
        if dfs:
            log(f"✅ {len(dfs)} table(s) extraite(s)", 'SUCCESS')
            # Trouver la plus grande table
            df_main = max(dfs, key=len)
            log(f"Table principale: {len(df_main)} lignes × {len(df_main.columns)} colonnes")
            
            if len(df_main) >= 30:  # Au moins 30 actions
                return df_main
        
        return pd.DataFrame()
        
    except Exception as e:
        log(f"Erreur Stratégie 1: {e}", 'ERROR')
        try:
            driver.quit()
        except:
            pass
        return pd.DataFrame()

def strategie_2_requetes_directes_multiples():
    """Requêtes HTTP directes avec TOUS les headers possibles."""
    log("🎯 STRATÉGIE 2: Requêtes HTTP Directes Multi-Headers")
    
    import requests
    from bs4 import BeautifulSoup
    
    urls = [
        "https://www.brvm.org/fr/investir/cours-et-cotations",
        "https://www.brvm.org/fr/cours-actions",
        "https://www.brvm.org/en/cours-actions",
    ]
    
    # Headers ultra-réalistes
    headers_variations = [
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.brvm.org/',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-fr',
            'Connection': 'keep-alive',
        },
    ]
    
    for url in urls:
        for headers in headers_variations:
            try:
                log(f"Test: {url[:50]}...")
                
                session = requests.Session()
                session.headers.update(headers)
                
                # Retry avec/sans SSL
                for verify_ssl in [True, False]:
                    try:
                        r = session.get(url, timeout=20, verify=verify_ssl)
                        
                        if r.status_code == 200 and len(r.content) > 10000:
                            log(f"✅ Connexion réussie ({len(r.content)} bytes)", 'SUCCESS')
                            
                            # Parser
                            dfs = pd.read_html(r.content, thousands=" ", decimal=",")
                            
                            if dfs:
                                df_main = max(dfs, key=len)
                                if len(df_main) >= 30:
                                    log(f"✅ {len(df_main)} lignes extraites", 'SUCCESS')
                                    return df_main
                        
                    except:
                        pass
                    
                    time.sleep(random.uniform(1, 3))
                    
            except Exception as e:
                log(f"Erreur: {str(e)[:50]}", 'WARNING')
                time.sleep(2)
    
    return pd.DataFrame()

def strategie_3_recherche_api_cachee():
    """Recherche d'API ou fichiers JSON/XML cachés."""
    log("🎯 STRATÉGIE 3: Recherche API Cachée")
    
    import requests
    
    endpoints = [
        "https://www.brvm.org/sites/default/files/cours_actions.json",
        "https://www.brvm.org/api/v1/stocks",
        "https://www.brvm.org/api/stocks/all",
        "https://www.brvm.org/data/cours.json",
        "https://api.brvm.org/v1/stocks",
        "https://www.brvm.org/sites/default/files/data/cours.xml",
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    for endpoint in endpoints:
        try:
            log(f"Test API: {endpoint}")
            r = requests.get(endpoint, headers=headers, timeout=10, verify=False)
            
            if r.status_code == 200:
                log(f"✅ API trouvée! {endpoint}", 'SUCCESS')
                
                # JSON
                try:
                    data = r.json()
                    if isinstance(data, list) and len(data) >= 30:
                        df = pd.DataFrame(data)
                        log(f"✅ {len(df)} actions depuis API JSON", 'SUCCESS')
                        return df
                except:
                    pass
                
                # XML
                if 'xml' in endpoint.lower():
                    try:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(r.content)
                        # Parser XML ici si trouvé
                    except:
                        pass
                        
        except:
            pass
    
    return pd.DataFrame()

def strategie_4_collecte_action_par_action():
    """Dernière chance: collecter action par action."""
    log("🎯 STRATÉGIE 4: Collecte Action par Action (fallback)")
    
    import requests
    from bs4 import BeautifulSoup
    
    actions_data = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    log(f"Collecte individuelle pour {len(ACTIONS_BRVM_47)} actions...")
    
    for idx, ticker in enumerate(ACTIONS_BRVM_47):
        try:
            url = f"https://www.brvm.org/fr/cours-action/{ticker}"
            r = requests.get(url, headers=headers, timeout=10, verify=False)
            
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, 'html.parser')
                
                # Chercher cours
                prix = None
                for elem in soup.find_all(['td', 'span', 'div']):
                    text = elem.text.strip()
                    if re.match(r'^\d+[\s,]\d+', text):  # Format nombre
                        prix = parse_french_number(text)
                        if prix and prix > 10:  # Vraisemblable
                            actions_data.append({
                                'Ticker': ticker,
                                'Cours': prix
                            })
                            log(f"  {ticker}: {prix}")
                            break
            
            if (idx + 1) % 10 == 0:
                log(f"  Progression: {idx + 1}/{len(ACTIONS_BRVM_47)}")
            
            time.sleep(random.uniform(0.5, 1.5))
            
        except:
            pass
    
    if actions_data:
        df = pd.DataFrame(actions_data)
        log(f"✅ {len(df)} actions collectées individuellement", 'SUCCESS')
        return df
    
    return pd.DataFrame()

def normaliser_dataframe(df):
    """Normalise le DataFrame avec colonnes BRVM."""
    
    if df.empty:
        return df
    
    # Renommer colonnes
    rename_map = {
        'Symbole': 'Ticker', 'Symbol': 'Ticker', 'Code': 'Ticker',
        'Libellé': 'Libelle', 'Name': 'Libelle', 'Nom': 'Libelle',
        'Dernier': 'Cours', 'Dernier cours': 'Cours', 'Last': 'Cours', 'Close': 'Cours', 'Clôture': 'Cours',
        'Variation (%)': 'Variation_%', 'Variation': 'Variation_%', 'Change (%)': 'Variation_%', 'Var. (%)': 'Variation_%',
        'Volume': 'Volume', 'Quantité': 'Volume', 'Qty': 'Volume',
        'Valeur': 'Valeur', 'Value': 'Valeur',
        'Ouverture': 'Ouverture', 'Open': 'Ouverture',
        'Plus Haut': 'Haut', 'High': 'Haut', 'Haut': 'Haut',
        'Plus Bas': 'Bas', 'Low': 'Bas', 'Bas': 'Bas',
        'Précédent': 'Precedent', 'Previous': 'Precedent',
        'Secteur': 'Secteur', 'Sector': 'Secteur',
    }
    
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})
    
    # Nettoyer Ticker
    if 'Ticker' in df.columns:
        df['Ticker'] = df['Ticker'].astype(str).str.strip().str.upper()
        df = df[df['Ticker'].isin(ACTIONS_BRVM_47)]
        df = df.drop_duplicates(subset=['Ticker'])
    
    # Convertir numériques
    numeric_cols = ['Cours', 'Variation_%', 'Volume', 'Valeur', 'Ouverture', 'Haut', 'Bas', 'Precedent']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_french_number)
    
    return df

def sauvegarder_mongodb(df, db):
    """Sauvegarde dans MongoDB."""
    
    if df.empty:
        return 0
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    saved = 0
    
    for _, row in df.iterrows():
        ticker = row.get('Ticker')
        cours = row.get('Cours')
        
        if pd.notna(ticker) and pd.notna(cours):
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE_COMPLET',
                'key': str(ticker),
                'ts': date_str,
                'value': float(cours),
                'attrs': {
                    'data_quality': 'REAL_SCRAPER',
                    'collecte_ts': datetime.now().isoformat(),
                    'libelle': str(row.get('Libelle', '')),
                    'secteur': str(row.get('Secteur', '')),
                    'cours': float(cours),
                    'variation_pct': float(row['Variation_%']) if pd.notna(row.get('Variation_%')) else None,
                    'volume': float(row['Volume']) if pd.notna(row.get('Volume')) else None,
                    'valeur': float(row['Valeur']) if pd.notna(row.get('Valeur')) else None,
                    'ouverture': float(row['Ouverture']) if pd.notna(row.get('Ouverture')) else None,
                    'haut': float(row['Haut']) if pd.notna(row.get('Haut')) else None,
                    'bas': float(row['Bas']) if pd.notna(row.get('Bas')) else None,
                    'precedent': float(row['Precedent']) if pd.notna(row.get('Precedent')) else None,
                }
            }
            
            db.curated_observations.update_one(
                {'source': 'BRVM', 'key': ticker, 'ts': date_str},
                {'$set': obs},
                upsert=True
            )
            saved += 1
    
    return saved

def main():
    print("=" * 100)
    print("🚀 COLLECTEUR BRVM ULTRA-GARANTI - 4 STRATÉGIES EN CASCADE")
    print("=" * 100)
    print()
    print("Objectif: TOUTES les 47 actions avec TOUTES les données disponibles")
    print("Méthode: Tenter 4 stratégies différentes jusqu'à succès")
    print()
    print("=" * 100)
    print()
    
    # MongoDB
    log("Connexion MongoDB...")
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        db = client['centralisation_db']
        client.server_info()
        log("✅ MongoDB connecté", 'SUCCESS')
    except Exception as e:
        log(f"❌ Erreur MongoDB: {e}", 'ERROR')
        return 1
    
    df_final = pd.DataFrame()
    strategie_reussie = None
    
    # STRATÉGIE 1: Selenium Ultra-Patient
    if df_final.empty or len(df_final) < 30:
        df = strategie_1_selenium_ultra_patient()
        if not df.empty:
            df = normaliser_dataframe(df)
            if len(df) >= 30:
                df_final = df
                strategie_reussie = "Selenium Ultra-Patient"
                log(f"✅ SUCCÈS STRATÉGIE 1: {len(df)} actions", 'SUCCESS')
    
    # STRATÉGIE 2: Requêtes HTTP Directes
    if df_final.empty or len(df_final) < 30:
        log("Passage à la Stratégie 2...")
        df = strategie_2_requetes_directes_multiples()
        if not df.empty:
            df = normaliser_dataframe(df)
            if len(df) >= 30:
                df_final = df
                strategie_reussie = "Requêtes HTTP Directes"
                log(f"✅ SUCCÈS STRATÉGIE 2: {len(df)} actions", 'SUCCESS')
    
    # STRATÉGIE 3: Recherche API Cachée
    if df_final.empty or len(df_final) < 30:
        log("Passage à la Stratégie 3...")
        df = strategie_3_recherche_api_cachee()
        if not df.empty:
            df = normaliser_dataframe(df)
            if len(df) >= 30:
                df_final = df
                strategie_reussie = "API Cachée"
                log(f"✅ SUCCÈS STRATÉGIE 3: {len(df)} actions", 'SUCCESS')
    
    # STRATÉGIE 4: Action par Action
    if df_final.empty or len(df_final) < 20:
        log("Passage à la Stratégie 4 (fallback)...")
        df = strategie_4_collecte_action_par_action()
        if not df.empty:
            df = normaliser_dataframe(df)
            if len(df) >= 20:
                df_final = df
                strategie_reussie = "Collecte Individuelle"
                log(f"✅ SUCCÈS STRATÉGIE 4: {len(df)} actions", 'SUCCESS')
    
    # Résultat final
    print()
    print("=" * 100)
    
    if df_final.empty:
        log("❌ ÉCHEC: Aucune stratégie n'a réussi", 'ERROR')
        print("=" * 100)
        client.close()
        return 1
    
    # Sauvegarder
    saved = sauvegarder_mongodb(df_final, db)
    
    # Export CSV
    import os
    os.makedirs('out_brvm', exist_ok=True)
    csv_path = f"out_brvm/brvm_garanti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_final.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # Résumé
    print("=" * 100)
    log(f"✅ COLLECTE RÉUSSIE", 'SUCCESS')
    print("=" * 100)
    print()
    log(f"Stratégie gagnante: {strategie_reussie}", 'SUCCESS')
    log(f"Actions collectées: {saved}/{len(ACTIONS_BRVM_47)}", 'SUCCESS')
    log(f"MongoDB: {saved} observations sauvegardées", 'SUCCESS')
    log(f"CSV: {csv_path}", 'SUCCESS')
    print()
    
    # Statistiques
    if len(df_final) > 0:
        print("📊 STATISTIQUES:")
        print(f"   Cours disponibles: {df_final['Cours'].notna().sum()}")
        if 'Variation_%' in df_final.columns:
            print(f"   Variations disponibles: {df_final['Variation_%'].notna().sum()}")
        if 'Volume' in df_final.columns:
            print(f"   Volumes disponibles: {df_final['Volume'].notna().sum()}")
        print()
        
        # Échantillon
        print("📋 ÉCHANTILLON:")
        cols_display = ['Ticker', 'Cours', 'Variation_%', 'Volume']
        cols_available = [c for c in cols_display if c in df_final.columns]
        print(df_final[cols_available].head(10).to_string(index=False))
    
    print()
    print("=" * 100)
    
    client.close()
    return 0 if saved >= 20 else 1

if __name__ == "__main__":
    sys.exit(main())
