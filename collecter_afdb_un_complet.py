#!/usr/bin/env python3
"""
Collecte COMPLETE AfDB + UN SDG (1990-2026)
"""
import sys
from pathlib import Path
from datetime import datetime
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# AfDB
INDICATEURS_AFDB = [
    'GDP_GROWTH',
    'DEBT_GDP',
    'FDI_GDP',
    'TRADE_BALANCE',
    'INFLATION',
    'UNEMPLOYMENT',
]

PAYS_AFDB = ['BJ', 'BF', 'CI', 'ML', 'NE', 'SN', 'TG', 'GH']

# UN SDG
SERIES_UN = [
    'SI_POV_DAY1',      # Pauvrete extreme
    'SL_TLF_UEM',       # Chomage
    'SH_DYN_MORT',      # Mortalite infantile
    'SE_PRM_CMPT_ZS',   # Achevement primaire
    'SH_H2O_SAFE',      # Acces eau potable
    'SH_STA_BASS',      # Assainissement
]

PAYS_UN = ['BEN', 'BFA', 'CIV', 'MLI', 'NER', 'SEN', 'TGO', 'GHA']

def collecter_afdb():
    """Collecter AfDB"""
    
    print("\n" + "="*80)
    print("COLLECTE AfDB (1990-2026)")
    print("="*80)
    
    resultats = {'succes': 0, 'echecs': 0, 'total_obs': 0}
    
    for pays in PAYS_AFDB:
        for indicateur in INDICATEURS_AFDB:
            try:
                print(f"  AfDB - {pays} - {indicateur}... ", end='', flush=True)
                
                # AfDB utilise dataset + key (ex: AFDB.GDP_GROWTH.BJ)
                result = run_ingestion(
                    source='afdb',
                    dataset='AFDB',
                    key=f'{indicateur}.{pays}'
                )
                
                if result and result > 0:
                    resultats['succes'] += 1
                    resultats['total_obs'] += result
                    print(f"OK - {result} obs")
                else:
                    resultats['echecs'] += 1
                    print("ECHEC - 0 obs")
                
                time.sleep(0.5)
                
            except Exception as e:
                resultats['echecs'] += 1
                print(f"ERREUR: {str(e)[:30]}")
    
    return resultats

def collecter_un_sdg():
    """Collecter UN SDG"""
    
    print("\n" + "="*80)
    print("COLLECTE UN SDG (1990-2026)")
    print("="*80)
    
    resultats = {'succes': 0, 'echecs': 0, 'total_obs': 0}
    
    for pays in PAYS_UN:
        for series in SERIES_UN:
            try:
                print(f"  UN SDG - {pays} - {series}... ", end='', flush=True)
                
                # UN SDG utilise source='un' (pas 'un_sdg') + series + area
                result = run_ingestion(
                    source='un',
                    series=series,
                    area=pays
                )
                
                if result and result > 0:
                    resultats['succes'] += 1
                    resultats['total_obs'] += result
                    print(f"OK - {result} obs")
                else:
                    resultats['echecs'] += 1
                    print("ECHEC - 0 obs")
                
                time.sleep(0.5)
                
            except Exception as e:
                resultats['echecs'] += 1
                print(f"ERREUR: {str(e)[:30]}")
    
    return resultats

def main():
    print("\n" + "="*80)
    print("COLLECTE COMPLETE AfDB + UN SDG (1990-2026)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    debut = time.time()
    
    # AfDB
    print("\n[1/2] AFDB...")
    resultats_afdb = collecter_afdb()
    
    # UN SDG
    print("\n[2/2] UN SDG...")
    resultats_un = collecter_un_sdg()
    
    # Rapport final
    duree = time.time() - debut
    minutes = int(duree // 60)
    secondes = int(duree % 60)
    
    print("\n" + "="*80)
    print("RAPPORT FINAL")
    print("="*80)
    print(f"\nAfDB:")
    print(f"  Succes: {resultats_afdb['succes']}")
    print(f"  Echecs: {resultats_afdb['echecs']}")
    print(f"  Observations: {resultats_afdb['total_obs']:,}")
    
    print(f"\nUN SDG:")
    print(f"  Succes: {resultats_un['succes']}")
    print(f"  Echecs: {resultats_un['echecs']}")
    print(f"  Observations: {resultats_un['total_obs']:,}")
    
    print(f"\nDuree totale: {minutes}m {secondes}s")
    
    # Verification en base
    _, db = get_mongo_db()
    total_afdb = db.curated_observations.count_documents({'source': 'AfDB'})
    total_un = db.curated_observations.count_documents({'source': 'UN_SDG'})
    
    print(f"\nTotal en base:")
    print(f"  AfDB: {total_afdb:,}")
    print(f"  UN SDG: {total_un:,}")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
