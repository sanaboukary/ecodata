#!/usr/bin/env python3
"""
🌍 COLLECTE COMPLÈTE FMI - PAYS UEMOA 1960-2026
Collecte tous les indicateurs FMI WEO pour les 8 pays UEMOA
"""

import os
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
        logging.FileHandler('collecte_imf_uemoa_complete.log'),
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

# INDICATEURS WEO PRIORITAIRES
INDICATEURS_WEO = {
    'NGDP_RPCH': 'Croissance du PIB réel (%)',
    'NGDPD': 'PIB nominal (USD)',
    'NGDPPC': 'PIB par habitant (USD)',
    'PCPI': 'Inflation (prix à la consommation, %)',
    'PCPIPCH': 'Variation inflation (%)',
    'LUR': 'Taux de chômage (%)',
    'BCA': 'Balance courante (milliards USD)',
    'BCA_NGDPD': 'Balance courante (% PIB)',
    'GGXWDG_NGDP': 'Dette publique brute (% PIB)',
    'GGXCNL_NGDP': 'Solde budgétaire net (% PIB)',
    'GGR_NGDP': 'Revenus gouvernementaux (% PIB)',
    'GGX_NGDP': 'Dépenses gouvernementales (% PIB)',
    'NID_NGDP': 'Investissement (% PIB)',
    'NGSD_NGDP': 'Épargne nationale brute (% PIB)',
    'TM_RPCH': 'Croissance importations (%)',
    'TX_RPCH': 'Croissance exportations (%)',
    'PPPPC': 'PIB par habitant (PPA, USD international)',
    'PPPEX': 'Taux de change PPA',
}

class CollecteurIMFComplet:
    """Collecteur complet FMI pour UEMOA"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.stats = {
            'tentatives': 0,
            'succes': 0,
            'echecs': 0,
            'observations': 0
        }
        self.debut = time.time()
    
    def collecter_weo_datamapper(self, indicateur, pays_code):
        """
        Collecter via l'API WEO DataMapper
        URL: https://www.imf.org/external/datamapper/api/v1/{indicateur}/{pays}
        """
        url = f"https://www.imf.org/external/datamapper/api/v1/{indicateur}/{pays_code}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Structure: {"values": {"INDICATEUR": {"PAYS": {"ANNEE": "VALEUR"}}}}
            if 'values' not in data:
                return []
            
            observations = []
            
            # Extraire les données
            if indicateur in data['values']:
                pays_data = data['values'][indicateur].get(pays_code, {})
                
                for annee, valeur in pays_data.items():
                    if valeur is None or valeur == 'n/a':
                        continue
                    
                    try:
                        valeur_float = float(valeur)
                    except (ValueError, TypeError):
                        continue
                    
                    observation = {
                        'source': 'IMF',
                        'dataset': 'WEO',
                        'key': f"{pays_code}.{indicateur}",
                        'ts': f"{annee}-12-31",  # Fin d'année
                        'value': valeur_float,
                        'attrs': {
                            'pays': pays_code,
                            'pays_nom': PAYS_UEMOA[pays_code],
                            'indicateur': indicateur,
                            'indicateur_nom': INDICATEURS_WEO[indicateur],
                            'annee': int(annee),
                            'source_api': 'WEO_DataMapper'
                        }
                    }
                    
                    observations.append(observation)
            
            return observations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur requête {indicateur}/{pays_code}: {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur parsing {indicateur}/{pays_code}: {e}")
            return []
    
    def sauvegarder_observations(self, observations):
        """Sauvegarder dans MongoDB"""
        count = 0
        
        for obs in observations:
            try:
                self.db.curated_observations.update_one(
                    {
                        'source': obs['source'],
                        'dataset': obs['dataset'],
                        'key': obs['key'],
                        'ts': obs['ts']
                    },
                    {'$set': obs},
                    upsert=True
                )
                count += 1
            except Exception as e:
                logger.error(f"Erreur sauvegarde: {e}")
        
        return count
    
    def collecter_tout(self):
        """Collecter tous les indicateurs pour tous les pays"""
        logger.info("="*100)
        logger.info("🌍 COLLECTE FMI COMPLÈTE - PAYS UEMOA")
        logger.info("="*100)
        logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🌍 {len(PAYS_UEMOA)} pays: {', '.join(PAYS_UEMOA.values())}")
        logger.info(f"📊 {len(INDICATEURS_WEO)} indicateurs WEO")
        logger.info(f"📈 Période: 1960 - {datetime.now().year}")
        logger.info("="*100)
        
        total_operations = len(INDICATEURS_WEO) * len(PAYS_UEMOA)
        logger.info(f"\n🎯 Total opérations: {total_operations}")
        logger.info(f"⏱  Temps estimé: ~{total_operations * 2 / 60:.1f} minutes\n")
        
        # Collecter par indicateur
        for idx, (code_indicateur, nom_indicateur) in enumerate(INDICATEURS_WEO.items(), 1):
            logger.info(f"\n[{idx}/{len(INDICATEURS_WEO)}] {code_indicateur} - {nom_indicateur}")
            logger.info("-" * 80)
            
            obs_indicateur = 0
            
            for code_pays, nom_pays in PAYS_UEMOA.items():
                self.stats['tentatives'] += 1
                
                try:
                    # Collecter
                    observations = self.collecter_weo_datamapper(code_indicateur, code_pays)
                    
                    if observations:
                        # Sauvegarder
                        count = self.sauvegarder_observations(observations)
                        
                        self.stats['succes'] += 1
                        self.stats['observations'] += count
                        obs_indicateur += count
                        
                        # Afficher période couverte
                        annees = sorted([obs['attrs']['annee'] for obs in observations])
                        periode = f"{annees[0]}-{annees[-1]}" if annees else "N/A"
                        
                        logger.info(f"  ✓ {nom_pays:20} : {count:3} obs ({periode})")
                    else:
                        logger.warning(f"  ⚠ {nom_pays:20} : Aucune donnée")
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"  ✗ {nom_pays:20} : {e}")
                    self.stats['echecs'] += 1
            
            logger.info(f"\n   Sous-total: {obs_indicateur} observations")
            
            # Pause entre indicateurs
            if idx % 5 == 0:
                logger.info(f"\n⏸  Pause 10s après {idx} indicateurs...")
                time.sleep(10)
        
        self.afficher_rapport_final()
    
    def afficher_rapport_final(self):
        """Rapport final"""
        duree = time.time() - self.debut
        
        logger.info("\n" + "="*100)
        logger.info("📊 RAPPORT FINAL - COLLECTE FMI UEMOA")
        logger.info("="*100)
        
        logger.info(f"\n⏱  Durée totale: {duree/60:.1f} minutes ({duree:.0f}s)")
        logger.info(f"📅 Période couverte: 1960 - {datetime.now().year}")
        
        logger.info(f"\n📈 STATISTIQUES:")
        logger.info(f"   Tentatives: {self.stats['tentatives']}")
        logger.info(f"   Succès: {self.stats['succes']}")
        logger.info(f"   Échecs: {self.stats['echecs']}")
        logger.info(f"   Observations: {self.stats['observations']:,}")
        
        if self.stats['tentatives'] > 0:
            taux = (self.stats['succes'] / self.stats['tentatives']) * 100
            logger.info(f"   Taux succès: {taux:.1f}%")
        
        if duree > 0:
            debit = self.stats['observations'] / (duree / 60)
            logger.info(f"   Débit: {debit:.0f} obs/min")
        
        # Vérification MongoDB
        logger.info(f"\n📊 VÉRIFICATION BASE DE DONNÉES:")
        
        total_imf = self.db.curated_observations.count_documents({'source': 'IMF'})
        total_weo = self.db.curated_observations.count_documents({
            'source': 'IMF',
            'dataset': 'WEO'
        })
        
        logger.info(f"   Total IMF: {total_imf:,} observations")
        logger.info(f"   Total WEO: {total_weo:,} observations")
        
        # Par pays
        logger.info(f"\n📍 RÉPARTITION PAR PAYS:")
        for code_pays, nom_pays in PAYS_UEMOA.items():
            count = self.db.curated_observations.count_documents({
                'source': 'IMF',
                'attrs.pays': code_pays
            })
            logger.info(f"   {nom_pays:20} : {count:5,} obs")
        
        # Par indicateur
        logger.info(f"\n📊 TOP 5 INDICATEURS:")
        for code_ind in list(INDICATEURS_WEO.keys())[:5]:
            count = self.db.curated_observations.count_documents({
                'source': 'IMF',
                'attrs.indicateur': code_ind
            })
            logger.info(f"   {code_ind:15} : {count:5,} obs - {INDICATEURS_WEO[code_ind]}")
        
        logger.info("\n" + "="*100)
        logger.info("✅ COLLECTE FMI TERMINÉE")
        logger.info("="*100 + "\n")

def main():
    collecteur = CollecteurIMFComplet()
    collecteur.collecter_tout()

if __name__ == '__main__':
    main()
