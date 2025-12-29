#!/usr/bin/env python3
"""
🔍 EXPLORER API BRVM POUR DONNÉES HISTORIQUES
Teste différents endpoints possibles
"""

import requests
from datetime import datetime, timedelta

ENDPOINTS = [
    # Endpoints potentiels API BRVM
    'https://www.brvm.org/fr/cours',
    'https://www.brvm.org/fr/investir/cours-et-cotations',
    'https://www.brvm.org/fr/api/stocks',
    'https://www.brvm.org/fr/api/cotations',
    'https://www.brvm.org/sites/default/files/cours.json',
]

def tester_endpoint(url):
    """Teste si un endpoint retourne des données exploitables"""
    
    print(f"  Test: {url}")
    
    try:
        response = requests.get(url, timeout=10, verify=False)
        
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f"    Type: {content_type}")
            print(f"    Taille: {len(response.content)} bytes")
            
            # Essayer JSON
            if 'json' in content_type.lower():
                try:
                    data = response.json()
                    print(f"    ✓ JSON valide")
                    print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                    return True
                except:
                    print(f"    ✗ JSON invalide")
            
            # Vérifier si HTML contient data
            if 'html' in content_type.lower():
                html = response.text
                if 'cours' in html.lower() or 'cotation' in html.lower():
                    print(f"    ~ HTML avec mots-clés")
                    return None  # Nécessite parsing HTML
        
        return False
    
    except Exception as e:
        print(f"    ✗ Erreur: {e}")
        return False

def explorer_api_brvm():
    """Explore les endpoints possibles"""
    
    print("=" * 80)
    print("EXPLORATION API BRVM")
    print("=" * 80)
    print()
    
    print("🔍 Test des endpoints potentiels...\n")
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    endpoints_valides = []
    
    for url in ENDPOINTS:
        resultat = tester_endpoint(url)
        
        if resultat:
            endpoints_valides.append(url)
        
        print()
    
    print("=" * 80)
    
    if endpoints_valides:
        print(f"✓ {len(endpoints_valides)} endpoint(s) valide(s)")
        for url in endpoints_valides:
            print(f"  - {url}")
    else:
        print("✗ Aucun endpoint JSON trouvé")
        print()
        print("ALTERNATIVES:")
        print("  1. Scraping HTML: python scripts/connectors/brvm_scraper_production.py")
        print("  2. Bulletins PDF: python parser_bulletins_brvm_pdf.py")
        print("  3. Saisie manuelle: Modifier CSV et importer")
    
    print()

if __name__ == '__main__':
    explorer_api_brvm()
