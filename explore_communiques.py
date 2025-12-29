#!/usr/bin/env python3
"""Exploration des communiqués BRVM via recherche"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.brvm.org/fr/search/node/communique"

print("="*80)
print("EXPLORATION: Communiqués BRVM (via recherche)")
print("="*80)

response = requests.get(url, verify=False, timeout=30)
print(f"\n✅ Status: {response.status_code}")
print(f"✅ Taille: {len(response.content)} bytes")

soup = BeautifulSoup(response.text, 'html.parser')

# 1. Chercher les résultats de recherche
print("\n" + "="*80)
print("RÉSULTATS DE RECHERCHE")
print("="*80)

# Chercher les items de résultats
result_items = soup.find_all(['div', 'li', 'article'], class_=re.compile('search-result|result|item'))
print(f"Items trouvés: {len(result_items)}")

# Chercher aussi les liens contenant "communique"
all_links = soup.find_all('a', href=True)
communique_links = [l for l in all_links if 'communique' in l.get('href', '').lower() or 'communiqué' in l.get_text().lower()]

print(f"Liens avec 'communiqué': {len(communique_links)}")

# Afficher les premiers résultats
print("\n📋 Premiers résultats:")

for i, item in enumerate(result_items[:10], 1):
    title = item.find(['h3', 'h2', 'a'])
    if title:
        title_text = title.get_text(strip=True)
        print(f"\n{i}. {title_text[:100]}")
        
        # Date
        date = item.find(['time', 'span'], class_=re.compile('date'))
        if date:
            print(f"   📅 {date.get_text(strip=True)}")
        
        # Snippet/extrait
        snippet = item.find(['p', 'div'], class_=re.compile('snippet|excerpt|teaser'))
        if snippet:
            print(f"   📄 {snippet.get_text(strip=True)[:150]}")
        
        # Lien
        link = item.find('a', href=True) or title.find('a', href=True) if title.name != 'a' else title
        if link and hasattr(link, 'get'):
            href = link.get('href')
            if not href.startswith('http'):
                href = f"https://www.brvm.org{href}"
            print(f"   🔗 {href}")

# Si pas de structure claire, chercher les titres directement
if len(result_items) < 5:
    print("\n" + "="*80)
    print("RECHERCHE ALTERNATIVE: Titres de page")
    print("="*80)
    
    h3_tags = soup.find_all('h3')
    print(f"Titres H3 trouvés: {len(h3_tags)}")
    
    for i, h3 in enumerate(h3_tags[:10], 1):
        text = h3.get_text(strip=True)
        if text:
            print(f"\n{i}. {text}")
            
            # Chercher lien associé
            link = h3.find('a', href=True)
            if link:
                href = link.get('href')
                if not href.startswith('http'):
                    href = f"https://www.brvm.org{href}"
                print(f"   🔗 {href}")

# Chercher PDFs
print("\n" + "="*80)
print("DOCUMENTS PDF DANS LES RÉSULTATS")
print("="*80)

pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
print(f"PDFs trouvés: {len(pdf_links)}")

for i, link in enumerate(pdf_links[:15], 1):
    href = link.get('href')
    text = link.get_text(strip=True) or 'PDF'
    
    if not href.startswith('http'):
        href = f"https://www.brvm.org{href}"
    
    print(f"\n{i}. {text[:70]}")
    print(f"   {href}")

# Chercher info sur les communiqués
print("\n" + "="*80)
print("ANALYSE MOTS-CLÉS DANS LES RÉSULTATS")
print("="*80)

text_content = soup.get_text().lower()

keywords = {
    'communiqué': text_content.count('communiqué') + text_content.count('communique'),
    'suspension': text_content.count('suspension'),
    'dividende': text_content.count('dividende'),
    'assemblée': text_content.count('assemblée') + text_content.count('assemblee'),
    'résultat': text_content.count('résultat') + text_content.count('resultat'),
    'exercice': text_content.count('exercice'),
    'ecobank': text_content.count('ecobank'),
    'crepmf': text_content.count('crepmf'),
}

print("Occurrences:")
for kw, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  • {kw}: {count}")
