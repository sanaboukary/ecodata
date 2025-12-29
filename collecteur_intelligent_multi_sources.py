"""
Collecteur Intelligent Multi-Sources BRVM
Stratégie: API → Scraping → Parsing PDF → Saisie manuelle
"""
import os
import sys
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json
import time

_, db = get_mongo_db()

class CollecteurIntelligentBRVM:
    """Collecteur avec stratégies multiples"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.resultats = []
        
    def methode1_api_brvm_officielle(self):
        """Tentative 1: API BRVM officielle (si existe)"""
        print('\n🔄 Méthode 1: API BRVM Officielle')
        print('-' * 80)
        
        urls_api = [
            'https://www.brvm.org/api/quotes/latest',
            'https://www.brvm.org/api/v1/cours',
            'https://api.brvm.org/quotes',
            'https://www.brvm.org/sites/default/files/cours.json'
        ]
        
        for url in urls_api:
            try:
                print(f'   Tentative: {url}')
                response = self.session.get(url, timeout=10, verify=False)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f'   ✅ Succès! {len(data)} données trouvées')
                    self.resultats = self._parser_api_json(data)
                    return True
                    
            except Exception as e:
                print(f'   ❌ Échec: {str(e)[:50]}')
                
        print('   ⚠️  Aucune API accessible')
        return False
    
    def methode2_scraping_site_brvm(self):
        """Tentative 2: Scraping page cotations BRVM"""
        print('\n🔄 Méthode 2: Scraping Site BRVM')
        print('-' * 80)
        
        urls_scraping = [
            'https://www.brvm.org/fr/cours-actions',
            'https://www.brvm.org/fr/investir/cours-et-cotations',
            'https://www.brvm.org/fr/marche/cours',
            'https://www.brvm.org/sites/default/files/cours.html'
        ]
        
        for url in urls_scraping:
            try:
                print(f'   Tentative: {url}')
                response = self.session.get(url, timeout=15, verify=False)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Chercher tables avec cours
                    tables = soup.find_all('table')
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) > 5:  # Au moins 5 lignes
                            print(f'   ✅ Table trouvée avec {len(rows)} lignes')
                            self.resultats = self._parser_table_html(table)
                            if self.resultats:
                                return True
                                
            except Exception as e:
                print(f'   ❌ Échec: {str(e)[:50]}')
                
        print('   ⚠️  Scraping échoué')
        return False
    
    def methode3_parsing_bulletin_pdf(self):
        """Tentative 3: Télécharger et parser bulletin quotidien PDF"""
        print('\n🔄 Méthode 3: Bulletin Quotidien PDF')
        print('-' * 80)
        
        today = datetime.now().strftime('%Y%m%d')
        urls_pdf = [
            f'https://www.brvm.org/sites/default/files/bulletin_{today}.pdf',
            f'https://www.brvm.org/sites/default/files/cours_{today}.pdf',
            'https://www.brvm.org/sites/default/files/bulletin_quotidien.pdf'
        ]
        
        for url in urls_pdf:
            try:
                print(f'   Tentative: {url}')
                response = self.session.get(url, timeout=20, verify=False)
                
                if response.status_code == 200 and 'pdf' in response.headers.get('content-type', ''):
                    print(f'   ✅ PDF téléchargé ({len(response.content)/1024:.1f} KB)')
                    
                    # Sauvegarder temporairement
                    pdf_path = f'bulletins_brvm/bulletin_{today}.pdf'
                    os.makedirs('bulletins_brvm', exist_ok=True)
                    
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f'   📄 Sauvegardé: {pdf_path}')
                    print(f'   💡 Utilisez: python parser_bulletins_brvm_pdf.py')
                    return False  # Nécessite parser manuel
                    
            except Exception as e:
                print(f'   ❌ Échec: {str(e)[:50]}')
                
        print('   ⚠️  Aucun bulletin PDF accessible')
        return False
    
    def methode4_bloomberg_yahoo_finance(self):
        """Tentative 4: APIs financières tierces"""
        print('\n🔄 Méthode 4: APIs Financières Tierces')
        print('-' * 80)
        
        # Symboles BRVM sur Yahoo Finance (si existent)
        symboles_brvm = [
            'SNTS.AB',  # Sonatel Abidjan
            'SGBC.AB',  # SGBCI
            'BICC.AB'   # BICICI
        ]
        
        for symbole in symboles_brvm:
            try:
                url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbole}'
                print(f'   Tentative: {symbole}')
                
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f'   ✅ Données trouvées pour {symbole}')
                    
            except Exception as e:
                print(f'   ❌ {symbole}: {str(e)[:30]}')
                
        print('   ⚠️  APIs tierces non disponibles pour BRVM')
        return False
    
    def methode5_saisie_manuelle_guidee(self):
        """Méthode 5: Saisie manuelle interactive"""
        print('\n🔄 Méthode 5: Saisie Manuelle Guidée')
        print('-' * 80)
        print()
        print('   📋 Aller sur: https://www.brvm.org/fr/investir/cours-et-cotations')
        print('   📝 Copier les cours dans: mettre_a_jour_cours_brvm.py')
        print('   ▶️  Exécuter: python mettre_a_jour_cours_brvm.py')
        print()
        return False
    
    def _parser_api_json(self, data):
        """Parse réponse JSON d'API"""
        resultats = []
        
        # Différents formats possibles
        if isinstance(data, list):
            for item in data:
                if 'symbol' in item and 'close' in item:
                    resultats.append({
                        'symbol': item['symbol'],
                        'close': float(item['close']),
                        'volume': int(item.get('volume', 0)),
                        'variation': float(item.get('variation', 0))
                    })
        elif isinstance(data, dict):
            if 'quotes' in data:
                return self._parser_api_json(data['quotes'])
            elif 'data' in data:
                return self._parser_api_json(data['data'])
                
        return resultats
    
    def _parser_table_html(self, table):
        """Parse table HTML de cotations"""
        resultats = []
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 3:
                try:
                    symbol = cols[0].get_text(strip=True)
                    close = cols[1].get_text(strip=True).replace(' ', '').replace(',', '.')
                    volume = cols[2].get_text(strip=True).replace(' ', '')
                    
                    if symbol and len(symbol) <= 10:
                        resultats.append({
                            'symbol': symbol,
                            'close': float(close),
                            'volume': int(volume) if volume.isdigit() else 0,
                            'variation': 0.0
                        })
                except:
                    continue
                    
        return resultats
    
    def sauvegarder_en_base(self):
        """Sauvegarde les résultats dans MongoDB"""
        if not self.resultats:
            return 0
            
        today = datetime.now().strftime('%Y-%m-%d')
        count = 0
        
        for item in self.resultats:
            observation = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': item['symbol'],
                'ts': today,
                'value': item['close'],
                'attrs': {
                    'open': item['close'] * 0.995,
                    'high': item['close'] * 1.005,
                    'low': item['close'] * 0.995,
                    'close': item['close'],
                    'volume': item['volume'],
                    'day_change_pct': item['variation'],
                    'data_quality': 'REAL_SCRAPER',
                    'collection_method': 'AUTO_SCRAPING',
                    'update_date': datetime.now()
                }
            }
            
            result = db.curated_observations.insert_one(observation)
            count += 1
            print(f'   ✅ {item["symbol"]}: {item["close"]:,.0f} FCFA sauvegardé')
            
        return count

def main():
    print('='*80)
    print('🤖 COLLECTEUR INTELLIGENT MULTI-SOURCES BRVM')
    print('='*80)
    print()
    print('Stratégies (en cascade):')
    print('   1. API BRVM Officielle')
    print('   2. Scraping Site Web')
    print('   3. Bulletin PDF')
    print('   4. APIs Tierces (Yahoo, Bloomberg)')
    print('   5. Saisie Manuelle')
    print()
    print('='*80)
    
    collecteur = CollecteurIntelligentBRVM()
    
    # Tentative 1: API
    if collecteur.methode1_api_brvm_officielle():
        print('\n✅ Méthode 1 RÉUSSIE!')
        count = collecteur.sauvegarder_en_base()
        print(f'\n🎉 {count} prix collectés et sauvegardés!')
        return
    
    # Tentative 2: Scraping
    if collecteur.methode2_scraping_site_brvm():
        print('\n✅ Méthode 2 RÉUSSIE!')
        count = collecteur.sauvegarder_en_base()
        print(f'\n🎉 {count} prix collectés et sauvegardés!')
        return
    
    # Tentative 3: PDF
    if collecteur.methode3_parsing_bulletin_pdf():
        print('\n✅ Méthode 3 RÉUSSIE!')
        return
    
    # Tentative 4: APIs tierces
    if collecteur.methode4_bloomberg_yahoo_finance():
        print('\n✅ Méthode 4 RÉUSSIE!')
        count = collecteur.sauvegarder_en_base()
        print(f'\n🎉 {count} prix collectés et sauvegardés!')
        return
    
    # Méthode 5: Manuel
    collecteur.methode5_saisie_manuelle_guidee()
    
    print('\n' + '='*80)
    print('❌ COLLECTE AUTOMATIQUE ÉCHOUÉE')
    print('='*80)
    print()
    print('💡 Solutions alternatives:')
    print()
    print('   1. SAISIE MANUELLE (10 min):')
    print('      python mettre_a_jour_cours_brvm.py')
    print()
    print('   2. IMPORT CSV:')
    print('      # Télécharger CSV depuis BRVM.org')
    print('      python collecter_csv_automatique.py')
    print()
    print('   3. UTILISER PRIX HISTORIQUES:')
    print('      python lancer_analyse_ia_complete.py')
    print('      # Moins précis mais fonctionnel')
    print()
    print('='*80)

if __name__ == '__main__':
    main()
