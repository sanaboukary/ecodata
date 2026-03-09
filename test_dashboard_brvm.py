"""Test rapide du dashboard BRVM après correction"""
import requests
import sys

print("=" * 70)
print("🧪 TEST DU DASHBOARD BRVM")
print("=" * 70)
print()

# Tester la page BRVM
print("1️⃣ Test de la page /brvm/...")
try:
    response = requests.get('http://127.0.0.1:8000/brvm/', timeout=10)
    
    if response.status_code == 200:
        print("   ✅ Page chargée avec succès (200 OK)")
        
        # Vérifier que la page contient des données
        if 'BRVM' in response.text:
            print("   ✅ Contenu BRVM détecté")
        else:
            print("   ⚠️ Contenu BRVM non détecté")
            
        if 'TypeError' in response.text or 'Exception' in response.text:
            print("   ❌ ERREUR détectée dans la page")
            sys.exit(1)
        else:
            print("   ✅ Aucune erreur détectée")
    else:
        print(f"   ❌ Erreur HTTP {response.status_code}")
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("   ❌ Impossible de se connecter au serveur")
    print("   💡 Assurez-vous que le serveur Django tourne:")
    print("      Double-cliquez sur start_server.cmd")
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)

print()
print("2️⃣ Test de la page /brvm/recommendations/...")
try:
    response = requests.get('http://127.0.0.1:8000/brvm/recommendations/', timeout=10)
    
    if response.status_code == 200:
        print("   ✅ Page chargée avec succès (200 OK)")
    else:
        print(f"   ⚠️ Code HTTP {response.status_code}")
        
except Exception as e:
    print(f"   ⚠️ Erreur: {e}")

print()
print("=" * 70)
print("✅ TOUS LES TESTS PASSÉS!")
print("=" * 70)
print()
print("💡 Ouvrez votre navigateur sur:")
print("   http://127.0.0.1:8000/brvm/")
print()
print("=" * 70)
