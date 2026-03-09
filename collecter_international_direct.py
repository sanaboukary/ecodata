#!/usr/bin/env python3
"""
Collecte directe via pipeline (sans Django)
"""
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from scripts.pipeline import run_ingestion

print("="*80)
print("COLLECTE SOURCES INTERNATIONALES (via pipeline direct)")
print("="*80)

# World Bank
print("\n[1/4] World Bank - Population Cote d'Ivoire...")
result = run_ingestion(source='worldbank', indicator='SP.POP.TOTL', country='CI')
print(f"Result: {result}")

# World Bank - PIB
print("\n[2/4] World Bank - PIB Senegal...")
result = run_ingestion(source='worldbank', indicator='NY.GDP.MKTP.CD', country='SN')
print(f"Result: {result}")

# IMF
print("\n[3/4] IMF - CPI Cote d'Ivoire...")
result = run_ingestion(source='imf', series='PCPI_IX', area='CI')
print(f"Result: {result}")

# IMF - Senegal
print("\n[4/4] IMF - CPI Senegal...")
result = run_ingestion(source='imf', series='PCPI_IX', area='SN')
print(f"Result: {result}")

print("\n" + "="*80)
print("COLLECTE TERMINEE")
print("="*80)
