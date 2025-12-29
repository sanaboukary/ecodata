#!/usr/bin/env python3
"""
🔥 SCRAPER BRVM AVEC SELENIUM (JavaScript rendering)
Récupère les VRAIES données du site officiel BRVM
"""
import sys
import os
import time
from datetime import datetime

print("="*80)
print("🔥 SCRAPER BRVM - VERSION SELENIUM (Données RÉELLES)")
print("="*80)
print()

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    
    print("✅ Bibliothèques Selenium chargées")
    
except ImportError as e:
    print(f"❌ ERREUR: {e}")
    print()
    print("Installation requise:")
    print("  .venv/Scripts/pip.exe install selenium webdriver-manager")
    sys.exit(1)

# Configuration Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')  # Mode sans interface
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--ignore-certificate-errors')

print("\n1️⃣  Initialisation du navigateur Chrome...")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("✅ Navigateur Chrome initialisé")
    
except Exception as e:
    print(f"❌ Erreur initialisation: {e}")
    print()
    print("Solution alternative: Utiliser Edge/Firefox ou saisie manuelle")
    print("  python mettre_a_jour_cours_REELS_22dec.py")
    sys.exit(1)

print("\n2️⃣  Connexion au site BRVM...")
url = "https://www.brvm.org/fr/investir/cours-et-cotations"

try:
    driver.get(url)
    print(f"✅ Page chargée: {url}")
    
    # Attendre que la page charge (max 10s)
    print("\n3️⃣  Attente du chargement JavaScript...")
    time.sleep(5)  # Laisser le temps au JS de s'exécuter
    
    # Sauvegarder HTML pour analyse
    html_file = f"brvm_selenium_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"✅ HTML sauvegardé: {html_file}")
    
    # Chercher les éléments du tableau de cotations
    print("\n4️⃣  Recherche des cours dans le tableau...")
    
    # Essayer plusieurs sélecteurs possibles
    selectors = [
        "table.table-striped tbody tr",
        "table.cotations tbody tr",
        "table tbody tr",
        "div.cours-actions tr",
        "div.cotations tr"
    ]
    
    rows = []
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 0:
                rows = elements
                print(f"✅ {len(rows)} lignes trouvées avec sélecteur: {selector}")
                break
        except:
            continue
    
    if len(rows) == 0:
        print("❌ Aucune ligne de cours trouvée")
        print()
        print("📋 SOLUTIONS:")
        print("  1. Vérifier brvm_selenium_*.html pour voir la structure")
        print("  2. Le site nécessite peut-être une authentification")
        print("  3. Utiliser la saisie manuelle:")
        print("     python mettre_a_jour_cours_REELS_22dec.py")
        driver.quit()
        sys.exit(1)
    
    # Extraire les données
    print(f"\n5️⃣  Extraction des cours...")
    data = []
    
    for row in rows[:10]:  # Tester sur les 10 premières lignes
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                symbol = cells[0].text.strip()
                price_text = cells[1].text.strip().replace(',', '').replace(' ', '')
                variation_text = cells[2].text.strip().replace('%', '').replace(',', '.')
                
                if symbol and price_text:
                    try:
                        price = float(price_text)
                        variation = float(variation_text) if variation_text else 0.0
                        
                        data.append({
                            'symbol': symbol,
                            'close': price,
                            'variation': variation
                        })
                        
                        print(f"  ✅ {symbol:<12} {price:>10,.0f} FCFA ({variation:+.2f}%)")
                    except ValueError:
                        continue
        except Exception as e:
            continue
    
    print()
    print("="*80)
    
    if len(data) > 0:
        print(f"✅ SUCCÈS: {len(data)} cours récupérés")
        print("="*80)
        print()
        
        # Vérifier ECOC
        ecoc = next((d for d in data if 'ECOC' in d['symbol']), None)
        if ecoc:
            print(f"🔍 ECOC trouvé: {ecoc['close']:,.0f} FCFA ({ecoc['variation']:+.2f}%)")
        
        print()
        print("📋 PROCHAINES ÉTAPES:")
        print("  1. Adapter le scraper avec les sélecteurs corrects")
        print("  2. Importer ces données dans MongoDB")
        print("  3. Générer les recommandations avec données RÉELLES")
        
    else:
        print(f"❌ Aucune donnée extraite")
        print("="*80)
        print()
        print("📋 SOLUTION IMMÉDIATE:")
        print("  Saisie manuelle des cours (5-10 minutes):")
        print("  python mettre_a_jour_cours_REELS_22dec.py")
    
    driver.quit()
    print()
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    driver.quit()

print("="*80)
print()
