#!/usr/bin/env python3
"""
🎯 SCRAPER BRVM RÉEL - TOLÉRANCE ZÉRO
Collecte les VRAIES données depuis https://www.brvm.org/fr/cours-actions/investisseurs
POLITIQUE: Aucune donnée fictive ou simulée autorisée
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import re
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Imports pour scraping
try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    print("💡 Installer: pip install requests beautifulsoup4")
    sys.exit(1)

# URL officielle BRVM
BRVM_URL = "https://www.brvm.org/fr/cours-actions/investisseurs"

class BRVMRealScraper:
    """Scraper pour données réelles BRVM uniquement"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def scrape_real_data(self):
        """Scraper les données réelles du site BRVM"""
        print("=" * 100)
        print("🎯 SCRAPING DONNÉES RÉELLES BRVM")
        print("=" * 100)
        print(f"URL: {BRVM_URL}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            print("📡 Connexion au site BRVM...")
            response = self.session.get(BRVM_URL, verify=False, timeout=30)
            response.raise_for_status()
            
            print(f"✅ Réponse HTTP {response.status_code}")
            print(f"📄 Taille page: {len(response.content):,} bytes")
            print()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher le tableau des cours
            print("🔍 Recherche du tableau des cours...")
            
            # Stratégies multiples pour trouver les données
            actions_data = []
            
            # Stratégie 1: Chercher table avec class contenant "cours" ou "actions"
            tables = soup.find_all('table')
            print(f"   Tables trouvées: {len(tables)}")
            
            for idx, table in enumerate(tables):
                rows = table.find_all('tr')
                if len(rows) > 5:  # Au moins quelques actions
                    print(f"   Table {idx+1}: {len(rows)} lignes")
                    
                    # Analyser les en-têtes
                    headers = []
                    header_row = table.find('thead') or table.find('tr')
                    if header_row:
                        ths = header_row.find_all(['th', 'td'])
                        headers = [th.get_text(strip=True).lower() for th in ths]
                        print(f"      En-têtes: {headers[:5]}...")
                    
                    # Vérifier si c'est le bon tableau (contient symbole, cours, volume)
                    keywords = ['symbole', 'code', 'cours', 'prix', 'dernier', 'volume', 'valeur']
                    if any(kw in ' '.join(headers) for kw in keywords):
                        print(f"   ✅ Table {idx+1} semble contenir les cours!")
                        actions_data = self._extract_from_table(table, headers)
                        if actions_data:
                            break
            
            # Stratégie 2: Chercher divs avec data-
            if not actions_data:
                print("   Recherche dans les divs...")
                divs = soup.find_all('div', {'data-symbol': True})
                if divs:
                    print(f"   Divs avec data-symbol: {len(divs)}")
                    actions_data = self._extract_from_divs(divs)
            
            # Stratégie 3: Chercher scripts JSON
            if not actions_data:
                print("   Recherche dans les scripts JavaScript...")
                scripts = soup.find_all('script')
                for script in scripts:
                    script_text = script.get_text()
                    if 'cours' in script_text.lower() or 'actions' in script_text.lower():
                        # Chercher patterns JSON
                        import json
                        json_matches = re.findall(r'\{[^}]*"symbol"[^}]*\}', script_text)
                        if json_matches:
                            print(f"   Patterns JSON trouvés: {len(json_matches)}")
                            try:
                                for match in json_matches[:5]:
                                    data = json.loads(match)
                                    if 'symbol' in data and 'price' in data:
                                        actions_data.append(data)
                            except:
                                pass
            
            if not actions_data:
                print()
                print("❌ AUCUNE DONNÉE TROUVÉE SUR LA PAGE")
                print("💡 Le site BRVM a peut-être changé de structure")
                print()
                print("📄 CONTENU DE LA PAGE (premiers 2000 caractères):")
                print("-" * 100)
                text_content = soup.get_text()[:2000]
                print(text_content)
                print("-" * 100)
                return []
            
            print()
            print(f"✅ {len(actions_data)} actions extraites")
            return actions_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
            return []
        except Exception as e:
            print(f"❌ Erreur scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_from_table(self, table, headers):
        """Extraire données d'un tableau HTML"""
        actions = []
        rows = table.find_all('tr')[1:]  # Skip header
        
        # Identifier les colonnes
        col_symbol = self._find_column_index(headers, ['symbole', 'code', 'ticker', 'symbol'])
        col_price = self._find_column_index(headers, ['cours', 'prix', 'dernier', 'price', 'close'])
        col_volume = self._find_column_index(headers, ['volume', 'quantité', 'qty'])
        col_var = self._find_column_index(headers, ['variation', 'var', 'change', '%'])
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            try:
                action = {}
                
                # Symbole
                if col_symbol is not None and col_symbol < len(cells):
                    symbol = cells[col_symbol].get_text(strip=True)
                    if symbol and len(symbol) >= 3:
                        action['symbol'] = symbol
                
                # Prix
                if col_price is not None and col_price < len(cells):
                    price_text = cells[col_price].get_text(strip=True)
                    price_text = re.sub(r'[^\d,.]', '', price_text)
                    price_text = price_text.replace(',', '.')
                    if price_text:
                        try:
                            action['price'] = float(price_text)
                        except:
                            pass
                
                # Volume
                if col_volume is not None and col_volume < len(cells):
                    vol_text = cells[col_volume].get_text(strip=True)
                    vol_text = re.sub(r'[^\d]', '', vol_text)
                    if vol_text:
                        try:
                            action['volume'] = int(vol_text)
                        except:
                            pass
                
                # Variation
                if col_var is not None and col_var < len(cells):
                    var_text = cells[col_var].get_text(strip=True)
                    var_text = re.sub(r'[^\d,.\-+]', '', var_text)
                    var_text = var_text.replace(',', '.')
                    if var_text:
                        try:
                            action['variation'] = float(var_text)
                        except:
                            pass
                
                if 'symbol' in action and 'price' in action:
                    actions.append(action)
                    
            except Exception as e:
                continue
        
        return actions
    
    def _extract_from_divs(self, divs):
        """Extraire données de divs avec attributs data-"""
        actions = []
        for div in divs:
            try:
                action = {
                    'symbol': div.get('data-symbol'),
                    'price': float(div.get('data-price', 0)),
                    'volume': int(div.get('data-volume', 0)),
                }
                if action['symbol'] and action['price'] > 0:
                    actions.append(action)
            except:
                continue
        return actions
    
    def _find_column_index(self, headers, keywords):
        """Trouver l'index d'une colonne par mots-clés"""
        for idx, header in enumerate(headers):
            for keyword in keywords:
                if keyword in header.lower():
                    return idx
        return None
    
    def insert_to_mongodb(self, actions_data):
        """Insérer données RÉELLES dans MongoDB"""
        if not actions_data:
            print("⚠️  Aucune donnée à insérer")
            return
        
        print()
        print("=" * 100)
        print("💾 INSERTION DANS MONGODB")
        print("=" * 100)
        
        date_aujourd_hui = datetime.now().strftime('%Y-%m-%d')
        inserted = 0
        updated = 0
        errors = 0
        
        for action in actions_data:
            try:
                symbol = action.get('symbol', '').strip().upper()
                price = action.get('price', 0)
                
                if not symbol or price <= 0:
                    continue
                
                observation = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': symbol,
                    'ts': date_aujourd_hui,
                    'value': price,
                    'attrs': {
                        'symbol': symbol,
                        'volume': action.get('volume', 0),
                        'variation': action.get('variation', 0),
                        'data_quality': 'REAL_SCRAPER',  # ✅ DONNÉES RÉELLES
                        'source_url': BRVM_URL,
                        'scrape_date': datetime.now().isoformat(),
                    }
                }
                
                # Upsert (update or insert)
                result = self.db.curated_observations.update_one(
                    {
                        'source': 'BRVM',
                        'dataset': 'STOCK_PRICE',
                        'key': symbol,
                        'ts': date_aujourd_hui
                    },
                    {'$set': observation},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted += 1
                    print(f"  ✅ {symbol:10s} = {price:>10,.0f} FCFA (nouveau)")
                else:
                    updated += 1
                    print(f"  🔄 {symbol:10s} = {price:>10,.0f} FCFA (mis à jour)")
                    
            except Exception as e:
                errors += 1
                print(f"  ❌ Erreur {symbol}: {e}")
        
        print()
        print("=" * 100)
        print("📊 RÉSULTAT")
        print("=" * 100)
        print(f"✅ Insérées    : {inserted}")
        print(f"🔄 Mises à jour: {updated}")
        print(f"❌ Erreurs     : {errors}")
        print(f"📅 Date        : {date_aujourd_hui}")
        print(f"🎯 Qualité     : REAL_SCRAPER (DONNÉES RÉELLES)")
        print("=" * 100)

def main():
    scraper = BRVMRealScraper()
    
    # Scraper données réelles
    actions_data = scraper.scrape_real_data()
    
    if actions_data:
        # Insérer dans MongoDB
        scraper.insert_to_mongodb(actions_data)
    else:
        print()
        print("=" * 100)
        print("❌ ÉCHEC DE LA COLLECTE")
        print("=" * 100)
        print("💡 SOLUTIONS:")
        print("   1. Vérifier que le site BRVM est accessible")
        print("   2. Le site a peut-être changé de structure")
        print("   3. Utiliser la saisie manuelle: mettre_a_jour_cours_brvm.py")
        print("=" * 100)

if __name__ == '__main__':
    main()
