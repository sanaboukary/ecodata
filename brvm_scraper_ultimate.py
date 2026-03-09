#!/usr/bin/env python3
"""
SCRAPER BRVM ULTIMATE - VERSION ULTRA-ROBUSTE
=============================================

Stratégies multiples pour garantir la collecte des 47 actions BRVM :
1. BeautifulSoup + Requests (sans navigateur)
2. Selenium Headless (anti-détection avancée)
3. Selenium Visible (si headless échoue)
4. Parsing HTML agressif (tous les patterns possibles)
5. Logs détaillés pour diagnostiquer échecs

POLITIQUE STRICTE : Données réelles uniquement (data_quality='REAL_SCRAPER')
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import pymongo
import os
from datetime import datetime
import re
import time
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import random

load_dotenv()

# Liste complète des 47 actions BRVM
ACTIONS_BRVM = [
    'BICC', 'BOAB', 'BOABF', 'BNBC', 'ETIT', 'NTLC', 'ONTBF', 'PALM', 'PRSC', 
    'SDCC', 'SDSC', 'SHEC', 'SIBC', 'SITC', 'SLBC', 'SMBC', 'SNTS', 'SOGB', 
    'STBC', 'STAC', 'TTLC', 'TTLS', 'UNXC', 'CIEC', 'CFAC', 'FTSC', 'NEIC', 
    'NSBC', 'ORGT', 'SAFC', 'SCRC', 'SGBC', 'SIVC', 'SPHC', 'TOAC', 'BOAC', 
    'CABC', 'ECOC', 'SETC', 'SICC', 'SOGC', 'ABJC', 'BOAM', 'CBIBF', 'SVOC', 
    'PALC', 'SEMC'
]

def extraire_nombre(texte):
    """Extraire nombre avec espaces, virgules"""
    if not texte:
        return None
    # Enlever espaces et remplacer virgules
    nombre_str = re.sub(r'[^\d,.]', '', str(texte))
    nombre_str = nombre_str.replace(' ', '').replace(',', '')
    try:
        return float(nombre_str) if nombre_str else None
    except:
        return None

def extraire_pourcentage(texte):
    """Extraire pourcentage (+2.5% → 2.5)"""
    if not texte:
        return None
    match = re.search(r'([+-]?\d+[.,]\d+)', str(texte))
    if match:
        try:
            return float(match.group(1).replace(',', '.'))
        except:
            return None
    return None


def extraire_donnees_enrichies(cells_texts, symbol):
    """
    Extraire TOUTES les données d'une ligne de table BRVM:
    - Prix: Open, High, Low, Close, Previous
    - Volume et liquidité
    - Variation (% et absolue)
    - Market Cap si disponible
    
    Format typique BRVM:
    [Symbol, Open, High, Low, Close, Variation%, Volume, Market_Cap, ...]
    ou variantes
    """
    data = {
        'symbol': symbol,
        'close': None,
        'open': None,
        'high': None,
        'low': None,
        'previous': None,
        'variation_pct': None,
        'variation_abs': None,
        'volume': None,
        'value_traded': None,  # Valeur échangée (FCFA)
        'market_cap': None,
        'trades_count': None,  # Nombre de transactions
    }
    
    # Extraire tous les nombres de la ligne
    nombres = []
    for text in cells_texts:
        nb = extraire_nombre(text)
        if nb:
            nombres.append(nb)
    
    # Heuristique: identifier les colonnes
    # Prix BRVM typiques: 100-100000 FCFA
    prix_candidats = [n for n in nombres if 50 < n < 100000]
    
    # Variation typique: -20% à +20% (ou valeurs absolues)
    variation_candidats = [n for n in nombres if -20 < n < 20 and n != 0]
    
    # Volumes typiques: > 100
    volume_candidats = [n for n in nombres if n > 100]
    
    # Attribution intelligente
    if len(prix_candidats) >= 1:
        data['close'] = prix_candidats[0]  # Premier prix = Close généralement
    
    if len(prix_candidats) >= 4:
        # Format OHLC probable
        data['open'] = prix_candidats[0]
        data['high'] = max(prix_candidats[:4])
        data['low'] = min(prix_candidats[:4])
        data['close'] = prix_candidats[3]
    elif len(prix_candidats) >= 2:
        data['previous'] = prix_candidats[1]
    
    # Variation: chercher %
    for text in cells_texts:
        if '%' in str(text) or '+' in str(text) or '-' in str(text):
            var = extraire_pourcentage(text)
            if var and -30 < var < 30:
                data['variation_pct'] = var
                break
    
    # Volume: plus grand nombre généralement
    if volume_candidats:
        data['volume'] = max(volume_candidats)
    
    # Calculer variation absolue si on a close et previous
    if data['close'] and data['previous']:
        data['variation_abs'] = data['close'] - data['previous']
        if not data['variation_pct'] and data['previous'] > 0:
            data['variation_pct'] = ((data['close'] - data['previous']) / data['previous']) * 100
    
    # Valeur échangée = volume × prix
    if data['volume'] and data['close']:
        data['value_traded'] = data['volume'] * data['close']
    
    return data


def calculer_metriques_liquidite(data, historique=None):
    """
    Calculer métriques de liquidité et volatilité
    
    Liquidité:
    - Volume relatif (vs moyenne)
    - Turnover ratio
    - Bid-ask spread (si disponible)
    
    Volatilité:
    - Écart-type des variations
    - ATR (Average True Range)
    """
    metriques = {}
    
    # Liquidité basique
    if data.get('volume'):
        metriques['volume'] = data['volume']
        metriques['liquidity_score'] = 'high' if data['volume'] > 5000 else ('medium' if data['volume'] > 1000 else 'low')
    
    if data.get('value_traded'):
        metriques['value_traded'] = data['value_traded']
        metriques['value_traded_millions'] = round(data['value_traded'] / 1_000_000, 2)
    
    # Volatilité du jour
    if data.get('variation_pct') is not None:
        metriques['volatility_daily'] = abs(data['variation_pct'])
        metriques['volatility_category'] = 'high' if abs(data['variation_pct']) > 3 else ('medium' if abs(data['variation_pct']) > 1 else 'low')
    
    # Range du jour (High-Low)
    if data.get('high') and data.get('low') and data.get('close'):
        daily_range = data['high'] - data['low']
        metriques['daily_range'] = daily_range
        metriques['daily_range_pct'] = (daily_range / data['close']) * 100 if data['close'] > 0 else 0
    
    return metriques


def scraper_beautifulsoup_direct():
    """
    STRATÉGIE 0: Requests + BeautifulSoup (sans navigateur)
    Plus rapide et moins détectable
    """
    print("\n🌐 BeautifulSoup: Requêtes HTTP directes...")
    actions_trouvees = {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    urls = [
        'https://www.brvm.org/fr/cours-actions',
        'https://www.brvm.org/fr/marche/titres-et-cotations',
        'https://www.brvm.org/fr',
        'https://www.brvm.org',
    ]
    
    for url in urls:
        if len(actions_trouvees) >= 40:
            break
            
        try:
            print(f"  📡 GET {url}")
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Sauvegarder HTML pour debug
                filename = f"debug_bs4_{url.split('/')[-1] or 'home'}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                print(f"    💾 Sauvegardé: {filename}")
                
                # Chercher dans tables
                tables = soup.find_all('table')
                print(f"    📊 {len(tables)} table(s) trouvée(s)")
                
                for idx, table in enumerate(tables):
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            cell_texts = [c.get_text(strip=True) for c in cells]
                            
                            # Chercher symbole
                            for symbol in ACTIONS_BRVM:
                                if any(symbol in ct for ct in cell_texts[:3]):
                                    if symbol not in actions_trouvees:
                                        # Extraction enrichie
                                        data = extraire_donnees_enrichies(cell_texts, symbol)
                                        
                                        if data['close']:
                                            # Calculer métriques
                                            metriques = calculer_metriques_liquidite(data)
                                            data.update(metriques)
                                            
                                            data['source'] = url
                                            data['method'] = 'beautifulsoup'
                                            
                                            actions_trouvees[symbol] = data
                                            
                                            # Affichage enrichi
                                            print(f"      ✓ {symbol}: {data['close']:,.0f} FCFA", end="")
                                            if data.get('variation_pct'):
                                                print(f" ({data['variation_pct']:+.2f}%)", end="")
                                            if data.get('volume'):
                                                print(f" Vol:{data['volume']:,}", end="")
                                            print()
                                    break
                
                # Chercher dans tout le texte
                text = soup.get_text()
                for symbol in ACTIONS_BRVM:
                    if symbol in text and symbol not in actions_trouvees:
                        # Pattern: SYMBOL ... PRIX (chercher dans 200 caractères après)
                        idx = text.find(symbol)
                        fragment = text[idx:idx+200]
                        
                        nombres = re.findall(r'\b(\d{2,6}[.,]?\d*)\b', fragment)
                        for nb in nombres:
                            prix = extraire_nombre(nb)
                            if prix and 50 < prix < 100000:
                                actions_trouvees[symbol] = {
                                    'symbol': symbol,
                                    'close': prix,
                                    'source': url,
                                    'method': 'beautifulsoup_text'
                                }
                                print(f"      ✓ {symbol}: {prix:,.0f} FCFA (texte)")
                                break
                
        except Exception as e:
            print(f"    ❌ Erreur: {str(e)[:100]}")
            continue
    
    print(f"\n  📊 BeautifulSoup: {len(actions_trouvees)}/47 actions")
    return actions_trouvees


def setup_driver(headless=True):
    """
    Configure Chrome avec anti-détection ULTRA-ROBUSTE
    """
    options = Options()
    
    # Headless optionnel
    if headless:
        options.add_argument('--headless=new')
    else:
        print("  ⚡ Mode VISIBLE activé pour contournement anti-bot")
    
    # Anti-détection ultra-robuste
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Performance
    options.add_argument('--disable-images')
    options.add_argument('--blink-settings=imagesEnabled=false')
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    # Stabilité
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    
    # User agents variés
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    
    # Langue française
    options.add_argument('--lang=fr-FR')
    
    driver = webdriver.Chrome(options=options)
    
    # Anti-détection JavaScript
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR', 'fr', 'en']});
            window.chrome = {runtime: {}};
        '''
    })
    
    # Timeouts généreux
    driver.set_page_load_timeout(120)  # 2 minutes
    driver.implicitly_wait(20)  # 20 secondes
    
    return driver


def scraper_selenium(headless=True, actions_existantes=None):
    """
    STRATÉGIE 1/2: Selenium avec headless configurable
    """
    if actions_existantes is None:
        actions_existantes = {}
    
    actions_trouvees = dict(actions_existantes)
    
    print(f"\n🤖 Selenium {'HEADLESS' if headless else 'VISIBLE'}...")
    
    try:
        driver = setup_driver(headless=headless)
        
        # URLs multiples (ordre stratégique)
        urls = [
            'https://www.brvm.org/fr/cours-actions',
            'https://www.brvm.org/fr/marche/titres-et-cotations',
            'https://www.brvm.org/fr/cotations',
            'https://www.brvm.org/fr/investir/cours-et-cotations',
            'https://www.brvm.org/fr/marche',
            'https://www.brvm.org/fr/cours',
            'https://www.brvm.org/en/market-data',
            'https://www.brvm.org/fr',
            'https://www.brvm.org',
        ]
        
        for tentative in range(3):  # 3 tentatives complètes
            if len(actions_trouvees) >= 40:
                break
            
            print(f"\n  🔄 Tentative #{tentative + 1}/3")
            
            for url in urls:
                if len(actions_trouvees) >= 45:
                    break
                
                try:
                    print(f"\n  📡 {url}")
                    driver.get(url)
                    
                    # Attente chargement
                    WebDriverWait(driver, 25).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(10)  # Attente JavaScript
                    
                    # Scroll multiple
                    for i in range(5):
                        driver.execute_script(f"window.scrollTo(0, {i * 500});")
                        time.sleep(0.5)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # Sauvegarder HTML
                    html = driver.page_source
                    filename = f"debug_selenium_{url.split('/')[-1] or 'home'}_{tentative}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"    💾 {filename}")
                    
                    # Parser avec BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Méthode 1: Tables
                    tables = soup.find_all('table')
                    print(f"    📊 {len(tables)} table(s)")
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                texts = [c.get_text(strip=True) for c in cells]
                                
                                for symbol in ACTIONS_BRVM:
                                    if symbol not in actions_trouvees:
                                        for i, t in enumerate(texts[:5]):
                                            if symbol in t:
                                                # Extraction enrichie
                                                data = extraire_donnees_enrichies(texts, symbol)
                                                
                                                if data['close']:
                                                    metriques = calculer_metriques_liquidite(data)
                                                    data.update(metriques)
                                                    
                                                    data['source'] = url
                                                    data['method'] = 'selenium_table'
                                                    
                                                    actions_trouvees[symbol] = data
                                                    
                                                    print(f"      ✓ {symbol}: {data['close']:,.0f} FCFA", end="")
                                                    if data.get('variation_pct'):
                                                        print(f" ({data['variation_pct']:+.2f}%)", end="")
                                                    if data.get('volume'):
                                                        print(f" Vol:{data['volume']:,}", end="")
                                                    if data.get('liquidity_score'):
                                                        print(f" [{data['liquidity_score']}]", end="")
                                                    print()
                                                break
                    
                    # Méthode 2: Tout le texte
                    text = soup.get_text()
                    for symbol in ACTIONS_BRVM:
                        if symbol not in actions_trouvees and symbol in text:
                            idx = text.find(symbol)
                            fragment = text[idx:idx+300]
                            nombres = re.findall(r'\b(\d{2,6}[.,]?\d*)\b', fragment)
                            
                            for nb in nombres:
                                prix = extraire_nombre(nb)
                                if prix and 50 < prix < 100000:
                                    actions_trouvees[symbol] = {
                                        'symbol': symbol,
                                        'close': prix,
                                        'source': url,
                                        'method': 'selenium_text'
                                    }
                                    print(f"      ✓ {symbol}: {prix:,.0f} FCFA (texte)")
                                    break
                    
                    print(f"    📊 Progression: {len(actions_trouvees)}/47")
                    
                except TimeoutException:
                    print(f"    ⏱️ Timeout")
                except Exception as e:
                    print(f"    ❌ {str(e)[:80]}")
                
                time.sleep(3)  # Pause entre URLs
        
        driver.quit()
        
    except Exception as e:
        print(f"  ❌ Erreur Selenium: {str(e)[:100]}")
    
    return actions_trouvees


def sauvegarder_mongodb(actions_data):
    """
    Sauvegarder dans MongoDB avec data_quality='REAL_SCRAPER'
    """
    if not actions_data:
        print("\n⚠️ Aucune donnée à sauvegarder")
        return 0
    
    try:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017')
        client = pymongo.MongoClient(mongodb_uri)
        db = client['centralisation_db']
        collection = db['curated_observations']
        
        today = datetime.now().strftime('%Y-%m-%d')
        saved_count = 0
        
        for symbol, data in actions_data.items():
            # Construire attrs avec TOUTES les métriques collectées
            attrs = {
                'data_quality': 'REAL_SCRAPER',
                'scraper_method': data.get('method', 'unknown'),
                'scraper_url': data.get('source', ''),
                'collected_at': datetime.now().isoformat(),
                
                # Prix OHLC
                'open': data.get('open'),
                'high': data.get('high'),
                'low': data.get('low'),
                'close': data.get('close'),
                'previous': data.get('previous'),
                
                # Variations
                'variation_pct': data.get('variation_pct'),
                'variation_abs': data.get('variation_abs'),
                
                # Volume et liquidité
                'volume': data.get('volume'),
                'value_traded': data.get('value_traded'),
                'value_traded_millions': data.get('value_traded_millions'),
                'liquidity_score': data.get('liquidity_score'),
                'trades_count': data.get('trades_count'),
                
                # Volatilité
                'volatility_daily': data.get('volatility_daily'),
                'volatility_category': data.get('volatility_category'),
                'daily_range': data.get('daily_range'),
                'daily_range_pct': data.get('daily_range_pct'),
                
                # Valorisation
                'market_cap': data.get('market_cap'),
            }
            
            # Nettoyer None values
            attrs = {k: v for k, v in attrs.items() if v is not None}
            
            doc = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbol,
                'ts': today,
                'value': data['close'],
                'attrs': attrs
            }
            
            # Upsert
            collection.update_one(
                {'source': 'BRVM', 'key': symbol, 'ts': today},
                {'$set': doc},
                upsert=True
            )
            saved_count += 1
        
        print(f"\n✅ MongoDB: {saved_count} observations sauvegardées")
        return saved_count
        
    except Exception as e:
        print(f"\n❌ Erreur MongoDB: {e}")
        return 0


def main():
    """
    Pipeline complet ultra-robuste
    """
    print("=" * 80)
    print("🚀 SCRAPER BRVM ULTIMATE - MULTI-STRATÉGIES")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Objectif: Collecter les 47 actions BRVM")
    print("=" * 80)
    
    # STRATÉGIE 0: BeautifulSoup direct
    print("\n" + "=" * 80)
    print("📦 STRATÉGIE 0: BeautifulSoup + Requests")
    print("=" * 80)
    
    actions = scraper_beautifulsoup_direct()
    print(f"\n📊 Résultat: {len(actions)}/47 actions ({len(actions)/47*100:.1f}%)")
    
    # STRATÉGIE 1: Selenium headless
    if len(actions) < 40:
        print("\n" + "=" * 80)
        print("🤖 STRATÉGIE 1: Selenium Headless")
        print("=" * 80)
        
        actions = scraper_selenium(headless=True, actions_existantes=actions)
        print(f"\n📊 Résultat: {len(actions)}/47 actions ({len(actions)/47*100:.1f}%)")
    
    # STRATÉGIE 2: Selenium visible (dernier recours)
    if len(actions) < 40:
        print("\n" + "=" * 80)
        print("👁️ STRATÉGIE 2: Selenium VISIBLE (contournement anti-bot)")
        print("=" * 80)
        
        actions = scraper_selenium(headless=False, actions_existantes=actions)
        print(f"\n📊 Résultat: {len(actions)}/47 actions ({len(actions)/47*100:.1f}%)")
    
    # RAPPORT FINAL
    print("\n" + "=" * 80)
    print("📊 RAPPORT FINAL")
    print("=" * 80)
    print(f"✅ Actions collectées: {len(actions)}/47 ({len(actions)/47*100:.1f}%)")
    
    if len(actions) >= 40:
        print("\n🎉 SUCCÈS! Taux de réussite >= 85%")
    elif len(actions) >= 20:
        print("\n⚠️ SUCCÈS PARTIEL: Collecte incomplète mais utilisable")
    else:
        print("\n❌ ÉCHEC: Collecte insuffisante")
    
    # Actions manquantes
    manquantes = [s for s in ACTIONS_BRVM if s not in actions]
    if manquantes:
        print(f"\n📋 Actions manquantes ({len(manquantes)}): {', '.join(manquantes)}")
    
    # Sauvegarde MongoDB
    if len(actions) > 0:
        print("\n" + "=" * 80)
        print("💾 SAUVEGARDE MONGODB")
        print("=" * 80)
        saved = sauvegarder_mongodb(actions)
        
        if saved > 0:
            print(f"\n✅ {saved} observations enregistrées avec data_quality='REAL_SCRAPER'")
    else:
        print("\n⚠️ Aucune donnée à sauvegarder")
    
    # Solutions alternatives
    if len(actions) < 40:
        print("\n" + "=" * 80)
        print("🔧 SOLUTIONS ALTERNATIVES")
        print("=" * 80)
        print("1. Saisie manuelle:")
        print("   python mettre_a_jour_cours_brvm.py")
        print("\n2. Import CSV:")
        print("   python collecter_csv_automatique.py")
        print("\n3. Télécharger bulletins PDF BRVM:")
        print("   python parser_bulletins_brvm_pdf.py")
    
    return len(actions)


if __name__ == '__main__':
    try:
        nb_actions = main()
        exit(0 if nb_actions >= 40 else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrompu par l'utilisateur")
        exit(130)
    except Exception as e:
        print(f"\n\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
