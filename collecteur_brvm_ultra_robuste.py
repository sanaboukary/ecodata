#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COLLECTEUR BRVM ULTRA-ROBUSTE - Multi-stratégies avec fallback complet
Garantit la collecte des données BRVM par tous les moyens possibles

Stratégies (dans l'ordre) :
1. Scraping BeautifulSoup (site BRVM)
2. Scraping Selenium (si BS échoue)
3. Import CSV automatique (si fichier présent)
4. Saisie manuelle guidée (dernière option)

Politique : Toujours des DONNÉES RÉELLES - Jamais de simulation
"""

import os
import sys
import io
import re
import time
from datetime import datetime
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import urllib3
import pandas as pd

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Désactiver warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
DB_NAME = 'centralisation_db'
BRVM_URL = 'https://www.brvm.org/fr/investir/cours-et-cotations'

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
    """Log avec timestamp et couleurs."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    symbols = {
        'INFO': '📊',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'STRATEGY': '🎯',
        'DATA': '💾'
    }
    print(f"[{timestamp}] {symbols.get(level, 'ℹ️')} {message}")

def get_mongo():
    """Connexion MongoDB."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        # Test connexion
        client.server_info()
        return client, db
    except Exception as e:
        log(f"Erreur connexion MongoDB : {e}", 'ERROR')
        raise

def check_existing_data(db, date_str):
    """Vérifie données existantes."""
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date_str,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    return count

def save_observations(db, observations, data_quality='REAL_SCRAPER'):
    """Sauvegarde observations dans MongoDB."""
    if not observations:
        return 0
    
    saved = 0
    for obs in observations:
        try:
            # Ajouter data_quality
            if 'attrs' not in obs:
                obs['attrs'] = {}
            obs['attrs']['data_quality'] = data_quality
            
            # Upsert
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
            log(f"Erreur sauvegarde {obs.get('key')}: {e}", 'WARNING')
    
    return saved

# ========== UTILITAIRES SELENIUM AVANCÉS ==========

def _dismiss_cookies_if_any(driver, timeout=3):
    """Ferme les popups de cookies automatiquement."""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait as Wait
        from selenium.webdriver.support import expected_conditions as EC
        
        btns = Wait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
        )
        for b in btns:
            t = (b.text or "").strip().lower()
            if any(x in t for x in ["accepter", "accept", "j'accepte", "i agree", "consentir"]):
                try:
                    b.click()
                    time.sleep(0.3)
                    log("Cookie popup fermé", 'INFO')
                except:
                    pass
    except Exception:
        pass

def _read_tables(driver, timeout=25):
    """Lit toutes les tables HTML de la page avec pandas."""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait as Wait
        from selenium.webdriver.support import expected_conditions as EC
        
        Wait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(0.8)
        
        frames = []
        try:
            for df in pd.read_html(driver.page_source, flavor="lxml", thousands=" ", decimal=","):
                df.columns = [str(c).strip() for c in df.columns]
                frames.append(df.dropna(how="all"))
        except ValueError:
            pass
        
        if not frames:
            return pd.DataFrame()
        
        out = pd.concat(frames, ignore_index=True)
        out = out.loc[:, ~out.columns.duplicated()]
        return out
    except Exception as e:
        log(f"Erreur lecture tables: {e}", 'WARNING')
        return pd.DataFrame()

def _parse_fr_number(x):
    """Parse un nombre au format français (espace milliers, virgule décimale)."""
    if pd.isna(x):
        return None
    s = str(x).strip()
    # Retirer espaces de milliers, homogénéiser virgule
    s = s.replace("\xa0", " ").replace(" ", "")
    s = s.replace(",", ".")
    # Garder chiffres, signe et point
    m = re.match(r"^-?\d*\.?\d+$", s)
    if not m:
        return None
    try:
        return float(s)
    except:
        return None

def _clean_numeric_cols(df, force_float_cols=None):
    """Convertit les colonnes numériques au format français."""
    if df.empty:
        return df
    
    force_float_cols = force_float_cols or []
    for col in df.columns:
        # Si ≥70% des valeurs ressemblent à des nombres → convertir
        vals = df[col].astype(str)
        looks = vals.str.replace(r"\s", "", regex=True).str.replace(",", ".", regex=False)\
                    .str.match(r"^-?\d*\.?\d+$", na=False)
        if col in force_float_cols or looks.mean() >= 0.7:
            df[col] = df[col].map(_parse_fr_number)
    return df

def _normalize_action_cols(df):
    """Normalise les noms de colonnes BRVM."""
    rename_map = {
        "Symbole": "Ticker",
        "Libellé": "Libelle",
        "Libelle": "Libelle",
        "Dernier": "Dernier",
        "Dernier cours": "Dernier",
        "Variation (%)": "Var_%",
        "Variation (%) ": "Var_%",
        "Variation": "Variation",
        "Volume": "Volume",
        "Valeur": "Valeur",
        "Sector": "Secteur",
        "Secteur": "Secteur",
        "ISIN": "ISIN"
    }
    
    cols = {c: rename_map.get(c, c) for c in df.columns}
    df = df.rename(columns=cols)
    
    # Nettoyage numériques
    df = _clean_numeric_cols(df, force_float_cols=["Dernier", "Var_%", "Variation", "Volume", "Valeur"])
    
    # Ticker/libellé propres
    if "Ticker" in df.columns:
        df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
    if "Libelle" in df.columns:
        df["Libelle"] = df["Libelle"].astype(str).str.strip()
    
    return df

# ========== STRATÉGIES DE COLLECTE ==========

def strategie_0_selenium_avance():
    """Stratégie 0: Scraping Selenium avancé avec gestion cookies et multi-langue."""
    log("Stratégie 0: Scraping Selenium Avancé (FR/EN fallback)", 'STRATEGY')
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Configuration Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        log("Installation/Lancement ChromeDriver...", 'INFO')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # URLs à tester (FR puis EN)
        urls = [
            "https://www.brvm.org/fr/cours-actions/0",
            "https://www.brvm.org/en/cours-actions/0"
        ]
        
        actions_df = pd.DataFrame()
        used_url = None
        
        for url in urls:
            try:
                log(f"Tentative: {url}", 'INFO')
                driver.get(url)
                
                # Gérer cookies
                _dismiss_cookies_if_any(driver)
                
                # Lire tables
                df = _read_tables(driver)
                
                if not df.empty:
                    actions_df = df
                    used_url = url
                    log(f"Tables trouvées: {len(df)} lignes", 'SUCCESS')
                    break
                else:
                    log(f"Aucune table sur {url}", 'WARNING')
                    
            except Exception as e:
                log(f"Erreur sur {url}: {e}", 'WARNING')
                continue
        
        driver.quit()
        
        if actions_df.empty:
            log("Aucune donnée trouvée avec Selenium", 'WARNING')
            return None
        
        # Normalisation
        actions_df = _normalize_action_cols(actions_df)
        
        # Dédupliquer
        subset_cols = [c for c in ["Ticker", "Libelle"] if c in actions_df.columns]
        if subset_cols:
            actions_df = actions_df.drop_duplicates(subset=subset_cols, keep="first")
        
        # Conversion en observations MongoDB
        observations = []
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        for _, row in actions_df.iterrows():
            ticker = row.get('Ticker', '')
            dernier = row.get('Dernier')
            
            if pd.notna(ticker) and pd.notna(dernier) and ticker in SYMBOLES_BRVM:
                obs = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': str(ticker).strip().upper(),
                    'ts': date_str,
                    'value': float(dernier),
                    'attrs': {
                        'data_quality': 'REAL_SCRAPER',
                        'scrape_method': 'Selenium_Advanced',
                        'source_url': used_url,
                        'volume': float(row['Volume']) if pd.notna(row.get('Volume')) else None,
                        'variation_pct': float(row['Var_%']) if pd.notna(row.get('Var_%')) else None,
                        'secteur': str(row['Secteur']) if pd.notna(row.get('Secteur')) else None,
                        'libelle': str(row['Libelle']) if pd.notna(row.get('Libelle')) else None
                    }
                }
                observations.append(obs)
        
        if observations:
            log(f"Selenium avancé réussi: {len(observations)} cours", 'SUCCESS')
            
            # Export CSV de sauvegarde
            try:
                os.makedirs('out_brvm', exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_path = f"out_brvm/brvm_selenium_{ts}.csv"
                actions_df.to_csv(csv_path, index=False)
                log(f"CSV sauvegardé: {csv_path}", 'DATA')
            except Exception as e:
                log(f"Erreur export CSV: {e}", 'WARNING')
            
            return observations
        else:
            log("Aucun cours valide extrait", 'WARNING')
            return None
            
    except ImportError as e:
        log(f"Modules Selenium manquants: {e}", 'WARNING')
        log("Installez: pip install selenium webdriver-manager", 'INFO')
        return None
    except Exception as e:
        log(f"Erreur Selenium avancé: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return None

def strategie_1_scraping_bs4():
    """Stratégie 1: Scraping avec BeautifulSoup."""
    log("Stratégie 1: Scraping BeautifulSoup", 'STRATEGY')
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(BRVM_URL, headers=headers, verify=False, timeout=30)
        
        if response.status_code != 200:
            log(f"HTTP {response.status_code}", 'WARNING')
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher tableau des cours
        tables = soup.find_all('table')
        log(f"Trouvé {len(tables)} tableau(x)", 'INFO')
        
        observations = []
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 3:
                    try:
                        symbole = cols[0].get_text(strip=True)
                        prix_text = cols[1].get_text(strip=True).replace(' ', '').replace(',', '.')
                        
                        if symbole in SYMBOLES_BRVM:
                            prix = float(prix_text)
                            
                            obs = {
                                'source': 'BRVM',
                                'dataset': 'STOCK_PRICE',
                                'key': symbole,
                                'ts': date_str,
                                'value': prix,
                                'attrs': {
                                    'data_quality': 'REAL_SCRAPER',
                                    'scrape_method': 'BeautifulSoup'
                                }
                            }
                            observations.append(obs)
                    except (ValueError, IndexError):
                        continue
        
        if observations:
            log(f"Scraping réussi: {len(observations)} cours", 'SUCCESS')
            return observations
        else:
            log("Aucun cours trouvé dans le HTML", 'WARNING')
            return None
            
    except Exception as e:
        log(f"Erreur scraping BS4: {e}", 'WARNING')
        return None

def strategie_2_import_csv():
    """Stratégie 2: Import CSV automatique si disponible."""
    log("Stratégie 2: Recherche fichier CSV", 'STRATEGY')
    
    csv_paths = [
        'cours_brvm.csv',
        'data/cours_brvm.csv',
        'cours_brvm_*.csv'
    ]
    
    import glob
    for pattern in csv_paths:
        files = glob.glob(pattern)
        if files:
            latest = max(files, key=os.path.getmtime)
            log(f"Fichier CSV trouvé: {latest}", 'INFO')
            
            try:
                import csv
                observations = []
                date_str = datetime.now().strftime('%Y-%m-%d')
                
                with open(latest, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'SYMBOL' in row and 'CLOSE' in row:
                            obs = {
                                'source': 'BRVM',
                                'dataset': 'STOCK_PRICE',
                                'key': row['SYMBOL'],
                                'ts': row.get('DATE', date_str),
                                'value': float(row['CLOSE']),
                                'attrs': {
                                    'data_quality': 'REAL_MANUAL',
                                    'import_method': 'CSV'
                                }
                            }
                            observations.append(obs)
                
                if observations:
                    log(f"Import CSV réussi: {len(observations)} cours", 'SUCCESS')
                    return observations
                    
            except Exception as e:
                log(f"Erreur import CSV: {e}", 'WARNING')
    
    log("Aucun fichier CSV trouvé", 'INFO')
    return None

def strategie_3_saisie_manuelle():
    """Stratégie 3: Saisie manuelle guidée."""
    log("Stratégie 3: Saisie manuelle", 'STRATEGY')
    
    print("\n" + "=" * 80)
    print("📝 SAISIE MANUELLE DES COURS BRVM")
    print("=" * 80)
    print("\n🌐 Allez sur: https://www.brvm.org/fr/investir/cours-et-cotations")
    print("\n📋 Saisissez les cours pour les principales actions:")
    print("   Format: SYMBOLE=PRIX (ex: SNTS=15500)")
    print("   Tapez 'fin' pour terminer")
    print("   Tapez 'skip' pour passer\n")
    
    observations = []
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    principales_actions = ['SNTS', 'SGBC', 'BOAM', 'UNLC', 'ONTBF', 'SICC', 'SLBC', 
                          'SOGB', 'TTLC', 'ETIT']
    
    for symbole in principales_actions:
        while True:
            try:
                entree = input(f"{symbole}: ").strip()
                
                if entree.lower() == 'fin':
                    if observations:
                        log(f"Saisie terminée: {len(observations)} cours", 'SUCCESS')
                        return observations
                    else:
                        log("Aucun cours saisi", 'WARNING')
                        return None
                
                if entree.lower() == 'skip':
                    log("Saisie annulée", 'WARNING')
                    return None
                
                if '=' in entree:
                    parts = entree.split('=')
                    sym = parts[0].strip().upper()
                    prix = float(parts[1].strip())
                else:
                    prix = float(entree)
                    sym = symbole
                
                obs = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': sym,
                    'ts': date_str,
                    'value': prix,
                    'attrs': {
                        'data_quality': 'REAL_MANUAL',
                        'entry_method': 'Manual Input',
                        'entry_date': datetime.now().isoformat()
                    }
                }
                observations.append(obs)
                log(f"{sym} = {prix} FCFA", 'DATA')
                break
                
            except ValueError:
                print("❌ Format invalide. Réessayez.")
            except KeyboardInterrupt:
                log("\nSaisie interrompue", 'WARNING')
                return observations if observations else None
    
    # Proposer de continuer pour autres actions
    print("\n✅ Principales actions saisies.")
    continuer = input("Continuer avec d'autres actions? (y/n): ").strip().lower()
    
    if continuer == 'y':
        while True:
            try:
                entree = input("Action (SYMBOLE=PRIX ou 'fin'): ").strip()
                if entree.lower() == 'fin':
                    break
                    
                if '=' in entree:
                    sym, prix = entree.split('=')
                    obs = {
                        'source': 'BRVM',
                        'dataset': 'STOCK_PRICE',
                        'key': sym.strip().upper(),
                        'ts': date_str,
                        'value': float(prix.strip()),
                        'attrs': {
                            'data_quality': 'REAL_MANUAL',
                            'entry_method': 'Manual Input'
                        }
                    }
                    observations.append(obs)
                    log(f"{sym} = {prix} FCFA", 'DATA')
            except (ValueError, KeyboardInterrupt):
                break
    
    if observations:
        log(f"Saisie terminée: {len(observations)} cours", 'SUCCESS')
        return observations
    else:
        log("Aucun cours saisi", 'WARNING')
        return None

def collecte_brvm_robuste():
    """Collecte BRVM ultra-robuste avec stratégies multiples."""
    print("=" * 80)
    print("🚀 COLLECTEUR BRVM ULTRA-ROBUSTE")
    print("=" * 80)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    log(f"Date de collecte: {date_str}")
    
    try:
        # Connexion MongoDB
        log("Connexion à MongoDB...")
        client, db = get_mongo()
        log("MongoDB connecté", 'SUCCESS')
        
        # Vérifier données existantes
        existing = check_existing_data(db, date_str)
        if existing > 0:
            log(f"Données déjà présentes: {existing} observations", 'INFO')
            forcer = input("Forcer la collecte? (y/n): ").strip().lower()
            if forcer != 'y':
                log("Collecte annulée", 'WARNING')
                client.close()
                return 0
        
        # Tentative des stratégies dans l'ordre
        strategies = [
            ('Scraping Selenium Avancé', strategie_0_selenium_avance),
            ('Scraping BeautifulSoup', strategie_1_scraping_bs4),
            ('Import CSV', strategie_2_import_csv),
            ('Saisie manuelle', strategie_3_saisie_manuelle)
        ]
        
        observations = None
        strategy_used = None
        
        for strategy_name, strategy_func in strategies:
            log(f"\n{'='*80}", 'INFO')
            log(f"Tentative: {strategy_name}", 'INFO')
            log(f"{'='*80}", 'INFO')
            
            try:
                observations = strategy_func()
                if observations and len(observations) > 0:
                    strategy_used = strategy_name
                    log(f"Stratégie réussie: {strategy_name}", 'SUCCESS')
                    break
            except Exception as e:
                log(f"Échec {strategy_name}: {e}", 'WARNING')
                continue
        
        # Sauvegarde des observations
        if observations:
            log(f"\nSauvegarde de {len(observations)} observations...", 'INFO')
            saved = save_observations(db, observations)
            
            print("\n" + "=" * 80)
            log(f"COLLECTE RÉUSSIE", 'SUCCESS')
            log(f"Stratégie utilisée: {strategy_used}", 'SUCCESS')
            log(f"Observations sauvegardées: {saved}", 'SUCCESS')
            log(f"Date: {date_str}", 'INFO')
            print("=" * 80)
            
            # Vérification finale
            final_count = check_existing_data(db, date_str)
            log(f"\nTotal BRVM pour {date_str}: {final_count} observations", 'DATA')
            
            client.close()
            return saved
        else:
            print("\n" + "=" * 80)
            log("ÉCHEC: Aucune stratégie n'a réussi", 'ERROR')
            log("Impossible de collecter des données réelles", 'ERROR')
            print("=" * 80)
            
            client.close()
            return 0
            
    except Exception as e:
        log(f"ERREUR CRITIQUE: {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    import sys
    result = collecte_brvm_robuste()
    sys.exit(0 if result > 0 else 1)
