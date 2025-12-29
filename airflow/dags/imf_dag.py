"""
DAG Airflow pour la collecte automatique des données IMF
Collecte plusieurs séries économiques pour les pays d'Afrique de l'Ouest
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.pipeline import run_ingestion

# Séries IMF à collecter (Format: Fréquence.Pays.Indicateur)
IMF_SERIES = {
    # Inflation (IPC) - Mensuel
    'M.BEN.PCPI_IX': 'Bénin - Indice des Prix à la Consommation',
    'M.BFA.PCPI_IX': 'Burkina Faso - IPC',
    'M.CIV.PCPI_IX': 'Côte d\'Ivoire - IPC',
    'M.MLI.PCPI_IX': 'Mali - IPC',
    'M.NER.PCPI_IX': 'Niger - IPC',
    'M.SEN.PCPI_IX': 'Sénégal - IPC',
    'M.TGO.PCPI_IX': 'Togo - IPC',
    
    # Taux de change - Mensuel
    'M.BEN.ENDA_XDC_USD_RATE': 'Bénin - Taux de change',
    'M.CIV.ENDA_XDC_USD_RATE': 'Côte d\'Ivoire - Taux de change',
    'M.SEN.ENDA_XDC_USD_RATE': 'Sénégal - Taux de change',
    
    # Réserves internationales - Mensuel
    'M.BEN.RAXG_USD': 'Bénin - Réserves internationales',
    'M.CIV.RAXG_USD': 'Côte d\'Ivoire - Réserves',
    'M.SEN.RAXG_USD': 'Sénégal - Réserves',
    
    # PIB - Annuel
    'A.BEN.NGDP_R_K_IX': 'Bénin - PIB réel (indice)',
    'A.BFA.NGDP_R_K_IX': 'Burkina Faso - PIB réel',
    'A.CIV.NGDP_R_K_IX': 'Côte d\'Ivoire - PIB réel',
    'A.MLI.NGDP_R_K_IX': 'Mali - PIB réel',
    'A.NER.NGDP_R_K_IX': 'Niger - PIB réel',
    'A.SEN.NGDP_R_K_IX': 'Sénégal - PIB réel',
    'A.TGO.NGDP_R_K_IX': 'Togo - PIB réel',
}

def extract_imf_series(dataset, key, series_name, **context):
    """Extrait une série IMF spécifique"""
    print(f"🔄 Extraction IMF: {series_name} ({key})")
    
    try:
        count = run_ingestion(
            "imf",
            dataset=dataset,
            key=key
        )
        print(f"✓ {count} observations pour {series_name}")
        return count
    except Exception as e:
        print(f"✗ Erreur pour {series_name}: {e}")
        raise

def validate_imf_data(**context):
    """Valide les données IMF collectées"""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    
    client, db = get_mongo_db()
    
    total = db.curated_observations.count_documents({'source': 'IMF'})
    series = db.curated_observations.distinct('key', {'source': 'IMF'})
    
    print(f"✓ Validation IMF: {total} observations, {len(series)} séries")
    
    client.close()
    
    return {"total_observations": total, "distinct_series": len(series)}

# Configuration du DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
    'execution_timeout': timedelta(hours=1),
}

dag = DAG(
    'imf_data_collection',
    default_args=default_args,
    description=f'Collecte automatique IMF - {len(IMF_SERIES)} séries économiques',
    schedule_interval='30 2 1 * *',  # Le 1er de chaque mois à 2h30
    start_date=days_ago(1),
    catchup=False,
    tags=['imf', 'economic-data', 'monthly'],
)

# Créer une tâche pour chaque série
tasks = []
for key, series_name in IMF_SERIES.items():
    # Dataset est toujours IFS (International Financial Statistics)
    task = PythonOperator(
        task_id=f'extract_{key.replace(".", "_").lower()}',
        python_callable=extract_imf_series,
        op_kwargs={
            'dataset': 'IFS',
            'key': key,
            'series_name': series_name
        },
        dag=dag,
    )
    tasks.append(task)

# Tâche de validation finale
validate_task = PythonOperator(
    task_id='validate_imf',
    python_callable=validate_imf_data,
    dag=dag,
)

# Toutes les tâches d'extraction avant la validation
tasks >> validate_task
