"""
Scraper BRVM amélioré - Navigation intelligente
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import datetime

def scraper_brvm_selenium():
    """Scraper BRVM avec navigation intelligente"""
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    
    print("=" * 80)
    print("SCRAPER BRVM SELENIUM - NAVIGATION INTELLIGENTE")
    print("=" * 80)
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Page d'accueil
        print("\n🌐 Chargement page d'accueil BRVM...")
        driver.get('https://www.brvm.org')
        time.sleep(3)
        
        # Chercher le menu "Investir" ou "Marché"
        print("🔍 Recherche du menu Investir/Marché...")
        menu_selectors = [
            "//a[contains(text(), 'Investir')]",
            "//a[contains(text(), 'Marché')]",
            "//a[contains(text(), 'Cours')]",
            "//li[contains(@class, 'menu')]//a[contains(text(), 'Investir')]",
        ]
        
        menu_found = False
        for selector in menu_selectors:
            try:
                menu = driver.find_element(By.XPATH, selector)
                print(f"✅ Menu trouvé: {menu.text}")
                menu.click()
                time.sleep(2)
                menu_found = True
                break
            except:
                continue
        
        if not menu_found:
            print("❌ Menu Investir non trouvé, recherche directe...")
        
        # Chercher tous les liens dans la page
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        cours_links = []
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                text = link.text.lower()
                if href and ('cours' in href.lower() or 'cotation' in href.lower() or 
                             'cours' in text or 'cotation' in text or 'marche' in text):
                    cours_links.append({
                        'text': link.text.strip(),
                        'href': href
                    })
            except:
                pass
        
        print(f"\n📋 {len(cours_links)} liens potentiels trouvés:")
        for link in cours_links[:10]:
            print(f"  - {link['text'][:50]} → {link['href']}")
        
        # Essayer chaque lien
        results = []
        for link in cours_links[:5]:  # Top 5 seulement
            try:
                print(f"\n🔗 Test: {link['href']}")
                driver.get(link['href'])
                time.sleep(3)
                
                # Chercher des tableaux avec des données financières
                tables = driver.find_elements(By.TAG_NAME, 'table')
                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    if len(rows) > 2:  # Table avec données
                        print(f"  ✅ Table trouvée: {len(rows)} lignes")
                        
                        # Extraire les données
                        for row in rows[:5]:
                            cells = row.find_elements(By.TAG_NAME, 'td')
                            if len(cells) >= 2:
                                print(f"    - {' | '.join([c.text for c in cells[:4]])}")
                
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
        
        # Méthode alternative : JavaScript pour obtenir les données
        print("\n⚡ Tentative extraction via JavaScript...")
        try:
            script = """
            var tables = document.querySelectorAll('table');
            var data = [];
            tables.forEach(function(table) {
                var rows = table.querySelectorAll('tr');
                rows.forEach(function(row) {
                    var cells = row.querySelectorAll('td, th');
                    if (cells.length > 0) {
                        var rowData = [];
                        cells.forEach(function(cell) {
                            rowData.push(cell.textContent.trim());
                        });
                        data.push(rowData);
                    }
                });
            });
            return data;
            """
            data = driver.execute_script(script)
            if data:
                print(f"✅ {len(data)} lignes extraites via JavaScript")
                for row in data[:10]:
                    if len(row) > 1:
                        print(f"  {row}")
        except Exception as e:
            print(f"❌ Erreur JavaScript: {e}")
    
    finally:
        driver.quit()
        print("\n" + "=" * 80)
        print("FIN DE L'ANALYSE")
        print("=" * 80)

if __name__ == "__main__":
    scraper_brvm_selenium()
