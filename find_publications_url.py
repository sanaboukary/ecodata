#!/usr/bin/env python
"""
Trouver l'URL exacte de la page Publications Officielles
"""
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_publications_url():
    print("🔍 Recherche de l'URL des Publications Officielles\n")
    print("=" * 80)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Commencer par la page d'accueil pour trouver les liens
    print("📍 Étape 1: Explorer la page d'accueil BRVM\n")
    
    try:
        response = requests.get("https://www.brvm.org/fr", headers=headers, timeout=10, verify=False)
        print(f"✅ Page d'accueil: Status {response.status_code}\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher tous les liens contenant "publication"
        print("📂 Liens contenant 'publication':")
        print("-" * 80)
        
        publication_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if 'publication' in href.lower() or 'publication' in text.lower():
                full_url = href if href.startswith('http') else f"https://www.brvm.org{href}"
                publication_links.append((text, full_url))
                print(f"  • {text[:50]:<50} → {full_url}")
        
        # Tester chaque lien trouvé
        print("\n\n🧪 Test des liens trouvés:")
        print("=" * 80)
        
        for text, url in publication_links[:10]:  # Limiter à 10
            try:
                r = requests.get(url, headers=headers, timeout=10, verify=False)
                status = "✅" if r.status_code == 200 else "❌"
                print(f"{status} {r.status_code} - {text[:40]}")
                
                if r.status_code == 200:
                    # Vérifier si c'est la bonne page
                    if 'bulletin officiel' in r.text.lower() and 'catégorie' in r.text.lower():
                        print(f"\n🎯 TROUVÉ: {url}")
                        print(f"   Cette page contient 'Bulletin Officiel' ET 'Catégorie'\n")
                        
                        # Analyser rapidement
                        s = BeautifulSoup(r.text, 'html.parser')
                        selects = s.find_all('select')
                        if selects:
                            print(f"   📋 {len(selects)} select(s) trouvé(s)")
                            for sel in selects[:2]:
                                opts = sel.find_all('option')
                                print(f"      → {len(opts)} options")
                        
                        return url
                        
            except Exception as e:
                print(f"❌ Erreur - {text[:40]}")
        
    except Exception as e:
        print(f"❌ Erreur page d'accueil: {e}")
    
    # Si pas trouvé, essayer des URLs spécifiques
    print("\n\n🎯 Essai d'URLs spécifiques:")
    print("=" * 80)
    
    specific_urls = [
        "https://www.brvm.org/fr/bulletins-officiels",
        "https://www.brvm.org/fr/bulletin-officiel-cote",
        "https://www.brvm.org/fr/boc",
        "https://www.brvm.org/fr/investisseurs/bulletins",
        "https://www.brvm.org/fr/investisseurs/boc",
        "https://www.brvm.org/fr/node/18",  # Node ID souvent utilisé par Drupal
        "https://www.brvm.org/fr/node/19",
        "https://www.brvm.org/fr/node/20",
    ]
    
    for url in specific_urls:
        try:
            r = requests.get(url, headers=headers, timeout=10, verify=False)
            status = "✅" if r.status_code == 200 else "❌"
            print(f"{status} {r.status_code} - {url}")
            
            if r.status_code == 200 and 'bulletin officiel' in r.text.lower():
                print(f"\n🎯 CANDIDAT: {url}")
                
                # Vérifier les catégories
                if 'assemblée' in r.text.lower() and 'dividende' in r.text.lower():
                    print(f"   ✅ Cette page contient les catégories attendues!")
                    return url
                    
        except:
            pass
    
    print("\n❌ URL des publications officielles non trouvée automatiquement")
    return None

if __name__ == "__main__":
    url = find_publications_url()
    if url:
        print(f"\n\n{'='*80}")
        print(f"✅ URL FINALE: {url}")
        print(f"{'='*80}")
