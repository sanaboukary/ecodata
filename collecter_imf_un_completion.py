#!/usr/bin/env python3
"""
🚀 COLLECTEUR IMF + UN SDG - COMPLÉTION
Complete les données manquantes IMF et UN SDG
"""
import sys
from pathlib import Path
from datetime import datetime
import logging
import time
import requests

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collecte_imf_un_completion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Pays UEMOA
PAYS_UEMOA = {
    'BJ': 'Benin',
    'BF': 'Burkina Faso', 
    'CI': "Cote d'Ivoire",
    'GW': 'Guinee-Bissau',
    'ML': 'Mali',
    'NE': 'Niger',
    'SN': 'Senegal',
    'TG': 'Togo'
}

# Indicateurs IMF WEO complets
INDICATEURS_IMF = [
    'NGDP_RPCH',      # Croissance PIB reel
    'NGDPD',          # PIB nominal
    'NGDPDPC',        # PIB par habitant
    'PPPGDP',         # PIB PPA
    'PPPPC',          # PIB PPA par habitant
    'PCPI',           # Inflation
    'PCPIPCH',        # Variation inflation
    'LUR',            # Taux de chomage
    'BCA',            # Balance courante
    'BCA_NGDPD',      # Balance courante % PIB
    'GGXWDG_NGDP',    # Dette publique % PIB
    'GGXCNL_NGDP',    # Solde budgetaire % PIB
    'TXG_RPCH',       # Croissance exports
    'TMG_RPCH',       # Croissance imports
    'TX_RPCH',        # Croissance volume exports
    'TM_RPCH',        # Croissance volume imports
    'GGR_NGDP',       # Revenus publics % PIB
    'GGX_NGDP',       # Depenses publiques % PIB
]

# Series UN SDG pour UEMOA
SERIES_UN_SDG = [
    'SI_POV_DAY1',    # Pauvrete extreme
    'SL_TLF_UEM',     # Chomage
    'SH_DYN_MORT',    # Mortalite infantile
    'SE_PRM_ENRR',    # Scolarisation primaire
    'SH_H2O_SAFE',    # Acces eau potable
    'EG_ELC_ACCS',    # Acces electricite
    'EN_ATM_CO2E',    # Emissions CO2
    'VC_IHR_PSRC',    # Homicides
]

class CollecteurIMFUNCompletion:
    """Collecteur pour completer IMF et UN SDG"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.session = requests.Session()
        self.stats = {
            'IMF': {'avant': 0, 'apres': 0, 'nouvelles': 0, 'erreurs': 0},
            'UN_SDG': {'avant': 0, 'apres': 0, 'nouvelles': 0, 'erreurs': 0}
        }
    
    def collecter_imf(self):
        """Collecte IMF via DataMapper API"""
        logger.info("\n" + "="*80)
        logger.info("1/2 - COLLECTE IMF (DataMapper)")
        logger.info("="*80)
        
        self.stats['IMF']['avant'] = self.db.curated_observations.count_documents({'source': 'IMF'})
        logger.info(f"Observations IMF initiales: {self.stats['IMF']['avant']:,}\n")
        
        compteur = 0
        erreurs = 0
        
        for i, indicateur in enumerate(INDICATEURS_IMF, 1):
            logger.info(f"[{i}/{len(INDICATEURS_IMF)}] {indicateur}")
            
            for code_pays, nom_pays in PAYS_UEMOA.items():
                try:
                    url = f"https://www.imf.org/external/datamapper/api/v1/{indicateur}/{code_pays}"
                    
                    response = self.session.get(url, timeout=8)
                    
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
                            
                            if pays_data:
                                logger.info(f"  OK {indicateur} - {nom_pays}: {len(pays_data)} obs")
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except KeyboardInterrupt:
                    logger.warning("\n⚠️ Interruption utilisateur détectée")
                    raise
                except requests.exceptions.Timeout:
                    erreurs += 1
                    logger.warning(f"  Timeout {indicateur} {code_pays} (API trop lente)")
                    continue
                except requests.exceptions.RequestException as e:
                    erreurs += 1
                    logger.warning(f"  Erreur réseau {indicateur} {code_pays}: {type(e).__name__}")
                    continue
                except Exception as e:
                    erreurs += 1
                    logger.warning(f"  Erreur {indicateur} {code_pays}: {e}")
                    continue
            
            if (i % 5 == 0):
                logger.info(f"\nProgression: {compteur:,} observations collectees\n")
        
        self.stats['IMF']['apres'] = self.db.curated_observations.count_documents({'source': 'IMF'})
        self.stats['IMF']['nouvelles'] = self.stats['IMF']['apres'] - self.stats['IMF']['avant']
        self.stats['IMF']['erreurs'] = erreurs
        
        logger.info(f"\nIMF termine: +{self.stats['IMF']['nouvelles']:,} nouvelles observations")
    
    def collecter_un_sdg(self):
        """Collecte UN SDG"""
        logger.info("\n" + "="*80)
        logger.info("2/2 - COLLECTE UN SDG")
        logger.info("="*80)
        
        self.stats['UN_SDG']['avant'] = self.db.curated_observations.count_documents({'source': 'UN_SDG'})
        logger.info(f"Observations UN SDG initiales: {self.stats['UN_SDG']['avant']:,}\n")
        
        compteur = 0
        erreurs = 0
        
        # Codes ISO3 pour UEMOA
        codes_iso3 = {
            'BJ': 'BEN', 'BF': 'BFA', 'CI': 'CIV', 'GW': 'GNB',
            'ML': 'MLI', 'NE': 'NER', 'SN': 'SEN', 'TG': 'TGO'
        }
        
        for i, serie in enumerate(SERIES_UN_SDG, 1):
            logger.info(f"[{i}/{len(SERIES_UN_SDG)}] {serie}")
            
            for code_pays, nom_pays in PAYS_UEMOA.items():
                try:
                    code_iso3 = codes_iso3.get(code_pays, code_pays)
                    
                    # API UN SDG
                    url = "https://unstats.un.org/sdgapi/v1/sdg/Series/Data"
                    params = {
                        'seriesCode': serie,
                        'areaCode': code_iso3,
                        'pageSize': 100
                    }
                    
                    response = self.session.get(url, params=params, timeout=20)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'data' in data:
                            for item in data['data']:
                                annee = item.get('timePeriodStart', '')
                                valeur = item.get('value')
                                
                                if annee and valeur:
                                    observation = {
                                        'source': 'UN_SDG',
                                        'dataset': 'SDG',
                                        'key': f'{serie}_{code_pays}',
                                        'ts': str(annee),
                                        'value': float(valeur),
                                        'attrs': {
                                            'series': serie,
                                            'country': code_pays,
                                            'country_name': nom_pays,
                                            'year': int(annee),
                                            'collecte_datetime': datetime.now().isoformat()
                                        }
                                    }
                                    
                                    self.db.curated_observations.update_one(
                                        {
                                            'source': 'UN_SDG',
                                            'key': f'{serie}_{code_pays}',
                                            'ts': str(annee)
                                        },
                                        {'$set': observation},
                                        upsert=True
                                    )
                                    compteur += 1
                            
                            if data['data']:
                                logger.info(f"  OK {serie} - {nom_pays}: {len(data['data'])} obs")
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    erreurs += 1
                    logger.warning(f"  Erreur {serie} {code_pays}: {e}")
                    continue
        
        self.stats['UN_SDG']['apres'] = self.db.curated_observations.count_documents({'source': 'UN_SDG'})
        self.stats['UN_SDG']['nouvelles'] = self.stats['UN_SDG']['apres'] - self.stats['UN_SDG']['avant']
        self.stats['UN_SDG']['erreurs'] = erreurs
        
        logger.info(f"\nUN SDG termine: +{self.stats['UN_SDG']['nouvelles']:,} nouvelles observations")
    
    def afficher_rapport_final(self):
        """Affiche le rapport final"""
        logger.info("\n" + "="*80)
        logger.info("RAPPORT FINAL")
        logger.info("="*80 + "\n")
        
        for source in ['IMF', 'UN_SDG']:
            avant = self.stats[source]['avant']
            apres = self.stats[source]['apres']
            nouvelles = self.stats[source]['nouvelles']
            erreurs = self.stats[source]['erreurs']
            
            logger.info(f"{source:10} | Avant: {avant:6,} | Apres: {apres:6,} | Gain: +{nouvelles:5,} | Erreurs: {erreurs:4,}")
        
        # Total global
        total = self.db.curated_observations.count_documents({})
        logger.info(f"\nTOTAL GLOBAL: {total:,} observations")
        logger.info("="*80 + "\n")
    
    def collecter(self):
        """Lance la collecte complete"""
        debut = time.time()
        
        logger.info("\n" + "="*80)
        logger.info("COLLECTEUR IMF + UN SDG - COMPLETION")
        logger.info("="*80)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"IMF: {len(INDICATEURS_IMF)} indicateurs x 8 pays")
        logger.info(f"UN SDG: {len(SERIES_UN_SDG)} series x 8 pays")
        logger.info("="*80 + "\n")
        
        # Collectes
        self.collecter_imf()
        self.collecter_un_sdg()
        
        # Rapport final
        self.afficher_rapport_final()
        
        duree = time.time() - debut
        logger.info(f"Duree totale: {duree/60:.1f} minutes\n")

def main():
    collecteur = CollecteurIMFUNCompletion()
    collecteur.collecter()

if __name__ == '__main__':
    main()
