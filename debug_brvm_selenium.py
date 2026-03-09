"""
Script de debug pour analyser la structure du site BRVM
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def debug_brvm_structure():
    """Analyser la structure du site BRVM pour trouver les données"""
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    print("🚗 Lancement Chrome headless...")
    driver = webdriver.Chrome(options=options)
    
    try:
        # Essayer différentes URLs
        urls_to_test = [
            'https://www.brvm.org',
            'https://www.brvm.org/fr',
            'https://www.brvm.org/fr/marche',
        ]
        
        for url in urls_to_test:
            print(f"\n📡 Test: {url}")
            try:
                driver.get(url)
                time.sleep(3)
                
                # Chercher les liens contenant "cours" ou "cotation"
                links = driver.find_elements(By.TAG_NAME, 'a')
                relevant_links = []
                
                for link in links:
                    try:
                        text = link.text.strip().lower()
                        href = link.get_attribute('href')
                        if href and ('cours' in text or 'cotation' in text or 'marche' in text):
                            relevant_links.append({'text': link.text.strip()[:50], 'href': href})
                    except:
                        pass
                
                if relevant_links:
                    print(f"  ✅ {len(relevant_links)} liens trouvés:")
                    for link in relevant_links[:5]:
                        print(f"    - {link['text']} → {link['href']}")
                    
                    # Sauvegarder la page
                    filename = url.replace('https://', '').replace('/', '_') + '.html'
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    print(f"  💾 Page sauvegardée: {filename}")
                    
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
        
        # Essayer la page spécifique des cours
        print("\n📈 Test direct: /fr/investir/cours-et-cotations")
        try:
            driver.get('https://www.brvm.org/fr/investir/cours-et-cotations')
            time.sleep(5)
            
            # Chercher les tables
            tables = driver.find_elements(By.TAG_NAME, 'table')
            print(f"  📊 {len(tables)} table(s) trouvée(s)")
            
            # Chercher les éléments avec des données numériques
            elements_with_numbers = driver.find_elements(By.XPATH, "//*[contains(text(), 'FCFA') or contains(text(), '%')]")
            print(f"  💰 {len(elements_with_numbers)} éléments avec FCFA ou %")
            
            if elements_with_numbers:
                print("  Exemples:")
                for elem in elements_with_numbers[:3]:
                    print(f"    - {elem.text[:80]}")
            
            # Sauvegarder
            with open('brvm_cours_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("  💾 Page sauvegardée: brvm_cours_page.html")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    finally:
        driver.quit()
        print("\n✅ Analyse terminée")

if __name__ == "__main__":
    debug_brvm_structure()
