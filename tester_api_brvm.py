#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de différentes URLs/endpoints BRVM pour trouver l'API
"""

import requests
import json

print("🔍 RECHERCHE API BRVM")
print("=" * 80)

# URLs potentielles
urls_test = [
    "https://www.brvm.org/api/actions",
    "https://www.brvm.org/api/cours",
    "https://www.brvm.org/api/stock-prices",
    "https://www.brvm.org/fr/api/cours-actions",
    "https://api.brvm.org/actions",
    "https://api.brvm.org/stocks",
    "https://www.brvm.org/sites/default/files/cours.json",
    "https://www.brvm.org/fr/cours-actions/data",
    "https://www.brvm.org/fr/investir/cours-et-cotations/data",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
}

for url in urls_test:
    try:
        print(f"\nTest: {url}")
        r = requests.get(url, headers=headers, timeout=5)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            print(f"  ✅ SUCCESS!")
            print(f"  Content-Type: {r.headers.get('content-type')}")
            print(f"  Taille: {len(r.content)} bytes")
            
            # Essayer de parser JSON
            try:
                data = r.json()
                print(f"  Format: JSON ({len(data)} items)" if isinstance(data, list) else f"  Format: JSON (objet)")
                print(f"  Aperçu: {str(data)[:200]}")
            except:
                print(f"  Format: HTML/Autre")
                print(f"  Début: {r.text[:150]}")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {str(e)[:50]}")

print("\n" + "=" * 80)
