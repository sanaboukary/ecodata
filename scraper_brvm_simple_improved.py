"""
🔥 SCRAPER BRVM SIMPLE AMÉLIORÉ
================================

Version simplifiée avec gestion gzip et headers réalistes
Sans Selenium (plus stable sur Windows)

UTILISATION:
python scraper_brvm_simple_improved.py            # Dry-run
python scraper_brvm_simple_improved.py --apply    # Import MongoDB
"""

import sys
import os
import time
import random
from datetime import datetime, timezone
import logging
import argparse
import re
import gzip
from io import BytesIO

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Dépendances manquantes: pip install requests beautifulsoup4")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Actions BRVM connues avec prix moyens (pour validation)
ACTIONS_BRVM = {
    'SNTS': (13000, 17000), 'SGBC': (1900, 2500), 'BOAB': (4000, 6000),
    'TTLS': (1200, 1900), 'ETIT': (16, 30), 'SVOC': (800, 1300),
    'BICC': (6000, 9000), 'CABC': (1700, 2400), 'ORGT': (4500, 6500),
    'SAFH': (250, 450), 'SIVC': (6400, 8500), 'PRSC': (540, 800),
    'ONTBF': (3800, 5200), 'TTLC': (2000, 3000), 'ECOC': (550, 850),
    'ABJC': (600000, 750000), 'SICC': (200, 350), 'NEIC': (650, 950),
    'CFAC': (5000, 7000), 'BOAM': (2500, 3500), 'NTLC': (1000, 1500),
    'BNBC': (5000, 7500), 'STAC': (380, 580), 'PALC': (6000, 8500),
    'SLBC': (14500, 17500), 'SCRC': (7500, 10500), 'SDCC': (3000, 4500),
    'SOGC': (6500, 9000), 'TTRC': (200, 400), 'UNXC': (1800, 2800),
    'BOAC': (4000, 6000), 'SMBC': (8500, 12000), 'CBIBF': (5500, 7500),
    'NSBC': (2800, 4200), 'FTSC': (950, 1450), 'SIBC': (3500, 5000),
    'SITC': (6000, 8500), 'CIEC': (1500, 2500), 'SDSC': (18000, 24000),
    'SICG': (6500, 9500), 'BOABF': (3800, 5500), 'UNLB': (1800, 2800),
    'SEMC': (1800, 2800), 'SOAC': (90000, 120000), 'SPHC': (5000, 7500),
    'TPCI': (2500, 3800), 'BISC': (38000, 52000)
}


class BRVMSimpleScraper:
    """Scraper BRVM simple avec gestion gzip"""
    
    def __init__(self):
        self.session = requests.Session()
        self.donnees = []
    
    def get_headers(self):
        """Génère headers réalistes"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def fetch_page(self, url, max_retries=3):
        """Fetch page avec gestion gzip"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = min(30, (2 ** attempt) + random.uniform(0, 2))
                    logger.info(f"⏳ Retry {attempt+1}/{max_retries} après {delay:.1f}s...")
                    time.sleep(delay)
                
                logger.info(f"🌐 Requête: {url}")
                
                response = self.session.get(
                    url,
                    headers=self.get_headers(),
                    timeout=30,
                    verify=False  # Contourner SSL si nécessaire
                )
                
                logger.info(f"📊 Status: {response.status_code} | Size: {len(response.content)} bytes")
                
                if response.status_code == 200:
                    # Décompresser si gzip
                    content = response.content
                    if content[:2] == b'\x1f\x8b':  # Magic number gzip
                        logger.info("📦 Décompression gzip...")
                        content = gzip.decompress(content)
                    
                    html = content.decode('utf-8', errors='ignore')
                    logger.info(f"✅ HTML décodé: {len(html)} caractères")
                    return html
                
                elif response.status_code == 403:
                    logger.warning("⚠️ 403 Forbidden - Détection possible")
                    time.sleep(random.uniform(3, 6))
                    continue
                
                else:
                    logger.error(f"❌ Status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur tentative {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
        
        return None
    
    def extraire_donnees(self, html):
        """Extrait données depuis HTML"""
        donnees = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Stratégie 1: Chercher tableaux de cours
            logger.info("🔍 Recherche tableaux...")
            tables = soup.find_all('table')
            logger.info(f"  Trouvé {len(tables)} tableaux")
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        texte = ' '.join([c.get_text() for c in cells])
                        
                        # Pattern: SYMBOL PRICE VARIATION
                        match = re.search(r'([A-Z]{4,6})\s+(\d{2,6})\s+([+\-]?\d+[\.,]?\d*)', texte)
                        if match:
                            symbol = match.group(1)
                            if symbol in ACTIONS_BRVM:
                                try:
                                    price = float(match.group(2).replace(' ', ''))
                                    variation = float(match.group(3).replace(',', '.'))
                                    
                                    # Valider prix dans range attendue
                                    min_price, max_price = ACTIONS_BRVM[symbol]
                                    if min_price <= price <= max_price:
                                        donnees.append({
                                            'symbol': symbol,
                                            'close': price,
                                            'variation': variation,
                                            'volume': 1000
                                        })
                                except:
                                    continue
            
            # Stratégie 2: Recherche texte brut
            if not donnees:
                logger.info("🔍 Fallback: Recherche texte brut...")
                texte_complet = soup.get_text()
                
                # Pattern large
                pattern = r'([A-Z]{4,6})\s+(\d{2,6})\s+([+\-]?\d+[\.,]?\d*)\s*%?'
                matches = re.findall(pattern, texte_complet)
                
                for match in matches:
                    symbol = match[0]
                    if symbol in ACTIONS_BRVM:
                        try:
                            price = float(match[1].replace(' ', ''))
                            variation = float(match[2].replace(',', '.'))
                            
                            min_price, max_price = ACTIONS_BRVM[symbol]
                            if min_price <= price <= max_price:
                                donnees.append({
                                    'symbol': symbol,
                                    'close': price,
                                    'variation': variation,
                                    'volume': 1000
                                })
                        except:
                            continue
            
            # Stratégie 3: Divs avec classes ticker/stock
            if not donnees:
                logger.info("🔍 Recherche divs ticker/stock...")
                divs = soup.find_all('div', class_=re.compile(r'(ticker|stock|quote|cours)', re.I))
                logger.info(f"  Trouvé {len(divs)} divs potentiels")
                
                for div in divs:
                    texte = div.get_text()
                    match = re.search(r'([A-Z]{4,6})\s+(\d{2,6})\s+([+\-]?\d+[\.,]?\d*)', texte)
                    if match and match.group(1) in ACTIONS_BRVM:
                        try:
                            symbol = match.group(1)
                            price = float(match.group(2).replace(' ', ''))
                            variation = float(match.group(3).replace(',', '.'))
                            
                            min_price, max_price = ACTIONS_BRVM[symbol]
                            if min_price <= price <= max_price:
                                donnees.append({
                                    'symbol': symbol,
                                    'close': price,
                                    'variation': variation,
                                    'volume': 1000
                                })
                        except:
                            continue
            
            # Dédupliquer
            unique = {}
            for d in donnees:
                if d['symbol'] not in unique:
                    unique[d['symbol']] = d
            
            return list(unique.values())
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction: {e}")
            return []
    
    def collecter(self):
        """Lance la collecte"""
        logger.info("\n" + "="*70)
        logger.info("🚀 SCRAPING BRVM SIMPLE")
        logger.info("="*70)
        
        # URLs à essayer
        urls = [
            'https://www.brvm.org',
            'https://www.brvm.org/fr',
            'https://www.brvm.org/fr/cours-actions',
        ]
        
        for url in urls:
            html = self.fetch_page(url)
            if html:
                # Sauvegarder HTML
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                html_file = f"brvm_simple_{timestamp}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info(f"💾 HTML sauvegardé: {html_file}")
                
                # Extraire données
                donnees = self.extraire_donnees(html)
                if donnees:
                    logger.info(f"\n✅ {len(donnees)} actions extraites")
                    return donnees
                else:
                    logger.warning(f"⚠️ Aucune donnée extraite de {url}")
            
            time.sleep(random.uniform(2, 4))
        
        logger.error("\n❌ Aucune URL n'a retourné de données")
        return []
    
    def sauvegarder_mongodb(self, donnees, dry_run=True):
        """Sauvegarde dans MongoDB"""
        if dry_run:
            logger.info("\n" + "="*70)
            logger.info("🔍 MODE DRY-RUN - Aperçu:\n")
            for d in sorted(donnees, key=lambda x: x['symbol'])[:20]:
                logger.info(f"  {d['symbol']:6s} | {d['close']:8.0f} FCFA | {d['variation']:+6.2f}%")
            if len(donnees) > 20:
                logger.info(f"  ... et {len(donnees)-20} autres")
            logger.info("\n💡 Pour appliquer: python scraper_brvm_simple_improved.py --apply")
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
                    'scrape_method': 'simple_improved'
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
        logger.info(f"✨ Qualité: REAL_SCRAPER (simple_improved)")
        logger.info("="*70)
        
        return inserted


def main():
    """Point d'entrée"""
    parser = argparse.ArgumentParser(description='Scraper BRVM Simple Amélioré')
    parser.add_argument('--apply', action='store_true', help='Appliquer')
    args = parser.parse_args()
    
    scraper = BRVMSimpleScraper()
    donnees = scraper.collecter()
    
    if donnees:
        scraper.sauvegarder_mongodb(donnees, dry_run=not args.apply)
        return 0
    else:
        logger.error("\n❌ Aucune donnée collectée")
        logger.info("\n💡 Solutions alternatives:")
        logger.info("  1. python collecter_csv_automatique.py")
        logger.info("  2. python mettre_a_jour_cours_brvm.py")
        return 1


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    sys.exit(main())
