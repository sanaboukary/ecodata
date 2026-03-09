#!/usr/bin/env python3
"""
🌍 COLLECTE HISTORIQUE COMPLÈTE WORLD BANK 1960-2026
Collecte exhaustive pour analyse macroéconomique UEMOA
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import logging

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'collecte_wb_1960_2026_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# 8 Pays UEMOA
PAYS_UEMOA = ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']

NOMS_PAYS = {
    'BJ': 'Bénin', 'BF': 'Burkina Faso', 'CI': 'Côte d\'Ivoire',
    'GW': 'Guinée-Bissau', 'ML': 'Mali', 'NE': 'Niger',
    'SN': 'Sénégal', 'TG': 'Togo'
}

# Tous les indicateurs demandés (80+)
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
    
    # Population & Démographie
    'SP.POP.TOTL', 'SP.POP.GROW', 'SP.URB.TOTL.IN.ZS',
    'SP.POP.0014.TO.ZS', 'SP.POP.1564.TO.ZS', 'SP.POP.65UP.TO.ZS',
    'SP.DYN.TFRT.IN', 'SP.DYN.LE00.IN',
    
    # Santé
    'SH.DYN.MORT', 'SH.DYN.NMRT', 'SH.STA.MMRT',
    'SH.XPD.CHEX.GD.ZS', 'SH.MED.PHYS.ZS',
    'SH.H2O.BASW.ZS', 'SH.STA.BASS.ZS',
    
    # Éducation
    'SE.PRM.ENRR', 'SE.SEC.ENRR', 'SE.TER.ENRR',
    'SE.XPD.TOTL.GD.ZS', 'SE.ADT.LITR.ZS', 'SE.PRM.CMPT.ZS',
    
    # Infrastructure
    'EG.ELC.ACCS.ZS', 'IT.NET.USER.ZS', 'IT.CEL.SETS.P2',
    'IS.ROD.PAVE.ZS', 'IS.AIR.PSGR',
    
    # Environnement & Agriculture
    'AG.LND.AGRI.ZS', 'AG.LND.FRST.ZS', 'EN.ATM.CO2E.KT',
    'AG.PRD.CROP.XD', 'AG.YLD.CREL.KG',
    
    # Pauvreté & Inégalités
    'SI.POV.DDAY', 'SI.POV.NAHC', 'SI.POV.GINI',
    'SI.DST.FRST.20', 'SI.DST.05TH.20',
]

# Période complète : 1960-2026 (67 ans)
ANNEES = list(range(1960, 2027))

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

def collecter_avec_retry(indicateur, pays, annee, max_retries=3):
    """Collecter avec retry en cas d'erreur"""
    for tentative in range(max_retries):
        try:
            result = run_ingestion(
                source='worldbank',
                indicator=indicateur,
                country=pays,
                year=annee
            )
            
            if result.get('status') == 'success':
                obs = result.get('obs_count', 0)
                if obs > 0:
                    return {'ok': True, 'obs': obs}
                return {'ok': True, 'obs': 0}
            else:
                if tentative < max_retries - 1:
                    time.sleep(1)
                    continue
                return {'ok': False, 'obs': 0}
        except Exception as e:
            if tentative < max_retries - 1:
                time.sleep(1)
                continue
            logger.error(f"Erreur {indicateur}|{pays}|{annee}: {e}")
            return {'ok': False, 'obs': 0}
    
    return {'ok': False, 'obs': 0}

def main():
    print("\n" + "="*100)
    print("COLLECTE HISTORIQUE COMPLETE WORLD BANK 1960-2026 - PAYS UEMOA")
    print("="*100)
    print(f"Debut: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Indicateurs: {len(INDICATEURS)}")
    print(f"Pays: {len(PAYS_UEMOA)} - {', '.join(PAYS_UEMOA)}")
    print(f"Periode: {ANNEES[0]}-{ANNEES[-1]} ({len(ANNEES)} ans)")
    
    total_ops = len(INDICATEURS) * len(PAYS_UEMOA) * len(ANNEES)
    duree_estimee_min = (total_ops * 0.5) / 60
    
    print(f"\nESTIMATION:")
    print(f"   Total operations: {total_ops:,}")
    print(f"   Duree estimee: ~{duree_estimee_min:.0f} minutes (~{duree_estimee_min/60:.1f} heures)")
    print("="*100 + "\n")
    
    # Verifier MongoDB
    ok, obs_initiales = verifier_mongodb()
    if not ok:
        logger.error("ERREUR: MongoDB non accessible")
        return
    
    print(f"Observations actuelles: {obs_initiales:,}\n")
    print("Demarrage de la collecte dans 3 secondes...")
    time.sleep(3)
    
    # Statistiques
    stats = {
        'total': 0,
        'succes': 0,
        'echecs': 0,
        'observations': 0,
        'sans_donnee': 0
    }
    
    debut = time.time()
    derniere_maj = time.time()
    
    # Collecte par annee (ordre chronologique)
    for idx_annee, annee in enumerate(ANNEES):
        print(f"\n{'='*100}")
        print(f"ANNEE {annee} ({idx_annee+1}/{len(ANNEES)})")
        print(f"{'='*100}")
        
        for indicateur in INDICATEURS:
            for pays in PAYS_UEMOA:
                stats['total'] += 1
                
                result = collecter_avec_retry(indicateur, pays, annee)
                
                if result['ok']:
                    stats['succes'] += 1
                    if result['obs'] > 0:
                        stats['observations'] += result['obs']
                        logger.debug(f"OK {annee}|{indicateur}|{pays}: {result['obs']} obs")
                    else:
                        stats['sans_donnee'] += 1
                else:
                    stats['echecs'] += 1
                    logger.warning(f"ECHEC {annee}|{indicateur}|{pays}")
                
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
                time.sleep(0.3)
        
        # Resume annee
        print(f"\nAnnee {annee} terminee - {stats['observations']:,} observations totales")
    
    duree_totale = time.time() - debut
    
    # Resume final
    print("\n" + "="*100)
    print("COLLECTE TERMINEE")
    print("="*100)
    print(f"\nDuree totale: {duree_totale/60:.1f} minutes ({duree_totale/3600:.2f} heures)")
    print(f"Operations: {stats['total']:,}")
    print(f"Succes: {stats['succes']:,} ({stats['succes']/stats['total']*100:.1f}%)")
    print(f"Echecs: {stats['echecs']:,} ({stats['echecs']/stats['total']*100:.1f}%)")
    print(f"Sans donnee: {stats['sans_donnee']:,}")
    print(f"Observations collectees: {stats['observations']:,}")
    
    # Etat final
    ok, obs_finales = verifier_mongodb()
    if ok:
        nouvelles = obs_finales - obs_initiales
        print(f"\nBASE DE DONNEES:")
        print(f"   Avant: {obs_initiales:,} observations")
        print(f"   Apres: {obs_finales:,} observations")
        print(f"   Ajoutees: {nouvelles:,} observations")
    
    print("="*100 + "\n")
    logger.info(f"Collecte 1960-2026 terminee - {stats['observations']:,} observations")

if __name__ == '__main__':
    main()
