#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COLLECTE RAPIDE BRVM - Sans Django, démarrage instantané
Test rapide de la stratégie Selenium avancée
"""

import sys
import os

# Fix encodage
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 80)
print("🚀 TEST RAPIDE - Stratégie Selenium Avancée BRVM")
print("=" * 80)
print()

# Test imports
print("📦 Vérification des modules...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait as Wait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    import pandas as pd
    import time
    print("✅ Tous les modules disponibles")
except ImportError as e:
    print(f"❌ Module manquant: {e}")
    print("\nInstallez avec: pip install -r requirements_collecteur.txt")
    sys.exit(1)

print()
print("🌐 Configuration Chrome...")

# Configuration Chrome headless
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

print("✅ Options configurées")
print()
print("🚗 Lancement ChromeDriver...")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("✅ ChromeDriver démarré")
except Exception as e:
    print(f"❌ Erreur ChromeDriver: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("🎯 COLLECTE EN COURS")
print("=" * 80)
print()

# Test URL FR
url = "https://www.brvm.org/fr/cours-actions/0"
print(f"📡 Connexion à: {url}")

try:
    driver.get(url)
    print("✅ Page chargée")
    
    # Attendre les tables
    print("⏳ Attente des tables...")
    Wait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    time.sleep(1)
    
    print("✅ Tables détectées")
    
    # Lire avec pandas
    print("📊 Lecture des données...")
    dfs = pd.read_html(driver.page_source, thousands=" ", decimal=",")
    
    total_rows = sum(len(df) for df in dfs)
    print(f"✅ {len(dfs)} table(s) lue(s), {total_rows} lignes total")
    
    # Afficher aperçu
    if dfs:
        print()
        print("=" * 80)
        print("📋 APERÇU DES DONNÉES")
        print("=" * 80)
        print()
        
        for i, df in enumerate(dfs[:2], 1):
            print(f"Table {i}:")
            print(df.head(10).to_string())
            print()
    
    # Fermer driver
    driver.quit()
    
    print("=" * 80)
    print("✅ TEST RÉUSSI")
    print("=" * 80)
    print()
    print("Le collecteur complet devrait fonctionner !")
    print("Lancez: python collecteur_brvm_ultra_robuste.py")
    
except Exception as e:
    driver.quit()
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
