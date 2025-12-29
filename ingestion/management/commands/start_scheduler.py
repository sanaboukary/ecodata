from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os
import logging

from scripts.pipeline import run_ingestion

logger = logging.getLogger(__name__)

WB_INDICATOR = os.getenv("WB_INDICATOR", "SP.POP.TOTL")
WB_DATE      = os.getenv("WB_DATE", "2000:2024")
WB_COUNTRY   = os.getenv("WB_COUNTRY", "all")

IMF_DATASET  = os.getenv("IMF_DATASET", "IFS")
IMF_KEY      = os.getenv("IMF_KEY", "M.CIV.PCPI_IX")

AFDB_DATASET = os.getenv("AFDB_DATASET", "SOCIO_ECONOMIC_DATABASE")
AFDB_KEY     = os.getenv("AFDB_KEY", "DEBT.EXTERNAL.TOTAL")

UN_SERIES    = os.getenv("UN_SERIES", "SL_TLF_UEM")
UN_AREA      = os.getenv("UN_AREA", "204,854,384,624,466,562,686,768")
UN_TIME      = os.getenv("UN_TIME", "")

BRVM_SYMBOLS = os.getenv("BRVM_SYMBOLS", "BICC,BOABF,BOAM,BOAB")

def job_brvm():
    logger.info(f"[{datetime.utcnow().isoformat()}Z] BRVM hourly job started")
    try:
        n = run_ingestion("brvm")
        logger.info(f"[BRVM] Successfully ingested {n} observations")
    except Exception as e:
        logger.error(f"[BRVM] Ingestion failed: {e}", exc_info=True)

def job_worldbank():
    logger.info(f"[{datetime.utcnow().isoformat()}Z] WorldBank mid-month job started")
    try:
        n = run_ingestion("worldbank", indicator=WB_INDICATOR, date=WB_DATE, country=WB_COUNTRY)
        logger.info(f"[WorldBank] {WB_INDICATOR} - Successfully ingested {n} observations")
    except Exception as e:
        logger.error(f"[WorldBank] Ingestion failed: {e}", exc_info=True)

def job_imf():
    logger.info(f"[{datetime.utcnow().isoformat()}Z] IMF monthly job started")
    try:
        n = run_ingestion("imf", dataset=IMF_DATASET, key=IMF_KEY)
        logger.info(f"[IMF] {IMF_DATASET}/{IMF_KEY} - Successfully ingested {n} observations")
    except Exception as e:
        logger.error(f"[IMF] Ingestion failed: {e}", exc_info=True)

def job_afdb():
    logger.info(f"[{datetime.utcnow().isoformat()}Z] AfDB quarterly job started")
    try:
        n = run_ingestion("afdb", dataset=AFDB_DATASET, key=AFDB_KEY)
        logger.info(f"[AfDB] {AFDB_DATASET}/{AFDB_KEY} - Successfully ingested {n} observations")
    except Exception as e:
        logger.error(f"[AfDB] Ingestion failed: {e}", exc_info=True)

def job_un():
    logger.info(f"[{datetime.utcnow().isoformat()}Z] UN SDG quarterly job started")
    try:
        n = run_ingestion("un", series=UN_SERIES, area=(UN_AREA or None), time=(UN_TIME or None))
        logger.info(f"[UN_SDG] {UN_SERIES} - Successfully ingested {n} observations")
    except Exception as e:
        logger.error(f"[UN_SDG] Ingestion failed: {e}", exc_info=True)

class Command(BaseCommand):
    help = "Scheduler multi-sources (Africa/Abidjan): BRVM(hourly), IMF(monthly), AfDB(quarterly), UN(quarterly), WorldBank(mid-month)"

    def handle(self, *args, **opts):
        sched = BlockingScheduler(timezone="Africa/Abidjan")
        
        # BRVM: Hourly during market hours (9am-4pm, Mon-Fri)
        sched.add_job(job_brvm, CronTrigger(hour="9-16", minute=0, day_of_week="mon-fri", timezone="Africa/Abidjan"))
        
        # IMF: Monthly on 1st day at 2:30 AM
        sched.add_job(job_imf, CronTrigger(hour=2, minute=30, day=1, timezone="Africa/Abidjan"))
        
        # AfDB: Quarterly (Jan, Apr, Jul, Oct 1st at 3 AM)
        sched.add_job(job_afdb, CronTrigger(hour=3, minute=0, day=1, month="1,4,7,10", timezone="Africa/Abidjan"))
        
        # UN SDG: Quarterly (Jan, Apr, Jul, Oct 1st at 3:15 AM)
        sched.add_job(job_un, CronTrigger(hour=3, minute=15, day=1, month="1,4,7,10", timezone="Africa/Abidjan"))
        
        # WorldBank: Mid-month (15th) at 2 AM
        sched.add_job(job_worldbank, CronTrigger(hour=2, minute=0, day=15, timezone="Africa/Abidjan"))
        
        self.stdout.write(self.style.SUCCESS("[OK] Scheduler multi-sources (Africa/Abidjan) demarre."))
        self.stdout.write("[PLANNING]")
        self.stdout.write("   - BRVM: Hourly 9am-4pm (Mon-Fri)")
        self.stdout.write("   - IMF: Monthly (1st, 2:30 AM)")
        self.stdout.write("   - WorldBank: Mid-month (15th, 2:00 AM)")
        self.stdout.write("   - AfDB & UN SDG: Quarterly (Jan/Apr/Jul/Oct 1st, 3:00/3:15 AM)")
        self.stdout.write(self.style.WARNING("[INFO] Press Ctrl+C to stop."))
        
        try:
            sched.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write(self.style.WARNING("Scheduler stopped by user."))
            sched.shutdown()
