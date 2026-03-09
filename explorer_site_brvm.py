#!/usr/bin/env python3
"""
🔍 EXPLORATEUR SITE BRVM - Recherche automatique des URLs de publications
"""
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def explorer_site_brvm():
    """Explorer le site BRVM pour trouver les sections publications"""
    
    print("\n" + "="*80)
    print("🔍 EXPLORATION SITE BRVM")
    print("="*80)
    
    base_url = "https://www.brvm.org"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # 1. Page d'accueil pour trouver le menu
    print(f"\n[1] Analyse page d'accueil: {base_url}")
    
    try:
        response = session.get(f"{base_url}/fr", verify=False, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher tous les liens du menu
        liens_menu = soup.find_all('a', href=True)
        
        # Filtrer les liens pertinents
        mots_cles_rapports = ['rapport', 'publication', 'document', 'financier', 'annuel']
        mots_cles_communiques = ['communique', 'presse', 'actualite', 'news']
        mots_cles_bulletins = ['bulletin', 'cotation', 'bourse', 'marche']
        
        print(f"\n📊 LIENS POTENTIELS RAPPORTS:")
        rapports_urls = []
        for link in liens_menu:
            href = link.get('href', '')
            texte = link.get_text(strip=True).lower()
            
            if any(mot in texte or mot in href.lower() for mot in mots_cles_rapports):
                url_complete = href if href.startswith('http') else f"{base_url}{href}"
                print(f"   • {texte[:50]:<50} → {url_complete}")
                rapports_urls.append(url_complete)
        
        print(f"\n📰 LIENS POTENTIELS COMMUNIQUÉS:")
        communiques_urls = []
        for link in liens_menu:
            href = link.get('href', '')
            texte = link.get_text(strip=True).lower()
            
            if any(mot in texte or mot in href.lower() for mot in mots_cles_communiques):
                url_complete = href if href.startswith('http') else f"{base_url}{href}"
                print(f"   • {texte[:50]:<50} → {url_complete}")
                communiques_urls.append(url_complete)
        
        print(f"\n📋 LIENS POTENTIELS BULLETINS:")
        bulletins_urls = []
        for link in liens_menu:
            href = link.get('href', '')
            texte = link.get_text(strip=True).lower()
            
            if any(mot in texte or mot in href.lower() for mot in mots_cles_bulletins):
                url_complete = href if href.startswith('http') else f"{base_url}{href}"
                print(f"   • {texte[:50]:<50} → {url_complete}")
                bulletins_urls.append(url_complete)
        
        # Tester chaque URL trouvée
        print(f"\n" + "="*80)
        print("🧪 TEST DES URLs TROUVÉES")
        print("="*80)
        
        urls_valides = {}
        
        # Tester rapports
        print(f"\n[RAPPORTS] Test {len(set(rapports_urls))} URLs...")
        for url in set(rapports_urls[:5]):  # 5 premières uniques
            try:
                r = session.get(url, verify=False, timeout=15)
                if r.status_code == 200:
                    soup_page = BeautifulSoup(r.content, 'html.parser')
                    nb_pdf = len(soup_page.find_all('a', href=lambda x: x and '.pdf' in x.lower()))
                    print(f"   ✅ {url}")
                    print(f"      → {nb_pdf} liens PDF trouvés")
                    if nb_pdf > 0:
                        urls_valides['rapports'] = url
                        break
                else:
                    print(f"   ❌ {url} (Status {r.status_code})")
            except Exception as e:
                print(f"   ❌ {url} (Erreur: {str(e)[:30]})")
        
        # Tester communiqués
        print(f"\n[COMMUNIQUÉS] Test {len(set(communiques_urls))} URLs...")
        for url in set(communiques_urls[:5]):
            try:
                r = session.get(url, verify=False, timeout=15)
                if r.status_code == 200:
                    soup_page = BeautifulSoup(r.content, 'html.parser')
                    nb_articles = len(soup_page.find_all(['article', 'div'], class_=lambda x: x and 'news' in str(x).lower()))
                    print(f"   ✅ {url}")
                    print(f"      → {nb_articles} articles/news trouvés")
                    if nb_articles > 0 or len(soup_page.find_all('a')) > 10:
                        urls_valides['communiques'] = url
                        break
                else:
                    print(f"   ❌ {url} (Status {r.status_code})")
            except Exception as e:
                print(f"   ❌ {url} (Erreur: {str(e)[:30]})")
        
        # Tester bulletins
        print(f"\n[BULLETINS] Test {len(set(bulletins_urls))} URLs...")
        for url in set(bulletins_urls[:5]):
            try:
                r = session.get(url, verify=False, timeout=15)
                if r.status_code == 200:
                    soup_page = BeautifulSoup(r.content, 'html.parser')
                    nb_pdf = len(soup_page.find_all('a', href=lambda x: x and 'bulletin' in str(x).lower() and '.pdf' in str(x).lower()))
                    print(f"   ✅ {url}")
                    print(f"      → {nb_pdf} bulletins PDF trouvés")
                    if nb_pdf > 0:
                        urls_valides['bulletins'] = url
                        break
                else:
                    print(f"   ❌ {url} (Status {r.status_code})")
            except Exception as e:
                print(f"   ❌ {url} (Erreur: {str(e)[:30]})")
        
        # Résumé final
        print(f"\n" + "="*80)
        print("📝 RÉSUMÉ - URLs VALIDES TROUVÉES")
        print("="*80)
        
        if urls_valides:
            for categorie, url in urls_valides.items():
                print(f"\n{categorie.upper()}:")
                print(f"  {url}")
        else:
            print("\n⚠️  Aucune URL valide trouvée automatiquement")
            print("\nSuggestions :")
            print("  1. Vérifier manuellement sur https://www.brvm.org")
            print("  2. Chercher dans les sections : Données > Publications")
        
        # Générer code Python
        print(f"\n" + "="*80)
        print("💻 CODE PYTHON À UTILISER")
        print("="*80)
        print("\nURLs à mettre dans collecter_publications_brvm.py:\n")
        
        if 'rapports' in urls_valides:
            print(f"url_rapports = \"{urls_valides['rapports']}\"")
        if 'communiques' in urls_valides:
            print(f"url_communiques = \"{urls_valides['communiques']}\"")
        if 'bulletins' in urls_valides:
            print(f"url_bulletins = \"{urls_valides['bulletins']}\"")
        
        print("\n" + "="*80)
        
        return urls_valides
        
    except Exception as e:
        print(f"\n❌ Erreur exploration: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == '__main__':
    explorer_site_brvm()
