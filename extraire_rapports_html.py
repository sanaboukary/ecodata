#!/usr/bin/env python3
"""
Extrait les rapports sociétés depuis le HTML sauvegardé
"""

from bs4 import BeautifulSoup
import json
from datetime import datetime

# Charger le HTML le plus récent
html_file = 'brvm_rapports_20251222_131055.html'

with open(html_file, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

print("="*80)
print("EXTRACTION RAPPORTS SOCIETES BRVM")
print("="*80)
print()

# Trouver toutes les tables
tables = soup.find_all('table')
print(f"Tables trouvees: {len(tables)}")
print()

rapports = []

for i, table in enumerate(tables, 1):
    print(f"TABLE {i}:")
    
    # Trouver headers
    headers_row = table.find('thead')
    if headers_row:
        headers = [th.get_text(strip=True) for th in headers_row.find_all('th')]
        print(f"  Headers: {headers}")
    
    # Trouver lignes de données
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"  Lignes de donnees: {len(rows)}")
        
        # Si c'est la table des rapports (beaucoup de lignes)
        if len(rows) > 20:
            print(f"\n  EXTRACTION DE LA TABLE DES RAPPORTS:")
            
            for row in rows:  # Tous les rapports
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Structure: Code | Emetteur | Description
                    code = cells[0].get_text(strip=True)
                    emetteur = cells[1].get_text(strip=True)
                    description = cells[2].get_text(strip=True)
                    
                    # Chercher lien PDF dans description
                    link = cells[2].find('a')
                    pdf_url = ''
                    if link and 'href' in link.attrs:
                        pdf_url = link['href']
                        if not pdf_url.startswith('http'):
                            pdf_url = f"https://www.brvm.org{pdf_url}"
                    
                    # Afficher 5 premiers
                    if len(rapports) < 5:
                        print(f"    - {emetteur:<35} | Code: {code:<10} | PDF: {'✓' if pdf_url else '✗'}")
                    
                    rapports.append({
                        'code': code,
                        'emetteur': emetteur,
                        'description': description,
                        'pdf_url': pdf_url,
                        'type': 'rapport_societe',
                        'date_collecte': datetime.now().isoformat()
                    })
            
            if len(rows) > 5:
                print(f"    ... et {len(rows)-5} autres rapports")
    
    print()

# Sauvegarder
if rapports:
    filename = f'rapports_brvm_extraits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(rapports, f, ensure_ascii=False, indent=2)
    
    print("="*80)
    print(f"✅ {len(rapports)} rapports extraits")
    print(f"   Fichier: {filename}")
    print("="*80)
else:
    print("❌ Aucun rapport extrait")
