from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from .pipeline import run_ingestion

def job():
    print(f"[{datetime.utcnow().isoformat()}Z] BRVM hourly ingestion...")
    n = run_ingestion("brvm")
    print(f"Ingested {n} BRVM observations.")

if __name__ == "__main__":
    sched = BlockingScheduler(timezone="UTC")
    sched.add_job(job, CronTrigger.from_crontab("0 * * * *"))  # every hour at :00
    print("Scheduler started. Ctrl+C to stop.")
    sched.start()
