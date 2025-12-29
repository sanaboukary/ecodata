#!/usr/bin/env python
"""
Explorer la page Publications Officielles pour trouver les communiqués
"""
import requests
from bs4 import BeautifulSoup
import re
import urllib3

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def explore_publications_page():
    print("🔍 Exploration de la page Publications Officielles BRVM\n")
    print("=" * 80)
    
    # URL de la page publications officielles
    url = "https://www.brvm.org/fr/publications-officielles"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"✅ Status: {response.status_code}")
        print(f"📏 Taille: {len(response.text)} caractères\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher les catégories
        print("📋 CATÉGORIES DISPONIBLES:")
        print("-" * 80)
        
        # Chercher les options du select
        selects = soup.find_all('select')
        for select in selects:
            options = select.find_all('option')
            if options:
                print(f"\nSelect trouvé ({len(options)} options):")
                for opt in options:
                    value = opt.get('value', '')
                    text = opt.get_text(strip=True)
                    print(f"  • {text} → {value}")
        
        # Chercher les liens de catégories
        print("\n📂 LIENS DE CATÉGORIES:")
        print("-" * 80)
        
        category_links = soup.find_all('a', href=re.compile(r'/(categorie|category|type)'))
        for link in category_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if text:
                print(f"  • {text} → {href}")
        
        # Chercher "communiqué" dans la page
        print("\n🔎 RECHERCHE DE 'COMMUNIQUÉ' DANS LA PAGE:")
        print("-" * 80)
        
        page_text = response.text.lower()
        if 'communiqué' in page_text or 'communique' in page_text:
            # Trouver les contextes
            contexts = []
            for match in re.finditer(r'.{0,100}communiqu[ée].{0,100}', page_text, re.IGNORECASE):
                contexts.append(match.group())
            
            print(f"✅ Trouvé {len(contexts)} occurrences de 'communiqué'\n")
            for i, ctx in enumerate(contexts[:5], 1):
                print(f"{i}. ...{ctx}...")
                print()
        else:
            print("❌ Aucune occurrence de 'communiqué' trouvée")
        
        # Chercher tous les types de publications mentionnés
        print("\n📊 TYPES DE PUBLICATIONS MENTIONNÉS:")
        print("-" * 80)
        
        types = set()
        for text in [
            'assemblée générale', 'assemblee generale',
            'bulletin officiel', 
            'cotation',
            'dividende',
            'opération corporate', 'operation corporate',
            'résultats financiers', 'resultats financiers',
            'communiqué', 'communique',
            'avis',
            'rapport',
            'actualité', 'actualite'
        ]:
            if text in page_text:
                types.add(text)
        
        for typ in sorted(types):
            print(f"  ✓ {typ}")
        
        # Chercher des filtres ou boutons
        print("\n🎛️ FILTRES ET CONTRÔLES:")
        print("-" * 80)
        
        buttons = soup.find_all(['button', 'input'], type=['submit', 'button'])
        for btn in buttons:
            text = btn.get_text(strip=True) or btn.get('value', '')
            if text:
                print(f"  • {text}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 80)
    
    # Tester l'URL avec le paramètre catégorie
    print("\n🧪 Test des URLs avec paramètres de catégorie\n")
    
    test_urls = [
        "https://www.brvm.org/fr/publications-officielles?categorie=communique",
        "https://www.brvm.org/fr/publications-officielles?type=communique",
        "https://www.brvm.org/fr/publications-officielles?category=communique",
        "https://www.brvm.org/fr/publications-officielles/communique",
        "https://www.brvm.org/fr/communiques",
        "https://www.brvm.org/fr/avis-communiques",
    ]
    
    for test_url in test_urls:
        try:
            r = requests.get(test_url, headers=headers, timeout=10, verify=False)
            print(f"{'✅' if r.status_code == 200 else '❌'} {r.status_code} - {test_url}")
        except Exception as e:
            print(f"❌ Erreur - {test_url}")

if __name__ == "__main__":
    explore_publications_page()
