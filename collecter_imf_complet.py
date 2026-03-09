#!/usr/bin/env python3
"""
Collecte COMPLETE IMF - Tous indicateurs UEMOA (1990-2026)
"""
import sys
from pathlib import Path
from datetime import datetime
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# Series IMF prioritaires
SERIES_IMF = [
    'PCPI_IX',          # CPI Index
    'NGDP_R_SA_IX',     # Real GDP Index
    'NGDP_R_PC',        # Real GDP Growth
    'BCA',              # Balance courante
    'GGXWDG_NGDP',      # Dette publique (% PIB)
    'NGDP_D',           # PIB nominal
    'LUR',              # Taux de chomage
    'BCA_NGDPD',        # Balance courante (% PIB)
]

PAYS_UEMOA = ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']

NOMS_SERIES = {
    'PCPI_IX': 'CPI Index',
    'NGDP_R_SA_IX': 'Real GDP Index',
    'NGDP_R_PC': 'Real GDP Growth',
    'BCA': 'Balance courante',
    'GGXWDG_NGDP': 'Dette publique (% PIB)',
    'NGDP_D': 'PIB nominal',
    'LUR': 'Taux chomage',
    'BCA_NGDPD': 'Balance courante (% PIB)',
}

NOMS_PAYS = {
    'BJ': 'Benin',
    'BF': 'Burkina Faso',
    'CI': 'Cote d\'Ivoire',
    'GW': 'Guinee-Bissau',
    'ML': 'Mali',
    'NE': 'Niger',
    'SN': 'Senegal',
    'TG': 'Togo',
}

def collecter_tout():
    """Collecter toutes les series pour tous les pays"""
    
    print("\n" + "="*80)
    print("COLLECTE IMF COMPLETE (1990-2026)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Periode: 1990-2026 (37 ans)")
    print(f"Series: {len(SERIES_IMF)}")
    print(f"Pays: {len(PAYS_UEMOA)}")
    print(f"Total combinaisons: {len(SERIES_IMF) * len(PAYS_UEMOA)}")
    print("="*80 + "\n")
    
    resultats = {
        'succes': 0,
        'echecs': 0,
        'total_obs': 0,
        'details': []
    }
    
    total_ops = len(SERIES_IMF) * len(PAYS_UEMOA)
    current_op = 0
    
    for series in SERIES_IMF:
        nom_series = NOMS_SERIES.get(series, series)
        
        print(f"\n[SERIE] {nom_series} ({series})")
        print("-" * 80)
        
        for pays in PAYS_UEMOA:
            current_op += 1
            nom_pays = NOMS_PAYS.get(pays, pays)
            
            try:
                print(f"  [{current_op}/{total_ops}] {nom_pays} ({pays})... ", end='', flush=True)
                
                # Format IMF: dataset + key comme M.PAYS.SERIES
                result = run_ingestion(
                    source='imf',
                    dataset='IFS',
                    key=f'M.{pays}.{series}'
                )
                
                # run_ingestion retourne juste obs_count (entier)
                if result and result > 0:
                    resultats['succes'] += 1
                    resultats['total_obs'] += result
                    print(f"OK - {result} obs")
                    
                    resultats['details'].append({
                        'pays': pays,
                        'series': series,
                        'status': 'succes',
                        'obs_count': result
                    })
                else:
                    resultats['echecs'] += 1
                    print("ECHEC - 0 obs")
                    
                    resultats['details'].append({
                        'pays': pays,
                        'series': series,
                        'status': 'echec',
                        'obs_count': 0
                    })
                
                time.sleep(0.5)
                
            except Exception as e:
                resultats['echecs'] += 1
                print(f"ERREUR: {str(e)[:50]}")
                
                resultats['details'].append({
                    'pays': pays,
                    'series': series,
                    'status': 'erreur',
                    'obs_count': 0,
                    'erreur': str(e)
                })
    
    return resultats

def afficher_rapport(resultats):
    """Afficher le rapport final"""
    
    print("\n" + "="*80)
    print("RAPPORT FINAL - COLLECTE IMF")
    print("="*80)
    
    print(f"\nOperations reussies: {resultats['succes']}")
    print(f"Operations echouees: {resultats['echecs']}")
    print(f"Total observations: {resultats['total_obs']:,}")
    
    _, db = get_mongo_db()
    total_imf = db.curated_observations.count_documents({'source': 'IMF'})
    print(f"\nTotal IMF en base: {total_imf:,}")
    
    print("\n" + "="*80)
    print("COLLECTE IMF TERMINEE")
    print("="*80 + "\n")

def main():
    debut = time.time()
    resultats = collecter_tout()
    duree = time.time() - debut
    minutes = int(duree // 60)
    secondes = int(duree % 60)
    print(f"\nDuree totale: {minutes}m {secondes}s")
    afficher_rapport(resultats)

if __name__ == '__main__':
    main()
