"""
DAG Airflow MASTER - Collecte hebdomadaire complète automatique
Toutes les sources, tous les indicateurs, zéro intervention humaine
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.pipeline import run_ingestion

# Configuration
CEDEAO_COUNTRIES = "BEN,BFA,CIV,GNB,MLI,NER,SEN,TGO,GHA,GMB,GIN,LBR,MRT,NGA,SLE"
IMF_COUNTRIES = "BEN,BFA,CIV,GHA,MLI,NER,SEN"
AFDB_COUNTRIES = "BEN,BFA,CIV,GIN,MLI,NER,SEN,TGO"

# ============================================================================
# WORLD BANK - 35 indicateurs
# ============================================================================
WORLDBANK_INDICATORS = {
    # Démographie
    'SP.POP.TOTL': 'Population totale',
    'SP.DYN.LE00.IN': 'Espérance de vie',
    'SP.URB.TOTL.IN.ZS': 'Population urbaine',
    # Économie
    'NY.GDP.MKTP.CD': 'PIB',
    'NY.GDP.MKTP.KD.ZG': 'Croissance PIB',
    'NY.GDP.PCAP.CD': 'PIB par habitant',
    'NY.GNP.PCAP.CD': 'RNB par habitant',
    'NE.EXP.GNFS.ZS': 'Exportations',
    'NE.IMP.GNFS.ZS': 'Importations',
    'FP.CPI.TOTL.ZG': 'Inflation',
    'NE.TRD.GNFS.ZS': 'Commerce',
    'BX.KLT.DINV.CD.WD': 'IDE',
    'DT.DOD.DECT.CD': 'Dette extérieure',
    # Éducation
    'SE.PRM.ENRR': 'Scolarisation primaire',
    'SE.SEC.ENRR': 'Scolarisation secondaire',
    'SE.ADT.LITR.ZS': 'Alphabétisation',
    'SE.XPD.TOTL.GD.ZS': 'Dépenses éducation',
    # Santé
    'SH.STA.MMRT': 'Mortalité maternelle',
    'SH.DYN.MORT': 'Mortalité infantile',
    'SH.MED.PHYS.ZS': 'Médecins',
    'SH.XPD.CHEX.GD.ZS': 'Dépenses santé',
    'SH.H2O.SMDW.ZS': 'Accès eau potable',
    # Infrastructure
    'EG.ELC.ACCS.ZS': 'Accès électricité',
    'IT.NET.USER.ZS': 'Utilisateurs Internet',
    'IT.CEL.SETS.P2': 'Abonnements mobile',
    'IS.RRS.TOTL.KM': 'Réseau ferroviaire',
    'IS.ROD.TOTL.KM': 'Réseau routier',
    # Environnement
    'EN.ATM.CO2E.PC': 'Émissions CO2',
    'AG.LND.FRST.ZS': 'Superficie forestière',
    'ER.H2O.FWTL.ZS': 'Prélèvements eau',
    # Social
    'SI.POV.DDAY': 'Pauvreté',
    'SL.UEM.TOTL.ZS': 'Chômage',
    'SL.TLF.TOTL.IN': 'Population active',
    'DT.ODA.ALLD.CD': 'Aide au développement',
}

# ============================================================================
# FONCTIONS DE COLLECTE
# ============================================================================

def collect_worldbank_batch(**context):
    """Collecter World Bank par lot pour éviter timeout"""
    print("🌐 Collecte World Bank - Batch complet")
    total = 0
    
    for indicator, name in WORLDBANK_INDICATORS.items():
        try:
            count = run_ingestion(
                "worldbank",
                indicator=indicator,
                date="2010:2024",
                country=CEDEAO_COUNTRIES
            )
            print(f"✅ {indicator}: {count} obs")
            total += count
        except Exception as e:
            print(f"❌ {indicator}: {e}")
    
    return total

def collect_imf_all(**context):
    """Collecter tous les indicateurs FMI"""
    print("💰 Collecte FMI - Tous indicateurs")
    
    indicators = ['PCPIPCH', 'NGDP_RPCH', 'NGDPD', 'NGDPDPC', 'PPPPC', 
                  'LUR', 'GGXCNL_NGDP', 'GGXWDG_NGDP', 'BCA_NGDPD',
                  'TX_RPCH', 'TM_RPCH']
    
    total = 0
    for indicator in indicators:
        try:
            count = run_ingestion("imf", indicator=indicator, country=IMF_COUNTRIES)
            print(f"✅ {indicator}: {count} obs")
            total += count
        except Exception as e:
            print(f"❌ {indicator}: {e}")
    
    return total

def collect_un_sdg_all(**context):
    """Collecter UN SDG"""
    print("🌍 Collecte ONU SDG")
    return run_ingestion("un_sdg")

def collect_afdb_all(**context):
    """Collecter BAD"""
    print("🏦 Collecte BAD")
    return run_ingestion("afdb", country=AFDB_COUNTRIES)

def validate_all_data(**context):
    """Valider les données collectées (WorldBank, IMF, UN, AfDB)"""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    client, db = get_mongo_db()
    
    # Sources hebdomadaires seulement (BRVM collectée séparément chaque heure)
    sources = ['WorldBank', 'IMF', 'UN_SDG', 'AfDB']
    stats = {}
    
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        datasets = len(db.curated_observations.distinct('dataset', {'source': source}))
        stats[source] = {'observations': count, 'datasets': datasets}
        print(f"{source}: {count} obs, {datasets} indicateurs")
    
    total = sum(s['observations'] for s in stats.values())
    print(f"✅ TOTAL (sources hebdomadaires): {total} observations")
    print(f"ℹ️  BRVM collectée séparément toutes les heures via brvm_data_collection_hourly")
    
    client.close()
    return stats

# ============================================================================
# CONFIGURATION DAG
# ============================================================================

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=30),
    'execution_timeout': timedelta(hours=3),
}

dag = DAG(
    'master_complete_collection',
    default_args=default_args,
    description='Collecte hebdomadaire - 4 sources (BRVM a son propre DAG horaire)',
    schedule_interval='0 3 * * 0',  # Chaque dimanche à 3h du matin
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,  # ✅ ACTIVÉ PAR DÉFAUT
    tags=['master', 'weekly', 'auto-collection', 'worldbank-imf-un-afdb'],
)

# Tâches de collecte
task_worldbank = PythonOperator(
    task_id='collect_worldbank',
    python_callable=collect_worldbank_batch,
    dag=dag,
)

task_imf = PythonOperator(
    task_id='collect_imf',
    python_callable=collect_imf_all,
    dag=dag,
)

task_un = PythonOperator(
    task_id='collect_un_sdg',
    python_callable=collect_un_sdg_all,
    dag=dag,
)

task_afdb = PythonOperator(
    task_id='collect_afdb',
    python_callable=collect_afdb_all,
    dag=dag,
)

# Note: BRVM a son propre DAG (brvm_dag.py) qui tourne TOUTES LES HEURES
# pour des données en temps réel du marché boursier

# Validation finale
task_validate = PythonOperator(
    task_id='validate_all',
    python_callable=validate_all_data,
    dag=dag,
)

# Pipeline: collectes des 4 sources en parallèle, puis validation
# BRVM exclue car collecte horaire 24/7 via brvm_data_collection_hourly
[task_worldbank, task_imf, task_un, task_afdb] >> task_validate
