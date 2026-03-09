"""Test rapide nouveaux endpoints"""
import requests

BASE_URL = "http://127.0.0.1:8000"

print("Test 1: Années WorldBank")
r = requests.get(f"{BASE_URL}/marketplace/get-years/?source=worldbank")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Années: {data.get('years', [])[:10]}")
    print(f"Source: {data.get('source')}")

print("\n" + "="*60)
print("Test 2: Datasets WorldBank 2023")
r = requests.get(f"{BASE_URL}/marketplace/get-datasets/?source=worldbank&year=2023")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Total datasets: {data.get('total')}")
    datasets = data.get('datasets', [])
    for ds in datasets[:3]:
        print(f"\n- {ds['name']}")
        print(f"  Code: {ds['code']}")
        print(f"  Obs: {ds['count']}")

print("\n" + "="*60)
print("Test 3: Téléchargement WorldBank CSV")
r = requests.post(f"{BASE_URL}/marketplace/prepare/", 
                  json={'source': 'worldbank', 'period': '1y', 'format': 'csv'})
print(f"Prepare status: {r.status_code}")
if r.status_code == 200:
    prep_data = r.json()
    print(f"Observations: {prep_data.get('count')}")
    
    # Télécharger
    r_dl = requests.get(f"{BASE_URL}/marketplace/download/?source=worldbank&period=1y&format=csv")
    print(f"Download status: {r_dl.status_code}")
    
    if r_dl.status_code == 200:
        lines = r_dl.text.split('\n')[:3]
        print("\nPremières lignes CSV:")
        for line in lines:
            print(line)
