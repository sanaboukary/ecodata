"""
DAG AIRFLOW - MISE À JOUR COMPLÈTE TOUTES SOURCES
Exécution quotidienne de la collecte pour toutes les sources (WorldBank, IMF, AfDB, UN SDG)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def collecter_worldbank():
    """Collecter données World Bank"""
    os.chdir(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    import django
    django.setup()
    
    from scripts.pipeline import run_ingestion
    
    indicateurs = ['SP.POP.TOTL', 'NY.GDP.MKTP.CD', 'FP.CPI.TOTL.ZG', 'SL.UEM.TOTL.ZS']
    pays = ['CI', 'BF', 'SN', 'ML', 'BJ', 'TG', 'NE', 'GW']
    
    for country in pays:
        for indicator in indicateurs:
            try:
                run_ingestion('worldbank', indicator=indicator, country=country)
            except Exception as e:
                print(f"Erreur {country}-{indicator}: {e}")

def collecter_imf():
    """Collecter données IMF"""
    os.chdir(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    import django
    django.setup()
    
    from scripts.pipeline import run_ingestion
    
    series = ['PCPI_IX', 'NGDP_R', 'BCA', 'GGXWDG']
    pays = ['CI', 'BF', 'SN', 'ML', 'BJ', 'TG', 'NE', 'GW']
    
    for area in pays:
        for s in series:
            try:
                run_ingestion('imf', series=s, area=area)
            except Exception as e:
                print(f"Erreur {area}-{s}: {e}")

def collecter_afdb():
    """Collecter données AfDB"""
    os.chdir(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    import django
    django.setup()
    
    from scripts.pipeline import run_ingestion
    run_ingestion('afdb')

def collecter_un_sdg():
    """Collecter données UN SDG"""
    os.chdir(project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    import django
    django.setup()
    
    from scripts.pipeline import run_ingestion
    run_ingestion('un_sdg')

# Configuration du DAG
default_args = {
    'owner': 'plateforme_centralisation',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'sources_internationales_quotidien',
    default_args=default_args,
    description='Mise à jour quotidienne des sources internationales (WB, IMF, AfDB, UN)',
    schedule_interval='0 3 * * *',  # 3h du matin tous les jours
    start_date=datetime(2026, 1, 8),
    catchup=False,
    tags=['worldbank', 'imf', 'afdb', 'un_sdg', 'quotidien'],
)

# Tâches en parallèle
task_wb = PythonOperator(
    task_id='collecter_worldbank',
    python_callable=collecter_worldbank,
    dag=dag,
)

task_imf = PythonOperator(
    task_id='collecter_imf',
    python_callable=collecter_imf,
    dag=dag,
)

task_afdb = PythonOperator(
    task_id='collecter_afdb',
    python_callable=collecter_afdb,
    dag=dag,
)

task_un = PythonOperator(
    task_id='collecter_un_sdg',
    python_callable=collecter_un_sdg,
    dag=dag,
)

# Exécution en parallèle
[task_wb, task_imf, task_afdb, task_un]
