#!/usr/bin/env python3
"""
COLLECTE OPTIMISEE WORLD BANK 1960-2026 - PAR BLOCS
Collecte par plages d'annees pour reduire le nombre de requetes
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import logging

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'collecte_wb_optimisee_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# 8 Pays UEMOA
PAYS_UEMOA = ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']

NOMS_PAYS = {
    'BJ': 'Benin', 'BF': 'Burkina Faso', 'CI': 'Cote d\'Ivoire',
    'GW': 'Guinee-Bissau', 'ML': 'Mali', 'NE': 'Niger',
    'SN': 'Senegal', 'TG': 'Togo'
}

# Indicateurs prioritaires (66 total)
INDICATEURS = [
    # PIB & Croissance
    'NY.GDP.MKTP.CD', 'NY.GDP.MKTP.KD.ZG', 'NY.GDP.PCAP.CD', 
    'NY.GDP.PCAP.KD.ZG', 'NY.GNP.PCAP.CD', 'NY.GNP.MKTP.CD',
    'NV.AGR.TOTL.ZS', 'NV.IND.TOTL.ZS', 'NV.SRV.TOTL.ZS',
    'NE.GDI.TOTL.ZS',
    
    # Commerce & IDE
    'NE.TRD.GNFS.ZS', 'NE.EXP.GNFS.ZS', 'NE.IMP.GNFS.ZS',
    'BX.KLT.DINV.WD.GD.ZS', 'BN.CAB.XOKA.GD.ZS',
    'TM.VAL.MRCH.CD.WT', 'TX.VAL.MRCH.CD.WT',
    
    # Inflation & Taux de change
    'FP.CPI.TOTL.ZG', 'FP.CPI.TOTL', 'PA.NUS.FCRF',
    
    # Dette & Finances publiques
    'GC.DOD.TOTL.GD.ZS', 'GC.BAL.CASH.GD.ZS', 'GC.REV.XGRT.GD.ZS',
    'GC.XPN.TOTL.GD.ZS', 'DT.DOD.DECT.CD',
    
    # Emploi
    'SL.UEM.TOTL.ZS', 'SL.UEM.TOTL.NE.ZS', 'SL.TLF.TOTL.IN',
    'SL.TLF.CACT.ZS', 'SL.EMP.VULN.ZS',
    
    # Population & Demographie
    'SP.POP.TOTL', 'SP.POP.GROW', 'SP.URB.TOTL.IN.ZS',
    'SP.POP.0014.TO.ZS', 'SP.POP.1564.TO.ZS', 'SP.POP.65UP.TO.ZS',
    'SP.DYN.TFRT.IN', 'SP.DYN.LE00.IN',
    
    # Sante
    'SH.DYN.MORT', 'SH.DYN.NMRT', 'SH.STA.MMRT',
    'SH.XPD.CHEX.GD.ZS', 'SH.MED.PHYS.ZS',
    'SH.H2O.BASW.ZS', 'SH.STA.BASS.ZS',
    
    # Education
    'SE.PRM.ENRR', 'SE.SEC.ENRR', 'SE.TER.ENRR',
    'SE.XPD.TOTL.GD.ZS', 'SE.ADT.LITR.ZS', 'SE.PRM.CMPT.ZS',
    
    # Infrastructure
    'EG.ELC.ACCS.ZS', 'IT.NET.USER.ZS', 'IT.CEL.SETS.P2',
    'IS.ROD.PAVE.ZS', 'IS.AIR.PSGR',
    
    # Environnement & Agriculture
    'AG.LND.AGRI.ZS', 'AG.LND.FRST.ZS', 'EN.ATM.CO2E.KT',
    'AG.PRD.CROP.XD', 'AG.YLD.CREL.KG',
    
    # Pauvrete & Inegalites
    'SI.POV.DDAY', 'SI.POV.NAHC', 'SI.POV.GINI',
    'SI.DST.FRST.20', 'SI.DST.05TH.20',
]

# Blocs d'annees (par decennie + annees recentes)
BLOCS_ANNEES = [
    ('1960:1969', 1960, 1969),  # Annees 60
    ('1970:1979', 1970, 1979),  # Annees 70
    ('1980:1989', 1980, 1989),  # Annees 80
    ('1990:1999', 1990, 1999),  # Annees 90
    ('2000:2009', 2000, 2009),  # Annees 2000
    ('2010:2019', 2010, 2019),  # Annees 2010
    ('2020:2026', 2020, 2026),  # Annees recentes
]

def verifier_mongodb():
    """Verifier MongoDB"""
    try:
        _, db = get_mongo_db()
        db.command('ping')
        count = db.curated_observations.count_documents({'source': 'WorldBank'})
        logger.info(f"MongoDB OK - {count:,} observations World Bank existantes")
        return True, count
    except Exception as e:
        logger.error(f"MongoDB inaccessible: {e}")
        return False, 0

def collecter_bloc(indicateur, pays, date_range):
    """Collecter un indicateur pour un pays et une plage d'annees"""
    try:
        # L'API World Bank accepte "2010:2020" pour une plage
        result = run_ingestion(
            source='worldbank',
            indicator=indicateur,
            country=pays,
            date=date_range  # Format "YYYY:YYYY"
        )
        
        if result.get('status') == 'success':
            obs = result.get('obs_count', 0)
            return {'ok': True, 'obs': obs}
        else:
            return {'ok': False, 'obs': 0}
    except Exception as e:
        logger.error(f"Erreur {indicateur}|{pays}|{date_range}: {e}")
        return {'ok': False, 'obs': 0}

def main():
    print("\n" + "="*100)
    print("COLLECTE OPTIMISEE WORLD BANK 1960-2026 - PAR BLOCS")
    print("="*100)
    print(f"Debut: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Indicateurs: {len(INDICATEURS)}")
    print(f"Pays: {len(PAYS_UEMOA)} - {', '.join(PAYS_UEMOA)}")
    print(f"Blocs: {len(BLOCS_ANNEES)} decennies")
    
    total_ops = len(INDICATEURS) * len(PAYS_UEMOA) * len(BLOCS_ANNEES)
    duree_estimee_min = (total_ops * 2.0) / 60  # 2s par bloc vs 0.5s par annee
    
    print(f"\nOPTIMISATION:")
    print(f"   Operations: {total_ops:,} (vs 35,376 avant)")
    print(f"   Reduction: {100 - (total_ops/35376*100):.0f}%")
    print(f"   Duree estimee: ~{duree_estimee_min:.0f} min (~{duree_estimee_min/60:.1f} heures)")
    print("="*100 + "\n")
    
    # Verifier MongoDB
    ok, obs_initiales = verifier_mongodb()
    if not ok:
        logger.error("ERREUR: MongoDB non accessible")
        return
    
    print(f"Observations actuelles: {obs_initiales:,}\n")
    print("Demarrage dans 3 secondes...")
    time.sleep(3)
    
    # Statistiques
    stats = {
        'total': 0,
        'succes': 0,
        'echecs': 0,
        'observations': 0,
        'par_bloc': {}
    }
    
    debut = time.time()
    derniere_maj = time.time()
    
    # Collecte par bloc
    for bloc_nom, annee_debut, annee_fin in BLOCS_ANNEES:
        print(f"\n{'='*100}")
        print(f"BLOC {bloc_nom} ({annee_debut}-{annee_fin})")
        print(f"{'='*100}")
        
        stats['par_bloc'][bloc_nom] = {
            'succes': 0,
            'echecs': 0,
            'observations': 0
        }
        
        for indicateur in INDICATEURS:
            for pays in PAYS_UEMOA:
                stats['total'] += 1
                
                result = collecter_bloc(indicateur, pays, bloc_nom)
                
                if result['ok']:
                    stats['succes'] += 1
                    stats['observations'] += result['obs']
                    stats['par_bloc'][bloc_nom]['succes'] += 1
                    stats['par_bloc'][bloc_nom]['observations'] += result['obs']
                    
                    if result['obs'] > 0:
                        logger.info(f"OK {bloc_nom}|{indicateur}|{pays}: {result['obs']} obs")
                else:
                    stats['echecs'] += 1
                    stats['par_bloc'][bloc_nom]['echecs'] += 1
                    logger.warning(f"ECHEC {bloc_nom}|{indicateur}|{pays}")
                
                # Affichage progres toutes les 30s
                if time.time() - derniere_maj > 30:
                    derniere_maj = time.time()
                    progress = (stats['total'] / total_ops) * 100
                    vitesse = stats['total'] / (time.time() - debut)
                    restant = (total_ops - stats['total']) / vitesse if vitesse > 0 else 0
                    
                    print(f"\n[{stats['total']:,}/{total_ops:,}] {progress:.1f}% | "
                          f"OK: {stats['succes']:,} | ECHEC: {stats['echecs']:,} | "
                          f"OBS: {stats['observations']:,} | "
                          f"Restant: {restant/60:.0f} min")
                
                # Pause anti-rate limit
                time.sleep(0.5)
        
        # Resume bloc
        print(f"\nBloc {bloc_nom} termine:")
        print(f"  Succes: {stats['par_bloc'][bloc_nom]['succes']}")
        print(f"  Echecs: {stats['par_bloc'][bloc_nom]['echecs']}")
        print(f"  Observations: {stats['par_bloc'][bloc_nom]['observations']:,}")
    
    duree_totale = time.time() - debut
    
    # Resume final
    print("\n" + "="*100)
    print("COLLECTE TERMINEE")
    print("="*100)
    print(f"\nDuree totale: {duree_totale/60:.1f} minutes ({duree_totale/3600:.2f} heures)")
    print(f"Operations: {stats['total']:,}")
    print(f"Succes: {stats['succes']:,} ({stats['succes']/stats['total']*100:.1f}%)")
    print(f"Echecs: {stats['echecs']:,} ({stats['echecs']/stats['total']*100:.1f}%)")
    print(f"Observations collectees: {stats['observations']:,}")
    
    print(f"\nPAR BLOC:")
    for bloc_nom in [b[0] for b in BLOCS_ANNEES]:
        bloc_stats = stats['par_bloc'][bloc_nom]
        print(f"  {bloc_nom}: {bloc_stats['observations']:,} obs "
              f"(OK: {bloc_stats['succes']}, ECHEC: {bloc_stats['echecs']})")
    
    # Etat final
    ok, obs_finales = verifier_mongodb()
    if ok:
        nouvelles = obs_finales - obs_initiales
        print(f"\nBASE DE DONNEES:")
        print(f"   Avant: {obs_initiales:,} observations")
        print(f"   Apres: {obs_finales:,} observations")
        print(f"   Ajoutees: {nouvelles:,} observations")
    
    print("="*100 + "\n")
    logger.info(f"Collecte optimisee terminee - {stats['observations']:,} observations")

if __name__ == '__main__':
    main()
