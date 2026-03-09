#!/usr/bin/env python3
"""
🌍 COLLECTE MASTER UEMOA - TOUTES LES SOURCES
Collecte exhaustive pour les 8 pays de l'UEMOA:
1. World Bank (66 indicateurs)
2. IMF WEO (18 indicateurs)
3. AfDB (African Economic Outlook + autres)
4. UN SDG (8 objectifs)

Période: 1960-2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import time
import subprocess

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collecte_master_uemoa.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# 8 PAYS UEMOA
PAYS_UEMOA = {
    'BJ': 'Bénin',
    'BF': 'Burkina Faso',
    'CI': "Côte d'Ivoire",
    'GW': 'Guinée-Bissau',
    'ML': 'Mali',
    'NE': 'Niger',
    'SN': 'Sénégal',
    'TG': 'Togo'
}

class CollecteurMasterUEMOA:
    """Collecteur master pour toutes les sources UEMOA"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.debut = time.time()
        self.stats_globales = {
            'worldbank': 0,
            'imf': 0,
            'afdb': 0,
            'un_sdg': 0,
            'brvm': 0
        }
    
    def afficher_etat_initial(self):
        """Afficher l'état actuel de la base"""
        logger.info("="*100)
        logger.info("📊 ÉTAT INITIAL DE LA BASE DE DONNÉES")
        logger.info("="*100)
        
        total = self.db.curated_observations.count_documents({})
        wb = self.db.curated_observations.count_documents({'source': 'WorldBank'})
        imf = self.db.curated_observations.count_documents({'source': 'IMF'})
        afdb = self.db.curated_observations.count_documents({'source': 'AfDB'})
        un = self.db.curated_observations.count_documents({'source': 'UN_SDG'})
        brvm = self.db.curated_observations.count_documents({'source': 'BRVM'})
        
        logger.info(f"\nObservations actuelles:")
        logger.info(f"  TOTAL         : {total:8,}")
        logger.info(f"  World Bank    : {wb:8,}")
        logger.info(f"  IMF           : {imf:8,}")
        logger.info(f"  AfDB          : {afdb:8,}")
        logger.info(f"  UN SDG        : {un:8,}")
        logger.info(f"  BRVM          : {brvm:8,}")
        
        self.stats_globales = {
            'worldbank': wb,
            'imf': imf,
            'afdb': afdb,
            'un_sdg': un,
            'brvm': brvm
        }
        
        logger.info("\n" + "="*100 + "\n")
    
    def collecter_worldbank(self):
        """Collecter World Bank via script existant"""
        logger.info("="*100)
        logger.info("🌍 1/4 - COLLECTE WORLD BANK")
        logger.info("="*100)
        logger.info("66 indicateurs × 8 pays × 67 années (1960-2026)")
        logger.info("Objectif: ~35,000 observations")
        logger.info("-"*100)
        
        try:
            # Utiliser le script optimisé existant
            script = BASE_DIR / "collecter_wb_optimise.py"
            
            if script.exists():
                logger.info("Lancement collecter_wb_optimise.py...")
                result = subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True,
                    text=True,
                    timeout=7200  # 2 heures max
                )
                
                if result.returncode == 0:
                    logger.info("✅ World Bank collecté avec succès")
                else:
                    logger.error(f"❌ Erreur World Bank: {result.stderr[:500]}")
            else:
                logger.warning("⚠️ Script collecter_wb_optimise.py introuvable")
                
        except subprocess.TimeoutExpired:
            logger.warning("⏱ World Bank timeout (>2h) - Probablement OK")
        except Exception as e:
            logger.error(f"❌ Erreur World Bank: {e}")
    
    def collecter_imf(self):
        """Collecter IMF via script existant"""
        logger.info("\n" + "="*100)
        logger.info("💰 2/4 - COLLECTE FMI")
        logger.info("="*100)
        logger.info("18 indicateurs WEO × 8 pays × 67 années")
        logger.info("Objectif: ~9,000 observations")
        logger.info("-"*100)
        
        try:
            script = BASE_DIR / "collecter_imf_uemoa_complet.py"
            
            if script.exists():
                logger.info("Lancement collecter_imf_uemoa_complet.py...")
                result = subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 heure max
                )
                
                if result.returncode == 0:
                    logger.info("✅ IMF collecté avec succès")
                else:
                    logger.error(f"❌ Erreur IMF: {result.stderr[:500]}")
            else:
                logger.warning("⚠️ Script collecter_imf_uemoa_complet.py introuvable")
                
        except subprocess.TimeoutExpired:
            logger.warning("⏱ IMF timeout (>1h)")
        except Exception as e:
            logger.error(f"❌ Erreur IMF: {e}")
    
    def collecter_afdb(self):
        """Collecter AfDB (African Economic Outlook)"""
        logger.info("\n" + "="*100)
        logger.info("🏦 3/4 - COLLECTE AFDB")
        logger.info("="*100)
        logger.info("African Economic Outlook + Infrastructure + Operations")
        logger.info("-"*100)
        
        from scripts.connectors.afdb import fetch_afdb_sdmx
        
        # Indicateurs clés AfDB
        indicateurs_afdb = [
            'GDP_GROWTH',
            'INFLATION',
            'FISCAL_BALANCE',
            'CURRENT_ACCOUNT',
            'DEBT_GDP',
            'FDI_GDP',
            'RESERVES',
            'TRADE_BALANCE'
        ]
        
        count_total = 0
        
        for indicateur in indicateurs_afdb:
            logger.info(f"\nIndicateur: {indicateur}")
            
            for code_pays, nom_pays in PAYS_UEMOA.items():
                try:
                    key = f"{code_pays}.{indicateur}"
                    obs = fetch_afdb_sdmx('AFDB_MAIN', key)
                    
                    if obs:
                        for observation in obs:
                            self.db.curated_observations.update_one(
                                {
                                    'source': observation['source'],
                                    'dataset': observation['dataset'],
                                    'key': observation['key'],
                                    'ts': observation['ts']
                                },
                                {'$set': observation},
                                upsert=True
                            )
                        
                        count_total += len(obs)
                        logger.info(f"  ✓ {nom_pays}: {len(obs)} obs")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"  ✗ {nom_pays}: {e}")
        
        logger.info(f"\n✅ AfDB: {count_total} observations collectées")
    
    def collecter_un_sdg(self):
        """Collecter UN SDG (Objectifs Développement Durable)"""
        logger.info("\n" + "="*100)
        logger.info("🌐 4/4 - COLLECTE UN SDG")
        logger.info("="*100)
        logger.info("8 objectifs développement durable × 8 pays")
        logger.info("-"*100)
        
        from scripts.connectors.un_sdg import fetch_un_sdg
        
        # Objectifs SDG clés
        series_sdg = [
            'SI_POV_DAY1',      # Pauvreté extrême
            'SL_TLF_UEM',       # Chômage
            'SH_DYN_MORT',      # Mortalité infantile
            'SE_PRM_ENRR',      # Scolarisation primaire
            'SH_H2O_SAFE',      # Eau potable
            'EG_ELC_ACCS',      # Électricité
            'EN_ATM_CO2E',      # CO2
            'VC_IHR_PSRC'       # Homicides
        ]
        
        count_total = 0
        
        for serie in series_sdg:
            logger.info(f"\nSérie: {serie}")
            
            for code_pays, nom_pays in PAYS_UEMOA.items():
                try:
                    obs = fetch_un_sdg(serie, code_pays, '2000:2026')
                    
                    if obs:
                        for observation in obs:
                            self.db.curated_observations.update_one(
                                {
                                    'source': observation['source'],
                                    'dataset': observation['dataset'],
                                    'key': observation['key'],
                                    'ts': observation['ts']
                                },
                                {'$set': observation},
                                upsert=True
                            )
                        
                        count_total += len(obs)
                        logger.info(f"  ✓ {nom_pays}: {len(obs)} obs")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"  ✗ {nom_pays}: {e}")
        
        logger.info(f"\n✅ UN SDG: {count_total} observations collectées")
    
    def afficher_rapport_final(self):
        """Rapport final complet"""
        duree = time.time() - self.debut
        
        # État final
        total = self.db.curated_observations.count_documents({})
        wb = self.db.curated_observations.count_documents({'source': 'WorldBank'})
        imf = self.db.curated_observations.count_documents({'source': 'IMF'})
        afdb = self.db.curated_observations.count_documents({'source': 'AfDB'})
        un = self.db.curated_observations.count_documents({'source': 'UN_SDG'})
        brvm = self.db.curated_observations.count_documents({'source': 'BRVM'})
        
        logger.info("\n" + "="*100)
        logger.info("🎯 RAPPORT FINAL - COLLECTE MASTER UEMOA")
        logger.info("="*100)
        
        logger.info(f"\n⏱  Durée totale: {duree/60:.1f} minutes ({duree/3600:.1f}h)")
        logger.info(f"📅 Période: 1960-2026 (67 années)")
        logger.info(f"🌍 Pays: {len(PAYS_UEMOA)} (UEMOA)")
        
        logger.info(f"\n📊 OBSERVATIONS FINALES:")
        logger.info(f"  TOTAL         : {total:8,} (+{total - sum(self.stats_globales.values()):,})")
        logger.info(f"  World Bank    : {wb:8,} (+{wb - self.stats_globales['worldbank']:,})")
        logger.info(f"  IMF           : {imf:8,} (+{imf - self.stats_globales['imf']:,})")
        logger.info(f"  AfDB          : {afdb:8,} (+{afdb - self.stats_globales['afdb']:,})")
        logger.info(f"  UN SDG        : {un:8,} (+{un - self.stats_globales['un_sdg']:,})")
        logger.info(f"  BRVM          : {brvm:8,} (+{brvm - self.stats_globales['brvm']:,})")
        
        # Répartition par pays
        logger.info(f"\n📍 RÉPARTITION PAR PAYS (hors BRVM):")
        for code_pays, nom_pays in PAYS_UEMOA.items():
            count_wb = self.db.curated_observations.count_documents({
                'source': 'WorldBank',
                'key': {'$regex': f'^{code_pays}\\.'}
            })
            count_imf = self.db.curated_observations.count_documents({
                'source': 'IMF',
                'attrs.pays': code_pays
            })
            count_total = count_wb + count_imf
            logger.info(f"   {nom_pays:20} : {count_total:6,} obs (WB:{count_wb:,} + IMF:{count_imf:,})")
        
        # Objectifs atteints
        logger.info(f"\n🎯 OBJECTIFS:")
        objectifs = {
            'World Bank': (wb, 35000),
            'IMF': (imf, 9000),
            'AfDB': (afdb, 1000),
            'UN SDG': (un, 500),
        }
        
        for source, (actuel, cible) in objectifs.items():
            progression = (actuel / cible * 100) if cible > 0 else 0
            status = "✅" if progression >= 80 else "⏳" if progression >= 50 else "⚠️"
            logger.info(f"   {status} {source:15} : {actuel:6,} / {cible:6,} ({progression:5.1f}%)")
        
        logger.info("\n" + "="*100)
        logger.info("✅ COLLECTE MASTER TERMINÉE")
        logger.info("="*100 + "\n")
    
    def collecter_tout(self):
        """Lancer collecte complète"""
        logger.info("\n" + "="*100)
        logger.info("🚀 COLLECTE MASTER UEMOA - DÉMARRAGE")
        logger.info("="*100)
        logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🌍 8 pays UEMOA: {', '.join(PAYS_UEMOA.values())}")
        logger.info(f"📊 4 sources: World Bank, IMF, AfDB, UN SDG")
        logger.info(f"📈 Période: 1960-2026")
        logger.info("="*100 + "\n")
        
        self.afficher_etat_initial()
        
        # 1. World Bank (prioritaire - le plus long)
        try:
            self.collecter_worldbank()
        except Exception as e:
            logger.error(f"❌ Erreur World Bank: {e}")
        
        # 2. IMF
        try:
            self.collecter_imf()
        except Exception as e:
            logger.error(f"❌ Erreur IMF: {e}")
        
        # 3. AfDB
        try:
            self.collecter_afdb()
        except Exception as e:
            logger.error(f"❌ Erreur AfDB: {e}")
        
        # 4. UN SDG
        try:
            self.collecter_un_sdg()
        except Exception as e:
            logger.error(f"❌ Erreur UN SDG: {e}")
        
        # Rapport final
        self.afficher_rapport_final()

def main():
    collecteur = CollecteurMasterUEMOA()
    collecteur.collecter_tout()

if __name__ == '__main__':
    main()
