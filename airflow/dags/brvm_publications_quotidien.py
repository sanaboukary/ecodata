"""
📰 DAG AIRFLOW - COLLECTE QUOTIDIENNE PUBLICATIONS BRVM
========================================================

Schedule : Tous les jours à 18h00 (après clôture BRVM)
Collecte : Bulletins, communiqués, rapports, actualités

🎯 OBJECTIF : Alimenter analyse de sentiment pour trading
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from collecter_publications_brvm_intelligent import BRVMPublicationCollector, CATEGORIES


# Configuration DAG
default_args = {
    'owner': 'brvm_data_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'brvm_publications_quotidien',
    default_args=default_args,
    description='Collecte quotidienne publications BRVM pour analyse sentiment',
    schedule_interval='0 18 * * *',  # 18h00 tous les jours
    start_date=days_ago(1),
    catchup=False,
    tags=['brvm', 'publications', 'sentiment', 'quotidien'],
)


def collect_all_publications(**context):
    """Collecter toutes les publications (priorité haute)"""
    collector = BRVMPublicationCollector()
    
    # Priorité 1-2 : Bulletins et communiqués récents
    collector.collect_all(limit_per_category=50)
    
    stats = collector.stats
    
    # Pousser stats dans XCom pour monitoring
    context['task_instance'].xcom_push(key='total_scraped', value=stats['total_scraped'])
    context['task_instance'].xcom_push(key='total_inserted', value=stats['total_inserted'])
    context['task_instance'].xcom_push(key='by_category', value=stats['by_category'])
    
    return stats['total_inserted']


def collect_bulletins_only(**context):
    """Collecter uniquement bulletins officiels (backup si collecte complète échoue)"""
    collector = BRVMPublicationCollector()
    
    config = CATEGORIES['BULLETIN_OFFICIEL']
    pubs = collector.scrape_category('BULLETIN_OFFICIEL', config)
    
    if pubs:
        inserted, _ = collector.insert_to_mongodb(pubs)
        return inserted
    
    return 0


def verify_collection(**context):
    """Vérifier que la collecte a bien fonctionné"""
    from plateforme_centralisation.mongo import get_mongo_db
    
    _, db = get_mongo_db()
    
    # Compter publications du jour
    today = datetime.now().strftime('%Y-%m-%d')
    count_today = db.curated_observations.count_documents({
        'source': 'BRVM_PUBLICATION',
        'attrs.scraped_at': {'$regex': f'^{today}'}
    })
    
    # Total publications
    count_total = db.curated_observations.count_documents({
        'source': 'BRVM_PUBLICATION'
    })
    
    print(f"✅ Publications collectées aujourd'hui : {count_today}")
    print(f"📊 Total publications en base : {count_total}")
    
    # Alerter si aucune collecte
    if count_today == 0:
        raise ValueError("⚠️ Aucune publication collectée aujourd'hui!")
    
    return count_today


# Tâches
task_collect_all = PythonOperator(
    task_id='collect_all_publications',
    python_callable=collect_all_publications,
    provide_context=True,
    dag=dag,
)

task_collect_bulletins_backup = PythonOperator(
    task_id='collect_bulletins_backup',
    python_callable=collect_bulletins_only,
    provide_context=True,
    trigger_rule='one_failed',  # Lancé si collecte complète échoue
    dag=dag,
)

task_verify = PythonOperator(
    task_id='verify_collection',
    python_callable=verify_collection,
    provide_context=True,
    dag=dag,
)

# Chaîne
task_collect_all >> task_verify
task_collect_all >> task_collect_bulletins_backup >> task_verify
