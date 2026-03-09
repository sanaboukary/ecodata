#!/usr/bin/env python3
"""
🔍 TEST CONNECTIVITÉ API WORLD BANK
Vérifie si l'API World Bank est accessible et répond correctement
"""
import requests
import time
from datetime import datetime

def test_api_worldbank():
    """Test complet de l'API World Bank"""
    print("\n" + "="*80)
    print("🔍 TEST CONNECTIVITÉ API WORLD BANK")
    print("="*80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = []
    
    # Test 1: Endpoint de base
    print("1️⃣  Test endpoint de base...")
    try:
        url = "https://api.worldbank.org/v2/country/CI/indicator/SP.POP.TOTL"
        params = {
            'format': 'json',
            'per_page': 1,
            'date': '2020'
        }
        
        start = time.time()
        response = requests.get(url, params=params, timeout=10)
        duration = time.time() - start
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    print(f"   ✅ Succès - Code: {response.status_code} - Temps: {duration:.2f}s")
                    print(f"   📊 Données reçues: {len(data[1])} observations")
                    tests.append(('Endpoint de base', True, duration))
                else:
                    print(f"   ⚠️  Réponse vide - Code: {response.status_code}")
                    tests.append(('Endpoint de base', False, duration))
            except Exception as e:
                print(f"   ❌ Erreur JSON: {e}")
                tests.append(('Endpoint de base', False, duration))
        else:
            print(f"   ❌ Échec - Code: {response.status_code}")
            tests.append(('Endpoint de base', False, duration))
            
    except requests.Timeout:
        print(f"   ❌ Timeout après 10s")
        tests.append(('Endpoint de base', False, 10))
    except requests.ConnectionError as e:
        print(f"   ❌ Erreur de connexion: {e}")
        tests.append(('Endpoint de base', False, 0))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('Endpoint de base', False, 0))
    
    print()
    
    # Test 2: Requête multi-pays
    print("2️⃣  Test requête multi-pays (CI;SN;BJ)...")
    try:
        url = "https://api.worldbank.org/v2/country/CI;SN;BJ/indicator/NY.GDP.MKTP.CD"
        params = {
            'format': 'json',
            'per_page': 100,
            'date': '2020:2022'
        }
        
        start = time.time()
        response = requests.get(url, params=params, timeout=15)
        duration = time.time() - start
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    print(f"   ✅ Succès - Code: {response.status_code} - Temps: {duration:.2f}s")
                    print(f"   📊 Données reçues: {len(data[1])} observations")
                    tests.append(('Multi-pays', True, duration))
                else:
                    print(f"   ⚠️  Réponse vide")
                    tests.append(('Multi-pays', False, duration))
            except Exception as e:
                print(f"   ❌ Erreur JSON: {e}")
                tests.append(('Multi-pays', False, duration))
        else:
            print(f"   ❌ Échec - Code: {response.status_code}")
            tests.append(('Multi-pays', False, duration))
            
    except requests.Timeout:
        print(f"   ❌ Timeout après 15s")
        tests.append(('Multi-pays', False, 15))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('Multi-pays', False, 0))
    
    print()
    
    # Test 3: Période étendue (1960-2026)
    print("3️⃣  Test période étendue (1960:2026)...")
    try:
        url = "https://api.worldbank.org/v2/country/CI/indicator/SP.POP.TOTL"
        params = {
            'format': 'json',
            'per_page': 100,
            'date': '1960:2026'
        }
        
        start = time.time()
        response = requests.get(url, params=params, timeout=15)
        duration = time.time() - start
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    print(f"   ✅ Succès - Code: {response.status_code} - Temps: {duration:.2f}s")
                    print(f"   📊 Données reçues: {len(data[1])} observations")
                    
                    # Vérifier la structure des données
                    if data[1]:
                        sample = data[1][0]
                        print(f"   📋 Exemple: Pays={sample.get('country', {}).get('value')}, "
                              f"Année={sample.get('date')}, Valeur={sample.get('value')}")
                    
                    tests.append(('Période étendue', True, duration))
                else:
                    print(f"   ⚠️  Réponse vide")
                    tests.append(('Période étendue', False, duration))
            except Exception as e:
                print(f"   ❌ Erreur JSON: {e}")
                print(f"   📄 Réponse brute: {response.text[:200]}")
                tests.append(('Période étendue', False, duration))
        else:
            print(f"   ❌ Échec - Code: {response.status_code}")
            print(f"   📄 Réponse: {response.text[:200]}")
            tests.append(('Période étendue', False, duration))
            
    except requests.Timeout:
        print(f"   ❌ Timeout après 15s")
        tests.append(('Période étendue', False, 15))
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('Période étendue', False, 0))
    
    print()
    
    # Test 4: Liste des indicateurs disponibles
    print("4️⃣  Test liste des indicateurs...")
    try:
        url = "https://api.worldbank.org/v2/indicator"
        params = {
            'format': 'json',
            'per_page': 5
        }
        
        start = time.time()
        response = requests.get(url, params=params, timeout=10)
        duration = time.time() - start
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    print(f"   ✅ Succès - Code: {response.status_code} - Temps: {duration:.2f}s")
                    print(f"   📊 Indicateurs reçus: {len(data[1])}")
                    tests.append(('Liste indicateurs', True, duration))
                else:
                    print(f"   ⚠️  Réponse vide")
                    tests.append(('Liste indicateurs', False, duration))
            except Exception as e:
                print(f"   ❌ Erreur JSON: {e}")
                tests.append(('Liste indicateurs', False, duration))
        else:
            print(f"   ❌ Échec - Code: {response.status_code}")
            tests.append(('Liste indicateurs', False, duration))
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        tests.append(('Liste indicateurs', False, 0))
    
    print()
    
    # Test 5: Connexion internet générale
    print("5️⃣  Test connexion internet (Google DNS)...")
    try:
        start = time.time()
        response = requests.get("https://www.google.com", timeout=5)
        duration = time.time() - start
        
        if response.status_code == 200:
            print(f"   ✅ Internet OK - Temps: {duration:.2f}s")
            tests.append(('Connexion internet', True, duration))
        else:
            print(f"   ⚠️  Code: {response.status_code}")
            tests.append(('Connexion internet', False, duration))
            
    except Exception as e:
        print(f"   ❌ Pas de connexion internet: {e}")
        tests.append(('Connexion internet', False, 0))
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80 + "\n")
    
    succes = sum(1 for _, ok, _ in tests if ok)
    total = len(tests)
    
    print(f"{'Test':<25} │ {'Statut':<10} │ {'Temps (s)':<12}")
    print(f"{'-'*25} │ {'-'*10} │ {'-'*12}")
    
    for nom, ok, duree in tests:
        statut = "✅ OK" if ok else "❌ ÉCHEC"
        temps = f"{duree:.2f}s" if duree > 0 else "N/A"
        print(f"{nom:<25} │ {statut:<10} │ {temps:<12}")
    
    print("\n" + "="*80)
    print(f"RÉSULTAT: {succes}/{total} tests réussis ({succes/total*100:.0f}%)")
    
    if succes == total:
        print("✅ API World Bank OPÉRATIONNELLE")
    elif succes >= total - 1:
        print("⚠️  API World Bank PARTIELLEMENT ACCESSIBLE")
    else:
        print("❌ API World Bank INACCESSIBLE ou PROBLÈME DE CONNEXION")
    
    print("="*80 + "\n")
    
    # Recommandations
    if succes < total:
        print("💡 RECOMMANDATIONS:\n")
        
        if not tests[4][1]:  # Connexion internet
            print("   1. Vérifier votre connexion internet")
            print("   2. Vérifier les paramètres proxy/firewall")
        
        if tests[4][1] and not tests[0][1]:  # Internet OK mais API KO
            print("   1. L'API World Bank pourrait être temporairement indisponible")
            print("   2. Vérifier si votre IP est bloquée (rate limiting)")
            print("   3. Attendre 15-30 minutes et réessayer")
            print("   4. Essayer avec un VPN si problème persiste")
        
        if tests[0][1] and not tests[2][1]:  # Base OK mais période étendue KO
            print("   1. Réduire la taille des requêtes (périodes plus courtes)")
            print("   2. Utiliser des blocs de 10 ans au lieu de 67 ans")
            print("   3. Augmenter les délais entre requêtes (rate limiting)")
        
        print()

if __name__ == '__main__':
    test_api_worldbank()
