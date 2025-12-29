"""
Script de collecte rapide des données Banque Mondiale
Collecte les principaux indicateurs pour les pays UEMOA
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from scripts.pipeline import run_ingestion
import time

# Indicateurs clés à collecter
INDICATORS = [
    "NY.GDP.MKTP.KD.ZG",  # Croissance PIB
    "FP.CPI.TOTL.ZG",     # Inflation
    "NY.GDP.MKTP.CD",     # PIB total
    "GC.DOD.TOTL.GD.ZS",  # Dette publique
    "SP.POP.TOTL",        # Population
]

# Pays UEMOA
COUNTRIES = ["BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"]

print("╔════════════════════════════════════════════════════════════════╗")
print("║       COLLECTE DES DONNÉES BANQUE MONDIALE - UEMOA            ║")
print("╚════════════════════════════════════════════════════════════════╝\n")

total_collected = 0

for i, indicator in enumerate(INDICATORS, 1):
    indicator_names = {
        "NY.GDP.MKTP.KD.ZG": "Croissance du PIB",
        "FP.CPI.TOTL.ZG": "Inflation (CPI)",
        "NY.GDP.MKTP.CD": "PIB total (USD)",
        "GC.DOD.TOTL.GD.ZS": "Dette publique (% PIB)",
        "SP.POP.TOTL": "Population totale"
    }
    
    print(f"📊 [{i}/{len(INDICATORS)}] Collecte: {indicator_names.get(indicator, indicator)}")
    print(f"    Indicateur: {indicator}")
    
    try:
        # Collecter pour tous les pays UEMOA
        count = run_ingestion(
            source="worldbank",
            indicator=indicator,
            country=";".join(COUNTRIES),  # Liste de pays séparés par ;
            date="2000:2024"  # Période 2000-2024
        )
        
        total_collected += count
        print(f"    ✅ {count} observations collectées\n")
        
        # Petit délai pour ne pas surcharger l'API
        time.sleep(1)
        
    except Exception as e:
        print(f"    ❌ Erreur: {str(e)}\n")

print("═" * 66)
print(f"✅ Collecte terminée: {total_collected} observations au total")
print("═" * 66)
print("\n💡 Lancez maintenant le dashboard:")
print("   python dashboard_worldbank.py")
