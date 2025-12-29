#!/usr/bin/env python
"""
Explorer la vraie page des publications officielles BRVM
"""
import requests
from bs4 import BeautifulSoup
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def explore_real_publications():
    print("🔍 Exploration des Publications Officielles BRVM\n")
    print("=" * 80)
    
    # URL correcte visible dans la capture
    urls_to_try = [
        "https://www.brvm.org/fr/content/publications-officielles-brvm",
        "https://www.brvm.org/fr/publications",
        "https://www.brvm.org/fr/investisseurs/publications-officielles",
        "https://www.brvm.org/fr/content/publications",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    working_url = None
    
    for url in urls_to_try:
        try:
            print(f"Essai: {url}")
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            print(f"  → Status: {response.status_code}")
            
            if response.status_code == 200:
                working_url = url
                print(f"  ✅ Trouvé!\n")
                break
        except Exception as e:
            print(f"  ❌ Erreur: {e}\n")
    
    if not working_url:
        print("❌ Aucune URL fonctionnelle trouvée")
        return
    
    print("=" * 80)
    print(f"\n✅ URL FONCTIONNELLE: {working_url}\n")
    print("=" * 80)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Chercher les catégories dans les select
    print("\n📋 CATÉGORIES DANS LES SELECTS:")
    print("-" * 80)
    
    selects = soup.find_all('select')
    for i, select in enumerate(selects, 1):
        print(f"\nSelect #{i}:")
        select_id = select.get('id', 'N/A')
        select_name = select.get('name', 'N/A')
        print(f"  ID: {select_id}, Name: {select_name}")
        
        options = select.find_all('option')
        for opt in options:
            value = opt.get('value', '')
            text = opt.get_text(strip=True)
            print(f"    • {text}")
            if value and value != text:
                print(f"      (value: {value})")
    
    # Chercher "communiqué" partout
    print("\n\n🔎 RECHERCHE DE 'COMMUNIQUÉ':")
    print("-" * 80)
    
    page_text_lower = response.text.lower()
    
    # Patterns à chercher
    patterns = [
        r'communiqu[ée]',
        r'avis.*communiqu[ée]',
        r'categor.*communiqu[ée]',
    ]
    
    for pattern in patterns:
        matches = list(re.finditer(pattern, page_text_lower))
        if matches:
            print(f"\n✅ Pattern '{pattern}': {len(matches)} occurrences")
            for match in matches[:3]:
                start = max(0, match.start() - 50)
                end = min(len(page_text_lower), match.end() + 50)
                context = response.text[start:end]
                print(f"  ...{context}...")
    
    # Chercher des URLs de catégories
    print("\n\n📂 URLS DE CATÉGORIES:")
    print("-" * 80)
    
    all_links = soup.find_all('a', href=True)
    category_keywords = ['categorie', 'category', 'type', 'filter', 'filtre']
    
    for link in all_links:
        href = link.get('href', '')
        if any(kw in href.lower() for kw in category_keywords):
            text = link.get_text(strip=True)
            print(f"  • {text} → {href}")
    
    # Sauvegarder le HTML pour analyse manuelle
    with open('publications_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print("\n\n💾 HTML sauvegardé dans 'publications_page.html'")
    print(f"📏 Taille totale: {len(response.text)} caractères")
    
    # Chercher les taxonomy terms (Drupal)
    print("\n\n🏷️ TAXONOMIE (si Drupal):")
    print("-" * 80)
    
    taxonomy_patterns = [
        r'taxonomy/term/\d+',
        r'tid=\d+',
        r'term-\d+',
    ]
    
    for pattern in taxonomy_patterns:
        matches = list(re.finditer(pattern, response.text))
        if matches:
            print(f"\n✅ Pattern '{pattern}': {len(matches)} occurrences")
            unique_terms = set([m.group() for m in matches])
            for term in list(unique_terms)[:5]:
                print(f"  • {term}")

if __name__ == "__main__":
    explore_real_publications()
