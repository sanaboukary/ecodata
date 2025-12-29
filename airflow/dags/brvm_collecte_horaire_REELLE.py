"""
DAG Airflow - COLLECTE HORAIRE BRVM - DONNÉES RÉELLES UNIQUEMENT
🔴 POLITIQUE ZÉRO TOLÉRANCE : Aucune donnée simulée
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def collecter_brvm_horaire_reel(**context):
    """
    Collecte RÉELLE des cours BRVM toutes les heures
    Sources autorisées : Scraping site officiel OU saisie manuelle
    JAMAIS de simulation/estimation
    """
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    from datetime import datetime
    
    print("\n" + "="*80)
    print(f"🔄 COLLECTE HORAIRE BRVM RÉELLE - {datetime.now()}")
    print("="*80)
    
    # Essayer le scraping d'abord
    donnees_collectees = False
    methode = None
    
    # TENTATIVE 1: Scraping site BRVM
    try:
        print("\n1️⃣ Tentative scraping site BRVM...")
        # Import du scraper s'il existe
        try:
            from scripts.connectors.brvm_scraper_production import scraper_brvm_officiel
            data = scraper_brvm_officiel()
            if data and len(data) > 0:
                donnees_collectees = True
                methode = "SCRAPING_SITE_OFFICIEL"
                print(f"   ✅ {len(data)} cours collectés par scraping")
        except ImportError:
            print("   ⚠️  Module scraper non disponible")
        except Exception as e:
            print(f"   ❌ Échec scraping: {e}")
    except Exception as e:
        print(f"   ❌ Erreur tentative scraping: {e}")
    
    # TENTATIVE 2: Vérifier si données du jour déjà en base (saisie manuelle)
    if not donnees_collectees:
        print("\n2️⃣ Vérification données manuelles du jour...")
        client, db = get_mongo_db()
        date_jour = datetime.now().strftime('%Y-%m-%d')
        
        count_jour = db.curated_observations.count_documents({
            'source': 'BRVM',
            'ts': date_jour,
            'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
        })
        
        if count_jour > 30:  # Au moins 30 actions avec données réelles
            print(f"   ✅ {count_jour} cours réels déjà en base (saisie manuelle)")
            donnees_collectees = True
            methode = "DEJA_EN_BASE"
        else:
            print(f"   ⚠️  Seulement {count_jour} cours réels en base")
    
    # RÉSULTAT
    if donnees_collectees:
        print(f"\n{'='*80}")
        print(f"✅ COLLECTE RÉUSSIE - Méthode: {methode}")
        print(f"{'='*80}\n")
        return {'status': 'SUCCESS', 'method': methode}
    else:
        print(f"\n{'='*80}")
        print(f"⚠️  AUCUNE DONNÉE RÉELLE COLLECTÉE")
        print(f"   Actions requises:")
        print(f"   1. Créer le scraper: scripts/connectors/brvm_scraper_production.py")
        print(f"   2. OU saisir manuellement: python mettre_a_jour_cours_brvm.py")
        print(f"   3. OU importer CSV: python import_rapide_brvm.py")
        print(f"\n🔴 POLITIQUE: Le système ne génère JAMAIS de données simulées")
        print(f"{'='*80}\n")
        
        # Ne pas échouer le DAG, juste logger
        return {'status': 'NO_REAL_DATA', 'method': 'NONE'}

def valider_qualite_donnees(**context):
    """Valide que les données sont RÉELLES, pas simulées"""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    
    client, db = get_mongo_db()
    date_jour = datetime.now().strftime('%Y-%m-%d')
    
    # Compter les données réelles vs suspectes
    total = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date_jour
    })
    
    reelles = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date_jour,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    
    suspectes = total - reelles
    
    print(f"\n{'='*80}")
    print(f"📊 VALIDATION QUALITÉ DONNÉES - {date_jour}")
    print(f"{'='*80}")
    print(f"  Total observations: {total}")
    print(f"  Données RÉELLES:    {reelles} ({reelles/total*100:.1f}%)" if total > 0 else "")
    print(f"  Données SUSPECTES:  {suspectes} ({suspectes/total*100:.1f}%)" if total > 0 else "")
    
    if suspectes > 0:
        print(f"\n  ⚠️  {suspectes} observations avec qualité douteuse détectées")
        print(f"      Vérifier et supprimer les données simulées")
    
    print(f"{'='*80}\n")
    
    return {'total': total, 'real': reelles, 'suspect': suspectes}

# Configuration DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(minutes=15),
}

dag = DAG(
    'brvm_collecte_horaire_REELLE',
    default_args=default_args,
    description='Collecte horaire BRVM - DONNÉES RÉELLES UNIQUEMENT (scraping + saisie manuelle)',
    schedule_interval='0 9-16 * * 1-5',  # ⏰ Toutes les heures de 9h à 16h, lun-ven
    start_date=days_ago(1),
    catchup=False,
    is_paused_upon_creation=False,  # ✅ Activé par défaut
    tags=['brvm', 'real-data', 'hourly', 'zero-tolerance'],
)

# Tâches
collecte_task = PythonOperator(
    task_id='collecter_brvm_reel',
    python_callable=collecter_brvm_horaire_reel,
    dag=dag,
)

validation_task = PythonOperator(
    task_id='valider_qualite',
    python_callable=valider_qualite_donnees,
    dag=dag,
)

# Pipeline
collecte_task >> validation_task
