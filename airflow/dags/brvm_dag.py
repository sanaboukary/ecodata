"""
DAG Airflow pour la collecte automatique des données BRVM
Collecte toutes les 47 actions cotées à la BRVM
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.pipeline import run_ingestion
from scripts.connectors.brvm import fetch_brvm
from scripts.connectors.brvm_stocks import get_all_symbols

def extract_brvm_data(**context):
    """Extrait les données BRVM pour toutes les actions"""
    print(f"🔄 Extraction des données BRVM - {datetime.now()}")
    
    data = fetch_brvm()
    symbols = get_all_symbols()
    
    print(f"✓ {len(data)} cotations extraites pour {len(symbols)} actions")
    
    # Pousser les données au contexte Airflow
    context['ti'].xcom_push(key='brvm_data', value=data)
    context['ti'].xcom_push(key='record_count', value=len(data))
    
    return len(data)

def load_brvm_data(**context):
    """Charge les données BRVM dans MongoDB"""
    print(f"💾 Chargement des données BRVM dans MongoDB")
    
    # Récupérer les données du contexte
    record_count = context['ti'].xcom_pull(key='record_count', task_ids='extract_brvm')
    
    # Utiliser le pipeline d'ingestion
    count = run_ingestion("brvm")
    
    print(f"✓ {count} observations insérées dans MongoDB")
    
    return count

def validate_brvm_data(**context):
    """Valide que les données ont bien été insérées"""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    
    client, db = get_mongo_db()
    
    # Vérifier le nombre d'observations BRVM
    total = db.curated_observations.count_documents({'source': 'BRVM'})
    symbols = db.curated_observations.distinct('key', {'source': 'BRVM'})
    
    print(f"✓ Validation: {total} observations BRVM, {len(symbols)} actions distinctes")
    
    client.close()
    
    # Échec si moins de 40 actions (il devrait y en avoir 47+)
    if len(symbols) < 40:
        raise ValueError(f"Nombre d'actions insuffisant: {len(symbols)} < 40")
    
    return {"total_observations": total, "distinct_symbols": len(symbols)}

# Configuration du DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

dag = DAG(
    'brvm_data_collection_hourly',
    default_args=default_args,
    description='Collecte automatique BRVM toutes les heures - 47 actions cotées',
    schedule_interval='0 * * * *',  # ⏰ TOUTES LES HEURES (24/7)
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,  # ✅ ACTIVÉ PAR DÉFAUT
    tags=['brvm', 'market-data', 'hourly', 'real-time'],
)

# Définir les tâches
extract_task = PythonOperator(
    task_id='extract_brvm',
    python_callable=extract_brvm_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_brvm',
    python_callable=load_brvm_data,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_brvm',
    python_callable=validate_brvm_data,
    dag=dag,
)

# Définir l'ordre d'exécution (ETL pipeline)
extract_task >> load_task >> validate_task
