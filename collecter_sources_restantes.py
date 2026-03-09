#!/usr/bin/env python3
"""
🚀 COLLECTEUR SOURCES RESTANTES - REPRISE
Continue les collectes World Bank, IMF, AfDB, UN SDG avec gestion d'erreurs robuste
"""
import sys
from pathlib import Path
from datetime import datetime
import logging
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collecte_sources_restantes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

try:
    import requests
    from wbgapi import economy as wb_economy
    import wbgapi as wb
except ImportError:
    logger.error("Installer: pip install requests wbgapi")
    sys.exit(1)

# Pays UEMOA
PAYS_UEMOA = {
    'BJ': 'Bénin',
    'BF': 'Burkina Faso', 
    'CI': 'Côte d\'Ivoire',
    'GW': 'Guinée-Bissau',
    'ML': 'Mali',
    'NE': 'Niger',
    'SN': 'Sénégal',
    'TG': 'Togo'
}

class CollecteurSourcesRestantes:
    """Collecteur robuste pour compléter les sources internationales"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.stats = {
            'WorldBank': {'debut': 0, 'fin': 0, 'nouvelles': 0, 'erreurs': 0},
            'IMF': {'debut': 0, 'fin': 0, 'nouvelles': 0, 'erreurs': 0},
            'AfDB': {'debut': 0, 'fin': 0, 'nouvelles': 0, 'erreurs': 0},
            'UN_SDG': {'debut': 0, 'fin': 0, 'nouvelles': 0, 'erreurs': 0}
        }
    
    def afficher_etat_initial(self):
        """Affiche l'état initial"""
        logger.info("\n" + "="*80)
        logger.info("ETAT INITIAL DE LA BASE DE DONNEES")
        logger.info("="*80)
        
        for source in self.stats.keys():
            count = self.db.curated_observations.count_documents({'source': source})
            self.stats[source]['debut'] = count
            logger.info(f"  {source:15} : {count:6,} observations")
        
        total = self.db.curated_observations.count_documents({})
        logger.info(f"  {'TOTAL':15} : {total:6,} observations")
        logger.info("="*80 + "\n")
    
    def collecter_worldbank_robuste(self):
        """Collecte World Bank avec wbgapi (plus robuste)"""
        logger.info("\n" + "="*80)
        logger.info("1/4 - COLLECTE WORLD BANK (wbgapi)")
        logger.info("="*80)
        
        # Indicateurs prioritaires (les plus importants)
        indicateurs_prioritaires = [
            'SP.POP.TOTL',      # Population
            'NY.GDP.MKTP.CD',   # PIB
            'FP.CPI.TOTL.ZG',   # Inflation
            'SL.UEM.TOTL.ZS',   # Chômage
            'SE.PRM.ENRR',      # Scolarisation primaire
            'SH.DYN.MORT',      # Mortalité infantile
            'NY.GDP.PCAP.CD',   # PIB par habitant
            'BN.CAB.XOKA.GD.ZS', # Balance courante
            'GC.DOD.TOTL.GD.ZS', # Dette publique
            'NE.EXP.GNFS.ZS',   # Exportations
            'NE.IMP.GNFS.ZS',   # Importations
            'SI.POV.GINI',      # GINI
        ]
        
        try:
            compteur = 0
            erreurs = 0
            
            for indicateur in indicateurs_prioritaires:
                for code_pays, nom_pays in PAYS_UEMOA.items():
                    try:
                        logger.info(f"Collecte {indicateur} - {nom_pays} ({code_pays})...")
                        
                        # Utiliser wbgapi pour récupérer les données
                        data = wb.data.DataFrame(
                            indicateur,
                            code_pays,
                            time=range(1960, 2027),
                            skipBlanks=True,
                            labels=False
                        )
                        
                        if not data.empty:
                            for year in data.index:
                                value = data.loc[year, code_pays]
                                
                                if value and not str(value).lower() in ['nan', 'none', '']:
                                    observation = {
                                        'source': 'WorldBank',
                                        'dataset': 'WDI',
                                        'key': f'{indicateur}_{code_pays}',
                                        'ts': str(year),
                                        'value': float(value),
                                        'attrs': {
                                            'indicator': indicateur,
                                            'country': code_pays,
                                            'country_name': nom_pays,
                                            'year': int(year),
                                            'collecte_datetime': datetime.now().isoformat()
                                        }
                                    }
                                    
                                    self.db.curated_observations.update_one(
                                        {
                                            'source': 'WorldBank',
                                            'key': f'{indicateur}_{code_pays}',
                                            'ts': str(year)
                                        },
                                        {'$set': observation},
                                        upsert=True
                                    )
                                    compteur += 1
                        
                        time.sleep(0.2)  # Rate limiting
                        
                    except Exception as e:
                        erreurs += 1
                        logger.warning(f"Erreur {indicateur} {code_pays}: {e}")
                        continue
                
                # Afficher progression
                if (indicateurs_prioritaires.index(indicateur) + 1) % 3 == 0:
                    logger.info(f"  Progression: {compteur:,} observations collectées")
            
            logger.info(f"\nWorld Bank terminé: {compteur:,} observations, {erreurs} erreurs")
            self.stats['WorldBank']['nouvelles'] = compteur
            self.stats['WorldBank']['erreurs'] = erreurs
            
        except Exception as e:
            logger.error(f"Erreur World Bank: {e}")
            import traceback
            traceback.print_exc()
    
    def collecter_imf_datamapper(self):
        """Collecte IMF via DataMapper API"""
        logger.info("\n" + "="*80)
        logger.info("2/4 - COLLECTE IMF (DataMapper)")
        logger.info("="*80)
        
        # Indicateurs WEO
        indicateurs_imf = [
            'NGDP_RPCH',    # Croissance PIB réel
            'PCPI',         # Inflation
            'LUR',          # Taux de chômage
            'BCA_NGDPD',    # Balance courante
            'GGXWDG_NGDP',  # Dette publique
        ]
        
        try:
            compteur = 0
            erreurs = 0
            
            for indicateur in indicateurs_imf:
                for code_pays, nom_pays in PAYS_UEMOA.items():
                    try:
                        url = f"https://www.imf.org/external/datamapper/api/v1/{indicateur}/{code_pays}"
                        
                        response = requests.get(url, timeout=15)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            if 'values' in data and indicateur in data['values']:
                                pays_data = data['values'][indicateur].get(code_pays, {})
                                
                                for annee, valeur in pays_data.items():
                                    if valeur is not None:
                                        observation = {
                                            'source': 'IMF',
                                            'dataset': 'WEO',
                                            'key': f'{indicateur}_{code_pays}',
                                            'ts': str(annee),
                                            'value': float(valeur),
                                            'attrs': {
                                                'indicator': indicateur,
                                                'country': code_pays,
                                                'country_name': nom_pays,
                                                'year': int(annee),
                                                'collecte_datetime': datetime.now().isoformat()
                                            }
                                        }
                                        
                                        self.db.curated_observations.update_one(
                                            {
                                                'source': 'IMF',
                                                'key': f'{indicateur}_{code_pays}',
                                                'ts': str(annee)
                                            },
                                            {'$set': observation},
                                            upsert=True
                                        )
                                        compteur += 1
                        
                        time.sleep(1.0)  # Rate limiting
                        
                    except Exception as e:
                        erreurs += 1
                        logger.warning(f"Erreur IMF {indicateur} {code_pays}: {e}")
                        continue
                
                logger.info(f"  {indicateur}: {compteur:,} observations")
            
            logger.info(f"\nIMF terminé: {compteur:,} observations, {erreurs} erreurs")
            self.stats['IMF']['nouvelles'] = compteur
            self.stats['IMF']['erreurs'] = erreurs
            
        except Exception as e:
            logger.error(f"Erreur IMF: {e}")
    
    def afficher_rapport_final(self):
        """Affiche le rapport final"""
        logger.info("\n" + "="*80)
        logger.info("RAPPORT FINAL DE COLLECTE")
        logger.info("="*80 + "\n")
        
        for source in self.stats.keys():
            count = self.db.curated_observations.count_documents({'source': source})
            self.stats[source]['fin'] = count
            
            debut = self.stats[source]['debut']
            fin = self.stats[source]['fin']
            nouvelles = self.stats[source]['nouvelles']
            erreurs = self.stats[source]['erreurs']
            gain = fin - debut
            
            logger.info(f"{source:15} | Avant: {debut:6,} | Après: {fin:6,} | Gain: +{gain:5,} | Erreurs: {erreurs:4,}")
        
        total = self.db.curated_observations.count_documents({})
        logger.info(f"\n{'TOTAL':15} | {total:6,} observations")
        logger.info("="*80)
    
    def collecter(self):
        """Lance la collecte complète"""
        debut_global = time.time()
        
        logger.info("\n" + "="*80)
        logger.info("COLLECTE SOURCES RESTANTES - DEMARRAGE")
        logger.info("="*80)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Sources: World Bank, IMF")
        logger.info("="*80 + "\n")
        
        self.afficher_etat_initial()
        
        # Collectes
        self.collecter_worldbank_robuste()
        self.collecter_imf_datamapper()
        
        # Rapport final
        self.afficher_rapport_final()
        
        duree = time.time() - debut_global
        logger.info(f"\nDurée totale: {duree/60:.1f} minutes")
        logger.info("="*80 + "\n")

def main():
    collecteur = CollecteurSourcesRestantes()
    collecteur.collecter()

if __name__ == '__main__':
    main()
