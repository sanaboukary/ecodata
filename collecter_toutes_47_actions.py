#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COLLECTE COMPLÈTE DES 47 ACTIONS BRVM - 29 DÉCEMBRE 2025
Collecte individuelle de chaque action pour avoir le dataset complet
"""

import os
import sys
import time
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("❌ Selenium non installé. Installation: pip install selenium webdriver-manager")
    sys.exit(1)

# Liste des 47 actions officielles BRVM
ACTIONS_BRVM_47 = [
    # Bancaire & Finance (16)
    'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'CABC', 'CBIBF',
    'ETIT', 'NSBC', 'SABC', 'SGBC', 'SIBC', 'SICB', 'SLBC', 'SMBC',
    
    # Industrie & Distribution (12)
    'CFAC', 'CIAC', 'FTSC', 'NEIC', 'NTLC', 'PALC', 'PRSC', 'SDCC',
    'SEMC', 'SHEC', 'SICC', 'UNXC',
    
    # Services Publics & Transport (9)
    'ABJC', 'CIE', 'ECOC', 'ONTBF', 'SDSC', 'SIVC', 'SNTS', 'SOGC', 'UNLC',
    
    # Agriculture & Mines (7)
    'ORGT', 'PHCC', 'SCRC', 'STAC', 'STBC', 'SVOC', 'TTLC',
    
    # Autres (3)
    'ORAC', 'TPCI', 'TTLS'
]

def collecter_action_brvm(driver, symbol, date_collecte):
    """Collecter les données d'une action spécifique"""
    try:
        # URL de recherche pour l'action
        search_url = f"https://www.brvm.org/fr/search/node/{symbol}"
        driver.get(search_url)
        time.sleep(3)
        
        # Chercher le lien vers la page de l'action
        try:
            # Cliquer sur le premier résultat qui contient le symbole
            link = driver.find_element(By.XPATH, f"//a[contains(text(), '{symbol}')]")
            link.click()
            time.sleep(3)
        except:
            # Si pas de lien trouvé, retourner None
            return None
        
        # Extraire les données de la page de l'action
        try:
            # Chercher le prix
            price_selectors = [
                ".field-name-field-cours-action .field-item",
                ".cours-actuel",
                "span.price",
                ".stock-price"
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = elem.text.strip()
                    # Nettoyer et convertir
                    price = float(price_text.replace(' ', '').replace(',', '.').replace('FCFA', ''))
                    break
                except:
                    continue
            
            if price is None:
                return None
            
            # Chercher la variation
            variation = 0
            var_selectors = [
                ".field-name-field-variation .field-item",
                ".variation",
                "span.variation"
            ]
            
            for selector in var_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    var_text = elem.text.strip().replace('%', '').replace('+', '').replace(' ', '')
                    variation = float(var_text)
                    break
                except:
                    continue
            
            return {
                'symbol': symbol,
                'price': price,
                'variation': variation,
                'date': date_collecte
            }
            
        except Exception as e:
            print(f"   ⚠️  Erreur extraction données {symbol}: {e}")
            return None
            
    except Exception as e:
        print(f"   ❌ Erreur collecte {symbol}: {e}")
        return None

def collecter_via_page_cotations(driver, date_collecte):
    """Méthode alternative: collecter depuis la page de cotations"""
    url = "https://www.brvm.org/fr/investir/cours-et-cotations"
    print(f"\n🌐 Chargement page cotations: {url}")
    driver.get(url)
    time.sleep(10)
    
    data = []
    
    # Chercher toutes les lignes du tableau
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        print(f"   📊 {len(rows)} lignes trouvées")
        
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    symbol_text = cells[0].text.strip()
                    price_text = cells[1].text.strip()
                    var_text = cells[2].text.strip()
                    
                    # Nettoyer le symbole
                    symbol = symbol_text.replace('.BC', '').replace('.BF', '').strip()
                    
                    # Nettoyer le prix
                    price = float(price_text.replace(' ', '').replace(',', ''))
                    
                    # Nettoyer la variation
                    variation = float(var_text.replace('%', '').replace('+', '').replace(' ', ''))
                    
                    data.append({
                        'symbol': symbol,
                        'price': price,
                        'variation': variation,
                        'date': date_collecte
                    })
            except:
                continue
        
    except Exception as e:
        print(f"   ❌ Erreur parsing tableau: {e}")
    
    return data

def sauvegarder_mongodb(data_list, date_collecte):
    """Sauvegarder les cours dans MongoDB"""
    if not data_list:
        print("\n❌ Aucune donnée à sauvegarder")
        return
    
    _, db = get_mongo_db()
    
    print(f"\n💾 Sauvegarde de {len(data_list)} cours dans MongoDB...")
    
    inserted = 0
    updated = 0
    
    for data in data_list:
        # Créer l'observation
        obs = {
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': data['symbol'],
            'ts': date_collecte,
            'value': float(data['price']),
            'attrs': {
                'close': float(data['price']),
                'variation': float(data['variation']),
                'data_quality': 'REAL_SCRAPER',
                'collected_at': datetime.now().isoformat(),
                'source_url': 'https://www.brvm.org'
            }
        }
        
        # Upsert (insert or update)
        result = db.curated_observations.update_one(
            {
                'source': 'BRVM',
                'key': data['symbol'],
                'ts': date_collecte
            },
            {'$set': obs},
            upsert=True
        )
        
        if result.upserted_id:
            inserted += 1
        else:
            updated += 1
    
    print(f"\n✅ Sauvegarde terminée:")
    print(f"   • Nouvelles observations: {inserted}")
    print(f"   • Mises à jour: {updated}")
    print(f"   • Total: {len(data_list)} cours RÉELS")

def main():
    print("="*80)
    print("COLLECTE COMPLÈTE DES 47 ACTIONS BRVM")
    print("="*80)
    
    date_collecte = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📅 Date: {date_collecte}")
    print(f"🎯 Objectif: {len(ACTIONS_BRVM_47)} actions")
    
    # Configuration Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    print("\n🚀 Lancement ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    
    try:
        # Méthode 1: Collecter depuis la page cotations (rapide)
        print("\n📊 MÉTHODE 1: Page cotations globale")
        data_cotations = collecter_via_page_cotations(driver, date_collecte)
        
        # Identifier les actions manquantes
        symbols_collectes = {d['symbol'] for d in data_cotations}
        manquantes = [s for s in ACTIONS_BRVM_47 if s not in symbols_collectes]
        
        print(f"\n✅ Page cotations: {len(data_cotations)} actions")
        print(f"⚠️  Actions manquantes: {len(manquantes)}")
        
        # Méthode 2: Collecter individuellement les manquantes
        if manquantes:
            print(f"\n🔍 MÉTHODE 2: Collecte individuelle des {len(manquantes)} actions manquantes")
            data_individuelles = []
            
            for i, symbol in enumerate(manquantes, 1):
                print(f"   [{i}/{len(manquantes)}] Collecte {symbol}...", end=' ')
                data = collecter_action_brvm(driver, symbol, date_collecte)
                if data:
                    data_individuelles.append(data)
                    print(f"✅ {data['price']:.0f} FCFA")
                else:
                    print("❌")
                time.sleep(2)  # Pause entre requêtes
            
            # Combiner les deux méthodes
            all_data = data_cotations + data_individuelles
        else:
            all_data = data_cotations
        
        print(f"\n" + "="*80)
        print(f"📊 RÉSULTAT FINAL: {len(all_data)}/{len(ACTIONS_BRVM_47)} actions collectées")
        print("="*80)
        
        # Sauvegarder
        if all_data:
            sauvegarder_mongodb(all_data, date_collecte)
            
            # Afficher résumé
            print(f"\n📋 COURS COLLECTÉS:")
            for data in sorted(all_data, key=lambda x: x['symbol']):
                arrow = '▲' if data['variation'] >= 0 else '▼'
                print(f"   {data['symbol']:10s}: {data['price']:8,.0f} FCFA {arrow} {data['variation']:+6.2f}%")
        
    finally:
        print("\n🔒 Fermeture Chrome...")
        driver.quit()
        print("✅ Terminé")

if __name__ == '__main__':
    main()
