#!/usr/bin/env python3
"""Collecte complete World Bank, IMF, AfDB, UN SDG"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from scripts.pipeline import run_ingestion

print("="*80)
print("COLLECTE DONNEES ECONOMIQUES - TOUTES SOURCES")
print("="*80)

# Pays ouest-africains
PAYS_BRVM = ['BEN', 'BFA', 'CI', 'GH', 'ML', 'NE', 'SN', 'TG']

# 1. WORLD BANK - Indicateurs cles
print("\n" + "="*80)
print("1. WORLD BANK")
print("="*80)

wb_indicators = {
    'SP.POP.TOTL': 'Population totale',
    'NY.GDP.MKTP.CD': 'PIB (USD)',
    'NY.GDP.PCAP.CD': 'PIB par habitant',
    'FP.CPI.TOTL.ZG': 'Inflation (CPI)',
    'SL.UEM.TOTL.ZS': 'Chomage',
    'NE.TRD.GNFS.ZS': 'Commerce (% PIB)',
    'GC.DOD.TOTL.GD.ZS': 'Dette publique (% PIB)',
    'BN.CAB.XOKA.GD.ZS': 'Balance courante (% PIB)',
}

wb_total = 0
for indicator, nom in wb_indicators.items():
    print(f"\nCollecte: {nom} ({indicator})")
    try:
        for pays in PAYS_BRVM:
            count = run_ingestion('worldbank', indicator=indicator, country=pays)
            wb_total += count
            print(f"   {pays}: {count} observations")
    except Exception as e:
        print(f"   Erreur: {e}")

print(f"\nTotal World Bank: {wb_total} observations")

# 2. IMF
print("\n" + "="*80)
print("2. IMF")
print("="*80)

imf_indicators = {
    'PCPI_IX': 'Indice prix consommation',
    'NGDP_R': 'PIB reel',
    'NGDP_RPCH': 'Croissance PIB',
    'PCPIPCH': 'Inflation',
    'LUR': 'Taux chomage',
}

imf_total = 0
for indicator, nom in imf_indicators.items():
    print(f"\nCollecte: {nom} ({indicator})")
    try:
        for pays in PAYS_BRVM:
            count = run_ingestion('imf', series=indicator, area=pays)
            imf_total += count
            print(f"   {pays}: {count} observations")
    except Exception as e:
        print(f"   Erreur: {e}")

print(f"\nTotal IMF: {imf_total} observations")

# 3. AfDB
print("\n" + "="*80)
print("3. AFDB (Banque Africaine de Developpement)")
print("="*80)

try:
    afdb_count = run_ingestion('afdb')
    print(f"Total AfDB: {afdb_count} observations")
except Exception as e:
    print(f"Erreur AfDB: {e}")

# 4. UN SDG
print("\n" + "="*80)
print("4. UN SDG (Objectifs Developpement Durable)")
print("="*80)

try:
    un_count = run_ingestion('un_sdg')
    print(f"Total UN SDG: {un_count} observations")
except Exception as e:
    print(f"Erreur UN SDG: {e}")

print("\n" + "="*80)
print("COLLECTE TERMINEE")
print("="*80)
print(f"\nTotal general:")
print(f"   World Bank: {wb_total}")
print(f"   IMF: {imf_total}")
print(f"   AfDB: {afdb_count if 'afdb_count' in locals() else 0}")
print(f"   UN SDG: {un_count if 'un_count' in locals() else 0}")
print(f"   TOTAL: {wb_total + imf_total + locals().get('afdb_count', 0) + locals().get('un_count', 0)}")
