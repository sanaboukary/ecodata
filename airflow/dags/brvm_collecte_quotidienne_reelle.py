"""
DAG Airflow - Collecte Quotidienne BRVM - DONNÉES RÉELLES UNIQUEMENT
Exécution : 17h00 lundi-vendredi (après clôture BRVM à 16h30)
Politique : Aucune estimation, aucune simulation - Données officielles uniquement
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Ajouter le chemin du projet
PROJECT_PATH = r'E:\DISQUE C\Desktop\Implementation plateforme'
sys.path.insert(0, PROJECT_PATH)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

default_args = {
    'owner': 'brvm_trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
}

dag = DAG(
    'brvm_collecte_quotidienne_reelle',
    default_args=default_args,
    description='Collecte quotidienne BRVM - Données réelles uniquement (scraping ou saisie manuelle)',
    schedule_interval='0 17 * * 1-5',  # 17h00 lundi-vendredi
    catchup=False,
    tags=['brvm', 'quotidien', 'production', 'real-data-only'],
)

def verifier_donnees_jour():
    """Vérifie si des données réelles existent pour aujourd'hui."""
    import django
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    from datetime import datetime
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    date_aujourd_hui = datetime.now().strftime('%Y-%m-%d')
    
    count = collection.count_documents({
        'source': 'BRVM',
        'ts': date_aujourd_hui,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    
    print(f"📊 Observations réelles trouvées pour {date_aujourd_hui} : {count}")
    
    if count == 0:
        print("⚠️  AUCUNE DONNÉE RÉELLE COLLECTÉE AUJOURD'HUI")
        print("   → Scraping échoué ET saisie manuelle non effectuée")
        print("   → Le système n'a PAS ajouté de données estimées")
        raise ValueError("Aucune donnée réelle disponible - Collecte échouée")
    
    if count < 40:
        print(f"⚠️  Seulement {count} observations (attendu: ~47)")
        print("   → Collecte partielle - Données incomplètes")
    else:
        print(f"✅ Collecte complète : {count} observations réelles")
    
    return count

def verifier_qualite_donnees():
    """Vérifie que TOUTES les données sont réelles (pas d'estimation)."""
    import django
    django.setup()
    
    from plateforme_centralisation.mongo import get_mongo_db
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    # Compter données sans marqueur de qualité
    count_sans_marqueur = collection.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$exists': False}
    })
    
    # Compter données simulées
    count_simulees = collection.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$nin': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    
    total_non_reel = count_sans_marqueur + count_simulees
    
    if total_non_reel > 0:
        print(f"🔴 ALERTE : {total_non_reel} observations NON RÉELLES détectées !")
        print(f"   • Sans marqueur : {count_sans_marqueur}")
        print(f"   • Simulées : {count_simulees}")
        raise ValueError("Données non réelles détectées - Violation politique qualité")
    
    print("✅ Toutes les données BRVM sont marquées comme réelles")
    return True

def notifier_echec_collecte():
    """Notification en cas d'échec de collecte."""
    print("\n" + "=" * 80)
    print("🔴 NOTIFICATION : COLLECTE QUOTIDIENNE ÉCHOUÉE")
    print("=" * 80)
    print("\n⚠️  Aucune donnée réelle n'a pu être collectée aujourd'hui")
    print("\n💡 Actions requises :")
    print("   1. Vérifier connexion Internet")
    print("   2. Vérifier accès site BRVM : https://www.brvm.org")
    print("   3. Saisir manuellement : python mettre_a_jour_cours_brvm.py")
    print("   4. Ou importer CSV : python collecter_csv_automatique.py")
    print("\n🔴 RAPPEL : Le système n'ajoute JAMAIS de données estimées")
    print("=" * 80 + "\n")

# TASK 1 : Collecte intelligente (scraping → saisie manuelle)
task_collecter = BashOperator(
    task_id='collecter_donnees_reelles',
    bash_command=f'cd "{PROJECT_PATH}" && python collecter_quotidien_intelligent.py',
    dag=dag,
)

# TASK 2 : Vérification présence données
task_verifier_presence = PythonOperator(
    task_id='verifier_donnees_collectees',
    python_callable=verifier_donnees_jour,
    dag=dag,
)

# TASK 3 : Vérification qualité (100% réel)
task_verifier_qualite = PythonOperator(
    task_id='verifier_qualite_100pct_reel',
    python_callable=verifier_qualite_donnees,
    dag=dag,
)

# TASK 4 : Notification échec (si tasks précédentes échouent)
task_notifier_echec = PythonOperator(
    task_id='notifier_echec_collecte',
    python_callable=notifier_echec_collecte,
    trigger_rule='one_failed',  # Exécuté si une task échoue
    dag=dag,
)

# TASK 5 : Rapport final
task_rapport = BashOperator(
    task_id='generer_rapport_final',
    bash_command=f'cd "{PROJECT_PATH}" && python collecter_quotidien_intelligent.py --rapport',
    dag=dag,
)

# Workflow
task_collecter >> task_verifier_presence >> task_verifier_qualite >> task_rapport
[task_collecter, task_verifier_presence, task_verifier_qualite] >> task_notifier_echec
