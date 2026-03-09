#!/usr/bin/env python3
"""
Collecte COMPLETE World Bank - Tous indicateurs UEMOA
"""
import sys
from pathlib import Path
from datetime import datetime
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# Indicateurs prioritaires World Bank
INDICATEURS_WB = [
    'SP.POP.TOTL',          # Population totale
    'NY.GDP.MKTP.CD',       # PIB (USD)
    'NY.GDP.PCAP.CD',       # PIB par habitant
    'FP.CPI.TOTL.ZG',       # Inflation CPI
    'NE.EXP.GNFS.ZS',       # Exportations (% PIB)
    'NE.IMP.GNFS.ZS',       # Importations (% PIB)
    'BX.KLT.DINV.WD.GD.ZS', # IDE (% PIB)
    'GC.DOD.TOTL.GD.ZS',    # Dette publique (% PIB)
    'SL.UEM.TOTL.ZS',       # Chomage
    'SE.PRM.ENRR',          # Taux scolarisation primaire
    'SH.DYN.MORT',          # Mortalite infantile
]

# Pays UEMOA
PAYS_UEMOA = ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']

NOMS_INDICATEURS = {
    'SP.POP.TOTL': 'Population totale',
    'NY.GDP.MKTP.CD': 'PIB (USD)',
    'NY.GDP.PCAP.CD': 'PIB par habitant',
    'FP.CPI.TOTL.ZG': 'Inflation CPI',
    'NE.EXP.GNFS.ZS': 'Exportations (% PIB)',
    'NE.IMP.GNFS.ZS': 'Importations (% PIB)',
    'BX.KLT.DINV.WD.GD.ZS': 'IDE (% PIB)',
    'GC.DOD.TOTL.GD.ZS': 'Dette publique (% PIB)',
    'SL.UEM.TOTL.ZS': 'Chomage',
    'SE.PRM.ENRR': 'Scolarisation primaire',
    'SH.DYN.MORT': 'Mortalite infantile',
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
    """Collecter tous les indicateurs pour tous les pays"""
    
    print("\n" + "="*80)
    print("COLLECTE WORLD BANK COMPLETE (1990-2026)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Periode: 1990-2026 (37 ans)")
    print(f"Indicateurs: {len(INDICATEURS_WB)}")
    print(f"Pays: {len(PAYS_UEMOA)}")
    print(f"Total combinaisons: {len(INDICATEURS_WB) * len(PAYS_UEMOA)}")
    print("="*80 + "\n")
    
    resultats = {
        'succes': 0,
        'echecs': 0,
        'total_obs': 0,
        'details': []
    }
    
    total_ops = len(INDICATEURS_WB) * len(PAYS_UEMOA)
    current_op = 0
    
    for indicateur in INDICATEURS_WB:
        nom_indic = NOMS_INDICATEURS.get(indicateur, indicateur)
        
        print(f"\n[INDICATEUR] {nom_indic} ({indicateur})")
        print("-" * 80)
        
        for pays in PAYS_UEMOA:
            current_op += 1
            nom_pays = NOMS_PAYS.get(pays, pays)
            
            try:
                print(f"  [{current_op}/{total_ops}] {nom_pays} ({pays})... ", end='', flush=True)
                
                result = run_ingestion(
                    source='worldbank',
                    indicator=indicateur,
                    country=pays,
                    date='1990:2026'
                )
                
                # run_ingestion retourne juste obs_count (entier)
                if result and result > 0:
                    resultats['succes'] += 1
                    resultats['total_obs'] += result
                    print(f"OK - {result} obs")
                    
                    resultats['details'].append({
                        'pays': pays,
                        'indicateur': indicateur,
                        'status': 'succes',
                        'obs_count': result
                    })
                else:
                    resultats['echecs'] += 1
                    print("ECHEC - 0 obs")
                    
                    resultats['details'].append({
                        'pays': pays,
                        'indicateur': indicateur,
                        'status': 'echec',
                        'obs_count': 0
                    })
                
                # Petite pause pour eviter de surcharger l'API
                time.sleep(0.5)
                
            except Exception as e:
                resultats['echecs'] += 1
                print(f"ERREUR: {str(e)[:50]}")
                
                resultats['details'].append({
                    'pays': pays,
                    'indicateur': indicateur,
                    'status': 'erreur',
                    'obs_count': 0,
                    'erreur': str(e)
                })
    
    return resultats

def afficher_rapport(resultats):
    """Afficher le rapport final"""
    
    print("\n" + "="*80)
    print("RAPPORT FINAL - COLLECTE WORLD BANK")
    print("="*80)
    
    print(f"\nOperations reussies: {resultats['succes']}")
    print(f"Operations echouees: {resultats['echecs']}")
    print(f"Total observations: {resultats['total_obs']:,}")
    
    # Verification en base
    _, db = get_mongo_db()
    total_wb = db.curated_observations.count_documents({'source': 'WorldBank'})
    print(f"\nTotal World Bank en base: {total_wb:,}")
    
    # Top pays par observations
    print("\n" + "-"*80)
    print("OBSERVATIONS PAR PAYS:")
    print("-"*80)
    
    obs_par_pays = {}
    for detail in resultats['details']:
        if detail['status'] == 'succes':
            pays = detail['pays']
            obs_par_pays[pays] = obs_par_pays.get(pays, 0) + detail['obs_count']
    
    for pays in sorted(obs_par_pays.keys()):
        nom_pays = NOMS_PAYS.get(pays, pays)
        count = obs_par_pays[pays]
        print(f"  {nom_pays:20} ({pays}): {count:>6,} observations")
    
    # Top indicateurs
    print("\n" + "-"*80)
    print("OBSERVATIONS PAR INDICATEUR:")
    print("-"*80)
    
    obs_par_indic = {}
    for detail in resultats['details']:
        if detail['status'] == 'succes':
            indic = detail['indicateur']
            obs_par_indic[indic] = obs_par_indic.get(indic, 0) + detail['obs_count']
    
    for indic in sorted(obs_par_indic.keys(), key=lambda x: obs_par_indic[x], reverse=True):
        nom_indic = NOMS_INDICATEURS.get(indic, indic)
        count = obs_par_indic[indic]
        print(f"  {nom_indic:30}: {count:>6,} observations")
    
    # Echantillon de donnees
    print("\n" + "-"*80)
    print("ECHANTILLON DE DONNEES (10 dernieres):")
    print("-"*80)
    print(f"{'PAYS':<8} {'INDICATEUR':<35} {'ANNEE':<6} {'VALEUR':>15}")
    print("-"*80)
    
    for obs in db.curated_observations.find(
        {'source': 'WorldBank'}
    ).sort('ts', -1).limit(10):
        pays = obs.get('key', 'N/A')[:8]
        indic = obs.get('dataset', 'N/A')[:35]
        annee = obs.get('ts', 'N/A')[:6]
        val = obs.get('value', 0)
        
        if isinstance(val, (int, float)):
            if val > 1e9:
                val_str = f"{val/1e9:.2f}B"
            elif val > 1e6:
                val_str = f"{val/1e6:.2f}M"
            else:
                val_str = f"{val:,.2f}"
        else:
            val_str = str(val)[:15]
        
        print(f"{pays:<8} {indic:<35} {annee:<6} {val_str:>15}")
    
    print("\n" + "="*80)
    print("COLLECTE TERMINEE")
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
