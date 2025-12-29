"""
🚀 COLLECTE AUTOMATIQUE COMPLÈTE - TOUTES LES SOURCES
Collecte intelligente qui garde l'existant et ajoute le manquant
"""
import os
import sys
import django
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# ============================================================================
# CONFIGURATION DES SOURCES ET INDICATEURS
# ============================================================================

# Pays CEDEAO (15 pays)
CEDEAO_COUNTRIES = "BEN,BFA,CIV,GNB,MLI,NER,SEN,TGO,GHA,GMB,GIN,LBR,MRT,NGA,SLE"

# 1. WORLD BANK - Indicateurs économiques et sociaux (35 indicateurs)
WORLDBANK_INDICATORS = [
    # Démographie (3)
    'SP.POP.TOTL',           # Population totale
    'SP.DYN.LE00.IN',        # Espérance de vie
    'SP.URB.TOTL.IN.ZS',     # Population urbaine (%)
    
    # Économie (10)
    'NY.GDP.MKTP.CD',        # PIB ($ US)
    'NY.GDP.MKTP.KD.ZG',     # Croissance PIB (%)
    'NY.GDP.PCAP.CD',        # PIB par habitant
    'NY.GNP.PCAP.CD',        # RNB par habitant
    'NE.EXP.GNFS.ZS',        # Exportations (% PIB)
    'NE.IMP.GNFS.ZS',        # Importations (% PIB)
    'FP.CPI.TOTL.ZG',        # Inflation
    'NE.TRD.GNFS.ZS',        # Commerce (% PIB)
    'BX.KLT.DINV.CD.WD',     # IDE
    'DT.DOD.DECT.CD',        # Dette extérieure
    
    # Éducation (4)
    'SE.PRM.ENRR',           # Scolarisation primaire
    'SE.SEC.ENRR',           # Scolarisation secondaire
    'SE.ADT.LITR.ZS',        # Alphabétisation
    'SE.XPD.TOTL.GD.ZS',     # Dépenses éducation (% PIB)
    
    # Santé (5)
    'SH.STA.MMRT',           # Mortalité maternelle
    'SH.DYN.MORT',           # Mortalité infantile
    'SH.MED.PHYS.ZS',        # Médecins (pour 1000)
    'SH.XPD.CHEX.GD.ZS',     # Dépenses santé (% PIB)
    'SH.H2O.SMDW.ZS',        # Accès eau potable
    
    # Infrastructure (5)
    'EG.ELC.ACCS.ZS',        # Accès électricité
    'IT.NET.USER.ZS',        # Utilisateurs Internet
    'IT.CEL.SETS.P2',        # Abonnements mobile
    'IS.RRS.TOTL.KM',        # Réseau ferroviaire
    'IS.ROD.TOTL.KM',        # Réseau routier
    
    # Environnement (3)
    'EN.ATM.CO2E.PC',        # Émissions CO2
    'AG.LND.FRST.ZS',        # Superficie forestière
    'ER.H2O.FWTL.ZS',        # Prélèvements eau
    
    # Social (4)
    'SI.POV.DDAY',           # Pauvreté
    'SL.UEM.TOTL.ZS',        # Chômage
    'SL.TLF.TOTL.IN',        # Population active
    'DT.ODA.ALLD.CD',        # Aide au développement
]

# 2. FMI - Indicateurs macroéconomiques (20 séries)
IMF_INDICATORS = [
    'PCPIPCH',     # Inflation (CPI)
    'NGDP_RPCH',   # Croissance PIB réel
    'NGDPD',       # PIB nominal
    'NGDPDPC',     # PIB par habitant
    'PPPPC',       # PIB PPA par habitant
    'LUR',         # Taux de chômage
    'GGXCNL_NGDP', # Solde budgétaire (% PIB)
    'GGXWDG_NGDP', # Dette publique (% PIB)
    'BCA_NGDPD',   # Balance courante (% PIB)
    'TX_RPCH',     # Croissance exportations
    'TM_RPCH',     # Croissance importations
]

# 3. UN SDG - Objectifs développement durable (8 indicateurs)
UN_SDG_INDICATORS = [
    'SL_TLF_UEM',      # Chômage
    'SI_POV_DAY1',     # Pauvreté extrême
    'SH_STA_MORT',     # Mortalité infantile
    'SE_PRM_CMPT_ZS',  # Achèvement primaire
    'SH_H2O_SAFE',     # Eau potable
    'EG_ELC_ACCS',     # Électricité
    'EN_ATM_CO2E',     # Émissions CO2
    'SG_GEN_PARL',     # Femmes au parlement
]

# 4. BAD - Dette et financement (6 indicateurs)
AFDB_INDICATORS = [
    'SOCIO_ECONOMIC_DATABASE',  # Dette extérieure
    'DEBT_SERVICE_RATIO',       # Service dette
    'GROSS_SAVINGS',            # Épargne brute
    'GROSS_INVESTMENT',         # Investissement brut
    'FISCAL_BALANCE',           # Solde budgétaire
    'EXTERNAL_BALANCE',         # Balance extérieure
]

# 5. BRVM - Actions (47 actions)
BRVM_STOCKS = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'CABC',
    'CBIBF', 'CFAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'NEIC', 'NSBC', 'NTLC',
    'ORAC', 'ORAC', 'PALC', 'PALMC', 'PRSC', 'SAFC', 'SAGC', 'SCRC', 'SDCC',
    'SDSC', 'SGBC', 'SHEC', 'SIBC', 'SICC', 'SICB', 'SICB', 'SIVC', 'SLBC',
    'SMBC', 'SNTS', 'SOGB', 'SPHC', 'STAC', 'STBC', 'SVOC', 'TTLC', 'TTLS',
    'UNXC', 'TTRC'
]

# ============================================================================
# FONCTIONS DE COLLECTE
# ============================================================================

def check_existing_data(source, dataset=None, key=None):
    """Vérifier si les données existent déjà"""
    _, db = get_mongo_db()
    
    query = {'source': source}
    if dataset:
        query['dataset'] = dataset
    if key:
        query['key'] = key
    
    count = db.curated_observations.count_documents(query)
    return count

def collect_worldbank():
    """Collecter toutes les données World Bank"""
    print("\n" + "="*80)
    print("🌐 WORLD BANK - Collecte 35 indicateurs × 15 pays")
    print("="*80)
    
    total_collected = 0
    
    for i, indicator in enumerate(WORLDBANK_INDICATORS, 1):
        existing = check_existing_data('WorldBank', dataset=indicator)
        print(f"\n[{i}/{len(WORLDBANK_INDICATORS)}] {indicator}")
        print(f"  📊 Existant: {existing} observations")
        
        try:
            count = run_ingestion(
                "worldbank",
                indicator=indicator,
                date="2010:2024",
                country=CEDEAO_COUNTRIES
            )
            total_collected += count
            print(f"  ✅ Collecté: {count} nouvelles observations")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    print(f"\n✅ World Bank: {total_collected} observations collectées")
    return total_collected

def collect_imf():
    """Collecter toutes les données FMI"""
    print("\n" + "="*80)
    print("💰 FMI - Collecte 11 indicateurs × 7 pays")
    print("="*80)
    
    total_collected = 0
    imf_countries = "BEN,BFA,CIV,GHA,MLI,NER,SEN"  # Pays avec données FMI
    
    for i, indicator in enumerate(IMF_INDICATORS, 1):
        existing = check_existing_data('IMF', dataset=indicator)
        print(f"\n[{i}/{len(IMF_INDICATORS)}] {indicator}")
        print(f"  📊 Existant: {existing} observations")
        
        try:
            count = run_ingestion(
                "imf",
                indicator=indicator,
                country=imf_countries
            )
            total_collected += count
            print(f"  ✅ Collecté: {count} nouvelles observations")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    print(f"\n✅ FMI: {total_collected} observations collectées")
    return total_collected

def collect_un_sdg():
    """Collecter toutes les données UN SDG"""
    print("\n" + "="*80)
    print("🌍 ONU SDG - Collecte 8 indicateurs × 8 pays")
    print("="*80)
    
    total_collected = 0
    
    # L'API UN utilise des codes pays numériques
    un_countries = {
        'BEN': '204', 'BFA': '854', 'CIV': '384', 'GHA': '288',
        'MLI': '466', 'NER': '562', 'SEN': '686', 'TGO': '768'
    }
    
    existing = check_existing_data('UN_SDG')
    print(f"\n📊 Existant: {existing} observations")
    
    try:
        count = run_ingestion("un_sdg")
        total_collected += count
        print(f"✅ Collecté: {count} nouvelles observations")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print(f"\n✅ ONU SDG: {total_collected} observations collectées")
    return total_collected

def collect_afdb():
    """Collecter toutes les données BAD"""
    print("\n" + "="*80)
    print("🏦 BAD - Collecte 6 indicateurs × 8 pays")
    print("="*80)
    
    total_collected = 0
    afdb_countries = "BEN,BFA,CIV,GIN,MLI,NER,SEN,TGO"
    
    existing = check_existing_data('AfDB')
    print(f"\n📊 Existant: {existing} observations")
    
    try:
        count = run_ingestion("afdb", country=afdb_countries)
        total_collected += count
        print(f"✅ Collecté: {count} nouvelles observations")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print(f"\n✅ BAD: {total_collected} observations collectées")
    return total_collected

def collect_brvm():
    """Collecter toutes les données BRVM"""
    print("\n" + "="*80)
    print("📈 BRVM - Collecte 47 actions")
    print("="*80)
    
    total_collected = 0
    
    existing = check_existing_data('BRVM')
    print(f"\n📊 Existant: {existing} observations")
    
    try:
        count = run_ingestion("brvm")
        total_collected += count
        print(f"✅ Collecté: {count} nouvelles observations")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print(f"\n✅ BRVM: {total_collected} observations collectées")
    return total_collected

def display_final_stats():
    """Afficher les statistiques finales"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("📊 STATISTIQUES FINALES - BASE DE DONNÉES")
    print("="*80)
    
    sources = ['WorldBank', 'IMF', 'UN_SDG', 'AfDB', 'BRVM']
    
    print(f"\n{'Source':<15} {'Observations':<15} {'Indicateurs':<15} {'Pays/Actions'}")
    print("-"*80)
    
    total_obs = 0
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        datasets = len(db.curated_observations.distinct('dataset', {'source': source}))
        keys = len(db.curated_observations.distinct('key', {'source': source}))
        
        print(f"{source:<15} {count:<15,} {datasets:<15} {keys}")
        total_obs += count
    
    print("-"*80)
    print(f"{'TOTAL':<15} {total_obs:<15,}")
    
    print("\n" + "="*80)
    print("✅ COLLECTE AUTOMATIQUE COMPLÈTE TERMINÉE")
    print("="*80)
    print("\n🎯 Prochaines étapes:")
    print("  1. Vérifier les dashboards: http://127.0.0.1:8000/")
    print("  2. Configurer Airflow pour collecte périodique automatique")
    print("  3. Les données sont mises à jour et prêtes à l'emploi")

# ============================================================================
# EXÉCUTION PRINCIPALE
# ============================================================================

def main():
    """Exécution principale de la collecte complète"""
    
    print("="*80)
    print("🚀 COLLECTE AUTOMATIQUE COMPLÈTE - 5 SOURCES")
    print("="*80)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Pays CEDEAO: {CEDEAO_COUNTRIES.replace(',', ', ')}")
    print(f"\n📊 Configuration:")
    print(f"  - World Bank: {len(WORLDBANK_INDICATORS)} indicateurs")
    print(f"  - FMI: {len(IMF_INDICATORS)} indicateurs")
    print(f"  - ONU SDG: {len(UN_SDG_INDICATORS)} indicateurs")
    print(f"  - BAD: {len(AFDB_INDICATORS)} indicateurs")
    print(f"  - BRVM: {len(BRVM_STOCKS)} actions")
    print(f"\n⏱️  Durée estimée: 15-20 minutes")
    print("\n" + "="*80)
    
    input("\n▶️  Appuyez sur ENTRÉE pour lancer la collecte complète...")
    
    start_time = datetime.now()
    
    # Collecter chaque source
    wb_count = collect_worldbank()
    imf_count = collect_imf()
    un_count = collect_un_sdg()
    afdb_count = collect_afdb()
    brvm_count = collect_brvm()
    
    # Statistiques finales
    end_time = datetime.now()
    duration = end_time - start_time
    
    display_final_stats()
    
    print(f"\n⏱️  Durée totale: {duration}")
    print(f"📊 Total nouvelles observations: {wb_count + imf_count + un_count + afdb_count + brvm_count:,}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Collecte interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
