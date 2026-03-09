"""
SCRAPER BRVM SELENIUM - PRODUCTION FINALE
Scraping avec navigation intelligente + extraction complète des données
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()

def setup_driver():
    """Configuration Chrome avec options anti-détection"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    # Anti-détection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extraire_nombre(texte):
    """Extraire un nombre depuis un texte (ex: '15 500 FCFA' → 15500)"""
    if not texte:
        return None
    # Retirer FCFA, espaces, puis convertir
    texte = texte.replace('FCFA', '').replace(' ', '').replace(',', '.').strip()
    try:
        return float(texte)
    except:
        return None

def extraire_pourcentage(texte):
    """Extraire pourcentage (ex: '+2,5%' → 2.5)"""
    if not texte:
        return None
    match = re.search(r'([+-]?\d+[,.]?\d*)', texte.replace('%', ''))
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

def scraper_brvm_selenium():
    """
    Scraper principal avec Selenium
    
    Stratégie:
    1. Charger page d'accueil BRVM
    2. Naviguer vers section cours/cotations
    3. Extraire toutes les tables de données
    4. Parser les informations des actions
    5. Sauvegarder dans MongoDB
    """
    
    print("=" * 80)
    print("🚀 SCRAPER BRVM SELENIUM - DÉMARRAGE")
    print("=" * 80)
    
    driver = setup_driver()
    resultats = []
    
    try:
        # ÉTAPE 1: Page d'accueil
        print("\n📡 Étape 1: Chargement page d'accueil...")
        driver.get('https://www.brvm.org')
        time.sleep(3)
        print(f"✅ Page chargée: {driver.title}")
        
        # ÉTAPE 2: Rechercher les cours via JavaScript
        print("\n🔍 Étape 2: Extraction données via JavaScript...")
        
        # Script pour extraire toutes les tables
        script_tables = """
        var tables = document.querySelectorAll('table');
        var data = [];
        tables.forEach(function(table, idx) {
            var tableData = {
                index: idx,
                className: table.className,
                rows: []
            };
            var rows = table.querySelectorAll('tr');
            rows.forEach(function(row) {
                var cells = [];
                row.querySelectorAll('td, th').forEach(function(cell) {
                    cells.push(cell.textContent.trim());
                });
                if (cells.length > 0) {
                    tableData.rows.push(cells);
                }
            });
            if (tableData.rows.length > 0) {
                data.push(tableData);
            }
        });
        return data;
        """
        
        tables_data = driver.execute_script(script_tables)
        print(f"📊 {len(tables_data)} table(s) trouvée(s)")
        
        # ÉTAPE 3: Parser les données
        print("\n⚙️  Étape 3: Parsing des données...")
        
        for table in tables_data:
            print(f"\n  Table {table['index']} ({table['className']}):")
            for row in table['rows'][:5]:  # Afficher 5 premières lignes
                print(f"    {' | '.join(row[:4])}")
        
        # ÉTAPE 4: Naviguer vers page cours si disponible
        print("\n🌐 Étape 4: Navigation vers page cours...")
        
        urls_a_tester = [
            'https://www.brvm.org/fr/marche',
            'https://www.brvm.org/fr/cours',
            'https://www.brvm.org/fr/investir',
        ]
        
        for url in urls_a_tester:
            try:
                print(f"\n  Test: {url}")
                driver.get(url)
                time.sleep(3)
                
                # Chercher des tables avec données financières
                tables = driver.find_elements(By.TAG_NAME, 'table')
                
                for table in tables:
                    try:
                        # Vérifier si la table contient des symboles boursiers
                        text = table.text
                        if any(symbol in text for symbol in ['SNTS', 'BOAB', 'BICC', 'SOGB', 'TTLS']):
                            print(f"    ✅ Table avec cours trouvée!")
                            
                            # Extraire les lignes
                            rows = table.find_elements(By.TAG_NAME, 'tr')
                            for row in rows:
                                cells = row.find_elements(By.TAG_NAME, 'td')
                                if len(cells) >= 3:
                                    data_row = [cell.text.strip() for cell in cells]
                                    print(f"      - {' | '.join(data_row[:5])}")
                                    
                                    # Parser si format reconnu
                                    if len(data_row) >= 4:
                                        symbol = data_row[0]
                                        if len(symbol) == 4:  # Format ticker BRVM (ex: SNTS, BOAB)
                                            cours = {
                                                'symbol': symbol,
                                                'close': extraire_nombre(data_row[1]) if len(data_row) > 1 else None,
                                                'variation': extraire_pourcentage(data_row[2]) if len(data_row) > 2 else None,
                                                'volume': extraire_nombre(data_row[3]) if len(data_row) > 3 else None,
                                                'source': url,
                                                'timestamp': datetime.now().isoformat()
                                            }
                                            resultats.append(cours)
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"    ❌ Erreur: {e}")
                continue
        
        # ÉTAPE 5: Extraction indices BRVM (toujours disponibles)
        print("\n📈 Étape 5: Extraction indices BRVM...")
        
        driver.get('https://www.brvm.org')
        time.sleep(2)
        
        # Chercher les indices dans le texte de la page
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # Patterns pour BRVM-C, BRVM-30, BRVM-PRES
        indices = ['BRVM-C', 'BRVM-30', 'BRVM-PRES', 'BRVM Composite', 'BRVM 10']
        
        for indice in indices:
            pattern = rf'{indice}[:\s]*(\d+[,.]?\d*)'
            match = re.search(pattern, page_text)
            if match:
                valeur = float(match.group(1).replace(',', '.'))
                print(f"  ✅ {indice}: {valeur}")
                resultats.append({
                    'symbol': indice.replace(' ', '_').replace('-', '_'),
                    'close': valeur,
                    'type': 'INDEX',
                    'timestamp': datetime.now().isoformat()
                })
        
        # ÉTAPE 6: Sauvegarder dans MongoDB
        if resultats:
            print(f"\n💾 Étape 6: Sauvegarde de {len(resultats)} enregistrement(s)...")
            sauvegarder_mongodb(resultats)
        else:
            print("\n❌ Aucune donnée extraite")
        
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n" + "=" * 80)
        print(f"✅ SCRAPING TERMINÉ - {len(resultats)} cours collectés")
        print("=" * 80)
    
    return resultats

def sauvegarder_mongodb(resultats):
    """Sauvegarder les cours dans MongoDB avec data_quality=REAL_SCRAPER"""
    
    try:
        # Connexion MongoDB
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/centralisation_db')
        client = MongoClient(mongo_uri)
        db = client.centralisation_db
        
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d')
        observations = []
        
        for cours in resultats:
            if cours.get('close'):  # Seulement si on a un prix
                obs = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_INDEX' if cours.get('type') == 'INDEX' else 'STOCK_PRICE',
                    'key': cours['symbol'],
                    'ts': date_aujourdhui,
                    'value': cours['close'],
                    'attrs': {
                        'data_quality': 'REAL_SCRAPER',  # ⚠️ CRITIQUE
                        'scraping_method': 'selenium',
                        'scraping_timestamp': cours['timestamp'],
                        'variation': cours.get('variation'),
                        'volume': cours.get('volume'),
                        'source_url': cours.get('source', 'https://www.brvm.org')
                    }
                }
                observations.append(obs)
        
        if observations:
            # Upsert (update si existe, insert sinon)
            for obs in observations:
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
            
            print(f"✅ {len(observations)} observation(s) sauvegardée(s) dans MongoDB")
            
            # Afficher un exemple
            if observations:
                print(f"\nExemple sauvegardé:")
                print(f"  Symbol: {observations[0]['key']}")
                print(f"  Prix: {observations[0]['value']} FCFA")
                print(f"  Qualité: {observations[0]['attrs']['data_quality']}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde MongoDB: {e}")

if __name__ == "__main__":
    resultats = scraper_brvm_selenium()
    
    if resultats:
        print("\n📋 RÉSUMÉ DES DONNÉES COLLECTÉES:")
        for r in resultats[:10]:  # Top 10
            print(f"  - {r.get('symbol', 'N/A'):10} | Prix: {r.get('close', 0):10.2f} | Var: {r.get('variation', 0):+6.2f}%")
    else:
        print("\n⚠️  AUCUNE DONNÉE COLLECTÉE")
        print("\n💡 SOLUTION DE REPLI:")
        print("  python mettre_a_jour_cours_brvm.py  # Saisie manuelle guidée")
