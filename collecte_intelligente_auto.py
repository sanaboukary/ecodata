"""
COLLECTE INTELLIGENTE AUTOMATISÉE BRVM - SELENIUM
🎯 Objectif: Recommandations trading avec données RÉELLES
🔴 Politique: ZÉRO TOLÉRANCE pour données simulées
"""
import sys
import os
from datetime import datetime, time as dt_time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

# Configuration Django
sys.path.insert(0, os.path.abspath('.'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


class CollecteurBRVMIntelligent:
    """
    Collecteur intelligent pour données BRVM
    - Scraping Selenium automatisé
    - Vérification qualité données
    - Sauvegarde MongoDB
    - Gestion erreurs robuste
    """
    
    def __init__(self):
        self.url_brvm = "https://www.brvm.org/fr/investir/cours-et-cotations"
        self.driver = None
        self.client = None
        self.db = None
        
    def setup_chrome(self):
        """Configuration Chrome optimisée"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        return chrome_options
    
    def scraper_cours_brvm(self):
        """
        Scraper les cours RÉELS du site BRVM
        Returns: list de dict avec cours ou None si erreur
        """
        print(f"\n{'='*80}")
        print(f"🌐 SCRAPING SITE BRVM - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        data = []
        
        try:
            # Initialiser Chrome
            print("\n🚀 Lancement Chrome...")
            chrome_options = self.setup_chrome()
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Accéder au site
            print(f"📡 Connexion: {self.url_brvm}")
            self.driver.get(self.url_brvm)
            
            # Attendre chargement JavaScript
            print("⏳ Chargement JavaScript...")
            time.sleep(8)
            
            # Sauvegarder HTML pour debug
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_file = f'brvm_auto_{timestamp}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Chercher les tableaux
            print("🔍 Extraction des cours...")
            selectors = [
                "table.cotations tbody tr",
                "table tbody tr",
                ".view-content table tbody tr",
            ]
            
            rows_found = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        rows_found = elements
                        break
                except:
                    continue
            
            if not rows_found:
                print(f"⚠️  Aucune donnée trouvée - HTML sauvegardé: {debug_file}")
                return None
            
            # Parser les lignes
            for row in rows_found:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        symbol_text = cells[0].text.strip()
                        price_text = cells[1].text.strip().replace(' ', '').replace(',', '')
                        var_text = cells[2].text.strip().replace('%', '').replace(',', '.')
                        
                        if symbol_text and price_text:
                            price = float(price_text)
                            variation = float(var_text) if var_text else 0.0
                            
                            if '.' not in symbol_text:
                                symbol_text += '.BC'
                            
                            data.append({
                                'symbol': symbol_text,
                                'close': price,
                                'variation': variation,
                                'volume': 0,
                                'data_quality': 'REAL_SCRAPER',
                                'collecte_datetime': datetime.now().isoformat()
                            })
                except:
                    continue
            
            if data:
                print(f"✅ {len(data)} cours collectés")
                # Afficher Top 3
                top3 = sorted(data, key=lambda x: x['variation'], reverse=True)[:3]
                print("\n📊 Top 3 variations:")
                for d in top3:
                    if d['symbol'] not in ['BRVM-C.BC', 'BRVM-30.BC', 'BRVM-PRES.BC']:
                        print(f"   {d['symbol']:<12} {d['close']:>10,.0f} FCFA ({d['variation']:+.2f}%)")
            
            return data
            
        except Exception as e:
            print(f"❌ ERREUR scraping: {e}")
            return None
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def verifier_qualite_donnees(self, data):
        """
        Vérifier la qualité des données collectées
        """
        if not data or len(data) == 0:
            return False
        
        print(f"\n🔍 VÉRIFICATION QUALITÉ...")
        
        # Vérifications
        checks = {
            'count_ok': len(data) >= 10,  # Au moins 10 actions
            'prices_ok': all(d['close'] > 0 for d in data),
            'variations_ok': all(-20 <= d['variation'] <= 20 for d in data),  # Variations réalistes
            'symbols_ok': all(d['symbol'].endswith('.BC') for d in data),
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}: {result}")
        
        return all(checks.values())
    
    def sauvegarder_mongodb(self, data):
        """
        Sauvegarder les cours dans MongoDB
        """
        if not data:
            return 0
        
        print(f"\n💾 SAUVEGARDE MONGODB...")
        
        try:
            self.client, self.db = get_mongo_db()
            
            today = datetime.now().strftime('%Y-%m-%d')
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
                        'collecte_method': 'SELENIUM_AUTO',
                        'collecte_datetime': datetime.now().isoformat()
                    }
                }
                observations.append(obs)
            
            # Upsert
            inserted = 0
            updated = 0
            
            for obs in observations:
                result = self.db.curated_observations.update_one(
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
            
            print(f"   ✅ {inserted} nouvelles | {updated} mises à jour")
            print(f"   📊 Total: {len(observations)} cours sauvegardés")
            
            return len(observations)
            
        except Exception as e:
            print(f"   ❌ ERREUR sauvegarde: {e}")
            return 0
        
        finally:
            if self.client:
                self.client.close()
    
    def generer_rapport(self, data, saved_count):
        """Générer un rapport de collecte"""
        rapport = {
            'timestamp': datetime.now().isoformat(),
            'success': data is not None and saved_count > 0,
            'cours_collectes': len(data) if data else 0,
            'cours_sauvegardes': saved_count,
            'source': 'BRVM_SELENIUM_AUTO',
            'data_quality': 'REAL_SCRAPER'
        }
        
        if data:
            # Top 5 variations
            top5 = sorted(
                [d for d in data if d['symbol'] not in ['BRVM-C.BC','BRVM-30.BC','BRVM-PRES.BC']],
                key=lambda x: x['variation'],
                reverse=True
            )[:5]
            
            rapport['top_5_variations'] = [
                {
                    'symbol': d['symbol'],
                    'price': d['close'],
                    'variation': d['variation']
                }
                for d in top5
            ]
        
        # Sauvegarder rapport
        filename = f"rapport_collecte_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)
        
        return rapport
    
    def executer_collecte(self):
        """
        Exécuter une collecte complète
        """
        print(f"\n{'='*80}")
        print(f"🎯 COLLECTE INTELLIGENTE BRVM - DÉMARRAGE")
        print(f"{'='*80}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔴 Politique: ZÉRO TOLÉRANCE données simulées")
        print(f"🎯 Objectif: Trading recommandations\n")
        
        # Étape 1: Scraping
        data = self.scraper_cours_brvm()
        
        if not data:
            print(f"\n❌ ÉCHEC SCRAPING - Aucune donnée collectée")
            return {'success': False, 'error': 'Scraping failed'}
        
        # Étape 2: Vérification qualité
        if not self.verifier_qualite_donnees(data):
            print(f"\n⚠️  QUALITÉ INSUFFISANTE - Données rejetées")
            return {'success': False, 'error': 'Quality check failed'}
        
        # Étape 3: Sauvegarde MongoDB
        saved_count = self.sauvegarder_mongodb(data)
        
        # Étape 4: Rapport
        rapport = self.generer_rapport(data, saved_count)
        
        # Afficher résumé
        print(f"\n{'='*80}")
        print(f"✅ COLLECTE TERMINÉE")
        print(f"{'='*80}")
        print(f"\n📊 RÉSUMÉ:")
        print(f"   • Cours collectés: {len(data)}")
        print(f"   • Cours sauvegardés: {saved_count}")
        print(f"   • Qualité: REAL_SCRAPER (site officiel)")
        print(f"   • Date: {datetime.now().strftime('%Y-%m-%d')}")
        
        if rapport.get('top_5_variations'):
            print(f"\n🏆 TOP 5 VARIATIONS:")
            for i, t in enumerate(rapport['top_5_variations'], 1):
                print(f"   {i}. {t['symbol']:<12} {t['price']:>10,.0f} FCFA ({t['variation']:+.2f}%)")
        
        print(f"\n{'='*80}\n")
        
        return rapport


def mode_collecte_unique():
    """Collecte unique immédiate"""
    collecteur = CollecteurBRVMIntelligent()
    rapport = collecteur.executer_collecte()
    
    if rapport['success']:
        print("✅ Prochaine étape: python generer_top5_nlp.py")
    else:
        print("❌ Collecte échouée - Vérifier logs")
    
    return rapport


def mode_collecte_horaire():
    """
    Collecte horaire pendant les heures de marché
    Lundi-Vendredi, 9h-16h
    """
    print(f"\n{'='*80}")
    print(f"🔄 MODE COLLECTE HORAIRE ACTIVÉ")
    print(f"{'='*80}")
    print(f"📅 Planning: Lundi-Vendredi, 9h-16h")
    print(f"⏰ Fréquence: Toutes les heures\n")
    
    collecteur = CollecteurBRVMIntelligent()
    
    while True:
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()  # 0=Lundi, 6=Dimanche
        
        # Vérifier si heure de marché (Lun-Ven 9h-16h)
        if current_day < 5 and 9 <= current_hour < 16:
            print(f"\n⏰ {now.strftime('%Y-%m-%d %H:%M:%S')} - Heure de collecte")
            
            rapport = collecteur.executer_collecte()
            
            if rapport['success']:
                print(f"✅ Collecte réussie - Attente prochaine heure...")
            else:
                print(f"⚠️  Collecte échouée - Réessai dans 15 min...")
                time.sleep(900)  # Attendre 15 min si échec
                continue
            
            # Attendre 1 heure
            time.sleep(3600)
        else:
            print(f"\n💤 Hors heures de marché - Pause jusqu'à demain 9h")
            # Calculer temps jusqu'à prochaine session
            if current_day >= 5:  # Weekend
                next_day = 7 - current_day  # Jours jusqu'à lundi
                wait_seconds = next_day * 24 * 3600 + (9 - current_hour) * 3600
            else:  # En semaine mais hors heures
                if current_hour < 9:
                    wait_seconds = (9 - current_hour) * 3600
                else:
                    wait_seconds = (24 - current_hour + 9) * 3600
            
            print(f"⏰ Prochaine collecte dans {wait_seconds//3600}h")
            time.sleep(wait_seconds)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Collecte intelligente BRVM')
    parser.add_argument('--mode', choices=['unique', 'horaire'], default='unique',
                        help='Mode de collecte (unique ou horaire)')
    
    args = parser.parse_args()
    
    if args.mode == 'unique':
        mode_collecte_unique()
    else:
        mode_collecte_horaire()
