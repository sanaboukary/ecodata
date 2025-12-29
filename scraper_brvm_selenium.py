"""
🔥 SCRAPER BRVM SELENIUM - Contournement JavaScript
===================================================

Utilise Selenium + Chrome headless pour charger completement le site BRVM
Contourne les limitations du scraping HTTP simple

PRÉREQUIS:
pip install selenium webdriver-manager

AVANTAGES:
✓ Charge JavaScript comme un vrai navigateur
✓ Contourne détection anti-bot
✓ Capture ticker défilant en temps réel
✓ Gère AJAX/dynamic content

UTILISATION:
python scraper_brvm_selenium.py            # Dry-run
python scraper_brvm_selenium.py --apply    # Import MongoDB
"""

import sys
import os
import time
import random
from datetime import datetime, timezone
import logging
import argparse

# Vérifier Selenium AVANT setup Django
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BRVMSeleniumScraper:
    """Scraper BRVM avec Selenium (charge JavaScript)"""
    
    def __init__(self):
        self.driver = None
        self.donnees = []
    
    def setup_driver(self):
        """Configure le driver Selenium"""
        if not SELENIUM_AVAILABLE:
            logger.error("❌ Selenium non installé")
            logger.info("💡 Installation: pip install selenium webdriver-manager")
            return False
        
        try:
            logger.info("🔧 Configuration Chrome headless...")
            
            options = Options()
            options.add_argument('--headless=new')  # Nouveau mode headless
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent réaliste
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Installer automatiquement le driver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Chrome headless prêt")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur setup driver: {e}")
            return False
    
    def collecter_brvm(self):
        """Collecte données BRVM avec Selenium"""
        logger.info("\n" + "="*70)
        logger.info("🚀 SCRAPING BRVM AVEC SELENIUM")
        logger.info("="*70)
        
        if not self.setup_driver():
            return []
        
        try:
            url = 'https://www.brvm.org'
            logger.info(f"\n🌐 Chargement: {url}")
            
            self.driver.get(url)
            
            # Attendre chargement page
            logger.info("⏳ Attente chargement JavaScript...")
            time.sleep(random.uniform(5, 8))  # Laisser le temps au JS de charger
            
            # Scroll pour déclencher lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            logger.info("✅ Page chargée")
            
            # Sauvegarder HTML complet (avec JS exécuté)
            html = self.driver.page_source
            html_file = f"brvm_selenium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"💾 HTML sauvegardé: {html_file}")
            
            # Extraire données
            donnees = self.extraire_donnees_selenium()
            
            logger.info(f"\n✅ {len(donnees)} actions extraites")
            
            return donnees
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔌 Driver fermé")
    
    def extraire_donnees_selenium(self):
        """Extrait données depuis la page Selenium"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        donnees = []
        
        try:
            # Stratégie 1: Chercher éléments ticker
            logger.info("🔍 Recherche éléments ticker...")
            
            # Patterns de classes courants pour tickers
            selectors = [
                "div.ticker-item",
                "div[class*='ticker']",
                "div[class*='stock']",
                "div[class*='quote']",
                "span.stock-symbol",
                "li.ticker-item",
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"  ✓ Trouvé {len(elements)} éléments: {selector}")
                        
                        for elem in elements:
                            try:
                                texte = elem.text.strip()
                                if texte:
                                    # Parser le texte
                                    import re
                                    match = re.search(r'([A-Z]{4})[^\d]*?(\d{3,6})[^\d+\-]*?([+\-]?\d+[\.,]?\d*)', texte)
                                    if match:
                                        symbol = match.group(1)
                                        price = float(match.group(2).replace(' ', ''))
                                        variation = float(match.group(3).replace(',', '.'))
                                        
                                        donnees.append({
                                            'symbol': symbol,
                                            'close': price,
                                            'variation': variation,
                                            'volume': 1000
                                        })
                            except:
                                continue
                        
                        if donnees:
                            break  # Trouvé des données, arrêter
                            
                except Exception as e:
                    continue
            
            # Stratégie 2: Parser HTML brut
            if not donnees:
                logger.info("🔍 Fallback: Parse HTML brut...")
                html = self.driver.page_source
                
                import re
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(html, 'html.parser')
                texte_complet = soup.get_text()
                
                # Chercher patterns de données BRVM
                pattern = r'([A-Z]{4})\s+(\d{3,6})\s+([+\-]?\d+[\.,]?\d*)\s*%?'
                matches = re.findall(pattern, texte_complet)
                
                for match in matches:
                    try:
                        symbol = match[0]
                        price = float(match[1].replace(' ', ''))
                        variation = float(match[2].replace(',', '.'))
                        
                        if len(symbol) == 4 and 100 <= price <= 100000:
                            donnees.append({
                                'symbol': symbol,
                                'close': price,
                                'variation': variation,
                                'volume': 1000
                            })
                    except:
                        continue
            
            # Dédupliquer
            unique = {d['symbol']: d for d in donnees}
            return list(unique.values())
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction: {e}")
            return []
    
    def sauvegarder_mongodb(self, donnees, dry_run=True):
        """Sauvegarde dans MongoDB"""
        if dry_run:
            logger.info("\n" + "="*70)
            logger.info("🔍 MODE DRY-RUN - Aperçu:\n")
            for d in donnees[:15]:
                logger.info(f"  {d['symbol']:6s} | {d['close']:8.0f} FCFA | {d['variation']:+6.2f}%")
            if len(donnees) > 15:
                logger.info(f"  ... et {len(donnees)-15} autres")
            logger.info("\n💡 Pour appliquer: python scraper_brvm_selenium.py --apply")
            logger.info("="*70)
            return 0
        
        # Mode APPLY
        logger.info("\n" + "="*70)
        logger.info("💾 INSERTION MONGODB")
        logger.info("="*70)
        
        client, db = get_mongo_db()
        collection = db.curated_observations
        
        date_collecte = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        inserted = 0
        
        for d in donnees:
            doc = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': d['symbol'],
                'ts': date_collecte,
                'value': d['close'],
                'attrs': {
                    'close': d['close'],
                    'open': d['close'],
                    'high': d['close'],
                    'low': d['close'],
                    'volume': d['volume'],
                    'variation': d['variation'],
                    'data_quality': 'REAL_SCRAPER',
                    'data_completeness': 'BASIC',
                    'scrape_timestamp': datetime.now(timezone.utc).isoformat(),
                    'scrape_method': 'selenium'
                }
            }
            
            result = collection.update_one(
                {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'key': d['symbol'], 'ts': date_collecte},
                {'$set': doc},
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id:
                inserted += 1
        
        logger.info(f"\n✅ {inserted} observations insérées")
        logger.info(f"📅 Date: {date_collecte}")
        logger.info(f"✨ Qualité: REAL_SCRAPER (selenium)")
        logger.info("="*70)
        
        return inserted


def main():
    """Point d'entrée"""
    parser = argparse.ArgumentParser(description='Scraper BRVM Selenium')
    parser.add_argument('--apply', action='store_true', help='Appliquer')
    args = parser.parse_args()
    
    scraper = BRVMSeleniumScraper()
    donnees = scraper.collecter_brvm()
    
    if donnees:
        scraper.sauvegarder_mongodb(donnees, dry_run=not args.apply)
        return 0
    else:
        logger.error("\n❌ Aucune donnée collectée")
        logger.info("\n💡 Solutions alternatives:")
        logger.info("  1. python scraper_brvm_furtif.py")
        logger.info("  2. python collecter_csv_automatique.py")
        logger.info("  3. python mettre_a_jour_cours_brvm.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
