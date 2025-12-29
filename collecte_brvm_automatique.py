"""
Collecte automatique des données BRVM toutes les heures
Lance la collecte BRVM en continu avec APScheduler
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Configuration Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from scripts.pipeline import run_ingestion

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/brvm_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def collect_brvm():
    """Collecte les données BRVM"""
    try:
        logger.info("="*80)
        logger.info("🚀 DÉBUT DE LA COLLECTE BRVM")
        logger.info("="*80)
        
        # Lancer la collecte BRVM
        run_ingestion(source="brvm")
        
        logger.info("✅ Collecte BRVM terminée avec succès")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la collecte BRVM: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Fonction principale - Lance le scheduler"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                  🤖 COLLECTE AUTOMATIQUE BRVM - MODE CONTINU                  ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

📊 Configuration de la collecte automatique:
   • Source: BRVM (Bourse Régionale des Valeurs Mobilières)
   • Fréquence: Toutes les heures
   • Actions: 47 actions cotées
   • Mode: Temps réel avec fallback simulation

🕐 Heures de collecte:
   • Toutes les heures de 00:00 à 23:00
   • Collection continue 24/7

📝 Logs:
   • Fichier: logs/brvm_collection.log
   • Console: Affichage en temps réel

🛑 Pour arrêter: Ctrl+C

════════════════════════════════════════════════════════════════════════════════
    """)
    
    # Créer le dossier logs s'il n'existe pas
    Path("logs").mkdir(exist_ok=True)
    
    # Créer le scheduler
    scheduler = BlockingScheduler()
    
    # Ajouter la tâche de collecte BRVM toutes les heures
    scheduler.add_job(
        collect_brvm,
        CronTrigger(minute=0),  # À chaque heure pile (minute 0)
        id='brvm_hourly_collection',
        name='Collecte BRVM horaire',
        replace_existing=True
    )
    
    logger.info("✅ Scheduler configuré - Collecte BRVM toutes les heures")
    logger.info(f"📅 Prochaine collecte: {scheduler.get_jobs()[0].next_run_time}")
    
    # Lancer une collecte immédiate au démarrage
    logger.info("🚀 Lancement d'une collecte immédiate...")
    collect_brvm()
    
    try:
        # Démarrer le scheduler
        logger.info("🔄 Démarrage du scheduler...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Arrêt du scheduler...")
        scheduler.shutdown()
        logger.info("✅ Scheduler arrêté proprement")

if __name__ == "__main__":
    main()
