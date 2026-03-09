#!/usr/bin/env python3
"""
🚀 COLLECTEUR WORLD BANK - API REST DIRECTE
Utilise l'API REST directement (méthode testée et validée)
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
        logging.FileHandler('collecte_wb_rest_direct.log'),
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
    'BJ': 'Bénin',
    'BF': 'Burkina Faso', 
    'CI': 'Côte d\'Ivoire',
    'GW': 'Guinée-Bissau',
    'ML': 'Mali',
    'NE': 'Niger',
    'SN': 'Sénégal',
    'TG': 'Togo'
}

# Top 30 indicateurs prioritaires
INDICATEURS_WB = [
    'SP.POP.TOTL',       # Population totale
    'NY.GDP.MKTP.CD',    # PIB ($ courants)
    'NY.GDP.MKTP.KD.ZG', # Croissance PIB
    'NY.GDP.PCAP.CD',    # PIB par habitant
    'FP.CPI.TOTL.ZG',    # Inflation
    'SL.UEM.TOTL.ZS',    # Taux de chômage
    'SE.PRM.ENRR',       # Scolarisation primaire
    'SE.SEC.ENRR',       # Scolarisation secondaire
    'SE.TER.ENRR',       # Scolarisation tertiaire
    'SH.DYN.MORT',       # Mortalité infantile
    'SP.DYN.LE00.IN',    # Espérance de vie
    'SH.XPD.CHEX.GD.ZS', # Dépenses santé
    'SE.XPD.TOTL.GD.ZS', # Dépenses éducation
    'BN.CAB.XOKA.GD.ZS', # Balance courante
    'GC.DOD.TOTL.GD.ZS', # Dette publique
    'NE.EXP.GNFS.ZS',    # Exportations
    'NE.IMP.GNFS.ZS',    # Importations
    'BX.KLT.DINV.WD.GD.ZS', # IDE
    'SI.POV.GINI',       # Indice GINI
    'SI.POV.DDAY',       # Pauvreté $2.15/jour
    'AG.LND.AGRI.ZS',    # Terres agricoles
    'EG.USE.ELEC.KH.PC', # Consommation électricité
    'EN.ATM.CO2E.PC',    # Émissions CO2
    'IT.NET.USER.ZS',    # Utilisateurs internet
    'SP.URB.TOTL.IN.ZS', # Population urbaine
    'SL.TLF.TOTL.IN',    # Population active
    'NY.ADJ.NNTY.PC.CD', # Revenu national net
    'NV.IND.TOTL.ZS',    # Industrie (% PIB)
    'NV.AGR.TOTL.ZS',    # Agriculture (% PIB)
    'NV.SRV.TOTL.ZS',    # Services (% PIB)
]

class CollecteurWBRestDirect:
    """Collecteur utilisant API REST directe"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.session = requests.Session()
        self.compteur_total = 0
        self.erreurs_total = 0
    
    def collecter_indicateur_pays(self, indicateur, code_pays, nom_pays):
        """Collecte un indicateur pour un pays"""
        try:
            url = f"https://api.worldbank.org/v2/country/{code_pays}/indicator/{indicateur}"
            params = {
                'format': 'json',
                'per_page': 100,
                'date': '1960:2026'
            }
            
            response = self.session.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 1:
                    observations = data[1]
                    
                    compteur_local = 0
                    for obs in observations:
                        if obs.get('value') is not None:
                            annee = obs.get('date', '')
                            valeur = obs.get('value')
                            
                            observation = {
                                'source': 'WorldBank',
                                'dataset': 'WDI',
                                'key': f'{indicateur}_{code_pays}',
                                'ts': str(annee),
                                'value': float(valeur),
                                'attrs': {
                                    'indicator': indicateur,
                                    'indicator_name': obs.get('indicator', {}).get('value', ''),
                                    'country': code_pays,
                                    'country_name': nom_pays,
                                    'year': int(annee),
                                    'unit': obs.get('unit', ''),
                                    'decimal': obs.get('decimal', 0),
                                    'collecte_datetime': datetime.now().isoformat()
                                }
                            }
                            
                            self.db.curated_observations.update_one(
                                {
                                    'source': 'WorldBank',
                                    'key': f'{indicateur}_{code_pays}',
                                    'ts': str(annee)
                                },
                                {'$set': observation},
                                upsert=True
                            )
                            compteur_local += 1
                    
                    self.compteur_total += compteur_local
                    if compteur_local > 0:
                        logger.info(f"  ✅ {indicateur} - {nom_pays}: {compteur_local} obs")
                    return True
                else:
                    logger.debug(f"  ⚠️  {indicateur} - {nom_pays}: réponse vide")
                    return False
            else:
                logger.warning(f"  ❌ {indicateur} - {nom_pays}: HTTP {response.status_code}")
                self.erreurs_total += 1
                return False
                
        except requests.Timeout:
            logger.warning(f"  ⏱️  {indicateur} - {nom_pays}: timeout")
            self.erreurs_total += 1
            return False
        except Exception as e:
            logger.warning(f"  ❌ {indicateur} - {nom_pays}: {e}")
            self.erreurs_total += 1
            return False
    
    def collecter(self):
        """Lance la collecte complète"""
        logger.info("\n" + "="*80)
        logger.info("COLLECTE WORLD BANK - API REST DIRECTE")
        logger.info("="*80)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Indicateurs: {len(INDICATEURS_WB)}")
        logger.info(f"Pays: {len(PAYS_UEMOA)}")
        logger.info(f"Période: 1960-2026")
        logger.info("="*80 + "\n")
        
        # État initial
        count_initial = self.db.curated_observations.count_documents({'source': 'WorldBank'})
        logger.info(f"Observations initiales: {count_initial:,}\n")
        
        debut = time.time()
        
        # Collecte par indicateur
        for i, indicateur in enumerate(INDICATEURS_WB, 1):
            logger.info(f"[{i}/{len(INDICATEURS_WB)}] {indicateur}")
            
            for code_pays, nom_pays in PAYS_UEMOA.items():
                self.collecter_indicateur_pays(indicateur, code_pays, nom_pays)
                time.sleep(0.3)  # Rate limiting
            
            # Afficher progression tous les 5 indicateurs
            if i % 5 == 0:
                logger.info(f"\n📊 Progression: {self.compteur_total:,} observations collectées\n")
        
        # Rapport final
        duree = time.time() - debut
        count_final = self.db.curated_observations.count_documents({'source': 'WorldBank'})
        gain = count_final - count_initial
        
        logger.info("\n" + "="*80)
        logger.info("RAPPORT FINAL")
        logger.info("="*80)
        logger.info(f"Durée: {duree/60:.1f} minutes")
        logger.info(f"Observations avant: {count_initial:,}")
        logger.info(f"Observations après: {count_final:,}")
        logger.info(f"Gain: +{gain:,}")
        logger.info(f"Requêtes réussies: {self.compteur_total:,}")
        logger.info(f"Erreurs: {self.erreurs_total}")
        logger.info("="*80 + "\n")

def main():
    collecteur = CollecteurWBRestDirect()
    collecteur.collecter()

if __name__ == '__main__':
    main()
