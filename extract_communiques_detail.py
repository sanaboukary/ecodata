#!/usr/bin/env python3
"""Extraction détaillée des communiqués"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.brvm.org/fr/search/node/communique"

response = requests.get(url, verify=False, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

print("="*80)
print("EXTRACTION COMMUNIQUÉS")
print("="*80)

# Chercher tous les H3 (titres des résultats)
h3_tags = soup.find_all('h3', class_=re.compile('title'))
print(f"\n{len(h3_tags)} résultats trouvés\n")

communiques = []

for i, h3 in enumerate(h3_tags[:20], 1):  # 20 premiers
    # Titre
    link = h3.find('a', href=True)
    if not link:
        continue
    
    title = link.get_text(strip=True)
    href = link.get('href')
    
    if not href.startswith('http'):
        href = f"https://www.brvm.org{href}"
    
    # Chercher date et infos dans le parent
    parent = h3.find_parent(['li', 'div', 'article'])
    
    date_elem = None
    snippet = None
    emetteur = None
    
    if parent:
        # Date
        date_elem = parent.find(['time', 'span'], class_=re.compile('date|submitted'))
        
        # Snippet/extrait
        snippet_elem = parent.find(['p', 'div'], class_=re.compile('snippet|search-snippet'))
        if snippet_elem:
            snippet = snippet_elem.get_text(strip=True)
        
        # Chercher émetteur dans le contenu
        if snippet:
            # Pattern: "Emetteur: XXXXX"
            emetteur_match = re.search(r'Emetteur:\s*([A-Z\s]+)', snippet)
            if emetteur_match:
                emetteur = emetteur_match.group(1).strip()
    
    communique = {
        'title': title,
        'url': href,
        'date': date_elem.get_text(strip=True) if date_elem else 'N/A',
        'snippet': snippet[:150] if snippet else 'N/A',
        'emetteur': emetteur or 'N/A'
    }
    
    communiques.append(communique)
    
    print(f"{i}. {title}")
    print(f"   📅 {communique['date']}")
    if emetteur:
        print(f"   🏢 Émetteur: {emetteur}")
    if snippet:
        print(f"   📄 {snippet[:100]}...")
    print(f"   🔗 {href}")
    print()

# Statistiques
print("="*80)
print("STATISTIQUES")
print("="*80)

# Classifier par type
types = {
    'exercice': 0,
    'dividende': 0,
    'suspension': 0,
    'assemblée': 0,
    'résultats': 0,
    'ifrs': 0,
    'autres': 0
}

for comm in communiques:
    text_lower = (comm['title'] + ' ' + comm['snippet']).lower()
    
    if 'exercice' in text_lower:
        types['exercice'] += 1
    elif 'dividende' in text_lower:
        types['dividende'] += 1
    elif 'suspension' in text_lower:
        types['suspension'] += 1
    elif 'assemblée' in text_lower or 'assemblee' in text_lower:
        types['assemblée'] += 1
    elif 'résultat' in text_lower or 'resultat' in text_lower:
        types['résultats'] += 1
    elif 'ifrs' in text_lower:
        types['ifrs'] += 1
    else:
        types['autres'] += 1

print(f"\nTotal communiqués: {len(communiques)}")
print("\nTypes:")
for typ, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  • {typ}: {count}")
