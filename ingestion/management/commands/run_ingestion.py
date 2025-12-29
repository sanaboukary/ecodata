import os
import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from plateforme_centralisation.mongo import get_mongo_db


class Command(BaseCommand):
    help = "Run data extraction/ingestion scripts from the scripts directory"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--scripts-dir",
            default=str(Path.cwd() / "scripts"),
            help="Directory containing extraction scripts to run",
        )
        parser.add_argument(
            "--pattern",
            default="*.py",
            help="Glob pattern to select scripts (default: *.py)",
        )

    def handle(self, *args, **options):
        scripts_dir = Path(options["scripts_dir"]).resolve()
        pattern = options["pattern"]

        if not scripts_dir.exists():
            self.stderr.write(self.style.ERROR(f"Scripts directory not found: {scripts_dir}"))
            sys.exit(1)

        scripts = sorted(scripts_dir.glob(pattern))
        if not scripts:
            self.stdout.write(self.style.WARNING(f"No scripts matched pattern {pattern} in {scripts_dir}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Running {len(scripts)} script(s) from {scripts_dir}..."))

        # Prepare env for child processes
        env = os.environ.copy()
        env["MONGODB_URI"] = settings.DATABASES["default"]["CLIENT"]["host"]  # type: ignore
        env["MONGODB_NAME"] = settings.DATABASES["default"]["NAME"]  # type: ignore

        client, db = get_mongo_db()
        run_doc = {
            "run_id": f"run_{Path(scripts_dir).name}_{os.getpid()}",
            "source_name": Path(scripts_dir).name,
            "started_at": __import__("datetime").datetime.utcnow(),
            "status": "running",
            "counts": {"read": 0, "valid": 0, "upserted": 0, "skipped": 0, "errors": 0},
            "parameters": {"scripts_dir": str(scripts_dir), "pattern": pattern},
            "logs": [],
        }
        run_id = db.ingestion_runs.insert_one(run_doc).inserted_id

        try:
            for script in scripts:
                self.stdout.write(self.style.NOTICE(f"Executing: {script.name}"))
                result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, env=env, cwd=str(scripts_dir))
                log_entry = {
                    "ts": __import__("datetime").datetime.utcnow(),
                    "level": "INFO" if result.returncode == 0 else "ERROR",
                    "message": f"{script.name}: rc={result.returncode}",
                    "stdout": result.stdout[-4000:] if result.stdout else "",
                    "stderr": result.stderr[-4000:] if result.stderr else "",
                }
                db.ingestion_runs.update_one({"_id": run_id}, {"$push": {"logs": log_entry}})
                if result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS(f"✓ {script.name} completed"))
                else:
                    self.stderr.write(self.style.ERROR(f"✗ {script.name} failed with code {result.returncode}"))
                    db.ingestion_runs.update_one({"_id": run_id}, {"$inc": {"counts.errors": 1}})
        finally:
            db.ingestion_runs.update_one({"_id": run_id}, {"$set": {"finished_at": __import__("datetime").datetime.utcnow(), "status": "success"}})
            client.close()

