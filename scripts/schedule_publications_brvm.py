"""
Scheduler pour collecter automatiquement les publications BRVM
Collecte à 10h et 15h chaque jour
"""
import schedule
import time
import logging
from datetime import datetime
from scripts.pipeline import run_ingestion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_brvm_publications():
    """Collecte les publications BRVM"""
    logger.info("🔔 Début collecte publications BRVM")
    try:
        count = run_ingestion("brvm_publications")
        logger.info(f"✅ Collecte publications terminée: {count} publications")
    except Exception as e:
        logger.error(f"❌ Erreur collecte publications: {e}")


def main():
    """Lance le scheduler pour les publications BRVM"""
    logger.info("🚀 Démarrage du scheduler publications BRVM")
    logger.info("📅 Planning: Collecte à 10h00 et 15h00 chaque jour")
    
    # Programmer la collecte à 10h et 15h
    schedule.every().day.at("10:00").do(collect_brvm_publications)
    schedule.every().day.at("15:00").do(collect_brvm_publications)
    
    # Collecte immédiate au démarrage
    logger.info("🔄 Collecte initiale...")
    collect_brvm_publications()
    
    logger.info("✅ Scheduler en attente des prochaines collectes...")
    
    # Boucle infinie
    while True:
        schedule.run_pending()
        time.sleep(60)  # Vérifier toutes les minutes


if __name__ == "__main__":
    main()
