#!/usr/bin/env python3
"""Extraction détaillée des rapports sociétés"""

import requests
from bs4 import BeautifulSoup

url = "https://www.brvm.org/fr/rapports-societes-cotees"

print("="*80)
print("EXTRACTION DÉTAILLÉE DES RAPPORTS")
print("="*80)

response = requests.get(url, verify=False, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Chercher le tableau principal des rapports
main_table = soup.find('table', class_='views-table')

if main_table:
    print("\n✅ Tableau principal trouvé")
    
    # Headers
    headers = main_table.find_all('th')
    header_texts = [th.get_text(strip=True) for th in headers]
    print(f"\nColonnes: {header_texts}")
    
    # Rows
    tbody = main_table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"\n📊 {len(rows)} rapports trouvés\n")
        
        print("="*80)
        print("LISTE DES RAPPORTS")
        print("="*80)
        
        for i, row in enumerate(rows[:15], 1):
            cells = row.find_all('td')
            
            if len(cells) >= 3:
                code = cells[0].get_text(strip=True)
                emetteur_cell = cells[1]
                description = cells[2].get_text(strip=True)
                
                # Extraire le nom de l'émetteur et le lien
                link = emetteur_cell.find('a', href=True)
                if link:
                    emetteur = link.get_text(strip=True)
                    href = link.get('href')
                    
                    # Normaliser l'URL
                    if href.startswith('/'):
                        href = f"https://www.brvm.org{href}"
                    
                    print(f"\n{i}. {code} - {emetteur}")
                    print(f"   📄 {description}")
                    print(f"   🔗 {href}")
                else:
                    emetteur = emetteur_cell.get_text(strip=True)
                    print(f"\n{i}. {code} - {emetteur}")
                    print(f"   📄 {description}")
                    print(f"   ⚠️  Pas de lien direct")
        
        # Statistiques
        print("\n" + "="*80)
        print("STATISTIQUES")
        print("="*80)
        
        # Compter les rapports par type
        types_rapport = {}
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                desc = cells[2].get_text(strip=True)
                types_rapport[desc] = types_rapport.get(desc, 0) + 1
        
        print(f"\nTypes de rapports:")
        for typ, count in sorted(types_rapport.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {typ}: {count}")
else:
    print("\n❌ Tableau principal non trouvé")
    
    # Plan B: chercher toutes les structures de type liste/grille
    print("\nRecherche alternative...")
    
    # Chercher les divs avec classe views
    view_content = soup.find('div', class_=re.compile('view-content'))
    if view_content:
        print("✅ Conteneur view-content trouvé")
        
        # Chercher tous les éléments de type "row"
        items = view_content.find_all(['tr', 'div'], class_=re.compile('views-row'))
        print(f"   {len(items)} items trouvés")
