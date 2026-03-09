#!/usr/bin/env python3
"""
🌍 COLLECTE COMPLÈTE WORLD BANK - TOUS INDICATEURS UEMOA
Collecte exhaustive des 12804+ indicateurs pour les 8 pays UEMOA
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import logging

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'collecte_wb_uemoa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# 8 Pays UEMOA (codes ISO-2)
PAYS_UEMOA = ['BJ', 'BF', 'CI', 'GW', 'ML', 'NE', 'SN', 'TG']

NOMS_PAYS = {
    'BJ': 'Bénin',
    'BF': 'Burkina Faso',
    'CI': 'Côte d\'Ivoire',
    'GW': 'Guinée-Bissau',
    'ML': 'Mali',
    'NE': 'Niger',
    'SN': 'Sénégal',
    'TG': 'Togo'
}

# Indicateurs prioritaires par catégorie (sélection stratégique parmi les 12804)
INDICATEURS_PRIORITAIRES = {
    # ========== ÉCONOMIE & CROISSANCE ==========
    'Économie': [
        'NY.GDP.MKTP.CD',           # PIB ($ courants)
        'NY.GDP.MKTP.KD.ZG',        # Croissance PIB (% annuel)
        'NY.GDP.PCAP.CD',           # PIB par habitant ($ courants)
        'NY.GDP.PCAP.KD.ZG',        # Croissance PIB/habitant (% annuel)
        'NY.GNP.PCAP.CD',           # RNB par habitant ($ courants)
        'NY.GNP.MKTP.CD',           # RNB ($ courants)
        'NV.AGR.TOTL.ZS',           # Agriculture, valeur ajoutée (% PIB)
        'NV.IND.TOTL.ZS',           # Industrie, valeur ajoutée (% PIB)
        'NV.SRV.TOTL.ZS',           # Services, valeur ajoutée (% PIB)
        'NE.GDI.TOTL.ZS',           # Formation brute de capital (% PIB)
    ],
    
    # ========== COMMERCE & INVESTISSEMENT ==========
    'Commerce': [
        'NE.TRD.GNFS.ZS',           # Commerce (% PIB)
        'NE.EXP.GNFS.ZS',           # Exportations (% PIB)
        'NE.IMP.GNFS.ZS',           # Importations (% PIB)
        'BX.KLT.DINV.WD.GD.ZS',     # IDE net entrants (% PIB)
        'BN.CAB.XOKA.GD.ZS',        # Balance courante (% PIB)
        'TM.VAL.MRCH.CD.WT',        # Importations marchandises ($)
        'TX.VAL.MRCH.CD.WT',        # Exportations marchandises ($)
    ],
    
    # ========== PRIX & INFLATION ==========
    'Prix': [
        'FP.CPI.TOTL.ZG',           # Inflation, prix consommateur (%)
        'FP.CPI.TOTL',              # IPC (2010 = 100)
        'PA.NUS.FCRF',              # Taux de change officiel (FCFA/USD)
    ],
    
    # ========== FINANCES PUBLIQUES & DETTE ==========
    'Finances Publiques': [
        'GC.DOD.TOTL.GD.ZS',        # Dette publique (% PIB)
        'GC.BAL.CASH.GD.ZS',        # Solde budgétaire (% PIB)
        'GC.REV.XGRT.GD.ZS',        # Recettes hors dons (% PIB)
        'GC.XPN.TOTL.GD.ZS',        # Dépenses (% PIB)
        'DT.DOD.DECT.CD',           # Dette extérieure totale ($)
    ],
    
    # ========== EMPLOI & MARCHÉ DU TRAVAIL ==========
    'Emploi': [
        'SL.UEM.TOTL.ZS',           # Taux de chômage total (%)
        'SL.UEM.TOTL.NE.ZS',        # Chômage, 15+ ans (%)
        'SL.TLF.TOTL.IN',           # Population active totale
        'SL.TLF.CACT.ZS',           # Taux d'activité (% 15+)
        'SL.EMP.VULN.ZS',           # Emploi vulnérable (%)
    ],
    
    # ========== POPULATION & DÉMOGRAPHIE ==========
    'Population': [
        'SP.POP.TOTL',              # Population totale
        'SP.POP.GROW',              # Croissance pop (% annuel)
        'SP.URB.TOTL.IN.ZS',        # Population urbaine (%)
        'SP.POP.0014.TO.ZS',        # Pop 0-14 ans (% total)
        'SP.POP.1564.TO.ZS',        # Pop 15-64 ans (% total)
        'SP.POP.65UP.TO.ZS',        # Pop 65+ ans (% total)
        'SP.DYN.TFRT.IN',           # Taux de fécondité (naissances/femme)
        'SP.DYN.LE00.IN',           # Espérance de vie à la naissance
    ],
    
    # ========== SANTÉ ==========
    'Santé': [
        'SH.DYN.MORT',              # Mortalité infantile (pour 1000)
        'SH.DYN.NMRT',              # Mortalité néonatale (pour 1000)
        'SH.STA.MMRT',              # Mortalité maternelle (pour 100k)
        'SH.XPD.CHEX.GD.ZS',        # Dépenses santé courantes (% PIB)
        'SH.MED.PHYS.ZS',           # Médecins (pour 1000 hab)
        'SH.H2O.BASW.ZS',           # Accès eau potable (% pop)
        'SH.STA.BASS.ZS',           # Accès assainissement (% pop)
    ],
    
    # ========== ÉDUCATION ==========
    'Éducation': [
        'SE.PRM.ENRR',              # Scolarisation primaire (% brut)
        'SE.SEC.ENRR',              # Scolarisation secondaire (% brut)
        'SE.TER.ENRR',              # Scolarisation tertiaire (% brut)
        'SE.XPD.TOTL.GD.ZS',        # Dépenses éducation publiques (% PIB)
        'SE.ADT.LITR.ZS',           # Taux d'alphabétisation adultes (%)
        'SE.PRM.CMPT.ZS',           # Achèvement primaire (%)
    ],
    
    # ========== INFRASTRUCTURE & TECHNOLOGIE ==========
    'Infrastructure': [
        'EG.ELC.ACCS.ZS',           # Accès électricité (% pop)
        'IT.NET.USER.ZS',           # Utilisateurs Internet (% pop)
        'IT.CEL.SETS.P2',           # Abonnements mobile (pour 100)
        'IS.ROD.PAVE.ZS',           # Routes pavées (% total)
        'IS.AIR.PSGR',              # Passagers aériens transportés
    ],
    
    # ========== ENVIRONNEMENT & AGRICULTURE ==========
    'Environnement': [
        'AG.LND.AGRI.ZS',           # Terres agricoles (% surface)
        'AG.LND.FRST.ZS',           # Forêts (% surface)
        'EN.ATM.CO2E.KT',           # Émissions CO2 (kt)
        'AG.PRD.CROP.XD',           # Indice production agricole
        'AG.YLD.CREL.KG',           # Rendement céréales (kg/hectare)
    ],
    
    # ========== PAUVRETÉ & INÉGALITÉS ==========
    'Pauvreté': [
        'SI.POV.DDAY',              # Pauvreté $2.15/jour (% pop)
        'SI.POV.NAHC',              # Pauvreté seuil national (% pop)
        'SI.POV.GINI',              # Indice Gini
        'SI.DST.FRST.20',           # Part revenu 20% les plus pauvres
        'SI.DST.05TH.20',           # Part revenu 20% les plus riches
    ],
}

# Aplatir la liste de tous les indicateurs
TOUS_INDICATEURS = []
for categorie, indicateurs in INDICATEURS_PRIORITAIRES.items():
    TOUS_INDICATEURS.extend(indicateurs)

# Périodes à collecter
ANNEES_RECENTES = list(range(2015, 2027))  # 2015-2026 (12 ans)
ANNEES_HISTORIQUES = list(range(1990, 2015))  # 1990-2014 (25 ans)

def verifier_mongodb():
    """Vérifier que MongoDB est accessible"""
    try:
        _, db = get_mongo_db()
        db.command('ping')
        logger.info("✅ Connexion MongoDB OK")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB inaccessible: {e}")
        logger.error("Démarrez MongoDB avec: mongod --dbpath C:\\data\\db")
        return False

def compter_observations_existantes():
    """Compter les observations World Bank existantes"""
    try:
        _, db = get_mongo_db()
        count = db.curated_observations.count_documents({'source': 'WorldBank'})
        logger.info(f"📊 Observations World Bank existantes: {count:,}")
        return count
    except Exception as e:
        logger.error(f"Erreur comptage: {e}")
        return 0

def collecter_indicateur_pays_annee(indicateur, pays, annee, categorie):
    """Collecter un indicateur pour un pays et une année"""
    try:
        result = run_ingestion(
            source='worldbank',
            indicator=indicateur,
            country=pays,
            year=annee
        )
        
        if result.get('status') == 'success':
            obs_count = result.get('obs_count', 0)
            if obs_count > 0:
                logger.info(f"   ✅ {categorie} | {indicateur} | {pays} | {annee}: {obs_count} obs")
                return {'succes': True, 'observations': obs_count}
            else:
                logger.debug(f"   ⚠️  {categorie} | {indicateur} | {pays} | {annee}: Aucune donnée")
                return {'succes': True, 'observations': 0}
        else:
            error_msg = result.get('error', 'Erreur inconnue')
            logger.warning(f"   ❌ {categorie} | {indicateur} | {pays} | {annee}: {error_msg}")
            return {'succes': False, 'observations': 0, 'erreur': error_msg}
            
    except Exception as e:
        logger.error(f"   ❌ Exception {categorie} | {indicateur} | {pays} | {annee}: {e}")
        return {'succes': False, 'observations': 0, 'erreur': str(e)}

def main():
    print("\n" + "="*100)
    print("🌍 COLLECTE EXHAUSTIVE WORLD BANK - PAYS UEMOA")
    print("="*100)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗂️  Catégories: {len(INDICATEURS_PRIORITAIRES)}")
    print(f"📊 Indicateurs: {len(TOUS_INDICATEURS)}")
    print(f"🌍 Pays UEMOA: {len(PAYS_UEMOA)} ({', '.join(PAYS_UEMOA)})")
    print(f"📆 Années récentes: {len(ANNEES_RECENTES)} ({ANNEES_RECENTES[0]}-{ANNEES_RECENTES[-1]})")
    print(f"📆 Années historiques: {len(ANNEES_HISTORIQUES)} ({ANNEES_HISTORIQUES[0]}-{ANNEES_HISTORIQUES[-1]})")
    
    total_operations = len(TOUS_INDICATEURS) * len(PAYS_UEMOA) * len(ANNEES_RECENTES)
    print(f"⚙️  Opérations récentes: {total_operations:,}")
    print("="*100 + "\n")
    
    # Vérifier MongoDB
    if not verifier_mongodb():
        logger.error("❌ Abandon: MongoDB non accessible")
        return
    
    # Compter données existantes
    obs_initiales = compter_observations_existantes()
    
    # Choix période
    print("\n📆 CHOIX DE LA PÉRIODE:")
    print("1. Données récentes uniquement (2015-2026) - RECOMMANDÉ")
    print("2. Données historiques complètes (1990-2026)")
    print("3. Année spécifique")
    
    choix = input("\nVotre choix (1/2/3): ").strip()
    
    if choix == '1':
        annees_a_collecter = ANNEES_RECENTES
        logger.info("✅ Collecte RÉCENTE: 2015-2026")
    elif choix == '2':
        annees_a_collecter = ANNEES_HISTORIQUES + ANNEES_RECENTES
        logger.info("✅ Collecte COMPLÈTE: 1990-2026")
    elif choix == '3':
        annee_spec = int(input("Année (ex: 2025): ").strip())
        annees_a_collecter = [annee_spec]
        logger.info(f"✅ Collecte ANNÉE: {annee_spec}")
    else:
        logger.warning("⚠️  Choix invalide, collecte récente par défaut")
        annees_a_collecter = ANNEES_RECENTES
    
    total_ops = len(TOUS_INDICATEURS) * len(PAYS_UEMOA) * len(annees_a_collecter)
    duree_estimee = (total_ops * 0.5) / 60  # 0.5s par requête
    
    print(f"\n⏱️  ESTIMATION:")
    print(f"   Opérations: {total_ops:,}")
    print(f"   Durée: ~{duree_estimee:.1f} minutes")
    print()
    
    confirmation = input("Lancer la collecte ? (o/n): ").lower()
    if confirmation != 'o':
        logger.info("❌ Collecte annulée")
        return
    
    # Statistiques
    stats = {
        'total': 0,
        'succes': 0,
        'echecs': 0,
        'observations': 0,
        'par_categorie': {}
    }
    
    debut = time.time()
    current_op = 0
    
    # Collecte par catégorie
    for categorie, indicateurs in INDICATEURS_PRIORITAIRES.items():
        logger.info(f"\n{'='*100}")
        logger.info(f"📂 CATÉGORIE: {categorie} ({len(indicateurs)} indicateurs)")
        logger.info(f"{'='*100}")
        
        stats['par_categorie'][categorie] = {
            'succes': 0,
            'echecs': 0,
            'observations': 0
        }
        
        for indicateur in indicateurs:
            for pays in PAYS_UEMOA:
                nom_pays = NOMS_PAYS[pays]
                
                for annee in annees_a_collecter:
                    current_op += 1
                    progress = (current_op / total_ops) * 100
                    
                    if current_op % 10 == 0:
                        logger.info(f"\n[{current_op}/{total_ops}] Progrès: {progress:.1f}%")
                    
                    result = collecter_indicateur_pays_annee(indicateur, pays, annee, categorie)
                    
                    stats['total'] += 1
                    if result['succes']:
                        stats['succes'] += 1
                        stats['observations'] += result['observations']
                        stats['par_categorie'][categorie]['succes'] += 1
                        stats['par_categorie'][categorie]['observations'] += result['observations']
                    else:
                        stats['echecs'] += 1
                        stats['par_categorie'][categorie]['echecs'] += 1
                    
                    # Pause anti-rate limit
                    time.sleep(0.5)
    
    duree = time.time() - debut
    
    # Résumé final
    print("\n" + "="*100)
    print("📊 RÉSUMÉ FINAL")
    print("="*100)
    print(f"\n⏱️  Durée: {duree/60:.1f} minutes")
    print(f"📊 Opérations: {stats['total']:,}")
    print(f"✅ Succès: {stats['succes']:,} ({stats['succes']/stats['total']*100:.1f}%)")
    print(f"❌ Échecs: {stats['echecs']:,} ({stats['echecs']/stats['total']*100:.1f}%)")
    print(f"📈 Observations collectées: {stats['observations']:,}")
    
    print(f"\n📂 PAR CATÉGORIE:")
    for categorie, cat_stats in stats['par_categorie'].items():
        print(f"   {categorie}:")
        print(f"      Succès: {cat_stats['succes']}, Échecs: {cat_stats['echecs']}, Obs: {cat_stats['observations']:,}")
    
    # État final base
    obs_finales = compter_observations_existantes()
    nouvelles_obs = obs_finales - obs_initiales
    
    print(f"\n💾 BASE DE DONNÉES:")
    print(f"   Avant: {obs_initiales:,} observations")
    print(f"   Après: {obs_finales:,} observations")
    print(f"   Ajoutées: {nouvelles_obs:,} observations")
    print("="*100 + "\n")
    
    logger.info("✅ Collecte terminée avec succès")

if __name__ == '__main__':
    main()
