#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspecte la structure du site BRVM pour comprendre comment collecter les 47 actions
"""

import sys
import io
import time
import json

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

print("=" * 100)
print("🔍 INSPECTION STRUCTURE SITE BRVM")
print("=" * 100)
print()

# Configuration Chrome
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    url = "https://www.brvm.org/fr/cours-actions/0"
    print(f"📡 Connexion: {url}")
    driver.get(url)
    time.sleep(3)
    
    # Fermer cookies
    try:
        btns = driver.find_elements(By.TAG_NAME, "button")
        for b in btns:
            if "accept" in (b.text or "").lower():
                b.click()
                time.sleep(0.5)
                break
    except:
        pass
    
    # Scroll pour charger tout
    print("📜 Scroll pour charger contenu...")
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    print()
    print("=" * 100)
    print("📊 ANALYSE DES TABLES HTML")
    print("=" * 100)
    
    # Trouver toutes les tables
    tables = driver.find_elements(By.TAG_NAME, "table")
    print(f"Nombre de tables trouvées: {len(tables)}")
    print()
    
    for idx, table in enumerate(tables):
        print(f"\n--- TABLE {idx + 1} ---")
        try:
            # Headers
            headers = table.find_elements(By.TAG_NAME, "th")
            if headers:
                header_texts = [h.text.strip() for h in headers if h.text.strip()]
                print(f"Colonnes ({len(header_texts)}): {header_texts}")
            
            # Lignes
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"Nombre de lignes: {len(rows)}")
            
            # Première ligne de données
            if len(rows) > 1:
                cells = rows[1].find_elements(By.TAG_NAME, "td")
                if cells:
                    sample = [c.text.strip()[:30] for c in cells[:5]]
                    print(f"Échantillon données: {sample}")
        except Exception as e:
            print(f"Erreur inspection table: {e}")
    
    print()
    print("=" * 100)
    print("🔍 RECHERCHE API/AJAX")
    print("=" * 100)
    
    # Intercepter requêtes réseau
    print("\nRecherche de requêtes AJAX/API...")
    
    # Vérifier si API REST
    script = """
    return window.performance.getEntries()
        .filter(e => e.initiatorType === 'xmlhttprequest' || e.initiatorType === 'fetch')
        .map(e => e.name);
    """
    
    xhr_requests = driver.execute_script(script)
    if xhr_requests:
        print(f"\n✅ {len(xhr_requests)} requêtes AJAX détectées:")
        for req in xhr_requests:
            print(f"   • {req}")
    else:
        print("\n❌ Aucune requête AJAX détectée")
    
    print()
    print("=" * 100)
    print("🌐 INSPECTION DOM")
    print("=" * 100)
    
    # Chercher divs/classes spécifiques
    print("\nRecherche d'éléments avec 'action', 'stock', 'cours'...")
    
    elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'action') or contains(@class, 'stock') or contains(@class, 'cours')]")
    print(f"Éléments trouvés: {len(elements)}")
    
    for elem in elements[:5]:
        try:
            print(f"  - {elem.tag_name}.{elem.get_attribute('class')}: {elem.text[:50]}")
        except:
            pass
    
    print()
    print("=" * 100)
    print("📋 RÉSUMÉ")
    print("=" * 100)
    
    # Comptage total lignes
    total_rows = sum(len(t.find_elements(By.TAG_NAME, "tr")) - 1 for t in tables)
    print(f"\nTotal lignes de données (approx): {total_rows}")
    print(f"Objectif: 47 actions")
    
    if total_rows < 20:
        print("\n⚠️ PROBLÈME: Pas assez de lignes détectées")
        print("Le site utilise probablement:")
        print("  1. Pagination AJAX (clics nécessaires)")
        print("  2. API REST cachée")
        print("  3. Lazy loading non déclenché")
    
    # Sauvegarder source page
    print("\n💾 Sauvegarde source HTML...")
    with open("brvm_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Source sauvegardée: brvm_source.html")

except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()

print()
print("=" * 100)
