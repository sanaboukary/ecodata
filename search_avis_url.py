#!/usr/bin/env python3
"""Recherche de la bonne URL pour les avis/communiqués"""

import requests
from bs4 import BeautifulSoup
import re

# Tester différentes URLs possibles
urls_to_test = [
    "https://www.brvm.org/fr/avis-et-communiques",
    "https://www.brvm.org/fr/avis-communiques",
    "https://www.brvm.org/fr/communiques",
    "https://www.brvm.org/fr/avis",
    "https://www.brvm.org/fr/actus-avis",
    "https://www.brvm.org/fr/actualites-avis",
    "https://www.brvm.org/fr/investisseurs/avis",
    "https://www.brvm.org/fr/marche/avis",
]

print("="*80)
print("RECHERCHE URL AVIS ET COMMUNIQUÉS")
print("="*80)

for url in urls_to_test:
    try:
        response = requests.get(url, verify=False, timeout=10)
        status = response.status_code
        size = len(response.content)
        
        if status == 200:
            print(f"\n✅ {url}")
            print(f"   Status: {status} | Taille: {size} bytes")
            
            # Chercher des indicateurs de contenu pertinent
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher mots-clés
            keywords = ['suspension', 'dividende', 'assemblée', 'convocation', 'capital', 'avis']
            text_lower = soup.get_text().lower()
            
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                print(f"   Mots-clés trouvés: {', '.join(found_keywords[:5])}")
            
            # Chercher documents/liens
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
            if pdf_links:
                print(f"   📄 {len(pdf_links)} PDFs trouvés")
        else:
            print(f"❌ {url} - Status: {status}")
    except Exception as e:
        print(f"❌ {url} - Erreur: {e}")

# Chercher dans la page d'accueil
print("\n" + "="*80)
print("RECHERCHE DANS LA PAGE D'ACCUEIL")
print("="*80)

try:
    response = requests.get("https://www.brvm.org/fr", verify=False, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Chercher liens contenant 'avis', 'communique', etc.
    nav_links = soup.find_all('a', href=True)
    
    relevant = []
    for link in nav_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        if any(kw in href.lower() for kw in ['avis', 'communique', 'annonce', 'publication']):
            relevant.append((text, href))
        elif any(kw in text.lower() for kw in ['avis', 'communiqué', 'annonce']):
            relevant.append((text, href))
    
    if relevant:
        print("\n📋 Liens pertinents trouvés:")
        for text, href in set(relevant)[:15]:
            print(f"  • {text[:50]} → {href}")
    else:
        print("\n❌ Aucun lien pertinent trouvé")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
