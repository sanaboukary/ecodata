"""
Scheduler automatique pour collecte quotidienne BRVM
Utilise APScheduler (plus léger qu'Airflow)
"""
import os
import sys
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import numpy as np
import json

from scripts.pipeline import run_ingestion
from dashboard.analytics.recommendation_engine import RecommendationEngine
from plateforme_centralisation.mongo import get_mongo_db


class NumpyEncoder(json.JSONEncoder):
    """Convert NumPy types to Python native types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def convert_numpy_to_python(obj):
    """Recursively convert NumPy types to Python native"""
    if isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Créer le scheduler
scheduler = BlockingScheduler()


def collect_brvm_stocks():
    """Collecte les prix des actions BRVM"""
    try:
        logger.info("=" * 60)
        logger.info("DEBUT: Collecte prix BRVM")
        count = run_ingestion('brvm')
        logger.info(f"SUCCES: {count} observations prix collectees")
        return count
    except Exception as e:
        logger.error(f"ERREUR collecte BRVM: {e}", exc_info=True)
        return 0


def collect_brvm_publications():
    """Collecte les publications officielles BRVM"""
    try:
        logger.info("=" * 60)
        logger.info("DEBUT: Collecte publications BRVM")
        count = run_ingestion('brvm_publications')
        logger.info(f"SUCCES: {count} publications collectees")
        return count
    except Exception as e:
        logger.error(f"ERREUR collecte publications: {e}", exc_info=True)
        return 0


def collect_brvm_fundamentals():
    """Collecte les données fondamentales"""
    try:
        logger.info("=" * 60)
        logger.info("DEBUT: Collecte fondamentaux BRVM")
        count = run_ingestion('brvm_fundamentals')
        logger.info(f"SUCCES: {count} donnees fondamentales collectees")
        return count
    except Exception as e:
        logger.error(f"ERREUR collecte fondamentaux: {e}", exc_info=True)
        return 0


def collect_worldbank_macro():
    """Collecte les indicateurs macro WorldBank"""
    try:
        logger.info("=" * 60)
        logger.info("DEBUT: Collecte WorldBank")
        
        indicators = [
            ('NY.GDP.MKTP.CD', 'GDP'),
            ('FP.CPI.TOTL.ZG', 'Inflation'),
            ('NE.EXP.GNFS.ZS', 'Exports'),
        ]
        
        total_count = 0
        for indicator_code, name in indicators:
            try:
                count = run_ingestion(
                    'worldbank',
                    indicator=indicator_code,
                    country='CI',
                    date='all'
                )
                logger.info(f"  {name}: {count} observations")
                total_count += count
            except Exception as e:
                logger.warning(f"  Erreur {name}: {e}")
        
        logger.info(f"SUCCES: {total_count} observations WorldBank collectees")
        return total_count
        
    except Exception as e:
        logger.error(f"ERREUR collecte WorldBank: {e}", exc_info=True)
        return 0


def generate_daily_recommendations():
    """Génère les recommandations IA du jour"""
    try:
        logger.info("=" * 60)
        logger.info("DEBUT: Generation recommandations IA")
        
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(days=60, min_confidence=65)
        
        # Convert NumPy types to Python native types
        recommendations_clean = convert_numpy_to_python(recommendations)
        
        buy_count = len(recommendations_clean['buy_signals'])
        sell_count = len(recommendations_clean['sell_signals'])
        premium_count = len(recommendations_clean['premium_opportunities'])
        
        # Sauvegarder dans MongoDB
        _, db = get_mongo_db()
        db.daily_recommendations.insert_one({
            'generated_at': datetime.now(),
            'recommendations': recommendations_clean,
            'summary': {
                'buy_count': buy_count,
                'sell_count': sell_count,
                'premium_count': premium_count,
                'total_analyzed': recommendations['total_actions_analyzed']
            }
        })
        
        logger.info(f"SUCCES: {buy_count} ACHAT, {sell_count} VENTE, {premium_count} PREMIUM")
        
        # Afficher top 3
        logger.info("\nTOP 3 RECOMMANDATIONS:")
        for i, rec in enumerate(recommendations['buy_signals'][:3], 1):
            logger.info(f"  {i}. {rec['symbol']}: +{rec['potential_gain']:.1f}% (confiance {rec['confidence']:.0f}%)")
        
        return buy_count + sell_count
        
    except Exception as e:
        logger.error(f"ERREUR generation recommandations: {e}", exc_info=True)
        return 0


def job_collecte_matinale():
    """Job du matin: collecte complète + recommandations"""
    logger.info("\n" + "=" * 60)
    logger.info("JOB MATINAL 8H - COLLECTE COMPLETE")
    logger.info("=" * 60)
    
    # Collecte complète
    stocks = collect_brvm_stocks()
    pubs = collect_brvm_publications()
    fundamentals = collect_brvm_fundamentals()
    wb = collect_worldbank_macro()
    
    # Générer recommandations
    recs = generate_daily_recommendations()
    
    logger.info("\n" + "=" * 60)
    logger.info("RESUME JOB MATINAL:")
    logger.info(f"  Prix BRVM: {stocks}")
    logger.info(f"  Publications: {pubs}")
    logger.info(f"  Fondamentaux: {fundamentals}")
    logger.info(f"  WorldBank: {wb}")
    logger.info(f"  Recommandations: {recs}")
    logger.info("=" * 60 + "\n")


def job_collecte_midi():
    """Job de midi: prix + publications seulement"""
    logger.info("\n" + "=" * 60)
    logger.info("JOB MIDI 12H - MISE A JOUR RAPIDE")
    logger.info("=" * 60)
    
    stocks = collect_brvm_stocks()
    pubs = collect_brvm_publications()
    
    logger.info("\n" + "=" * 60)
    logger.info("RESUME JOB MIDI:")
    logger.info(f"  Prix BRVM: {stocks}")
    logger.info(f"  Publications: {pubs}")
    logger.info("=" * 60 + "\n")


def job_collecte_soir():
    """Job du soir: collecte complète + recommandations"""
    logger.info("\n" + "=" * 60)
    logger.info("JOB SOIR 16H - COLLECTE COMPLETE + RECOMMANDATIONS")
    logger.info("=" * 60)
    
    stocks = collect_brvm_stocks()
    pubs = collect_brvm_publications()
    fundamentals = collect_brvm_fundamentals()
    
    # Générer nouvelles recommandations
    recs = generate_daily_recommendations()
    
    logger.info("\n" + "=" * 60)
    logger.info("RESUME JOB SOIR:")
    logger.info(f"  Prix BRVM: {stocks}")
    logger.info(f"  Publications: {pubs}")
    logger.info(f"  Fondamentaux: {fundamentals}")
    logger.info(f"  Recommandations: {recs}")
    logger.info("=" * 60 + "\n")


# Configuration des jobs
# Lundi à Vendredi: 8h, 12h, 16h
scheduler.add_job(
    job_collecte_matinale,
    CronTrigger(day_of_week='mon-fri', hour=8, minute=0),
    id='job_8h',
    name='Collecte matinale 8h',
    replace_existing=True
)

scheduler.add_job(
    job_collecte_midi,
    CronTrigger(day_of_week='mon-fri', hour=12, minute=0),
    id='job_12h',
    name='Collecte midi 12h',
    replace_existing=True
)

scheduler.add_job(
    job_collecte_soir,
    CronTrigger(day_of_week='mon-fri', hour=16, minute=0),
    id='job_16h',
    name='Collecte soir 16h',
    replace_existing=True
)

# Job de test immédiat (optionnel)
def job_test_immediat():
    """Job de test exécuté immédiatement"""
    logger.info("\n" + "=" * 60)
    logger.info("JOB TEST IMMEDIAT")
    logger.info("=" * 60)
    
    stocks = collect_brvm_stocks()
    pubs = collect_brvm_publications()
    fundamentals = collect_brvm_fundamentals()
    recs = generate_daily_recommendations()
    
    logger.info("\n" + "=" * 60)
    logger.info("RESUME JOB TEST:")
    logger.info(f"  Prix BRVM: {stocks}")
    logger.info(f"  Publications: {pubs}")
    logger.info(f"  Fondamentaux: {fundamentals}")
    logger.info(f"  Recommandations: {recs}")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("DEMARRAGE SCHEDULER AUTOMATIQUE BRVM")
    logger.info("=" * 60)
    logger.info("Jobs configures:")
    logger.info("  - 8h00  : Collecte complete + Recommandations")
    logger.info("  - 12h00 : Mise a jour rapide (prix + publications)")
    logger.info("  - 16h00 : Collecte complete + Recommandations")
    logger.info("  - Jours : Lundi a Vendredi")
    logger.info("=" * 60)
    
    # Lancer un job de test immédiatement
    logger.info("\nExecution d'un job de test immediat...\n")
    job_test_immediat()
    
    logger.info("\nScheduler demarre. En attente des prochains jobs...")
    logger.info("Appuyez sur Ctrl+C pour arreter\n")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\nArret du scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler arrete.")
