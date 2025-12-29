"""
DAG Airflow pour la collecte automatique des données AfDB et UN SDG
Collecte les indicateurs de développement
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.pipeline import run_ingestion

# Indicateurs AfDB
AFDB_INDICATORS = {
    'DEBT.EXTERNAL.TOTAL': 'Dette extérieure totale',
    'DEBT.DOMESTIC.TOTAL': 'Dette intérieure totale',
    'GDP.GROWTH.RATE': 'Taux de croissance du PIB',
    'FDI.INFLOWS': 'Flux d\'IDE entrants',
    'TRADE.BALANCE': 'Balance commerciale',
    'INFLATION.RATE': 'Taux d\'inflation',
}

# Pays AfDB
AFDB_COUNTRIES = ['BEN', 'BFA', 'CIV', 'GIN', 'MLI', 'NER', 'SEN', 'TGO']

# Séries UN SDG (Objectifs de Développement Durable)
UN_SDG_SERIES = {
    'SL_TLF_UEM': 'Taux de chômage',
    'SI_POV_DAY1': 'Pauvreté (< $1.90/jour)',
    'SH_STA_MORT': 'Mortalité infantile',
    'SE_TOT_PRFL': 'Taux d\'achèvement du primaire',
    'SG_GEN_PARL': 'Proportion de femmes au parlement',
    'EN_ATM_CO2E': 'Émissions de CO2',
    'SH_H2O_SAFE': 'Accès à l\'eau potable',
    'SH_SAN_SAFE': 'Accès à l\'assainissement',
}

# Codes pays UN (numeric)
UN_COUNTRIES = "204,854,384,624,466,562,686,768"  # BEN,BFA,CIV,GIN,MLI,NER,SEN,TGO

def extract_afdb_indicator(indicator, description, **context):
    """Extrait un indicateur AfDB pour tous les pays"""
    print(f"🔄 Extraction AfDB: {description} ({indicator})")
    
    total_count = 0
    for country in AFDB_COUNTRIES:
        try:
            key = f"{country}.{indicator}"
            count = run_ingestion(
                "afdb",
                dataset="SOCIO_ECONOMIC_DATABASE",
                key=key
            )
            total_count += count
            print(f"  ✓ {country}: {count} observations")
        except Exception as e:
            print(f"  ✗ {country}: Erreur - {e}")
    
    print(f"✓ Total {description}: {total_count} observations")
    return total_count

def extract_un_sdg_series(series_code, series_name, **context):
    """Extrait une série UN SDG"""
    print(f"🔄 Extraction UN SDG: {series_name} ({series_code})")
    
    try:
        count = run_ingestion(
            "un",
            series=series_code,
            area=UN_COUNTRIES,
            time=""  # Toutes les périodes disponibles
        )
        print(f"✓ {count} observations pour {series_name}")
        return count
    except Exception as e:
        print(f"✗ Erreur pour {series_name}: {e}")
        raise

def validate_afdb_data(**context):
    """Valide les données AfDB collectées"""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    
    client, db = get_mongo_db()
    
    total = db.curated_observations.count_documents({'source': 'AfDB'})
    keys = db.curated_observations.distinct('key', {'source': 'AfDB'})
    
    print(f"✓ Validation AfDB: {total} observations, {len(keys)} séries")
    
    client.close()
    return {"total_observations": total}

def validate_un_data(**context):
    """Valide les données UN SDG collectées"""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    
    client, db = get_mongo_db()
    
    total = db.curated_observations.count_documents({'source': 'UN_SDG'})
    series = db.curated_observations.distinct('dataset', {'source': 'UN_SDG'})
    
    print(f"✓ Validation UN SDG: {total} observations, {len(series)} séries")
    
    client.close()
    return {"total_observations": total}

# ===== DAG AfDB =====
default_args_afdb = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=1),
}

dag_afdb = DAG(
    'afdb_data_collection',
    default_args=default_args_afdb,
    description=f'Collecte automatique AfDB - {len(AFDB_INDICATORS)} indicateurs, {len(AFDB_COUNTRIES)} pays',
    schedule_interval='0 3 1 1,4,7,10 *',  # Trimestriel (Jan/Avr/Jul/Oct) à 3h
    start_date=days_ago(1),
    catchup=False,
    tags=['afdb', 'development-data', 'quarterly'],
)

# Tâches AfDB
afdb_tasks = []
for indicator, description in AFDB_INDICATORS.items():
    task = PythonOperator(
        task_id=f'extract_{indicator.replace(".", "_").lower()}',
        python_callable=extract_afdb_indicator,
        op_kwargs={
            'indicator': indicator,
            'description': description
        },
        dag=dag_afdb,
    )
    afdb_tasks.append(task)

validate_afdb_task = PythonOperator(
    task_id='validate_afdb',
    python_callable=validate_afdb_data,
    dag=dag_afdb,
)

afdb_tasks >> validate_afdb_task

# ===== DAG UN SDG =====
default_args_un = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=1),
}

dag_un = DAG(
    'un_sdg_data_collection',
    default_args=default_args_un,
    description=f'Collecte automatique UN SDG - {len(UN_SDG_SERIES)} séries ODD',
    schedule_interval='15 3 1 1,4,7,10 *',  # Trimestriel (Jan/Avr/Jul/Oct) à 3h15
    start_date=days_ago(1),
    catchup=False,
    tags=['un-sdg', 'development-data', 'quarterly'],
)

# Tâches UN SDG
un_tasks = []
for series_code, series_name in UN_SDG_SERIES.items():
    task = PythonOperator(
        task_id=f'extract_{series_code.lower()}',
        python_callable=extract_un_sdg_series,
        op_kwargs={
            'series_code': series_code,
            'series_name': series_name
        },
        dag=dag_un,
    )
    un_tasks.append(task)

validate_un_task = PythonOperator(
    task_id='validate_un_sdg',
    python_callable=validate_un_data,
    dag=dag_un,
)

un_tasks >> validate_un_task
