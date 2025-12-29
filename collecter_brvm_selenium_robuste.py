"""
COLLECTE BRVM RÉELLE AVEC SELENIUM - 23 DÉCEMBRE 2025
🔴 DONNÉES RÉELLES UNIQUEMENT - Scraping site officiel BRVM
Source: https://www.brvm.org/fr/investir/cours-et-cotations
"""
import sys
import os
from datetime import datetime
import time

print("\n" + "="*80)
print("COLLECTE BRVM RÉELLE - 23 DÉCEMBRE 2025")
print("="*80)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    
    print("\n✅ Selenium importé")
    
except ImportError as e:
    print(f"\n❌ Selenium non installé: {e}")
    print("\n📋 Installation requise:")
    print("   pip install selenium webdriver-manager")
    sys.exit(1)

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath('.'))

def scraper_brvm_selenium_robuste():
    """
    Scraper BRVM avec Selenium - Gestion robuste des erreurs
    Retourne les VRAIS cours du site officiel BRVM
    """
    
    print("\n🌐 Tentative de connexion au site BRVM...")
    print("   URL: https://www.brvm.org/fr/investir/cours-et-cotations")
    
    # Configuration Chrome en mode headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    data = []
    
    try:
        # Initialiser Chrome avec ChromeDriver automatique
        print("\n🚀 Installation/Lancement ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        print("✅ Chrome lancé avec succès")
        
        # Accéder à la page des cotations
        url = "https://www.brvm.org/fr/investir/cours-et-cotations"
        print(f"\n📡 Chargement de la page...")
        driver.get(url)
        
        # Attendre que la page charge
        print("⏳ Attente du chargement JavaScript (10 secondes)...")
        time.sleep(10)
        
        # Sauvegarder HTML pour analyse
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_file = f'brvm_selenium_{timestamp}.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"📄 HTML sauvegardé: {debug_file}")
        
        # Chercher les tableaux
        print("\n🔍 Recherche des données de cotation...")
        
        # Essayer plusieurs sélecteurs CSS
        selectors_to_try = [
            ("table.cotations tbody tr", "Table cotations"),
            ("table.stock-list tbody tr", "Table stock-list"),
            (".view-content table tbody tr", "View content table"),
            ("table tbody tr", "Tous les tableaux"),
        ]
        
        rows_found = []
        for selector, description in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✅ {description}: {len(elements)} lignes trouvées")
                    rows_found = elements
                    break
            except Exception as e:
                print(f"   ⏭️  {description}: non trouvé")
                continue
        
        if not rows_found:
            print("\n⚠️  Aucune ligne de tableau trouvée avec les sélecteurs standards")
            print("📋 Analyse du HTML sauvegardé requise")
            return None
        
        # Parser les lignes
        print(f"\n📊 Analyse de {len(rows_found)} lignes...")
        
        for row in rows_found:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    # Format attendu: Symbole | Cours | Variation (%)
                    symbol_text = cells[0].text.strip()
                    price_text = cells[1].text.strip().replace(' ', '').replace(',', '')
                    var_text = cells[2].text.strip().replace('%', '').replace(',', '.')
                    
                    if symbol_text and price_text:
                        try:
                            price = float(price_text)
                            variation = float(var_text) if var_text else 0.0
                            
                            # Normaliser le symbole
                            if '.' not in symbol_text:
                                symbol_text += '.BC'
                            
                            data.append({
                                'symbol': symbol_text,
                                'close': price,
                                'variation': variation,
                                'volume': 0,  # Volume pas toujours disponible
                                'data_quality': 'REAL_SCRAPER',
                                'source': 'BRVM_SELENIUM',
                                'collecte_datetime': datetime.now().isoformat()
                            })
                            
                        except ValueError:
                            continue
            except Exception as e:
                continue
        
        if data:
            print(f"\n{'='*80}")
            print(f"✅ {len(data)} COURS RÉELS COLLECTÉS")
            print(f"{'='*80}")
            
            # Afficher échantillon
            print(f"\n{'SYMBOLE':<12} {'PRIX':>12} {'VARIATION':>12}")
            print(f"{'-'*12} {'-'*12} {'-'*12}")
            
            for stock in sorted(data, key=lambda x: x['symbol'])[:10]:
                print(f"{stock['symbol']:<12} {stock['close']:>12,.0f} {stock['variation']:>+11.2f}%")
            
            if len(data) > 10:
                print(f"\n... et {len(data) - 10} autres actions")
        
        return data
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du scraping: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        if driver:
            driver.quit()
            print("\n🔒 Chrome fermé")


def sauvegarder_en_mongodb(data):
    """Sauvegarder les cours RÉELS dans MongoDB"""
    
    if not data or len(data) == 0:
        print("\n⚠️  Aucune donnée à sauvegarder")
        return 0
    
    print("\n" + "="*80)
    print("SAUVEGARDE DANS MONGODB")
    print("="*80)
    
    try:
        import django
        os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
        django.setup()
        
        from plateforme_centralisation.mongo import get_mongo_db
        
        client, db = get_mongo_db()
        
        # Date du jour
        today = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n📅 Date: {today}")
        print(f"📊 Nombre de cours à sauvegarder: {len(data)}")
        
        # Préparer les observations
        observations = []
        for stock in data:
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': stock['symbol'],
                'ts': today,
                'value': stock['close'],
                'attrs': {
                    'close': stock['close'],
                    'variation': stock['variation'],
                    'volume': stock.get('volume', 0),
                    'data_quality': 'REAL_SCRAPER',
                    'collecte_method': 'SELENIUM_SCRAPING',
                    'collecte_datetime': datetime.now().isoformat()
                }
            }
            observations.append(obs)
        
        # Upsert dans MongoDB
        inserted = 0
        updated = 0
        
        for obs in observations:
            result = db.curated_observations.update_one(
                {
                    'source': obs['source'],
                    'dataset': obs['dataset'],
                    'key': obs['key'],
                    'ts': obs['ts']
                },
                {'$set': obs},
                upsert=True
            )
            
            if result.upserted_id:
                inserted += 1
            elif result.modified_count > 0:
                updated += 1
        
        print(f"\n✅ Sauvegarde terminée:")
        print(f"   • {inserted} nouvelles observations")
        print(f"   • {updated} observations mises à jour")
        print(f"   • Total: {len(observations)} cours RÉELS du {today}")
        
        # Vérifier le total en base
        total = db.curated_observations.count_documents({
            'source': 'BRVM',
            'ts': today
        })
        
        print(f"\n📈 Total observations BRVM du {today}: {total}")
        
        client.close()
        return len(observations)
        
    except Exception as e:
        print(f"\n❌ ERREUR sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    
    print("\n🎯 OBJECTIF: Collecter les VRAIS cours BRVM du 23/12/2025")
    print("   Politique: ZÉRO TOLÉRANCE pour données simulées")
    print("   Source: Site officiel BRVM uniquement")
    
    # Étape 1: Scraper
    data = scraper_brvm_selenium_robuste()
    
    if data and len(data) > 0:
        
        # Étape 2: Demander confirmation
        print(f"\n{'='*80}")
        print(f"💾 SAUVEGARDER CES {len(data)} COURS RÉELS?")
        print(f"{'='*80}")
        
        reponse = input("\n   Confirmer (o/N): ").strip().lower()
        
        if reponse in ['o', 'oui', 'y', 'yes']:
            count = sauvegarder_en_mongodb(data)
            
            if count > 0:
                print(f"\n{'='*80}")
                print(f"✅ SUCCÈS - {count} cours RÉELS du 23/12/2025 en base")
                print(f"{'='*80}")
                print(f"\n🎯 PROCHAINE ÉTAPE:")
                print(f"   python generer_top5_nlp.py")
        else:
            print("\n⏭️  Sauvegarde annulée")
    
    else:
        print(f"\n{'='*80}")
        print(f"❌ ÉCHEC DU SCRAPING SELENIUM")
        print(f"{'='*80}")
        print(f"\n📋 SOLUTIONS:")
        print(f"\n   1. Analyser le HTML sauvegardé (brvm_selenium_*.html)")
        print(f"      pour comprendre la structure réelle du site")
        print(f"\n   2. Saisie manuelle GUIDÉE:")
        print(f"      • Aller sur: https://www.brvm.org/fr/investir/cours-et-cotations")
        print(f"      • Copier les cours affichés")
        print(f"      • Les saisir dans un script")
        print(f"\n   3. Importer un CSV téléchargé du site BRVM")
    
    print(f"\n{'='*80}\n")
