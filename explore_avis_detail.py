#!/usr/bin/env python3
"""Exploration détaillée de /fr/avis"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.brvm.org/fr/avis"

print("="*80)
print("EXPLORATION DÉTAILLÉE: /fr/avis")
print("="*80)

response = requests.get(url, verify=False, timeout=30)
print(f"\n✅ Status: {response.status_code}")
print(f"✅ Taille: {len(response.content)} bytes")

soup = BeautifulSoup(response.text, 'html.parser')

# 1. Chercher tableau
print("\n" + "="*80)
print("STRUCTURE TABLEAU")
print("="*80)

tables = soup.find_all('table')
print(f"Nombre de tableaux: {len(tables)}")

for idx, table in enumerate(tables, 1):
    print(f"\nTableau #{idx}:")
    
    headers = table.find_all('th')
    if headers:
        header_texts = [h.get_text(strip=True) for h in headers]
        print(f"  Colonnes: {header_texts}")
    
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
    else:
        rows = table.find_all('tr')[1:]  # Skip header
    
    print(f"  Lignes: {len(rows)}")
    
    if idx == 1 and len(header_texts) > 2:  # Premier tableau avec contenu
        print(f"\n  📋 Aperçu des {min(10, len(rows))} premières lignes:")
        for i, row in enumerate(rows[:10], 1):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                cell_texts = [c.get_text(strip=True) for c in cells[:4]]  # 4 premières colonnes
                print(f"\n  {i}. {' | '.join(cell_texts)}")
                
                # Chercher lien
                link = row.find('a', href=True)
                if link:
                    href = link.get('href')
                    if not href.startswith('http'):
                        href = f"https://www.brvm.org{href}"
                    print(f"     🔗 {href}")

# 2. Si pas de tableau, chercher structure liste
if not tables or len(tables) <= 1:
    print("\n" + "="*80)
    print("RECHERCHE STRUCTURE ALTERNATIVE")
    print("="*80)
    
    # Chercher articles/divs
    items = soup.find_all(['article', 'div'], class_=re.compile('node|item|avis|view-content'))
    print(f"Items trouvés: {len(items)}")
    
    for i, item in enumerate(items[:5], 1):
        title = item.find(['h2', 'h3', 'a'])
        if title:
            print(f"\n{i}. {title.get_text(strip=True)}")

# 3. Chercher tous les PDFs
print("\n" + "="*80)
print("DOCUMENTS PDF")
print("="*80)

pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
print(f"PDFs trouvés: {len(pdf_links)}")

for i, link in enumerate(pdf_links[:15], 1):
    href = link.get('href')
    text = link.get_text(strip=True) or link.get('title', 'Sans titre')
    
    if not href.startswith('http'):
        href = f"https://www.brvm.org{href}"
    
    print(f"\n{i}. {text[:70]}")
    print(f"   {href}")

# 4. Chercher patterns de mots-clés
print("\n" + "="*80)
print("ANALYSE CONTENU (Mots-clés)")
print("="*80)

text_content = soup.get_text().lower()

keywords = {
    'suspension': text_content.count('suspension'),
    'dividende': text_content.count('dividende'),
    'assemblée': text_content.count('assemblée') + text_content.count('assemblee'),
    'capital': text_content.count('capital'),
    'convocation': text_content.count('convocation'),
    'résultat': text_content.count('résultat') + text_content.count('resultat'),
    'avis': text_content.count('avis'),
}

print("Occurrences:")
for kw, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  • {kw}: {count}")
