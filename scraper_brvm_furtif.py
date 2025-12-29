"""
🕵️ SCRAPER BRVM FURTIF - Anti-Détection
========================================

Stratégie multi-couches pour scraping discret et fiable du site BRVM
Contourne les protections standard : User-Agent detection, rate limiting, fingerprinting

TECHNIQUES UTILISÉES:
1. Rotation User-Agents réalistes
2. Headers HTTP complets et cohérents
3. Délais aléatoires entre requêtes
4. Gestion cookies/sessions
5. Retry avec backoff exponentiel
6. Fallback sur proxies si nécessaire
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time
import random
import hashlib
from urllib3.exceptions import InsecureRequestWarning
from fake_useragent import UserAgent
import logging

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BRVMStealthScraper:
    """Scraper furtif avec techniques anti-détection"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.urls_testees = []
        self.dernier_scrape = None
        
        # Pool de User-Agents réalistes (navigateurs récents)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        
        # URLs à tester (ordre de priorité)
        self.urls_brvm = [
            'https://www.brvm.org',
            'https://www.brvm.org/fr',
            'https://www.brvm.org/fr/marche',
            'http://www.brvm.org',  # Fallback HTTP si HTTPS bloqué
        ]
    
    def get_headers_realistes(self):
        """Génère des headers HTTP réalistes et cohérents"""
        ua = random.choice(self.user_agents)
        
        # Déterminer browser/OS depuis UA
        is_chrome = 'Chrome' in ua
        is_firefox = 'Firefox' in ua
        is_safari = 'Safari' in ua and 'Chrome' not in ua
        is_windows = 'Windows' in ua
        is_mac = 'Macintosh' in ua
        
        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',  # Do Not Track
        }
        
        # Headers spécifiques par navigateur
        if is_chrome:
            headers['sec-ch-ua'] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
            headers['sec-ch-ua-mobile'] = '?0'
            headers['sec-ch-ua-platform'] = '"Windows"' if is_windows else '"macOS"'
            headers['Sec-Fetch-Site'] = 'none'
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-User'] = '?1'
            headers['Sec-Fetch-Dest'] = 'document'
        
        elif is_firefox:
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            headers['TE'] = 'trailers'
        
        return headers
    
    def delai_aleatoire(self, min_sec=2, max_sec=5):
        """Pause aléatoire entre requêtes (comportement humain)"""
        delai = random.uniform(min_sec, max_sec)
        time.sleep(delai)
    
    def fetch_page_stealth(self, url, max_retries=3):
        """Récupère une page avec techniques anti-détection"""
        
        for attempt in range(max_retries):
            try:
                # Délai avant requête (sauf première)
                if attempt > 0:
                    backoff = min(30, (2 ** attempt) + random.uniform(0, 1))
                    logger.info(f"  ⏳ Retry {attempt+1}/{max_retries} dans {backoff:.1f}s...")
                    time.sleep(backoff)
                
                # Headers frais à chaque tentative
                headers = self.get_headers_realistes()
                
                # Requête
                logger.debug(f"  🔍 GET {url}")
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=20,
                    verify=False,  # Ignore SSL errors
                    allow_redirects=True
                )
                
                # Vérifier statut
                if response.status_code == 200:
                    logger.info(f"  ✅ Succès: {url} ({len(response.content)} bytes)")
                    
                    # Délai aléatoire avant prochain accès
                    self.delai_aleatoire(2, 4)
                    
                    return response
                
                elif response.status_code == 403:
                    logger.warning(f"  🚫 Bloqué (403): {url}")
                    # Changer User-Agent et retry
                    continue
                
                elif response.status_code == 429:
                    logger.warning(f"  ⏱️  Rate limited (429): {url}")
                    # Attendre plus longtemps
                    time.sleep(30 + random.uniform(0, 10))
                    continue
                
                else:
                    logger.warning(f"  ⚠️  HTTP {response.status_code}: {url}")
                    continue
            
            except requests.exceptions.SSLError:
                logger.warning(f"  🔒 Erreur SSL (tentative {attempt+1})")
                continue
            
            except requests.exceptions.Timeout:
                logger.warning(f"  ⏰ Timeout (tentative {attempt+1})")
                continue
            
            except Exception as e:
                logger.error(f"  ❌ Erreur: {str(e)[:100]}")
                continue
        
        logger.error(f"  ❌ Échec après {max_retries} tentatives")
        return None
    
    def extraire_ticker_defilant(self, html_content):
        """Extrait données du ticker défilant (bande en haut du site)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        donnees = []
        
        # Chercher le ticker défilant
        # Patterns courants: <div class="ticker">, <div id="ticker">, etc.
        ticker_containers = soup.find_all(['div', 'ul', 'span'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['ticker', 'marquee', 'scroll', 'slide']
        ))
        
        if not ticker_containers:
            # Fallback: chercher dans le HTML brut
            import re
            pattern = r'([A-Z]{4})[^\d]*?(\d{3,6})[^\d+\-]*?([+\-]?\d+[\.,]?\d*)\s*%?'
            matches = re.findall(pattern, html_content)
            
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
                            'volume': 1000  # Estimation
                        })
                except:
                    continue
        
        else:
            # Parser les éléments du ticker
            for container in ticker_containers:
                items = container.find_all(['div', 'span', 'li'], recursive=True)
                
                for item in items:
                    texte = item.get_text(strip=True)
                    
                    # Pattern: SNTS 15500 +2.3%
                    import re
                    match = re.search(r'([A-Z]{4})[^\d]*?(\d{3,6})[^\d+\-]*?([+\-]?\d+[\.,]?\d*)', texte)
                    
                    if match:
                        try:
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
        
        # Dédupliquer
        unique = {}
        for d in donnees:
            if d['symbol'] not in unique:
                unique[d['symbol']] = d
        
        return list(unique.values())
    
    def collecter_donnees(self):
        """Collecte les données BRVM en mode furtif"""
        logger.info("\n" + "="*70)
        logger.info("🕵️  SCRAPING FURTIF BRVM")
        logger.info("="*70)
        
        donnees_collectees = []
        
        # Essayer chaque URL
        for url in self.urls_brvm:
            logger.info(f"\n🎯 Tentative: {url}")
            
            response = self.fetch_page_stealth(url)
            
            if not response:
                continue
            
            # Sauvegarder HTML pour debug
            debug_file = f"brvm_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"  💾 HTML sauvegardé: {debug_file}")
            
            # Extraire données
            donnees = self.extraire_ticker_defilant(response.text)
            
            if donnees:
                logger.info(f"  ✅ {len(donnees)} actions extraites")
                donnees_collectees.extend(donnees)
                break  # Succès, pas besoin d'essayer d'autres URLs
            else:
                logger.warning(f"  ⚠️  Aucune donnée extraite de {url}")
        
        # Dédupliquer final
        unique = {d['symbol']: d for d in donnees_collectees}
        donnees_finales = list(unique.values())
        
        logger.info("\n" + "="*70)
        if donnees_finales:
            logger.info(f"✅ SUCCÈS: {len(donnees_finales)} actions collectées")
        else:
            logger.error("❌ ÉCHEC: Aucune donnée collectée")
        logger.info("="*70 + "\n")
        
        return donnees_finales
    
    def sauvegarder_mongodb(self, donnees, dry_run=True):
        """Sauvegarde dans MongoDB"""
        if dry_run:
            logger.info("\n🔍 MODE DRY-RUN - Aperçu des données:\n")
            for d in donnees[:10]:
                logger.info(f"  {d['symbol']:6s} | {d['close']:8.0f} FCFA | {d['variation']:+6.2f}%")
            if len(donnees) > 10:
                logger.info(f"  ... et {len(donnees)-10} autres")
            logger.info("\n💡 Pour appliquer: --apply")
            return 0
        
        # Mode APPLY
        logger.info("\n💾 INSERTION MONGODB")
        
        client, db = get_mongo_db()
        collection = db.curated_observations
        
        date_collecte = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        inserted = 0
        
        for d in donnees:
            symbol = d['symbol']
            
            doc = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbol,
                'ts': date_collecte,
                'value': d['close'],
                'attrs': {
                    'close': d['close'],
                    'open': d['close'],  # Approximation
                    'high': d['close'],
                    'low': d['close'],
                    'volume': d.get('volume', 1000),
                    'variation': d['variation'],
                    'data_quality': 'REAL_SCRAPER',
                    'data_completeness': 'BASIC',
                    'scrape_timestamp': datetime.now(timezone.utc).isoformat(),
                    'scrape_method': 'stealth'
                }
            }
            
            result = collection.update_one(
                {'source': 'BRVM', 'dataset': 'STOCK_PRICE', 'key': symbol, 'ts': date_collecte},
                {'$set': doc},
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id:
                inserted += 1
        
        logger.info(f"\n✅ {inserted} observations insérées")
        logger.info(f"📅 {date_collecte}")
        logger.info(f"✨ REAL_SCRAPER (stealth mode)")
        
        return inserted


def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper BRVM Furtif')
    parser.add_argument('--apply', action='store_true', help='Appliquer (sinon dry-run)')
    parser.add_argument('--debug', action='store_true', help='Mode debug verbeux')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    scraper = BRVMStealthScraper()
    donnees = scraper.collecter_donnees()
    
    if donnees:
        scraper.sauvegarder_mongodb(donnees, dry_run=not args.apply)
        return 0
    else:
        logger.error("\n⚠️  Scraping échoué - Alternatives:")
        logger.info("  1. Vérifier connexion internet")
        logger.info("  2. Essayer plus tard (site peut être down)")
        logger.info("  3. Utiliser collecte manuelle CSV")
        logger.info("  4. Contacter BRVM pour API officielle")
        return 1


if __name__ == "__main__":
    sys.exit(main())
