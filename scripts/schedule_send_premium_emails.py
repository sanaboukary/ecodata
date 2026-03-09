from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dashboard.email_service import send_recommendations_to_premium_users
from datetime import datetime

def job():
    print(f"[{datetime.utcnow().isoformat()}Z] Envoi des recommandations premium...")
    n = send_recommendations_to_premium_users()
    print(f"E-mails envoyés à {n} utilisateurs premium.")

if __name__ == "__main__":
    sched = BlockingScheduler(timezone="Africa/Abidjan")
    # Tous les jours à 8h00
    sched.add_job(job, CronTrigger(hour=8, minute=0))
    print("Scheduler pour envoi automatique des recommandations premium démarré. Ctrl+C pour arrêter.")
    sched.start()
