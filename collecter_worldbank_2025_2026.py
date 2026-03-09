#!/usr/bin/env python3
"""
Collecte World Bank 2025-2026 - Données manquantes
"""
import sys
from pathlib import Path
from datetime import datetime
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# Indicateurs World Bank
INDICATEURS_WB = [
    'SP.POP.TOTL',          # Population totale
    'NY.GDP.PCAP.CD',       # PIB par habitant
    'NY.GDP.MKTP.KD.ZG',    # Croissance PIB
    'FP.CPI.TOTL.ZG',       # Inflation CPI
    'NE.TRD.GNFS.ZS',       # Commerce (% PIB)
    'NE.EXP.GNFS.ZS',       # Exportations (% PIB)
    'NE.IMP.GNFS.ZS',       # Importations (% PIB)
    'BX.KLT.DINV.WD.GD.ZS', # IDE (% PIB)
    'SL.UEM.TOTL.ZS',       # Taux de chômage
    'SE.PRM.ENRR',          # Scolarisation primaire
    'SH.DYN.MORT',          # Mortalité infantile
    'IT.NET.USER.ZS',       # Utilisateurs Internet
    'EG.ELC.ACCS.ZS',       # Accès électricité
]

# Pays CEDEAO (codes ISO-2)
PAYS_CEDEAO = ['BJ', 'BF', 'CI', 'GH', 'GW', 'ML', 'NE', 'NG', 'SN', 'TG', 'GN', 'MR', 'CV', 'GM', 'LR']

NOMS_PAYS = {
    'BJ': 'Bénin', 'BF': 'Burkina Faso', 'CI': 'Côte d\'Ivoire',
    'GH': 'Ghana', 'GW': 'Guinée-Bissau', 'ML': 'Mali',
    'NE': 'Niger', 'NG': 'Nigeria', 'SN': 'Sénégal',
    'TG': 'Togo', 'GN': 'Guinée', 'MR': 'Mauritanie',
    'CV': 'Cap-Vert', 'GM': 'Gambie', 'LR': 'Liberia'
}

def verifier_donnees_existantes(year):
    """Vérifier quelles données existent déjà pour une année"""
    _, db = get_mongo_db()
    
    count = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': f'^{year}'}
    })
    
    return count

def collecter_annee(year):
    """Collecter tous les indicateurs pour une année"""
    
    print(f"\n{'='*80}")
    print(f"COLLECTE WORLD BANK {year}")
    print(f"{'='*80}")
    
    # Vérifier données existantes
    existing = verifier_donnees_existantes(year)
    print(f"Observations existantes {year}: {existing}")
    
    if existing > 0:
        print(f"⚠️  Des données {year} existent déjà. Voulez-vous continuer ? (y/n)")
        response = input().lower()
        if response != 'y':
            print("Collecte annulée")
            return {'succes': 0, 'echecs': 0, 'total_obs': 0}
    
    resultats = {
        'succes': 0,
        'echecs': 0,
        'total_obs': 0,
        'details': []
    }
    
    total_ops = len(INDICATEURS_WB) * len(PAYS_CEDEAO)
    current_op = 0
    
    for indicateur in INDICATEURS_WB:
        for pays in PAYS_CEDEAO:
            current_op += 1
            nom_pays = NOMS_PAYS.get(pays, pays)
            
            print(f"\n[{current_op}/{total_ops}] Collecte {indicateur} pour {nom_pays} ({pays})...")
            
            try:
                result = run_ingestion(
                    source='worldbank',
                    indicator=indicateur,
                    country=pays,
                    year=year
                )
                
                if result.get('status') == 'success':
                    obs_count = result.get('obs_count', 0)
                    resultats['succes'] += 1
                    resultats['total_obs'] += obs_count
                    print(f"   ✅ {obs_count} observations collectées")
                    
                    resultats['details'].append({
                        'pays': pays,
                        'indicateur': indicateur,
                        'observations': obs_count,
                        'statut': 'succes'
                    })
                else:
                    resultats['echecs'] += 1
                    error_msg = result.get('error', 'Erreur inconnue')
                    print(f"   ❌ Échec: {error_msg}")
                    
                    resultats['details'].append({
                        'pays': pays,
                        'indicateur': indicateur,
                        'observations': 0,
                        'statut': 'echec',
                        'erreur': error_msg
                    })
                
                # Pause entre requêtes pour éviter rate limit
                time.sleep(0.5)
                
            except Exception as e:
                resultats['echecs'] += 1
                print(f"   ❌ Erreur: {e}")
                
                resultats['details'].append({
                    'pays': pays,
                    'indicateur': indicateur,
                    'observations': 0,
                    'statut': 'erreur',
                    'erreur': str(e)
                })
    
    return resultats

def main():
    print("\n" + "="*80)
    print("COLLECTE WORLD BANK 2025-2026 - DONNÉES MANQUANTES")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Indicateurs: {len(INDICATEURS_WB)}")
    print(f"Pays: {len(PAYS_CEDEAO)}")
    print(f"Années: 2025, 2026")
    print("="*80)
    
    # Collecter 2025
    print("\n🔹 Phase 1: Collecte données 2025")
    resultats_2025 = collecter_annee(2025)
    
    # Collecter 2026
    print("\n🔹 Phase 2: Collecte données 2026")
    resultats_2026 = collecter_annee(2026)
    
    # Résumé global
    print("\n" + "="*80)
    print("RÉSUMÉ GLOBAL")
    print("="*80)
    print(f"\n2025:")
    print(f"  Succès: {resultats_2025['succes']}")
    print(f"  Échecs: {resultats_2025['echecs']}")
    print(f"  Observations: {resultats_2025['total_obs']}")
    
    print(f"\n2026:")
    print(f"  Succès: {resultats_2026['succes']}")
    print(f"  Échecs: {resultats_2026['echecs']}")
    print(f"  Observations: {resultats_2026['total_obs']}")
    
    print(f"\nTOTAL:")
    print(f"  Succès: {resultats_2025['succes'] + resultats_2026['succes']}")
    print(f"  Échecs: {resultats_2025['echecs'] + resultats_2026['echecs']}")
    print(f"  Observations: {resultats_2025['total_obs'] + resultats_2026['total_obs']}")
    print("="*80 + "\n")
    
    # Vérifier état final
    _, db = get_mongo_db()
    count_2025 = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': '^2025'}
    })
    count_2026 = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'ts': {'$regex': '^2026'}
    })
    
    print(f"📊 ÉTAT FINAL BASE DE DONNÉES:")
    print(f"  2025: {count_2025} observations")
    print(f"  2026: {count_2026} observations")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
