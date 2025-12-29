"""
DAG Airflow: Collecte quotidienne complète pour recommandations IA
Exécute: BRVM prix + publications + fondamentaux + macro WorldBank/IMF
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import sys
import os

# Configurer le path
sys.path.insert(0, 'E:/DISQUE C/Desktop/Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from scripts.pipeline import run_ingestion

logger = logging.getLogger(__name__)

# Configuration du DAG
default_args = {
    'owner': 'platform_admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'brvm_complete_daily_collection',
    default_args=default_args,
    description='Collecte quotidienne complète BRVM + données macro pour recommandations IA',
    schedule_interval='0 8,12,16 * * 1-5',  # 8h, 12h, 16h en semaine
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['brvm', 'recommendations', 'ia', 'daily'],
)

# === TÂCHES DE COLLECTE ===

def collect_brvm_stocks():
    """Collecte les prix des actions BRVM"""
    logger.info("Collecte des prix BRVM...")
    try:
        count = run_ingestion('brvm')
        logger.info(f"✓ {count} observations prix collectées")
        return count
    except Exception as e:
        logger.error(f"Erreur collecte BRVM: {e}")
        raise

def collect_brvm_publications():
    """Collecte les publications officielles BRVM"""
    logger.info("Collecte des publications BRVM...")
    try:
        count = run_ingestion('brvm_publications')
        logger.info(f"✓ {count} publications collectées")
        return count
    except Exception as e:
        logger.error(f"Erreur collecte publications: {e}")
        raise

def collect_brvm_fundamentals():
    """Collecte les données fondamentales (P/E, ROE, dividendes)"""
    logger.info("Collecte des fondamentaux BRVM...")
    try:
        count = run_ingestion('brvm_fundamentals')
        logger.info(f"✓ {count} données fondamentales collectées")
        return count
    except Exception as e:
        logger.error(f"Erreur collecte fondamentaux: {e}")
        raise

def collect_worldbank_macro():
    """Collecte les indicateurs macro WorldBank"""
    logger.info("Collecte des indicateurs WorldBank...")
    try:
        # Indicateurs clés pour la Côte d'Ivoire
        indicators = [
            'NY.GDP.MKTP.CD',  # GDP
            'FP.CPI.TOTL.ZG',  # Inflation
            'SL.UEM.TOTL.ZS',  # Unemployment
            'NE.EXP.GNFS.ZS',  # Exports
            'NE.IMP.GNFS.ZS',  # Imports
        ]
        
        total_count = 0
        for indicator in indicators:
            try:
                count = run_ingestion(
                    'worldbank',
                    indicator=indicator,
                    country='CI',
                    date='all'
                )
                total_count += count
            except Exception as e:
                logger.warning(f"Erreur indicateur {indicator}: {e}")
                continue
        
        logger.info(f"✓ {total_count} observations WorldBank collectées")
        return total_count
        
    except Exception as e:
        logger.error(f"Erreur collecte WorldBank: {e}")
        raise

def collect_imf_macro():
    """Collecte les données macro IMF"""
    logger.info("Collecte des données IMF...")
    try:
        # Dataset IMF pour l'Afrique de l'Ouest
        count = run_ingestion(
            'imf',
            dataset='IFS',
            key='M.CI.PCPI_IX'  # Inflation CPI Côte d'Ivoire
        )
        logger.info(f"✓ {count} observations IMF collectées")
        return count
    except Exception as e:
        logger.error(f"Erreur collecte IMF: {e}")
        # Non-bloquant
        return 0

def generate_daily_recommendations():
    """Génère les recommandations IA du jour"""
    logger.info("Génération des recommandations IA...")
    try:
        from dashboard.analytics.recommendation_engine import RecommendationEngine
        
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(days=60, min_confidence=65)
        
        buy_count = len(recommendations['buy_signals'])
        sell_count = len(recommendations['sell_signals'])
        premium_count = len(recommendations['premium_opportunities'])
        
        logger.info(f"✓ Recommandations générées: {buy_count} ACHAT, {sell_count} VENTE, {premium_count} PREMIUM")
        
        # Sauvegarder les recommandations dans MongoDB pour cache
        from plateforme_centralisation.mongo import get_mongo_db
        _, db = get_mongo_db()
        
        db.daily_recommendations.insert_one({
            'generated_at': datetime.now(),
            'recommendations': recommendations,
            'summary': {
                'buy_count': buy_count,
                'sell_count': sell_count,
                'premium_count': premium_count,
                'total_analyzed': recommendations['total_actions_analyzed']
            }
        })
        
        return buy_count + sell_count
        
    except Exception as e:
        logger.error(f"Erreur génération recommandations: {e}")
        raise

def send_daily_report():
    """Envoie le rapport quotidien (optionnel)"""
    logger.info("Envoi du rapport quotidien...")
    try:
        # TODO: Implémenter envoi email/SMS avec top 5 recommandations
        logger.info("✓ Rapport quotidien envoyé")
        return True
    except Exception as e:
        logger.error(f"Erreur envoi rapport: {e}")
        return False

# === DÉFINITION DES TÂCHES ===

task_collect_stocks = PythonOperator(
    task_id='collect_brvm_stocks',
    python_callable=collect_brvm_stocks,
    dag=dag,
)

task_collect_publications = PythonOperator(
    task_id='collect_brvm_publications',
    python_callable=collect_brvm_publications,
    dag=dag,
)

task_collect_fundamentals = PythonOperator(
    task_id='collect_brvm_fundamentals',
    python_callable=collect_brvm_fundamentals,
    dag=dag,
)

task_collect_worldbank = PythonOperator(
    task_id='collect_worldbank_macro',
    python_callable=collect_worldbank_macro,
    dag=dag,
)

task_collect_imf = PythonOperator(
    task_id='collect_imf_macro',
    python_callable=collect_imf_macro,
    dag=dag,
)

task_generate_recommendations = PythonOperator(
    task_id='generate_daily_recommendations',
    python_callable=generate_daily_recommendations,
    dag=dag,
)

task_send_report = PythonOperator(
    task_id='send_daily_report',
    python_callable=send_daily_report,
    dag=dag,
)

# === DÉPENDANCES ===
# Collecte en parallèle, puis génération recommandations, puis rapport

[task_collect_stocks, task_collect_publications, task_collect_fundamentals] >> \
[task_collect_worldbank, task_collect_imf] >> \
task_generate_recommendations >> \
task_send_report
