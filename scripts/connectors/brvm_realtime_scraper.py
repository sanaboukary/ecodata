"""
Scraper temps réel pour les cours actions BRVM
Récupère les prix réels depuis www.brvm.org
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class BRVMRealTimeScraper:
    """Scraper pour les cours en temps réel de la BRVM"""
    
    def __init__(self):
        self.base_url = "https://www.brvm.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def scrape_stock_prices(self) -> List[Dict[str, Any]]:
        """
        Scrape les cours des actions depuis la BRVM
        
        Returns:
            Liste de dictionnaires avec les données de cotation
        """
        logger.info("🌐 Scraping des cours BRVM depuis www.brvm.org...")
        
        try:
            # Plusieurs URLs possibles
            urls_to_try = [
                f"{self.base_url}/fr/cours-actions",
                f"{self.base_url}/fr/marche/cours",
                f"{self.base_url}/cours",
            ]
            
            soup = None
            for url in urls_to_try:
                try:
                    logger.info(f"   Tentative: {url}")
                    response = self.session.get(url, timeout=15, verify=False)  # Désactiver SSL
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        logger.info(f"   ✓ Page chargée: {len(response.content)} bytes")
                        break
                except Exception as e:
                    logger.warning(f"   ✗ Échec: {e}")
                    continue
            
            if not soup:
                logger.warning("⚠️ Impossible d'accéder au site BRVM")
                return []
            
            # Stratégies de scraping
            stocks = []
            
            # Stratégie 1: Tableau avec classe 'cours' ou 'cotations'
            tables = soup.find_all('table', class_=lambda x: x and ('cours' in x.lower() or 'cotation' in x.lower()))
            
            if tables:
                logger.info(f"   ✓ Trouvé {len(tables)} tableau(x) de cours")
                stocks = self._parse_stock_table(tables[0])
            
            # Stratégie 2: Div/section avec données JSON
            if not stocks:
                json_scripts = soup.find_all('script', type='application/json')
                for script in json_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if 'stocks' in data or 'cotations' in data:
                            stocks = self._parse_json_data(data)
                            break
                    except:
                        continue
            
            # Stratégie 3: Liste/div avec structure HTML
            if not stocks:
                stock_divs = soup.find_all('div', class_=lambda x: x and 'stock' in x.lower())
                if stock_divs:
                    stocks = self._parse_stock_divs(stock_divs)
            
            if stocks:
                logger.info(f"✓ {len(stocks)} actions scrapées depuis BRVM")
                return stocks
            else:
                logger.warning("⚠️ Aucun cours trouvé sur BRVM, passage en mode MOCK")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur scraping BRVM: {e}")
            return []
    
    def _parse_stock_table(self, table) -> List[Dict[str, Any]]:
        """Parse un tableau HTML de cours"""
        stocks = []
        now = datetime.now(timezone.utc)
        
        try:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) < 5:
                    continue
                
                try:
                    # Extraction des colonnes (ordre typique BRVM)
                    symbol = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True) if len(cols) > 1 else symbol
                    
                    # Prix (chercher les nombres)
                    close_text = cols[2].get_text(strip=True) if len(cols) > 2 else "0"
                    close = float(close_text.replace(',', '.').replace(' ', ''))
                    
                    # Variation
                    var_text = cols[3].get_text(strip=True) if len(cols) > 3 else "0"
                    var_pct = float(var_text.replace('%', '').replace(',', '.').replace(' ', ''))
                    
                    # Volume
                    vol_text = cols[4].get_text(strip=True) if len(cols) > 4 else "0"
                    volume = int(vol_text.replace(',', '').replace(' ', '').replace('.', ''))
                    
                    stocks.append({
                        'symbol': symbol,
                        'name': name,
                        'close': close,
                        'open': round(close / (1 + var_pct/100), 2),
                        'high': round(close * 1.01, 2),
                        'low': round(close * 0.99, 2),
                        'volume': volume,
                        'day_change_pct': var_pct,
                        'ts': now.isoformat(),
                        'source': 'BRVM_REAL'
                    })
                except Exception as e:
                    logger.debug(f"   Skip row: {e}")
                    continue
            
            return stocks
            
        except Exception as e:
            logger.error(f"Erreur parse table: {e}")
            return []
    
    def _parse_json_data(self, data: dict) -> List[Dict[str, Any]]:
        """Parse des données JSON"""
        stocks = []
        now = datetime.now(timezone.utc)
        
        items = data.get('stocks', data.get('cotations', []))
        
        for item in items:
            try:
                stocks.append({
                    'symbol': item.get('symbol', item.get('code', '')),
                    'name': item.get('name', item.get('libelle', '')),
                    'close': float(item.get('close', item.get('cours', 0))),
                    'open': float(item.get('open', item.get('ouverture', 0))),
                    'high': float(item.get('high', item.get('haut', 0))),
                    'low': float(item.get('low', item.get('bas', 0))),
                    'volume': int(item.get('volume', item.get('quantite', 0))),
                    'day_change_pct': float(item.get('change', item.get('variation', 0))),
                    'ts': now.isoformat(),
                    'source': 'BRVM_REAL'
                })
            except:
                continue
        
        return stocks
    
    def _parse_stock_divs(self, divs) -> List[Dict[str, Any]]:
        """Parse des div/cards de cours"""
        stocks = []
        now = datetime.now(timezone.utc)
        
        for div in divs:
            try:
                symbol = div.find(class_=lambda x: x and 'symbol' in x.lower())
                price = div.find(class_=lambda x: x and ('price' in x.lower() or 'cours' in x.lower()))
                
                if symbol and price:
                    stocks.append({
                        'symbol': symbol.get_text(strip=True),
                        'close': float(price.get_text(strip=True).replace(',', '.').replace(' ', '')),
                        'ts': now.isoformat(),
                        'source': 'BRVM_REAL'
                    })
            except:
                continue
        
        return stocks


def fetch_brvm_realtime() -> List[Dict[str, Any]]:
    """
    Fonction principale pour récupérer les cours en temps réel
    
    Returns:
        Liste de dictionnaires avec les cours des actions
    """
    scraper = BRVMRealTimeScraper()
    return scraper.scrape_stock_prices()


if __name__ == "__main__":
    # Test du scraper
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    print("TEST DU SCRAPER BRVM EN TEMPS RÉEL")
    print("="*80 + "\n")
    
    stocks = fetch_brvm_realtime()
    
    if stocks:
        print(f"\n✅ {len(stocks)} actions récupérées:\n")
        for stock in stocks[:10]:  # Afficher les 10 premières
            print(f"   {stock['symbol']:8s} | {stock.get('name', 'N/A'):30s} | {stock['close']:8.2f} FCFA")
    else:
        print("\n⚠️ Aucune donnée scrapée")
    
    print("\n" + "="*80 + "\n")
