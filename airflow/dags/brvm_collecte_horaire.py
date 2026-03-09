"""
DAG Airflow - Collecte HORAIRE BRVM - DONNÉES RÉELLES UNIQUEMENT
Exécution : Toutes les heures de 9h à 16h, lundi-vendredi (heures de trading)
Politique : Scraping site officiel BRVM → Aucune estimation
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.time_delta import TimeDeltaSensor
import sys
import os

# Ajouter le chemin du projet
PROJECT_PATH = r'E:\DISQUE C\Desktop\Implementation plateforme'
sys.path.insert(0, PROJECT_PATH)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')


def collecter_brvm_horaire():
    """
    Collecte horaire BRVM via scraping intelligent
    - Tente scraping site officiel
    - Évite les doublons (vérification timestamp)
    - Marque data_quality = REAL_SCRAPER
    - JAMAIS d'estimation
    """
    import django
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    from datetime import datetime
    import logging
    
    logger = logging.getLogger('airflow.task')
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    # Timestamp actuel
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    heure_str = now.strftime('%H:%M')
    
    logger.info(f"🕐 Collecte BRVM horaire - {date_str} {heure_str}")
    
    # 1. Vérifier si déjà collecté cette heure
    last_hour = now.replace(minute=0, second=0, microsecond=0)
    count_heure_actuelle = collection.count_documents({
        'source': 'BRVM',
        'ts': {'$gte': last_hour.isoformat()}
    })
    
    if count_heure_actuelle > 0:
        logger.warning(f"⏭️  Déjà collecté cette heure ({count_heure_actuelle} obs) - Skip")
        return {'status': 'skip', 'count': count_heure_actuelle, 'reason': 'already_collected'}
    
    # 2. Importer le scraper production
    sys.path.insert(0, os.path.join(PROJECT_PATH, 'scripts', 'connectors'))
    from brvm_scraper_production import scraper_brvm_complet
    
    # 3. Exécuter le scraping
    logger.info("🌐 Scraping site officiel BRVM...")
    try:
        resultats = scraper_brvm_complet()
        
        if not resultats or len(resultats) == 0:
            logger.error("❌ Scraping échoué - Aucune donnée récupérée")
            return {'status': 'error', 'count': 0, 'reason': 'scraping_failed'}
        
        logger.info(f"✅ Scraping réussi - {len(resultats)} actions récupérées")
        
        # 4. Insérer dans MongoDB
        from scripts.pipeline import run_ingestion
        
        observations = []
        for action, data in resultats.items():
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': action,
                'ts': date_str,
                'value': float(data.get('close', 0)),
                'attrs': {
                    'open': float(data.get('open', 0)),
                    'high': float(data.get('high', 0)),
                    'low': float(data.get('low', 0)),
                    'close': float(data.get('close', 0)),
                    'volume': int(data.get('volume', 0)),
                    'variation': float(data.get('variation', 0)),
                    'data_quality': 'REAL_SCRAPER',
                    'collected_at': now.isoformat(),
                    'collection_hour': now.hour,
                    'scraping_method': 'beautifulsoup'
                }
            }
            observations.append(obs)
        
        # Insertion bulk
        if observations:
            from scripts.mongo_utils import upsert_observations
            upsert_observations(observations)
            
            logger.info(f"💾 {len(observations)} observations insérées dans MongoDB")
            
            return {
                'status': 'success',
                'count': len(observations),
                'date': date_str,
                'hour': heure_str,
                'method': 'scraping'
            }
        
    except Exception as e:
        logger.error(f"❌ Erreur collecte: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {'status': 'error', 'count': 0, 'reason': str(e)}


def verifier_heures_trading():
    """Vérifie qu'on est bien pendant les heures de trading BRVM"""
    now = datetime.now()
    
    # Heures de trading BRVM : 9h30 - 16h30 (fermeture)
    heure = now.hour
    
    if heure < 9 or heure >= 17:
        raise ValueError(f"Hors heures de trading (actuellement {heure}h)")
    
    # Vérifier jour ouvrable (lundi=0, vendredi=4)
    if now.weekday() > 4:
        raise ValueError(f"Hors jours ouvrables (actuellement {now.strftime('%A')})")
    
    print(f"✅ Trading actif - {now.strftime('%A %d/%m/%Y %H:%M')}")
    return True


def generer_rapport_horaire():
    """Génère un rapport de la collecte horaire"""
    import django
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    from datetime import datetime, timedelta
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    
    # Statistiques du jour
    count_jour = collection.count_documents({
        'source': 'BRVM',
        'ts': date_str
    })
    
    # Nombre d'actions distinctes
    actions = collection.distinct('key', {
        'source': 'BRVM',
        'ts': date_str
    })
    
    # Heures de collecte
    pipeline = [
        {'$match': {'source': 'BRVM', 'ts': date_str}},
        {'$group': {'_id': '$attrs.collection_hour', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ]
    heures_collecte = list(collection.aggregate(pipeline))
    
    print(f"\n📊 RAPPORT COLLECTE HORAIRE - {date_str}")
    print(f"   Total observations: {count_jour}")
    print(f"   Actions distinctes: {len(actions)}")
    print(f"   Heures collectées: {len(heures_collecte)}")
    print(f"\n   Détail par heure:")
    for h in heures_collecte:
        heure = h['_id'] if h['_id'] else 'N/A'
        count = h['count']
        print(f"      {heure}h00: {count} obs")
    
    return {
        'date': date_str,
        'total': count_jour,
        'actions': len(actions),
        'heures': len(heures_collecte)
    }


# Configuration DAG
default_args = {
    'owner': 'brvm_trading',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 6),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=10),
}

dag = DAG(
    'brvm_collecte_horaire_automatique',
    default_args=default_args,
    description='Collecte horaire BRVM pendant heures de trading (9h-16h, lun-ven)',
    schedule_interval='0 9-16 * * 1-5',  # Toutes les heures de 9h à 16h, lundi-vendredi
    catchup=False,
    max_active_runs=1,  # Une seule exécution à la fois
    tags=['brvm', 'horaire', 'production', 'real-time', 'scraping'],
)

# Tâche 1: Vérification heures trading
verif_heures = PythonOperator(
    task_id='verifier_heures_trading',
    python_callable=verifier_heures_trading,
    dag=dag,
)

# Tâche 2: Collecte via scraping
collecte = PythonOperator(
    task_id='collecter_brvm_horaire',
    python_callable=collecter_brvm_horaire,
    dag=dag,
)

# Tâche 3: Rapport horaire
rapport = PythonOperator(
    task_id='generer_rapport_horaire',
    python_callable=generer_rapport_horaire,
    dag=dag,
)

# Workflow
verif_heures >> collecte >> rapport
