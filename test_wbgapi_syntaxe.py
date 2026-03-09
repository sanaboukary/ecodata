"""
Test rapide de la syntaxe wbgapi pour comprendre comment récupérer les données
"""
import wbgapi as wb
import pandas as pd

print("🔍 TEST WBGAPI - Syntaxe correcte\n")

# Test 1: Essayer avec des entiers (recommandé par wbgapi)
print("=" * 80)
print("TEST 1: range(2020, 2027) - Entiers")
print("=" * 80)
try:
    data1 = wb.data.DataFrame(
        'NY.GDP.MKTP.KD.ZG',  # Croissance PIB
        ['SN', 'CI'],  # Sénégal, Côte d'Ivoire
        time=range(2020, 2027),  # 2020-2026
        labels=False
    )
    print(f"✅ SUCCÈS avec range(2020, 2027)")
    print(f"Colonnes: {list(data1.columns)}")
    print(f"Index (pays): {list(data1.index)}")
    print("\nDonnées:")
    print(data1)
    print(f"\nNombre de valeurs non-nulles: {data1.notna().sum().sum()}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print("\n")

# Test 2: Essayer avec format YR
print("=" * 80)
print("TEST 2: ['YR2020', 'YR2021', ...] - Format YR")
print("=" * 80)
try:
    data2 = wb.data.DataFrame(
        'NY.GDP.MKTP.KD.ZG',
        ['SN', 'CI'],
        time=[f'YR{y}' for y in range(2020, 2027)],
        labels=False
    )
    print(f"✅ SUCCÈS avec ['YR2020', ...]")
    print(f"Colonnes: {list(data2.columns)}")
    print("\nDonnées:")
    print(data2)
except Exception as e:
    print(f"❌ ERREUR: {e}")

print("\n")

# Test 3: Essayer sans le paramètre time (toutes les années disponibles)
print("=" * 80)
print("TEST 3: Sans paramètre time - Toutes les années")
print("=" * 80)
try:
    data3 = wb.data.DataFrame(
        'NY.GDP.MKTP.KD.ZG',
        ['SN', 'CI'],
        labels=False
    )
    print(f"✅ SUCCÈS sans paramètre time")
    print(f"Colonnes: {list(data3.columns)}")
    print(f"Nombre total de colonnes: {len(data3.columns)}")
    
    # Afficher les 10 dernières colonnes (années récentes)
    recent_cols = list(data3.columns)[-10:]
    print(f"\n10 dernières colonnes (années récentes): {recent_cols}")
    print("\nDonnées récentes:")
    print(data3[recent_cols])
    
    # Vérifier si 2025 et 2026 sont disponibles
    if 'YR2025' in data3.columns:
        print("\n✅ YR2025 disponible!")
        print(f"Valeurs 2025: {data3['YR2025'].to_dict()}")
    else:
        print("\n⚠️ YR2025 NON disponible")
        
    if 'YR2026' in data3.columns:
        print("\n✅ YR2026 disponible!")
        print(f"Valeurs 2026: {data3['YR2026'].to_dict()}")
    else:
        print("\n⚠️ YR2026 NON disponible")
        
except Exception as e:
    print(f"❌ ERREUR: {e}")

print("\n")

# Test 4: Utiliser wb.data.fetch() au lieu de DataFrame
print("=" * 80)
print("TEST 4: wb.data.fetch() - API alternative")
print("=" * 80)
try:
    # Fetch retourne un générateur
    results = list(wb.data.fetch(
        'NY.GDP.MKTP.KD.ZG',
        ['SN', 'CI'],
        time=range(2020, 2027)
    ))
    print(f"✅ SUCCÈS avec fetch()")
    print(f"Nombre de résultats: {len(results)}")
    if results:
        print(f"\nPremiers résultats:")
        for r in results[:5]:
            print(f"  {r}")
except Exception as e:
    print(f"❌ ERREUR: {e}")

print("\n" + "=" * 80)
print("🎯 CONCLUSION: Méthode recommandée")
print("=" * 80)
