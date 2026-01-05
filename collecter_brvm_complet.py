#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COLLECTEUR COMPLET BRVM - 47 Actions
Collecte: Cours, Variations, Volatilité, Liquidité + Tous les indicateurs disponibles
"""

import sys
import os
import io
import re
import time
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
from pymongo import MongoClient
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
DB_NAME = 'centralisation_db'

# User-agents multiples pour rotation (navigateurs réels)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Headers HTTP réalistes
def get_realistic_headers():
    """Génère headers HTTP réalistes avec randomisation."""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': random.choice(['fr-FR,fr;q=0.9,en;q=0.8', 'en-US,en;q=0.9,fr;q=0.8']),
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def random_delay(min_sec=1.0, max_sec=3.0):
    """Délai aléatoire pour simuler comportement humain."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

# 47 Actions BRVM officielles
ACTIONS_BRVM_47 = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAS',
    'CABC', 'CFAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'NTLC', 'NSBC',
    'ONTBF', 'ORAC', 'ORGT', 'PALC', 'PRSC', 'SAFC', 'SAGC', 'SCRC',
    'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICC', 'SICB',
    'SLBC', 'SMBC', 'SNTS', 'SOGB', 'SPHC', 'STAC', 'STBC', 'SVOC',
    'TTLC', 'TTRC', 'TUBC', 'UNLC', 'UNXC', 'NEIC', 'TOTAL'
]

def log(message, level='INFO'):
    """Log avec timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    symbols = {'INFO': '📊', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌', 'DATA': '💾'}
    print(f"[{timestamp}] {symbols.get(level, 'ℹ️')} {message}")

def parse_french_number(x):
    """Parse nombre format français."""
    if pd.isna(x) or x == '' or x == '-':
        return None
    s = str(x).strip()
    s = s.replace('\xa0', ' ').replace(' ', '').replace(',', '.')
    m = re.match(r'^-?\d*\.?\d+$', s)
    if not m:
        return None
    try:
        return float(s)
    except:
        return None

def collecter_selenium_complet():
    """Collecte complète avec Selenium - Toutes métriques - Mode FURTIF."""
    log("Démarrage collecte Selenium FURTIVE")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait as Wait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        # User-agent aléatoire
        user_agent = random.choice(USER_AGENTS)
        log(f"User-Agent: {user_agent[:50]}...")
        
        # Configuration Chrome ANTI-DÉTECTION
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Mode headless moderne
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Masquer automation
        chrome_options.add_argument(f'--user-agent={user_agent}')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--dns-prefetch-disable')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Préférences anti-détection
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        log("Lancement ChromeDriver FURTIF...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Script anti-détection : masquer webdriver
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR', 'fr', 'en-US', 'en']})")
        
        log("✅ ChromeDriver configuré en mode INDÉTECTABLE", 'SUCCESS')
        
        # URLs à essayer
        urls = [
            "https://www.brvm.org/fr/cours-actions/0",
            "https://www.brvm.org/en/cours-actions/0"
        ]
        
        all_data = []
        
        for url in urls:
            try:
                log(f"Connexion: {url}")
                
                # Délai humain avant requête
                random_delay(0.5, 1.5)
                
                driver.get(url)
                
                # Comportement humain : attendre un peu
                random_delay(1.0, 2.0)
                
                # Scroll aléatoire léger (simulation humaine)
                driver.execute_script(f"window.scrollTo(0, {random.randint(50, 150)});")
                random_delay(0.3, 0.7)
                driver.execute_script("window.scrollTo(0, 0);")
                
                # Fermer cookies avec délai humain
                try:
                    btns = Wait(driver, 3).until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
                    )
                    for b in btns:
                        if any(x in (b.text or "").lower() for x in ["accept", "accepter", "agree"]):
                            random_delay(0.2, 0.5)  # Délai avant clic
                            b.click()
                            random_delay(0.3, 0.6)  # Délai après clic
                            log("Cookies acceptés", 'INFO')
                            break
                except:
                    pass
                
                # Attendre tables
                Wait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                
                # SCROLL pour charger TOUTES les actions (pagination lazy-load) - MODE HUMAIN
                log("Scroll progressif pour charger toutes les 47 actions...")
                last_height = driver.execute_script("return document.body.scrollHeight")
                scroll_attempts = 0
                max_scrolls = 15
                
                while scroll_attempts < max_scrolls:
                    # Scroll progressif (pas instantané, comme un humain)
                    current_position = driver.execute_script("return window.pageYOffset;")
                    scroll_increment = random.randint(300, 600)
                    target_position = min(current_position + scroll_increment, last_height)
                    
                    driver.execute_script(f"window.scrollTo({{top: {target_position}, behavior: 'smooth'}});")
                    
                    # Délai aléatoire humain
                    random_delay(1.2, 2.5)
                    
                    # Parfois scroll retour (comportement humain)
                    if random.random() < 0.2:  # 20% de chance
                        back_scroll = random.randint(50, 150)
                        driver.execute_script(f"window.scrollBy(0, -{back_scroll});")
                        random_delay(0.3, 0.8)
                    
                    # Vérifier si nouvelle hauteur
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height and target_position >= last_height - 100:
                        # Scroll vers le bas absolu pour forcer chargement
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        random_delay(2.0, 3.0)
                        
                        final_height = driver.execute_script("return document.body.scrollHeight")
                        if final_height == new_height:
                            # Plus de contenu à charger
                            break
                    
                    last_height = new_height
                    scroll_attempts += 1
                    
                    # Compter lignes chargées
                    try:
                        temp_dfs = pd.read_html(driver.page_source, thousands=" ", decimal=",")
                        if temp_dfs:
                            max_rows = max(len(df) for df in temp_dfs)
                            log(f"  Scroll {scroll_attempts}: ~{max_rows} lignes")
                            if max_rows >= 47:
                                log("✅ 47+ lignes détectées", 'SUCCESS')
                                random_delay(1.0, 2.0)  # Attendre un peu plus
                                break
                    except:
                        pass
                
                # Scroll final vers le haut (naturel)
                driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
                random_delay(1.5, 2.5)
                
                # Lire toutes les tables
                dfs = pd.read_html(driver.page_source, thousands=" ", decimal=",")
                
                for df in dfs:
                    if not df.empty and len(df.columns) >= 3:
                        all_data.append(df)
                
                if all_data:
                    log(f"✅ {len(all_data)} table(s) collectée(s)", 'SUCCESS')
                    break
                    
            except Exception as e:
                log(f"Erreur sur {url}: {e}", 'WARNING')
                random_delay(2.0, 4.0)  # Délai avant retry
                continue
        
        # Comportement humain avant fermeture
        random_delay(0.5, 1.0)
        driver.quit()
        log("ChromeDriver fermé proprement", 'INFO')
        
        if not all_data:
            log("Aucune donnée collectée", 'ERROR')
            return pd.DataFrame()
        
        # Concat et nettoyage
        df_combined = pd.concat(all_data, ignore_index=True).dropna(how='all')
        
        # Normalisation colonnes
        rename_map = {
            'Symbole': 'Ticker', 'Symbol': 'Ticker',
            'Libellé': 'Libelle', 'Libelle': 'Libelle', 'Name': 'Libelle',
            'Dernier': 'Cours', 'Dernier cours': 'Cours', 'Last': 'Cours', 'Close': 'Cours',
            'Cours': 'Cours',
            'Variation (%)': 'Variation_%', 'Variation': 'Variation_%', 'Change (%)': 'Variation_%',
            'Volume': 'Volume', 'Quantité': 'Volume',
            'Valeur': 'Valeur', 'Value': 'Valeur',
            'Ouverture': 'Ouverture', 'Open': 'Ouverture',
            'Plus Haut': 'Haut', 'High': 'Haut', 'Haut': 'Haut',
            'Plus Bas': 'Bas', 'Low': 'Bas', 'Bas': 'Bas',
            'Secteur': 'Secteur', 'Sector': 'Secteur',
            'Précédent': 'Precedent', 'Previous': 'Precedent',
            'Nb Trans': 'Nb_Transactions', 'Transactions': 'Nb_Transactions',
            'Cap. Bours.': 'Capitalisation', 'Market Cap': 'Capitalisation'
        }
        
        cols = {c: rename_map.get(c, c) for c in df_combined.columns}
        df_combined = df_combined.rename(columns=cols)
        
        # Convertir numériques
        numeric_cols = ['Cours', 'Variation_%', 'Volume', 'Valeur', 'Ouverture', 
                       'Haut', 'Bas', 'Precedent', 'Nb_Transactions', 'Capitalisation']
        
        for col in numeric_cols:
            if col in df_combined.columns:
                df_combined[col] = df_combined[col].apply(parse_french_number)
        
        # Nettoyer Ticker
        if 'Ticker' in df_combined.columns:
            df_combined['Ticker'] = df_combined['Ticker'].astype(str).str.strip().str.upper()
            
            # Log avant filtrage
            log(f"Actions brutes collectées: {len(df_combined)}")
            
            # Filtrer seulement les 47 actions (mais garder toutes si tickers différents)
            valid_mask = df_combined['Ticker'].isin(ACTIONS_BRVM_47)
            if valid_mask.any():  # Fix: use .any() au lieu de if len()
                df_combined = df_combined[valid_mask]
            else:
                log("⚠️ Aucun ticker connu trouvé, conservation de tous", 'WARNING')
        
        # Dédupliquer
        if 'Ticker' in df_combined.columns:
            df_combined = df_combined.drop_duplicates(subset=['Ticker'], keep='first')
        
        log(f"Données nettoyées: {len(df_combined)} actions (objectif: 47)", 'SUCCESS' if len(df_combined) >= 40 else 'WARNING')
        
        return df_combined
        
    except Exception as e:
        log(f"Erreur Selenium: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def calculer_metriques_avancees(df, db):
    """Calcule volatilité et liquidité depuis l'historique."""
    
    if df.empty or 'Ticker' not in df.columns:
        return df
    
    log("Calcul métriques avancées (volatilité, liquidité)...")
    
    # Récupérer historique 30 jours pour volatilité
    date_fin = datetime.now()
    date_debut = date_fin - timedelta(days=30)
    
    volatilites = {}
    liquidites = {}
    
    for ticker in df['Ticker'].unique():
        # Historique cours
        hist = list(db.curated_observations.find({
            'source': 'BRVM',
            'key': ticker,
            'ts': {'$gte': date_debut.strftime('%Y-%m-%d')}
        }).sort('ts', 1))
        
        if len(hist) >= 5:  # Minimum 5 jours pour calcul
            prix = [h['value'] for h in hist if h.get('value')]
            volumes = [h.get('attrs', {}).get('volume', 0) for h in hist]
            
            # Volatilité = écart-type des rendements
            if len(prix) >= 2:
                rendements = [(prix[i] - prix[i-1]) / prix[i-1] for i in range(1, len(prix))]
                volatilites[ticker] = np.std(rendements) * 100 if rendements else 0
            
            # Liquidité = volume moyen
            if volumes:
                liquidites[ticker] = np.mean([v for v in volumes if v > 0])
    
    # Ajouter au DataFrame
    df['Volatilite_%'] = df['Ticker'].map(volatilites).fillna(0)
    df['Liquidite_Moy'] = df['Ticker'].map(liquidites).fillna(0)
    
    log(f"Volatilité calculée pour {len(volatilites)} actions", 'DATA')
    log(f"Liquidité calculée pour {len(liquidites)} actions", 'DATA')
    
    return df

def sauvegarder_mongodb(df, db):
    """Sauvegarde dans MongoDB avec toutes les métriques."""
    
    if df.empty:
        return 0
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    saved = 0
    
    for _, row in df.iterrows():
        ticker = row.get('Ticker')
        cours = row.get('Cours')
        
        if pd.isna(ticker) or pd.isna(cours):
            continue
        
        obs = {
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE_COMPLET',
            'key': str(ticker),
            'ts': date_str,
            'value': float(cours),
            'attrs': {
                'data_quality': 'REAL_SCRAPER',
                'scrape_method': 'Selenium_Complet',
                'collecte_ts': datetime.now().isoformat(),
                
                # Données de base
                'libelle': str(row.get('Libelle', '')),
                'secteur': str(row.get('Secteur', '')),
                
                # Prix et variations
                'cours': float(cours),
                'ouverture': float(row['Ouverture']) if pd.notna(row.get('Ouverture')) else None,
                'haut': float(row['Haut']) if pd.notna(row.get('Haut')) else None,
                'bas': float(row['Bas']) if pd.notna(row.get('Bas')) else None,
                'precedent': float(row['Precedent']) if pd.notna(row.get('Precedent')) else None,
                
                # Variation
                'variation_pct': float(row['Variation_%']) if pd.notna(row.get('Variation_%')) else None,
                
                # Volume et liquidité
                'volume': float(row['Volume']) if pd.notna(row.get('Volume')) else None,
                'valeur': float(row['Valeur']) if pd.notna(row.get('Valeur')) else None,
                'nb_transactions': float(row['Nb_Transactions']) if pd.notna(row.get('Nb_Transactions')) else None,
                'liquidite_moyenne': float(row['Liquidite_Moy']) if pd.notna(row.get('Liquidite_Moy')) else None,
                
                # Volatilité
                'volatilite_pct': float(row['Volatilite_%']) if pd.notna(row.get('Volatilite_%')) else None,
                
                # Capitalisation
                'capitalisation': float(row['Capitalisation']) if pd.notna(row.get('Capitalisation')) else None
            }
        }
        
        # Upsert
        db.curated_observations.update_one(
            {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE_COMPLET',
                'key': ticker,
                'ts': date_str
            },
            {'$set': obs},
            upsert=True
        )
        saved += 1
    
    return saved

def main():
    print("=" * 80)
    print("🚀 COLLECTEUR COMPLET BRVM - 47 ACTIONS")
    print("=" * 80)
    print()
    print("📊 Métriques collectées:")
    print("   • Cours (prix actuel)")
    print("   • Variations (%)")
    print("   • Volatilité (écart-type 30j)")
    print("   • Liquidité (volume moyen)")
    print("   • OHLC (Ouverture, Haut, Bas, Clôture)")
    print("   • Volume, Valeur, Transactions")
    print("   • Capitalisation boursière")
    print()
    print("🎯 Objectif: Collecter LES 47 ACTIONS COTÉES")
    print("=" * 80)
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
    
    # Collecte Selenium
    df = collecter_selenium_complet()
    
    if df.empty:
        log("Échec collecte - Aucune donnée", 'ERROR')
        client.close()
        return 1
    
    log(f"Données brutes: {len(df)} actions", 'DATA')
    
    # Vérification objectif 47 actions
    if len(df) < 40:
        log(f"⚠️ Seulement {len(df)}/47 actions collectées", 'WARNING')
        log("Le site BRVM a peut-être changé de structure ou problème de chargement", 'WARNING')
    elif len(df) >= 47:
        log(f"✅ OBJECTIF ATTEINT: {len(df)}/47 actions", 'SUCCESS')
    
    # Calculer métriques avancées
    df = calculer_metriques_avancees(df, db)
    
    # Sauvegarder MongoDB
    log("Sauvegarde MongoDB...")
    saved = sauvegarder_mongodb(df, db)
    
    # Export CSV
    log("Export CSV...")
    os.makedirs('out_brvm', exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"out_brvm/brvm_complet_{ts}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # Résumé
    print()
    print("=" * 80)
    log(f"COLLECTE TERMINÉE", 'SUCCESS')
    print("=" * 80)
    print()
    log(f"Actions collectées: {saved}/47", 'DATA')
    log(f"CSV exporté: {csv_path}", 'DATA')
    print()
    
    # Afficher échantillon
    if not df.empty:
        print("📋 ÉCHANTILLON DES DONNÉES:")
        print("=" * 80)
        
        cols_display = ['Ticker', 'Cours', 'Variation_%', 'Volatilite_%', 
                       'Volume', 'Liquidite_Moy', 'Secteur']
        cols_available = [c for c in cols_display if c in df.columns]
        
        print(df[cols_available].head(10).to_string(index=False))
        print()
        
        # Stats
        print("=" * 80)
        print("📊 STATISTIQUES:")
        print("=" * 80)
        actions_avec_volatilite = (df['Volatilite_%'] > 0).sum()
        actions_avec_volume = (df['Volume'] > 0).sum() if 'Volume' in df.columns else 0
        
        log(f"Actions avec cours: {len(df)}", 'DATA')
        log(f"Actions avec variation: {df['Variation_%'].notna().sum()}" if 'Variation_%' in df.columns else "N/A", 'DATA')
        log(f"Actions avec volatilité calculée: {actions_avec_volatilite}", 'DATA')
        log(f"Actions avec volume: {actions_avec_volume}", 'DATA')
        
        print()
        
        # Actions manquantes
        tickers_collectes = set(df['Ticker'].unique())
        tickers_manquants = set(ACTIONS_BRVM_47) - tickers_collectes
        
        if tickers_manquants:
            log(f"Actions non trouvées ({len(tickers_manquants)}): {', '.join(sorted(tickers_manquants))}", 'WARNING')
        else:
            log("✅ TOUTES LES 47 ACTIONS COLLECTÉES", 'SUCCESS')
    
    print()
    print("=" * 80)
    
    client.close()
    return 0 if saved > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
