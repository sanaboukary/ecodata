"""
Test des nouveaux endpoints Marketplace améliorés
Teste les années disponibles et datasets par source
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def tester_years(source):
    """Test récupération années"""
    print(f"\n{'='*60}")
    print(f"📅 ANNÉES DISPONIBLES - {source.upper()}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/marketplace/get-years/?source={source}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            years = data.get('years', [])
            source_name = data.get('source', '')
            
            print(f"✅ Source MongoDB: {source_name}")
            print(f"📊 Nombre d'années: {len(years)}")
            
            if years:
                print(f"📆 Années disponibles:")
                # Afficher par groupe de 10
                for i in range(0, len(years), 10):
                    group = years[i:i+10]
                    print(f"   {', '.join(map(str, group))}")
            else:
                print("⚠️ Aucune année disponible")
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("Assurez-vous que le serveur Django est lancé: python manage.py runserver")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def tester_datasets(source, year='all'):
    """Test récupération datasets"""
    print(f"\n{'='*60}")
    print(f"📊 DATASETS DISPONIBLES - {source.upper()} ({year})")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/marketplace/get-datasets/?source={source}"
    if year != 'all':
        url += f"&year={year}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            datasets = data.get('datasets', [])
            total = data.get('total', 0)
            
            print(f"✅ Total datasets: {total}")
            print(f"📋 Détails:\n")
            
            for i, ds in enumerate(datasets[:10], 1):  # Afficher top 10
                print(f"{i}. {ds['name']}")
                print(f"   Code: {ds['code']}")
                print(f"   Observations: {ds['count']}")
                print(f"   Période: {ds['first_date']} → {ds['last_date']}")
                print(f"   Exemple: {ds['sample_key']} = {ds['sample_value']}")
                print()
            
            if total > 10:
                print(f"... et {total - 10} autres datasets")
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def tester_download_filtre(source, year, format_type='csv'):
    """Test téléchargement avec filtre année"""
    print(f"\n{'='*60}")
    print(f"💾 TEST TÉLÉCHARGEMENT - {source.upper()} {year}")
    print(f"{'='*60}")
    
    # 1. Préparer
    url_prepare = f"{BASE_URL}/marketplace/prepare/"
    data_prepare = {
        'source': source,
        'period': 'all',
        'format': format_type
    }
    
    try:
        response = requests.post(url_prepare, json=data_prepare)
        
        if response.status_code == 200:
            result = response.json()
            count = result.get('count', 0)
            
            print(f"✅ Préparation réussie")
            print(f"📊 Observations: {count}")
            
            if count > 0:
                # 2. Télécharger
                url_download = f"{BASE_URL}/marketplace/download/"
                url_download += f"?source={source}&period=all&format={format_type}"
                
                response_dl = requests.get(url_download)
                
                if response_dl.status_code == 200:
                    # Afficher premières lignes du CSV
                    content = response_dl.text
                    lines = content.split('\n')[:5]
                    
                    print(f"✅ Téléchargement réussi")
                    print(f"📄 Premières lignes:\n")
                    for line in lines:
                        if line.strip():
                            print(f"   {line[:100]}...")  # 100 premiers caractères
                else:
                    print(f"❌ Erreur téléchargement: {response_dl.status_code}")
            else:
                print("⚠️ Aucune donnée à télécharger")
        else:
            print(f"❌ Erreur préparation: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    print("="*60)
    print("🧪 TEST MARKETPLACE AMÉLIORÉ")
    print("="*60)
    
    # Sources à tester
    sources = ['brvm', 'worldbank', 'imf', 'un_sdg', 'afdb']
    
    for source in sources:
        # Test 1: Récupérer années disponibles
        tester_years(source)
        
        # Test 2: Récupérer datasets (toutes années)
        tester_datasets(source, 'all')
        
        # Test 3: Récupérer datasets pour année spécifique
        if source == 'worldbank':
            tester_datasets(source, '2023')
        elif source == 'imf':
            tester_datasets(source, '2024')
        elif source == 'brvm':
            tester_datasets(source, '2026')
    
    # Test 4: Téléchargement avec nouveau format
    print("\n" + "="*60)
    print("💾 TESTS DE TÉLÉCHARGEMENT AVEC NOUVEAU FORMAT")
    print("="*60)
    
    tester_download_filtre('worldbank', '2023', 'csv')
    tester_download_filtre('imf', '2024', 'csv')
    tester_download_filtre('brvm', '2026', 'csv')
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60)
