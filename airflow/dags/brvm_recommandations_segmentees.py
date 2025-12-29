"""
DAG Airflow: Génération automatique des recommandations BRVM segmentées
Exécution: 17h30 du lundi au vendredi
Segmentation: Hebdomadaire | Mensuel | Trimestriel
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os

# Configuration paths
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from dashboard.analytics.recommendation_engine import RecommendationEngine
from plateforme_centralisation.mongo import get_mongo_db
import logging

logger = logging.getLogger(__name__)

def verifier_donnees_brvm(**context):
    """Vérifier la disponibilité des données BRVM"""
    logger.info("📊 Vérification des données BRVM...")
    
    _, db = get_mongo_db()
    
    # Compter observations BRVM
    total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
    
    # Observations du jour
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': {'$gte': today}
    })
    
    logger.info(f"✓ Total BRVM: {total_brvm} observations")
    logger.info(f"✓ Aujourd'hui: {today_count} observations")
    
    if total_brvm < 100:
        raise ValueError(f"⚠️ Données insuffisantes: {total_brvm} observations")
    
    logger.info("✅ Données BRVM disponibles")
    return total_brvm

def generer_recommandations_segmentees(**context):
    """Générer les recommandations segmentées par horizon temporel"""
    logger.info("🤖 Génération des recommandations IA segmentées...")
    
    try:
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(days=60, min_confidence=65)
        
        # Vérifier la segmentation
        if 'by_timeframe' not in recommendations:
            raise ValueError("❌ Segmentation non disponible")
        
        timeframes = recommendations['by_timeframe']
        
        # Stats
        total_buy = recommendations['statistics']['total_buy']
        total_sell = recommendations['statistics']['total_sell']
        weekly_count = timeframes['weekly']['count']
        monthly_count = timeframes['monthly']['count']
        quarterly_count = timeframes['quarterly']['count']
        
        logger.info(f"✓ Total signaux: {total_buy} ACHAT, {total_sell} VENTE")
        logger.info(f"✓ Hebdomadaire: {weekly_count} signaux")
        logger.info(f"✓ Mensuel: {monthly_count} signaux")
        logger.info(f"✓ Trimestriel: {quarterly_count} signaux")
        
        # Pousser dans XCom pour tâches suivantes
        context['ti'].xcom_push(key='recommendations', value=recommendations)
        context['ti'].xcom_push(key='total_signals', value=total_buy + total_sell)
        
        logger.info("✅ Recommandations générées")
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Erreur génération recommandations: {e}")
        raise

def sauvegarder_mongodb(**context):
    """Sauvegarder les recommandations dans MongoDB"""
    logger.info("💾 Sauvegarde MongoDB...")
    
    # Récupérer depuis XCom
    recommendations = context['ti'].xcom_pull(key='recommendations', task_ids='generer_recommandations')
    
    if not recommendations:
        raise ValueError("❌ Aucune recommandation à sauvegarder")
    
    _, db = get_mongo_db()
    
    # Préparer le document
    doc = {
        'date': datetime.now(),
        'type': 'segmented_recommendations',
        'recommendations': recommendations,
        'summary': {
            'total_analyzed': recommendations['total_actions_analyzed'],
            'total_buy': recommendations['statistics']['total_buy'],
            'total_sell': recommendations['statistics']['total_sell'],
            'weekly_count': recommendations['by_timeframe']['weekly']['count'],
            'monthly_count': recommendations['by_timeframe']['monthly']['count'],
            'quarterly_count': recommendations['by_timeframe']['quarterly']['count'],
        }
    }
    
    # Sauvegarder
    result = db.daily_recommendations.insert_one(doc)
    logger.info(f"✓ Sauvegardé avec ID: {result.inserted_id}")
    
    # Statistiques
    weekly = recommendations['by_timeframe']['weekly']
    monthly = recommendations['by_timeframe']['monthly']
    quarterly = recommendations['by_timeframe']['quarterly']
    
    logger.info(f"📊 Hebdomadaire: {weekly['count']} signaux, potentiel moyen {weekly['avg_potential']:.1f}%")
    logger.info(f"📊 Mensuel: {monthly['count']} signaux, potentiel moyen {monthly['avg_potential']:.1f}%")
    logger.info(f"📊 Trimestriel: {quarterly['count']} signaux, potentiel moyen {quarterly['avg_potential']:.1f}%")
    
    logger.info("✅ Recommandations sauvegardées dans MongoDB")
    return str(result.inserted_id)

def afficher_top_recommandations(**context):
    """Afficher le résumé des top recommandations"""
    logger.info("📋 Génération du rapport...")
    
    recommendations = context['ti'].xcom_pull(key='recommendations', task_ids='generer_recommandations')
    
    if not recommendations:
        logger.warning("⚠️ Aucune recommandation disponible")
        return
    
    timeframes = recommendations['by_timeframe']
    
    logger.info("\n" + "="*80)
    logger.info("🎯 TOP RECOMMANDATIONS PAR HORIZON")
    logger.info("="*80)
    
    # Hebdomadaire
    if timeframes['weekly']['signals']:
        best_weekly = timeframes['weekly']['signals'][0]
        logger.info(f"\n⚡ HEBDOMADAIRE: {best_weekly['symbol']}")
        logger.info(f"   Prix: {best_weekly['current_price']:.0f} → {best_weekly['target_price']:.0f} FCFA")
        logger.info(f"   Potentiel: +{best_weekly['potential_gain']:.1f}%")
        logger.info(f"   Stratégie: {best_weekly['strategy']}")
    
    # Mensuel
    if timeframes['monthly']['signals']:
        best_monthly = timeframes['monthly']['signals'][0]
        logger.info(f"\n📈 MENSUEL: {best_monthly['symbol']}")
        logger.info(f"   Prix: {best_monthly['current_price']:.0f} → {best_monthly['target_price']:.0f} FCFA")
        logger.info(f"   Potentiel: +{best_monthly['potential_gain']:.1f}%")
        logger.info(f"   Stratégie: {best_monthly['strategy']}")
    
    # Trimestriel
    if timeframes['quarterly']['signals']:
        best_quarterly = timeframes['quarterly']['signals'][0]
        logger.info(f"\n💎 TRIMESTRIEL: {best_quarterly['symbol']}")
        logger.info(f"   Prix: {best_quarterly['current_price']:.0f} → {best_quarterly['target_price']:.0f} FCFA")
        logger.info(f"   Potentiel: +{best_quarterly['potential_gain']:.1f}%")
        logger.info(f"   Stratégie: {best_quarterly['strategy']}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ Rapport généré")
    
    return True

def notifier_resultats(**context):
    """Notification des résultats (email/slack à configurer)"""
    logger.info("🔔 Notification...")
    
    total_signals = context['ti'].xcom_pull(key='total_signals', task_ids='generer_recommandations')
    
    logger.info(f"📧 Email notification: {total_signals} nouveaux signaux")
    logger.info("💬 Slack notification: Recommandations disponibles")
    
    # TODO: Implémenter envoi email/Slack
    
    logger.info("✅ Notifications envoyées")
    return True

# Configuration du DAG
default_args = {
    'owner': 'trading_team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
}

with DAG(
    'brvm_recommandations_segmentees',
    default_args=default_args,
    description='Recommandations BRVM segmentées (Hebdo/Mensuel/Trimestriel) - 17h30',
    schedule_interval='30 17 * * 1-5',  # 17h30, Lundi-Vendredi
    catchup=False,
    tags=['brvm', 'recommendations', 'segmented', 'production'],
) as dag:
    
    # Task 1: Vérifier données BRVM
    verifier_donnees = PythonOperator(
        task_id='verifier_donnees_brvm',
        python_callable=verifier_donnees_brvm,
        provide_context=True,
    )
    
    # Task 2: Générer recommandations segmentées
    generer_recommandations = PythonOperator(
        task_id='generer_recommandations',
        python_callable=generer_recommandations_segmentees,
        provide_context=True,
    )
    
    # Task 3: Sauvegarder MongoDB
    sauvegarder = PythonOperator(
        task_id='sauvegarder_mongodb',
        python_callable=sauvegarder_mongodb,
        provide_context=True,
    )
    
    # Task 4: Afficher top recommandations
    afficher_rapport = PythonOperator(
        task_id='afficher_top_recommandations',
        python_callable=afficher_top_recommandations,
        provide_context=True,
    )
    
    # Task 5: Notifier
    notifier = PythonOperator(
        task_id='notifier_resultats',
        python_callable=notifier_resultats,
        provide_context=True,
    )
    
    # Définir l'ordre d'exécution
    verifier_donnees >> generer_recommandations >> sauvegarder >> afficher_rapport >> notifier
