#!/usr/bin/env python3
"""
🇫🇷 COLLECTE COMPLÈTE UEMOA 2000-2026
======================================
8 pays : Bénin, Burkina Faso, Côte d'Ivoire, Guinée-Bissau, Mali, Niger, Sénégal, Togo
TOUS les indicateurs du dashboard : Croissance PIB, Population, Pauvreté, Santé, Éducation, Alphabétisation, Électricité, Internet

🎯 OBJECTIF : Remplir 100% du dashboard Banque Mondiale
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collecte_uemoa_complete.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# 🇫🇷 8 PAYS UEMOA
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

# 📊 INDICATEURS DASHBOARD (ceux affichés sur la page)
INDICATEURS_DASHBOARD = {
    # Croissance PIB
    'NY.GDP.MKTP.KD.ZG': 'Croissance PIB (%)',
    
    # Population
    'SP.POP.TOTL': 'Population totale',
    
    # Pauvreté
    'SI.POV.DDAY': 'Pauvreté $2.15/jour (%)',
    'SI.POV.NAHC': 'Taux pauvreté national (%)',
    
    # Santé
    'SH.XPD.CHEX.GD.ZS': 'Dépenses santé (% PIB)',
    'SH.DYN.MORT': 'Mortalité infantile (‰)',
    
    # Éducation
    'SE.XPD.TOTL.GD.ZS': 'Dépenses éducation (% PIB)',
    'SE.PRM.ENRR': 'Taux scolarisation primaire (%)',
    
    # Alphabétisation
    'SE.ADT.LITR.ZS': 'Taux alphabétisation adultes (%)',
    
    # Infrastructure
    'EG.ELC.ACCS.ZS': 'Accès électricité (%)',
    'IT.NET.USER.ZS': 'Utilisateurs Internet (%)',
}

# 📈 INDICATEURS COMPLETS (pour analyses approfondies)
INDICATEURS_COMPLETS = {
    # Économie
    'NY.GDP.MKTP.CD': 'PIB ($ courants)',
    'NY.GDP.PCAP.CD': 'PIB par habitant ($ courants)',
    'NY.GDP.MKTP.KD.ZG': 'Croissance PIB (%)',
    'FP.CPI.TOTL.ZG': 'Inflation, prix consommateur (%)',
    'BN.CAB.XOKA.GD.ZS': 'Balance compte courant (% PIB)',
    'NE.TRD.GNFS.ZS': 'Commerce (% PIB)',
    'GC.REV.XGRT.GD.ZS': 'Revenus gouvernement (% PIB)',
    'GC.XPN.TOTL.GD.ZS': 'Dépenses gouvernement (% PIB)',
    'GC.DOD.TOTL.GD.ZS': 'Dette publique (% PIB)',
    'BX.KLT.DINV.WD.GD.ZS': 'IDE nets (% PIB)',
    'NE.GDI.FTOT.ZS': 'Formation brute capital fixe (% PIB)',
    
    # Population & Démographie
    'SP.POP.TOTL': 'Population totale',
    'SP.POP.GROW': 'Croissance population (%)',
    'SP.URB.TOTL.IN.ZS': 'Population urbaine (%)',
    'SP.DYN.LE00.IN': 'Espérance de vie (années)',
    'SP.DYN.TFRT.IN': 'Taux fertilité (naissances/femme)',
    
    # Pauvreté & Emploi
    'SI.POV.DDAY': 'Pauvreté $2.15/jour (%)',
    'SI.POV.NAHC': 'Taux pauvreté national (%)',
    'SL.UEM.TOTL.ZS': 'Chômage (%)',
    
    # Santé
    'SH.XPD.CHEX.GD.ZS': 'Dépenses santé (% PIB)',
    'SH.DYN.MORT': 'Mortalité infantile (‰)',
    'SH.STA.MMRT': 'Mortalité maternelle (‱)',
    'SH.H2O.BASW.ZS': 'Accès eau potable (%)',
    'SH.STA.BASS.ZS': 'Accès assainissement (%)',
    
    # Éducation
    'SE.XPD.TOTL.GD.ZS': 'Dépenses éducation (% PIB)',
    'SE.PRM.ENRR': 'Taux scolarisation primaire (%)',
    'SE.SEC.ENRR': 'Taux scolarisation secondaire (%)',
    'SE.TER.ENRR': 'Taux scolarisation tertiaire (%)',
    'SE.ADT.LITR.ZS': 'Taux alphabétisation adultes (%)',
    
    # Infrastructure
    'EG.ELC.ACCS.ZS': 'Accès électricité (%)',
    'IT.NET.USER.ZS': 'Utilisateurs Internet (%)',
    'IT.CEL.SETS.P2': 'Abonnements téléphone mobile (‱)',
    'IS.ROD.PAVE.ZP': 'Routes pavées (%)',
    
    # Environnement
    'AG.LND.FRST.ZS': 'Superficie forestière (%)',
    'EN.ATM.CO2E.PC': 'Émissions CO2 (tonnes/hab)',
}


class CollecteurUEMOAComplet:
    """Collecteur complet pour les 8 pays UEMOA"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.stats = {
            'total': 0,
            'par_pays': {code: 0 for code in PAYS_UEMOA.keys()},
            'par_indicateur': {}
        }
    
    def collecter_uemoa_complet(self):
        """Collecter tous les indicateurs UEMOA 2000-2026"""
        logger.info("\n" + "🇫🇷"*50)
        logger.info("📊 COLLECTE COMPLÈTE UEMOA 2000-2026")
        logger.info("🇫🇷"*50)
        
        logger.info(f"\n📋 CONFIGURATION:")
        logger.info(f"   Pays UEMOA: {len(PAYS_UEMOA)}")
        for code, nom in PAYS_UEMOA.items():
            logger.info(f"      • {code} - {nom}")
        
        logger.info(f"\n   Indicateurs: {len(INDICATEURS_COMPLETS)}")
        logger.info(f"   Période: 2000-2024 (25 ans) - Données disponibles API")
        logger.info(f"   Note: 2025-2026 seront ajoutés via projections FMI/BCEAO")
        logger.info(f"   Observations attendues: ~{len(INDICATEURS_COMPLETS) * len(PAYS_UEMOA) * 25:,}")
        
        try:
            import wbgapi as wb
            
            logger.info("\n✅ Module wbgapi chargé")
            logger.info("\n" + "="*100)
            
            total_count = 0
            
            # Collecter chaque indicateur
            for idx, (ind_code, ind_nom) in enumerate(INDICATEURS_COMPLETS.items(), 1):
                logger.info(f"\n[{idx}/{len(INDICATEURS_COMPLETS)}] 📈 {ind_nom}")
                logger.info(f"   Code: {ind_code}")
                
                try:
                    # Récupérer données WorldBank API
                    # Note: WorldBank API v2 a les données jusqu'à 2024 seulement
                    # 2025-2026 seront ajoutés via FMI/BCEAO
                    years_range = range(2000, 2025)  # 2000-2024 (25 ans)
                    
                    data = wb.data.DataFrame(
                        ind_code,
                        list(PAYS_UEMOA.keys()),
                        time=years_range,
                        labels=False
                    )
                    
                    count_indicateur = 0
                    
                    # Parser et sauvegarder
                    for country_code in PAYS_UEMOA.keys():
                        for year in range(2000, 2025):  # 2000-2024
                            try:
                                year_col = f"YR{year}"
                                if country_code in data.index and year_col in data.columns:
                                    value = data.loc[country_code, year_col]
                                    
                                    # Vérifier si valeur valide
                                    if value is not None and not (isinstance(value, float) and value != value):  # Not NaN
                                        observation = {
                                            'source': 'WorldBank',
                                            'dataset': ind_code,
                                            'key': country_code,
                                            'ts': f'{year}-01-01',
                                            'value': float(value),
                                            'attrs': {
                                                'indicator_code': ind_code,
                                                'indicator_name': ind_nom,
                                                'country_code': country_code,
                                                'country_name': PAYS_UEMOA[country_code],
                                                'year': year,
                                                'region': 'UEMOA',
                                                'data_quality': 'OFFICIAL_API',
                                                'collecte_date': datetime.now().isoformat()
                                            }
                                        }
                                        
                                        # Upsert dans MongoDB
                                        self.db.curated_observations.update_one(
                                            {
                                                'source': 'WorldBank',
                                                'dataset': ind_code,
                                                'key': country_code,
                                                'ts': f'{year}-01-01'
                                            },
                                            {'$set': observation},
                                            upsert=True
                                        )
                                        
                                        count_indicateur += 1
                                        total_count += 1
                                        
                                        # Stats
                                        self.stats['par_pays'][country_code] += 1
                                        
                            except Exception as e:
                                logger.debug(f"   Erreur {country_code} {year}: {e}")
                                continue
                    
                    self.stats['par_indicateur'][ind_code] = count_indicateur
                    
                    logger.info(f"   ✅ {count_indicateur} observations collectées")
                    
                    # Pause pour éviter rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"   ❌ Erreur {ind_code}: {e}")
                    self.stats['par_indicateur'][ind_code] = 0
                    continue
            
            self.stats['total'] = total_count
            
            # Afficher résumé
            self.afficher_statistiques()
            
        except ImportError:
            logger.error("❌ Module wbgapi non installé")
            logger.info("💡 Installer avec: pip install wbgapi")
        except Exception as e:
            logger.error(f"❌ Erreur collecte: {e}")
            import traceback
            traceback.print_exc()
    
    def afficher_statistiques(self):
        """Afficher statistiques détaillées"""
        logger.info("\n" + "="*100)
        logger.info("📊 STATISTIQUES FINALES")
        logger.info("="*100)
        
        logger.info(f"\n✅ TOTAL: {self.stats['total']:,} observations collectées")
        
        # Par pays
        logger.info(f"\n🌍 PAR PAYS:")
        for code, nom in PAYS_UEMOA.items():
            count = self.stats['par_pays'][code]
            logger.info(f"   {code} {nom:20s}: {count:6,} observations")
        
        # Top indicateurs
        logger.info(f"\n📈 TOP 10 INDICATEURS:")
        top_indicateurs = sorted(
            self.stats['par_indicateur'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for code, count in top_indicateurs:
            nom = INDICATEURS_COMPLETS.get(code, code)
            logger.info(f"   {nom:50s}: {count:4,} obs")
        
        # Indicateurs vides
        indicateurs_vides = [
            code for code, count in self.stats['par_indicateur'].items()
            if count == 0
        ]
        
        if indicateurs_vides:
            logger.info(f"\n⚠️  INDICATEURS SANS DONNÉES ({len(indicateurs_vides)}):")
            for code in indicateurs_vides[:5]:
                nom = INDICATEURS_COMPLETS.get(code, code)
                logger.info(f"   • {nom}")
        
        # Vérification MongoDB
        logger.info(f"\n🔍 VÉRIFICATION MONGODB:")
        count_wb = self.db.curated_observations.count_documents({
            'source': 'WorldBank',
            'attrs.region': 'UEMOA'
        })
        logger.info(f"   WorldBank UEMOA: {count_wb:,} observations")
        
        # Par pays dans MongoDB
        logger.info(f"\n🌍 DÉTAIL PAR PAYS (MongoDB):")
        for code, nom in PAYS_UEMOA.items():
            count = self.db.curated_observations.count_documents({
                'source': 'WorldBank',
                'key': code,
                'attrs.region': 'UEMOA'
            })
            logger.info(f"   {code} {nom:20s}: {count:6,} observations")
        
        logger.info("\n" + "="*100)
        logger.info("✅ COLLECTE UEMOA TERMINÉE !")
        logger.info("="*100)
        
        logger.info(f"\n💡 PROCHAINES ÉTAPES:")
        logger.info(f"   1. Actualiser le dashboard: http://127.0.0.1:8000/worldbank/")
        logger.info(f"   2. Vérifier les indicateurs: python show_complete_data.py")
        logger.info(f"   3. Logs détaillés: collecte_uemoa_complete.log")


def main():
    """Point d'entrée"""
    logger.info("\n" + "🚀"*50)
    logger.info("DÉMARRAGE COLLECTE UEMOA COMPLÈTE")
    logger.info("🚀"*50)
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("🚀"*50 + "\n")
    
    collecteur = CollecteurUEMOAComplet()
    collecteur.collecter_uemoa_complet()


if __name__ == '__main__':
    main()
