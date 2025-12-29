"""
SCRAPER PRODUCTION BRVM - DONNÉES RÉELLES UNIQUEMENT
🔴 POLITIQUE ZÉRO TOLÉRANCE : Scraping site officiel BRVM
Source: https://www.brvm.org/fr/investir/cours-et-cotations
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

def scraper_brvm_officiel():
    """
    Scraper le site officiel BRVM pour obtenir les cours en temps réel
    
    Returns:
        list: Liste de dict avec {symbol, close, volume, variation, open, high, low, ...}
        None: Si le scraping échoue
    """
    url = "https://www.brvm.org/fr/search/node/cours%20et%20cotation"
    
    print(f"\n🌐 Scraping BRVM officiel: {url}")
    
    try:
        # Headers pour simuler un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        # Requête HTTP avec timeout
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        
        print(f"✅ Réponse HTTP {response.status_code} - {len(response.content)} bytes")
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Sauvegarder le HTML pour debug
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_file = f'brvm_scrape_{timestamp}.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"📄 HTML sauvegardé: {debug_file}")
        
        # Chercher la table des cotations
        # Patterns possibles: table.cotations, table#stock-list, div.stock-quotes, etc.
        tables = soup.find_all('table')
        print(f"\n🔍 {len(tables)} table(s) trouvée(s) dans le HTML")
        
        data = []
        
        # Essayer de trouver et parser la bonne table
        for idx, table in enumerate(tables):
            print(f"\n   Analyse table {idx+1}...")
            
            # Extraire les headers
            headers = []
            header_row = table.find('thead')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
                print(f"      Headers: {headers}")
            
            # Extraire les lignes de données
            rows = table.find_all('tr')
            print(f"      {len(rows)} ligne(s) de données")
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:  # Minimum: symbol, price, variation
                    continue
                
                try:
                    # Extraction basique (à adapter selon la structure réelle)
                    text_cells = [cell.get_text(strip=True) for cell in cells]
                    
                    # Essayer de détecter la structure
                    # Format typique: SYMBOL | DERNIER | VARIATION | VOLUME | ...
                    if len(text_cells) >= 3:
                        symbol = text_cells[0]
                        
                        # Vérifier que c'est un vrai symbol BRVM (lettres + point)
                        if not re.match(r'^[A-Z]{3,6}\.[A-Z]{2}$', symbol):
                            continue
                        
                        # Parser le prix (format: "15 500" ou "15500" ou "15,500")
                        price_str = text_cells[1].replace(' ', '').replace(',', '')
                        price = float(price_str)
                        
                        # Parser la variation (format: "+2.3%" ou "-1.5")
                        variation_str = text_cells[2].replace('%', '').replace('+', '')
                        variation = float(variation_str) if variation_str else 0.0
                        
                        # Volume si disponible
                        volume = 0
                        if len(text_cells) >= 4:
                            try:
                                volume_str = text_cells[3].replace(' ', '').replace(',', '')
                                volume = int(volume_str)
                            except:
                                volume = 0
                        
                        data.append({
                            'symbol': symbol,
                            'close': price,
                            'variation': variation,
                            'volume': volume,
                            'data_quality': 'REAL_SCRAPER',
                            'scraped_at': datetime.now().isoformat(),
                        })
                        
                        print(f"      ✅ {symbol}: {price} FCFA ({variation:+.2f}%)")
                
                except Exception as e:
                    # Ignorer les lignes mal formées
                    continue
        
        if len(data) > 0:
            print(f"\n✅ SUCCÈS: {len(data)} cours scrapés")
            return data
        else:
            print(f"\n❌ ÉCHEC: Aucun cours trouvé dans le HTML")
            print(f"   Vérifier la structure HTML dans {debug_file}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERREUR HTTP: {e}")
        return None
    except Exception as e:
        print(f"\n❌ ERREUR SCRAPING: {e}")
        import traceback
        traceback.print_exc()
        return None

def scraper_brvm_avec_selenium():
    """
    Alternative avec Selenium si le site utilise JavaScript
    Nécessite: pip install selenium webdriver-manager
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("\n🚗 Scraping BRVM avec Selenium...")
        
        # Configuration Chrome headless
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get("https://www.brvm.org/fr/search/node/cours%20et%20cotation")
        
        # Attendre que la table se charge
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # Parser le HTML rendu
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        # Même logique d'extraction que scraper_brvm_officiel()
        # ... (code à compléter)
        
        return []
        
    except ImportError:
        print("❌ Selenium non installé: pip install selenium webdriver-manager")
        return None
    except Exception as e:
        print(f"❌ ERREUR Selenium: {e}")
        return None

if __name__ == "__main__":
    """Test du scraper"""
    print("="*80)
    print("TEST SCRAPER BRVM PRODUCTION")
    print("="*80)
    
    # Tentative 1: Scraping BeautifulSoup
    data = scraper_brvm_officiel()
    
    # Tentative 2: Selenium si échec
    if not data:
        print("\n🔄 Tentative avec Selenium...")
        data = scraper_brvm_avec_selenium()
    
    # Afficher résultats
    if data:
        print(f"\n{'='*80}")
        print(f"✅ RÉSULTATS: {len(data)} cours récupérés")
        print(f"{'='*80}")
        
        for stock in data[:5]:  # Afficher les 5 premiers
            print(f"  {stock['symbol']:12} {stock['close']:>10,.0f} FCFA  {stock['variation']:>+6.2f}%  Vol: {stock['volume']:>10,}")
        
        if len(data) > 5:
            print(f"  ... et {len(data)-5} autres")
    else:
        print(f"\n{'='*80}")
        print(f"❌ ÉCHEC: Impossible de scraper les données")
        print(f"{'='*80}")
        print(f"\n📋 SOLUTIONS DE REPLI:")
        print(f"  1. Vérifier que le site est accessible: https://www.brvm.org")
        print(f"  2. Adapter le scraper selon la structure HTML réelle")
        print(f"  3. Utiliser la saisie manuelle: python mettre_a_jour_cours_brvm.py")
        print(f"  4. Importer un CSV: python import_rapide_brvm.py")
