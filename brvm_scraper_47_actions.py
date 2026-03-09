"""
SCRAPER BRVM SELENIUM - TOUTES LES 47 ACTIONS
Collecte complète des cours de toutes les actions cotées à la BRVM
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import re
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()

# Liste des 47 actions BRVM (symboles officiels)
ACTIONS_BRVM = [
    'BICC', 'BOAB', 'BOABF', 'BNBC', 'ETIT', 'NTLC', 'ONTBF', 'PALM', 'PRSC',
    'SDCC', 'SDSC', 'SHEC', 'SIBC', 'SITC', 'SLBC', 'SMBC', 'SNTS', 'SOGB',
    'STBC', 'STAC', 'TTLC', 'TTLS', 'UNXC', 'CIEC', 'CFAC', 'FTSC', 'NEIC',
    'NSBC', 'ORGT', 'SAFC', 'SCRC', 'SGBC', 'SIVC', 'SPHC', 'TOAC', 'BOAC',
    'CABC', 'ECOC', 'SETC', 'SICC', 'SOGC', 'ABJC', 'BOAM', 'CBIBF', 'SVOC',
    'PALC', 'SEMC'
]

def setup_driver():
    """Configuration Chrome ULTRA-ROBUSTE avec anti-détection maximale"""
    options = Options()
    
    # Mode headless optimisé
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # Anti-détection
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent réaliste
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Fenêtre et langue
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=fr-FR')
    options.add_argument('--accept-lang=fr-FR,fr;q=0.9')
    
    # Performance
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-images')  # Charger plus rapide
    options.add_argument('--blink-settings=imagesEnabled=false')
    
    # Préférences
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # Désactiver images pour vitesse
        }
    }
    options.add_experimental_option('prefs', prefs)
    
    driver = webdriver.Chrome(options=options)
    
    # Anti-détection JavaScript
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR', 'fr']});
        '''
    })
    
    # Timeouts généreux
    driver.set_page_load_timeout(90)  # 90s au lieu de 60s
    driver.implicitly_wait(15)  # 15s au lieu de 10s
    
    # User agents variés
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    
    return driver

def extraire_nombre(texte):
    """Extraire nombre depuis texte"""
    if not texte:
        return None
    texte = str(texte).replace('FCFA', '').replace(' ', '').replace(',', '.').strip()
    texte = re.sub(r'[^\d.]', '', texte)
    try:
        return float(texte) if texte else None
    except:
        return None

def extraire_pourcentage(texte):
    """Extraire pourcentage"""
    if not texte:
        return None
    match = re.search(r'([+-]?\d+[,.]?\d*)', str(texte).replace('%', ''))
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

def scraper_toutes_actions():
    """
    Scraper ULTRA-ROBUSTE pour TOUTES les 47 actions
    
    Stratégies multiples avec retry automatique
    """
    
    print("=" * 80)
    print("🚀 SCRAPER BRVM ULTRA-ROBUSTE V2 - 47 ACTIONS")
    print("=" * 80)
    
    actions_trouvees = {}
    tentatives_par_url = 3  # 3 retry au lieu de 2
    
    # STRATÉGIE 0: BeautifulSoup direct (sans Selenium) - PLUS RAPIDE
    print("\n" + "="*80)
    print("🌐 STRATÉGIE 0: REQUÊTES HTTP DIRECTES (BeautifulSoup)")
    print("="*80)
    
    actions_trouvees = scraper_beautifulsoup_direct()
    
    if len(actions_trouvees) >= 40:
        print(f"\n✅ SUCCÈS avec BeautifulSoup: {len(actions_trouvees)}/47")
        return actions_trouvees
    
    print(f"\n⚠️ BeautifulSoup insuffisant: {len(actions_trouvees)}/47")
    print("\n" + "="*80)
    print("🤖 STRATÉGIE 1: SELENIUM MODE HEADLESS")
    print("="*80)
    
    driver = setup_driver(headless=True)
    
    try:
        # URLs à tester (plus de variantes)
        urls_a_tester = [
            ('https://www.brvm.org/fr/cours-actions', 'Cours Actions'),
            ('https://www.brvm.org/fr/marche/titres-et-cotations', 'Titres et Cotations'),
            ('https://www.brvm.org/fr/investir/cours-et-cotations', 'Investir Cours'),
            ('https://www.brvm.org/fr/cotations', 'Cotations'),
            ('https://www.brvm.org/fr/marche', 'Marché'),
            ('https://www.brvm.org/fr/cours', 'Cours'),
            ('https://www.brvm.org/fr/investir', 'Investir'),
            ('https://www.brvm.org/fr/marche-boursier', 'Marché Boursier'),
            ('https://www.brvm.org/en/market-data', 'Market Data EN'),
            ('https://www.brvm.org/fr', 'Page FR'),
            ('https://www.brvm.org', 'Accueil'),
        ]
        
        for tentative_globale in range(tentatives_par_url):
            if len(actions_trouvees) >= 40:  # 85% des actions = succès
                break
                
            print(f"\n{'='*80}")
            print(f"🔄 TENTATIVE GLOBALE #{tentative_globale + 1}")
            print(f"{'='*80}")
            
            for url, nom in urls_a_tester:
                if len(actions_trouvees) >= 45:  # Presque toutes trouvées
                    break
                    
                print(f"\n📡 {nom} → {url}")
                
                try:
                    # Chargement avec timeout
                    driver.get(url)
                    
                    # Attente intelligente : attendre que le body soit chargé
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Attente supplémentaire pour JavaScript (plus longue)
                    time.sleep(8)
                    
                    # Scroll multiple pour déclencher lazy loading
                    for _ in range(3):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1.5)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                    
                    # Sauvegarder HTML pour debug
                    html_content = driver.page_source
                    with open(f'debug_brvm_{nom.replace(" ", "_")}.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print(f"  💾 HTML sauvegardé: debug_brvm_{nom.replace(' ', '_')}.html")
                    
                    print(f"  ✅ Page chargée: {driver.title[:50]}")
                    
                    # MÉTHODE 1: Tables HTML classiques
                    print(f"  🔍 Méthode 1: Extraction des tables...")
                    tables = driver.find_elements(By.TAG_NAME, 'table')
                    print(f"     {len(tables)} table(s) trouvée(s)")
                    
                    for idx, table in enumerate(tables):
                        try:
                            table_html = table.get_attribute('outerHTML')
                            table_text = table.text
                            
                            # Compter actions présentes
                            actions_presentes = [a for a in ACTIONS_BRVM if a in table_text]
                            
                            if len(actions_presentes) >= 3:  # Au moins 3 actions
                                print(f"     📊 Table {idx}: {len(actions_presentes)} actions détectées")
                                
                                # Extraire lignes
                                rows = table.find_elements(By.TAG_NAME, 'tr')
                                
                                for row_idx, row in enumerate(rows):
                                    try:
                                        # Essayer td puis th
                                        cells = row.find_elements(By.TAG_NAME, 'td')
                                        if not cells:
                                            cells = row.find_elements(By.TAG_NAME, 'th')
                                        
                                        if len(cells) >= 2:
                                            cell_texts = [c.text.strip() for c in cells]
                                            
                                            # Identifier le symbole
                                            symbol = None
                                            for cell_text in cell_texts[:3]:  # Chercher dans les 3 premières colonnes
                                                if cell_text in ACTIONS_BRVM:
                                                    symbol = cell_text
                                                    break
                                            
                                            if symbol and symbol not in actions_trouvees:
                                                # Extraire prix (colonne 1 ou 2)
                                                prix = None
                                                for i in [1, 2, 3]:
                                                    if i < len(cell_texts):
                                                        prix = extraire_nombre(cell_texts[i])
                                                        if prix and prix > 10:  # Prix réaliste
                                                            break
                                                
                                                if prix:
                                                    variation = extraire_pourcentage(cell_texts[2]) if len(cell_texts) > 2 else None
                                                    volume = extraire_nombre(cell_texts[3]) if len(cell_texts) > 3 else None
                                                    
                                                    actions_trouvees[symbol] = {
                                                        'symbol': symbol,
                                                        'close': prix,
                                                        'variation': variation,
                                                        'volume': volume,
                                                        'source': url,
                                                        'method': 'table_html',
                                                        'table_index': idx
                                                    }
                                                    print(f"        ✓ {symbol}: {prix:,.0f} FCFA")
                                    except Exception as e:
                                        continue
                        except Exception as e:
                            continue
                    
                    # MÉTHODE 2: Extraction JavaScript avancée
                    if len(actions_trouvees) < 20:
                        print(f"  ⚡ Méthode 2: Extraction JavaScript avancée...")
                        
                        script_extract = """
                        var symbols = %s;
                        var results = [];
                        
                        // Stratégie 1: Chercher dans tous les éléments
                        var allElements = document.querySelectorAll('*');
                        
                        allElements.forEach(function(elem) {
                            var text = elem.textContent;
                            if (!text) return;
                            
                            symbols.forEach(function(symbol) {
                                if (text.includes(symbol) && text.length < 500) {
                                    // Chercher prix après symbole
                                    var lines = text.split('\\n');
                                    lines.forEach(function(line) {
                                        if (line.includes(symbol)) {
                                            // Pattern: SYMBOL ... PRIX
                                            var matches = line.match(/([\\d\\s,]+)(?=\\s*FCFA|\\s*$)/g);
                                            if (matches && matches.length > 0) {
                                                results.push({
                                                    symbol: symbol,
                                                    line: line.trim(),
                                                    matches: matches
                                                });
                                            }
                                        }
                                    });
                                }
                            });
                        });
                        
                        return results;
                        """ % str(ACTIONS_BRVM).replace("'", '"')
                        
                        try:
                            js_results = driver.execute_script(script_extract)
                            
                            for item in js_results:
                                symbol = item['symbol']
                                if symbol not in actions_trouvees and item.get('matches'):
                                    # Prendre le premier nombre significatif
                                    for match in item['matches']:
                                        prix = extraire_nombre(match)
                                        if prix and prix > 100:  # Prix BRVM typique
                                            actions_trouvees[symbol] = {
                                                'symbol': symbol,
                                                'close': prix,
                                                'source': url,
                                                'method': 'javascript'
                                            }
                                            print(f"        ✓ {symbol}: {prix:,.0f} FCFA (JS)")
                                            break
                        except Exception as e:
                            print(f"     ❌ Erreur JS: {e}")
                    
                    # MÉTHODE 3: XPath pour sélecteurs spécifiques
                    if len(actions_trouvees) < 15:
                        print(f"  🎯 Méthode 3: XPath sélecteurs spécifiques...")
                        
                        xpath_selectors = [
                            "//div[contains(@class, 'stock')]",
                            "//div[contains(@class, 'quote')]",
                            "//div[contains(@class, 'cours')]",
                            "//span[contains(@class, 'ticker')]",
                            "//tr[contains(@class, 'stock-row')]",
                        ]
                        
                        for xpath in xpath_selectors:
                            try:
                                elements = driver.find_elements(By.XPATH, xpath)
                                for elem in elements[:50]:  # Limiter pour performance
                                    text = elem.text
                                    for symbol in ACTIONS_BRVM:
                                        if symbol in text and symbol not in actions_trouvees:
                                            prix = extraire_nombre(text.split(symbol)[-1][:30])
                                            if prix and prix > 100:
                                                actions_trouvees[symbol] = {
                                                    'symbol': symbol,
                                                    'close': prix,
                                                    'source': url,
                                                    'method': 'xpath'
                                                }
                                                print(f"        ✓ {symbol}: {prix:,.0f} FCFA (XPath)")
                            except:
                                continue
                    
                    # Afficher progression
                    print(f"\n  📊 Progression: {len(actions_trouvees)}/47 actions collectées")
                    
                except TimeoutException:
                    print(f"  ⏱️  Timeout sur {nom}")
                except Exception as e:
                    print(f"  ❌ Erreur {nom}: {str(e)[:100]}")
                
                # Pause courte entre URLs
                time.sleep(2)
        
        # RAPPORT FINAL
        print("\n" + "=" * 80)
        print(f"📊 COLLECTE TERMINÉE: {len(actions_trouvees)}/47 actions ({(len(actions_trouvees)/47*100):.1f}%)")
        print("=" * 80)
        
        if actions_trouvees:
            print(f"\n✅ Actions collectées:")
            for symbol in sorted(actions_trouvees.keys()):
                data = actions_trouvees[symbol]
                variation_str = f"{data.get('variation', 0):+.2f}%" if data.get('variation') else "N/A"
                volume_str = f"{int(data.get('volume', 0)):,}" if data.get('volume') else "N/A"
                print(f"  {symbol:6} | {data['close']:>10,.0f} FCFA | Var: {variation_str:>8} | Vol: {volume_str:>12}")
        
        # Actions manquantes
        actions_manquantes = set(ACTIONS_BRVM) - set(actions_trouvees.keys())
        if actions_manquantes:
            print(f"\n⚠️  {len(actions_manquantes)} actions NON trouvées:")
            print(f"  {', '.join(sorted(actions_manquantes))}")
        
        # Sauvegarder dans MongoDB
        if actions_trouvees:
            sauvegarder_mongodb(actions_trouvees)
        
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
    
    return actions_trouvees

def sauvegarder_mongodb(actions_dict):
    """Sauvegarder dans MongoDB"""
    
    try:
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/centralisation_db')
        client = MongoClient(mongo_uri)
        db = client.centralisation_db
        
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d')
        count_saved = 0
        
        for symbol, data in actions_dict.items():
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbol,
                'ts': date_aujourdhui,
                'value': data['close'],
                'attrs': {
                    'data_quality': 'REAL_SCRAPER',
                    'scraping_method': 'selenium',
                    'scraping_timestamp': datetime.now().isoformat(),
                    'variation': data.get('variation'),
                    'volume': data.get('volume'),
                    'source_url': data.get('source'),
                    'extraction_method': data.get('table_index', 'javascript')
                }
            }
            
            db.curated_observations.update_one(
                {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': symbol,
                    'ts': date_aujourdhui
                },
                {'$set': obs},
                upsert=True
            )
            count_saved += 1
        
        print(f"\n💾 {count_saved} actions sauvegardées dans MongoDB")
        print(f"   Collection: curated_observations")
        print(f"   Date: {date_aujourdhui}")
        print(f"   Qualité: REAL_SCRAPER")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")

if __name__ == "__main__":
    print(f"\n🎯 Objectif: Collecter les 47 actions de la BRVM")
    print(f"📋 Actions cibles: {', '.join(ACTIONS_BRVM[:10])}... (+ {len(ACTIONS_BRVM)-10} autres)\n")
    
    resultats = scraper_toutes_actions()
    
    taux_reussite = (len(resultats) / len(ACTIONS_BRVM)) * 100 if resultats else 0
    
    print(f"\n📈 TAUX DE RÉUSSITE: {taux_reussite:.1f}% ({len(resultats)}/47)")
    
    if taux_reussite < 50:
        print(f"\n⚠️  COLLECTE INSUFFISANTE")
        print(f"💡 SOLUTIONS:")
        print(f"  1. Réessayer: python brvm_scraper_47_actions.py")
        print(f"  2. Saisie manuelle: python mettre_a_jour_cours_brvm.py")
        print(f"  3. Import CSV: python collecter_csv_automatique.py")
