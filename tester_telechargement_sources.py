#!/usr/bin/env python3
"""
Tester le téléchargement de données par source
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 80)
print("🧪 TEST TÉLÉCHARGEMENT DONNÉES PAR SOURCE")
print("=" * 80)

sources_to_test = ['brvm', 'worldbank', 'imf', 'un_sdg', 'afdb']

for source in sources_to_test:
    print(f"\n📊 Test source: {source.upper()}")
    print("-" * 80)
    
    # 1. Préparer téléchargement (preview)
    try:
        response = requests.post(
            f"{BASE_URL}/marketplace/prepare/",
            json={
                'source': source,
                'period': '30d',
                'format': 'csv'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Preview OK:")
                print(f"   Observations: {data.get('count', 0):,}")
                print(f"   Taille estimée: {data.get('estimated_size', 'N/A')}")
                print(f"   Aperçu: {len(data.get('preview', []))} lignes")
                
                if data.get('count', 0) > 0:
                    # 2. Télécharger vraiment
                    download_url = f"{BASE_URL}/marketplace/download/?source={source}&period=30d&format=csv"
                    dl_response = requests.get(download_url)
                    
                    if dl_response.status_code == 200:
                        content_length = len(dl_response.content)
                        print(f"✅ Téléchargement OK: {content_length:,} bytes")
                        
                        # Vérifier contenu CSV
                        lines = dl_response.text.split('\n')
                        print(f"   Lignes CSV: {len(lines)}")
                        if lines:
                            print(f"   En-tête: {lines[0][:100]}...")
                    else:
                        print(f"❌ Téléchargement échoué: {dl_response.status_code}")
                else:
                    print(f"⚠️  Aucune donnée disponible pour cette source")
            else:
                print(f"❌ Preview échoué: {data.get('error', 'Erreur inconnue')}")
        else:
            print(f"❌ Requête échouée: {response.status_code}")
            print(f"   Réponse: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

print("\n" + "=" * 80)
print("✅ TESTS TERMINÉS")
print("=" * 80)
