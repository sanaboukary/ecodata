#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COLLECTE COMPLETE - TOUTES LES SOURCES
World Bank + IMF + AfDB + UN SDG
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# Configuration des sources
SOURCES_CONFIG = {
    'worldbank': {
        'nom': 'World Bank',
        'indicateurs': [
            'SP.POP.TOTL',      # Population totale
            'NY.GDP.MKTP.CD',   # PIB (USD)
            'NY.GDP.PCAP.CD',   # PIB par habitant
            'FP.CPI.TOTL.ZG',   # Inflation CPI
            'NE.EXP.GNFS.ZS',   # Exportations (% PIB)
            'NE.IMP.GNFS.ZS',   # Importations (% PIB)
            'BX.KLT.DINV.WD.GD.ZS', # IDE (% PIB)
            'GC.DOD.TOTL.GD.ZS',    # Dette publique (% PIB)
            'SL.UEM.TOTL.ZS',   # Chômage
            'SE.PRM.ENRR',      # Taux scolarisation primaire
            'SH.DYN.MORT',      # Mortalité infantile
        ],
        'pays': ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']  # UEMOA
    },
    'imf': {
        'nom': 'IMF',
        'series': [
            'PCPI_IX',          # CPI Index
            'NGDP_R_SA_IX',     # Real GDP Index
            'NGDP_R_PC',        # Real GDP Growth
            'BCA',              # Balance courante
            'GGXWDG_NGDP',     # Dette publique (% PIB)
        ],
        'pays': ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']
    },
    'afdb': {
        'nom': 'African Development Bank',
        'indicateurs': [
            'GDP_GROWTH',
            'DEBT_GDP',
            'FDI_GDP',
            'TRADE_BALANCE',
        ],
        'pays': ['BJ', 'BF', 'CI', 'ML', 'NE', 'SN', 'TG', 'GH']
    },
    'un_sdg': {
        'nom': 'UN Sustainable Development Goals',
        'series': [
            'SI_POV_DAY1',      # Pauvreté extrême
            'SL_TLF_UEM',       # Chômage
            'SH_DYN_MORT',      # Mortalité infantile
            'SE_PRM_CMPT_ZS',   # Achèvement primaire
        ],
        'pays': ['BEN', 'BFA', 'CIV', 'MLI', 'NER', 'SEN', 'TGO', 'GHA']
    }
}

def collecter_worldbank():
    """Collecte World Bank - Indicateurs macro"""
    print("\n" + "="*80)
    print("[WORLD BANK] Collecte indicateurs macroeconomiques")
    print("="*80)
    
    config = SOURCES_CONFIG['worldbank']
    total_obs = 0
    
    for pays in config['pays']:
        for indicator in config['indicateurs']:
            try:
                print(f"\n📊 {pays} - {indicator}...")
                result = run_ingestion(
                    source='worldbank',
                    indicator=indicator,
                    country=pays
                )
                
                if result and result.get('obs_count', 0) > 0:
                    count = result['obs_count']
                    total_obs += count
                    print(f"   ✅ {count} observations collectées")
                else:
                    print(f"   ⚠️  Aucune donnée")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] World Bank: {total_obs} observations au total")
    print(f"{'='*80}")
    return total_obs

def collecter_imf():
    """Collecte IMF - Données monétaires"""
    print("\n" + "="*80)
    print("[IMF] Collecte donnees monetaires et conjoncture")
    print("="*80)
    
    config = SOURCES_CONFIG['imf']
    total_obs = 0
    
    for pays in config['pays']:
        for series in config['series']:
            try:
                print(f"\n📊 {pays} - {series}...")
                result = run_ingestion(
                    source='imf',
                    series=series,
                    area=pays
                )
                
                if result and result.get('obs_count', 0) > 0:
                    count = result['obs_count']
                    total_obs += count
                    print(f"   ✅ {count} observations collectées")
                else:
                    print(f"   ⚠️  Aucune donnée")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] IMF: {total_obs} observations au total")
    print(f"{'='*80}")
    return total_obs

def collecter_afdb():
    """Collecte AfDB - Développement africain"""
    print("\n" + "="*80)
    print("[AfDB] Collecte donnees developpement")
    print("="*80)
    
    config = SOURCES_CONFIG['afdb']
    total_obs = 0
    
    for pays in config['pays']:
        for indicator in config['indicateurs']:
            try:
                print(f"\n📊 {pays} - {indicator}...")
                result = run_ingestion(
                    source='afdb',
                    indicator=indicator,
                    country=pays
                )
                
                if result and result.get('obs_count', 0) > 0:
                    count = result['obs_count']
                    total_obs += count
                    print(f"   ✅ {count} observations collectées")
                else:
                    print(f"   ⚠️  Aucune donnée")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] AfDB: {total_obs} observations au total")
    print(f"{'='*80}")
    return total_obs

def collecter_un_sdg():
    """Collecte UN SDG - Objectifs développement durable"""
    print("\n" + "="*80)
    print("[UN SDG] Collecte objectifs developpement durable")
    print("="*80)
    
    config = SOURCES_CONFIG['un_sdg']
    total_obs = 0
    
    for pays in config['pays']:
        for series in config['series']:
            try:
                print(f"\n📊 {pays} - {series}...")
                result = run_ingestion(
                    source='un_sdg',
                    series=series,
                    area=pays
                )
                
                if result and result.get('obs_count', 0) > 0:
                    count = result['obs_count']
                    total_obs += count
                    print(f"   ✅ {count} observations collectées")
                else:
                    print(f"   ⚠️  Aucune donnée")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] UN SDG: {total_obs} observations au total")
    print(f"{'='*80}")
    return total_obs

def afficher_statistiques():
    """Afficher les statistiques globales"""
    print("\n" + "="*80)
    print("[STATS] STATISTIQUES GLOBALES")
    print("="*80)
    
    _, db = get_mongo_db()
    
    sources = ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG']
    
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        print(f"{source:15} : {count:>8,} observations")
    
    total = db.curated_observations.count_documents({})
    print(f"{'-'*80}")
    print(f"{'TOTAL':15} : {total:>8,} observations")
    print(f"{'='*80}\n")

def main():
    print("\n" + "="*80)
    print("[COLLECTE COMPLETE] TOUTES LES SOURCES INTERNATIONALES")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sources: World Bank + IMF + AfDB + UN SDG")
    print("="*80 + "\n")
    
    # Statistiques avant
    print("[STATS] Statistiques AVANT collecte:")
    afficher_statistiques()
    
    # Collectes
    total_worldbank = collecter_worldbank()
    total_imf = collecter_imf()
    total_afdb = collecter_afdb()
    total_un_sdg = collecter_un_sdg()
    
    # Statistiques après
    print("\n\n[STATS] Statistiques APRES collecte:")
    afficher_statistiques()
    
    # Résumé final
    print("\n" + "="*80)
    print("[SUCCESS] COLLECTE COMPLETE TERMINEE")
    print("="*80)
    print(f"World Bank : {total_worldbank:>6,} nouvelles observations")
    print(f"IMF        : {total_imf:>6,} nouvelles observations")
    print(f"AfDB       : {total_afdb:>6,} nouvelles observations")
    print(f"UN SDG     : {total_un_sdg:>6,} nouvelles observations")
    print(f"{'-'*80}")
    print(f"TOTAL      : {total_worldbank + total_imf + total_afdb + total_un_sdg:>6,} nouvelles observations")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
