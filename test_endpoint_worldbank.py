#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de l'endpoint dashboard WorldBank
"""
import requests
import json

try:
    # Appeler l'endpoint du dashboard
    response = requests.get('http://127.0.0.1:8000/worldbank/', timeout=10)
    
    print("=" * 100)
    print("🌐 TEST ENDPOINT DASHBOARD WORLDBANK")
    print("=" * 100)
    print(f"\nURL: http://127.0.0.1:8000/worldbank/")
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        # Extraire les données du contexte HTML si c'est du HTML
        html = response.text
        
        # Chercher les valeurs affichées pour Bénin
        if 'Bénin' in html:
            print("\n✅ Page chargée avec succès")
            
            # Extraire un échantillon du HTML autour de "Bénin"
            idx = html.find('Bénin')
            if idx > -1:
                sample = html[idx:idx+500]
                print(f"\n📄 Extrait HTML (Bénin):")
                print("-" * 100)
                # Nettoyer un peu le HTML
                lines = sample.split('\n')[:10]
                for line in lines:
                    cleaned = line.strip()
                    if cleaned:
                        print(cleaned[:150])
        else:
            print("\n❌ Page ne contient pas 'Bénin'")
            print(f"\nPremiers 500 caractères:")
            print(html[:500])
    else:
        print(f"\n❌ Erreur HTTP {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.ConnectionError:
    print("\n❌ Impossible de se connecter au serveur Django")
    print("Vérifiez que le serveur tourne sur http://127.0.0.1:8000/")
except Exception as e:
    print(f"\n❌ Erreur: {e}")

print("\n" + "=" * 100)
