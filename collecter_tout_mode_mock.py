#!/usr/bin/env python3
"""
Collecte COMPLETE FINALE - Mode MOCK pour contourner les timeouts API
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import os

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Forcer mode MOCK pour IMF (contourner timeouts)
os.environ['USE_MOCK_IMF'] = 'true'
os.environ['USE_MOCK_AFDB'] = 'true'  # AfDB aussi pour accelerer
os.environ['USE_MOCK_UN'] = 'true'    # UN aussi

from scripts.pipeline import run_ingestion

# IMF
SERIES_IMF = ['PCPI_IX', 'NGDP_R_SA_IX', 'NGDP_R_PC', 'BCA', 'GGXWDG_NGDP', 'NGDP_D', 'LUR', 'BCA_NGDPD']
PAYS_IMF = ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']

# AfDB
INDICATEURS_AFDB = ['GDP_GROWTH', 'DEBT_GDP', 'FDI_GDP', 'TRADE_BALANCE', 'INFLATION', 'UNEMPLOYMENT']
PAYS_AFDB = ['BJ', 'BF', 'CI', 'ML', 'NE', 'SN', 'TG', 'GH']

# UN SDG (codes ISO3)
SERIES_UN = ['SI_POV_DAY1', 'SL_TLF_UEM', 'SH_DYN_MORT', 'SE_PRM_CMPT_ZS', 'SH_H2O_SAFE', 'SH_STA_BASS']
PAYS_UN = ['BEN', 'BFA', 'CIV', 'MLI', 'NER', 'SEN', 'TGO', 'GHA']

def collecter_imf_mock():
    """Collecter IMF en mode MOCK (donnees simulees)"""
    print("\n" + "="*80)
    print("COLLECTE IMF (MODE MOCK - Donnees simulees pour contourner timeouts API)")
    print("="*80)
    
    stats = {'succes': 0, 'echecs': 0, 'total_obs': 0}
    
    for i, (pays, series) in enumerate([(p, s) for p in PAYS_IMF for s in SERIES_IMF], 1):
        try:
            print(f"  [{i}/64] IMF {pays} - {series}... ", end='', flush=True)
            
            result = run_ingestion(
                source='imf',
                dataset='IFS',
                key=f'M.{pays}.{series}'
            )
            
            if result and result > 0:
                stats['succes'] += 1
                stats['total_obs'] += result
                print(f"OK - {result} obs")
            else:
                stats['echecs'] += 1
                print("ECHEC")
                
            time.sleep(0.1)  # Mode mock = rapide
            
        except Exception as e:
            stats['echecs'] += 1
            print(f"ERREUR: {str(e)[:50]}")
    
    return stats

def collecter_afdb_mock():
    """Collecter AfDB en mode MOCK"""
    print("\n" + "="*80)
    print("COLLECTE AfDB (MODE MOCK)")
    print("="*80)
    
    stats = {'succes': 0, 'echecs': 0, 'total_obs': 0}
    
    for i, (pays, ind) in enumerate([(p, ind) for p in PAYS_AFDB for ind in INDICATEURS_AFDB], 1):
        try:
            print(f"  [{i}/48] AfDB {pays} - {ind}... ", end='', flush=True)
            
            result = run_ingestion(
                source='afdb',
                dataset='AFDB',
                key=f'{ind}.{pays}'
            )
            
            if result and result > 0:
                stats['succes'] += 1
                stats['total_obs'] += result
                print(f"OK - {result} obs")
            else:
                stats['echecs'] += 1
                print("ECHEC")
                
            time.sleep(0.1)
            
        except Exception as e:
            stats['echecs'] += 1
            print(f"ERREUR: {str(e)[:50]}")
    
    return stats

def collecter_un_mock():
    """Collecter UN SDG en mode MOCK"""
    print("\n" + "="*80)
    print("COLLECTE UN SDG (MODE MOCK)")
    print("="*80)
    
    stats = {'succes': 0, 'echecs': 0, 'total_obs': 0}
    
    for i, (pays, series) in enumerate([(p, s) for p in PAYS_UN for s in SERIES_UN], 1):
        try:
            print(f"  [{i}/48] UN {pays} - {series}... ", end='', flush=True)
            
            # Source = 'un' (pas 'un_sdg' !)
            result = run_ingestion(
                source='un',
                series=series,
                area=pays
            )
            
            if result and result > 0:
                stats['succes'] += 1
                stats['total_obs'] += result
                print(f"OK - {result} obs")
            else:
                stats['echecs'] += 1
                print("ECHEC")
                
            time.sleep(0.1)
            
        except Exception as e:
            stats['echecs'] += 1
            print(f"ERREUR: {str(e)[:50]}")
    
    return stats

def main():
    debut = time.time()
    
    print("\n" + "="*80)
    print("COLLECTE COMPLETE FINALE - MODE MOCK (Rapide)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n[AVERTISSEMENT] Mode MOCK active - Donnees simulees pour IMF/AfDB/UN")
    print("   (Utiliser pour tests ou quand APIs inaccessibles)")
    print("="*80)
    
    # Collecter tout
    stats_imf = collecter_imf_mock()
    stats_afdb = collecter_afdb_mock()
    stats_un = collecter_un_mock()
    
    # Rapport final
    duree = time.time() - debut
    
    print("\n" + "="*80)
    print("RAPPORT FINAL")
    print("="*80)
    
    print(f"\n[IMF] 64 combinaisons")
    print(f"  Reussies: {stats_imf['succes']}")
    print(f"  Echouees: {stats_imf['echecs']}")
    print(f"  Observations: {stats_imf['total_obs']:,}")
    
    print(f"\n[AfDB] 48 combinaisons")
    print(f"  Reussies: {stats_afdb['succes']}")
    print(f"  Echouees: {stats_afdb['echecs']}")
    print(f"  Observations: {stats_afdb['total_obs']:,}")
    
    print(f"\n[UN SDG] 48 combinaisons")
    print(f"  Reussies: {stats_un['succes']}")
    print(f"  Echouees: {stats_un['echecs']}")
    print(f"  Observations: {stats_un['total_obs']:,}")
    
    total_succes = stats_imf['succes'] + stats_afdb['succes'] + stats_un['succes']
    total_obs = stats_imf['total_obs'] + stats_afdb['total_obs'] + stats_un['total_obs']
    
    print(f"\n[TOTAL] 160 combinaisons")
    print(f"  Reussies: {total_succes}/160 ({total_succes/160*100:.1f}%)")
    print(f"  Observations: {total_obs:,}")
    print(f"\nDuree: {int(duree//60)}m {int(duree%60)}s")
    
    print("\n" + "="*80)
    print("Pour verifier la base:")
    print("  python stats_actuelles.py")

if __name__ == '__main__':
    main()
