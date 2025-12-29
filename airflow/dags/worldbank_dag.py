"""
DAG Airflow pour la collecte automatique des données WorldBank
Collecte TOUS les indicateurs économiques et sociaux
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.pipeline import run_ingestion

# Liste complète des indicateurs WorldBank à collecter
WORLDBANK_INDICATORS = {
    # Démographie
    'SP.POP.TOTL': 'Population totale',
    'SP.DYN.LE00.IN': 'Espérance de vie',
    'SP.URB.TOTL.IN.ZS': 'Population urbaine (% du total)',
    
    # Économie
    'NY.GDP.MKTP.CD': 'PIB ($ US courants)',
    'NY.GDP.MKTP.KD.ZG': 'Croissance du PIB (% annuel)',
    'NY.GDP.PCAP.CD': 'PIB par habitant ($ US courants)',
    'NY.GNP.PCAP.CD': 'RNB par habitant ($ US courants)',
    'NE.EXP.GNFS.ZS': 'Exportations (% du PIB)',
    'NE.IMP.GNFS.ZS': 'Importations (% du PIB)',
    'FP.CPI.TOTL.ZG': 'Inflation (IPC)',
    
    # Éducation
    'SE.PRM.ENRR': 'Taux de scolarisation primaire',
    'SE.SEC.ENRR': 'Taux de scolarisation secondaire',
    'SE.ADT.LITR.ZS': 'Taux d\'alphabétisation des adultes',
    'SE.XPD.TOTL.GD.ZS': 'Dépenses d\'éducation (% du PIB)',
    
    # Santé
    'SH.STA.MMRT': 'Taux de mortalité maternelle',
    'SH.DYN.MORT': 'Taux de mortalité infantile',
    'SH.MED.PHYS.ZS': 'Médecins (pour 1000 habitants)',
    'SH.XPD.CHEX.GD.ZS': 'Dépenses de santé (% du PIB)',
    'SH.H2O.SMDW.ZS': 'Accès à l\'eau potable (% de la population)',
    
    # Infrastructure & Technologie
    'EG.ELC.ACCS.ZS': 'Accès à l\'électricité (% de la population)',
    'IT.NET.USER.ZS': 'Utilisateurs d\'Internet (% de la population)',
    'IT.CEL.SETS.P2': 'Abonnements à la téléphonie mobile (pour 100 personnes)',
    'IS.RRS.TOTL.KM': 'Réseau ferroviaire (km)',
    'IS.ROD.TOTL.KM': 'Réseau routier (km)',
    
    # Environnement
    'EN.ATM.CO2E.PC': 'Émissions de CO2 (tonnes par habitant)',
    'AG.LND.FRST.ZS': 'Superficie forestière (% du territoire)',
    'ER.H2O.FWTL.ZS': 'Prélèvements d\'eau douce',
    
    # Commerce & Investissement
    'BX.KLT.DINV.CD.WD': 'Investissements directs étrangers',
    'NE.TRD.GNFS.ZS': 'Commerce (% du PIB)',
    'TX.VAL.TECH.CD': 'Exportations de haute technologie',
    
    # Dette & Aide
    'DT.DOD.DECT.CD': 'Dette extérieure totale',
    'DT.ODA.ALLD.CD': 'Aide publique au développement nette',
    
    # Emploi
    'SL.UEM.TOTL.ZS': 'Taux de chômage',
    'SL.TLF.TOTL.IN': 'Population active',
}

# Pays de l'Afrique de l'Ouest (UEMOA + autres)
COUNTRIES = "BEN,BFA,CIV,GNB,MLI,NER,SEN,TGO,GHA,GMB,GIN,LBR,MRT,NGA,SLE"

def extract_worldbank_indicator(indicator_code, indicator_name, **context):
    """Extrait un indicateur WorldBank spécifique"""
    print(f"🔄 Extraction WorldBank: {indicator_name} ({indicator_code})")
    
    try:
        count = run_ingestion(
            "worldbank",
            indicator=indicator_code,
            date="2010:2024",
            country=COUNTRIES
        )
        print(f"✓ {count} observations pour {indicator_name}")
        return count
    except Exception as e:
        print(f"✗ Erreur pour {indicator_name}: {e}")
        raise

def validate_worldbank_data(**context):
    """Valide les données WorldBank collectées"""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    
    client, db = get_mongo_db()
    
    total = db.curated_observations.count_documents({'source': 'WorldBank'})
    indicators = db.curated_observations.distinct('dataset', {'source': 'WorldBank'})
    indicators = [i for i in indicators if i is not None]
    
    print(f"✓ Validation WorldBank: {total} observations, {len(indicators)} indicateurs")
    
    client.close()
    
    return {"total_observations": total, "distinct_indicators": len(indicators)}

# Configuration du DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=2),
}

dag = DAG(
    'worldbank_data_collection',
    default_args=default_args,
    description=f'Collecte automatique WorldBank - {len(WORLDBANK_INDICATORS)} indicateurs',
    schedule_interval='0 2 15 * *',  # Le 15 de chaque mois à 2h
    start_date=days_ago(1),
    catchup=False,
    tags=['worldbank', 'economic-data', 'monthly'],
)

# Créer une tâche pour chaque indicateur
tasks = []
for indicator_code, indicator_name in WORLDBANK_INDICATORS.items():
    task = PythonOperator(
        task_id=f'extract_{indicator_code.replace(".", "_").lower()}',
        python_callable=extract_worldbank_indicator,
        op_kwargs={
            'indicator_code': indicator_code,
            'indicator_name': indicator_name
        },
        dag=dag,
    )
    tasks.append(task)

# Tâche de validation finale
validate_task = PythonOperator(
    task_id='validate_worldbank',
    python_callable=validate_worldbank_data,
    dag=dag,
)

# Toutes les tâches d'extraction avant la validation
tasks >> validate_task
