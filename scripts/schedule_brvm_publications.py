from apscheduler.schedulers.blocking import BlockingScheduler
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from scripts.connectors.brvm_publications import download_and_store_pdfs

scheduler = BlockingScheduler(timezone='Africa/Abidjan')

@scheduler.scheduled_job('cron', hour=11, minute=0)
def job():
    print('[BRVM Publications] Lancement de la collecte quotidienne...')
    download_and_store_pdfs()
    print('[BRVM Publications] Collecte terminée.')

if __name__ == "__main__":
    print('Scheduler BRVM Publications démarré (tous les jours à 11h)')
    scheduler.start()
