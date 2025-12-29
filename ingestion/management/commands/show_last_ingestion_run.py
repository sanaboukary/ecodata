from django.core.management.base import BaseCommand
from plateforme_centralisation.mongo import get_mongo_db


class Command(BaseCommand):
    help = "Affiche le dernier document ingestion_runs et les derniers logs"

    def handle(self, *args, **options):
        client, db = get_mongo_db()
        try:
            doc = db.ingestion_runs.find().sort("started_at", -1).limit(1)
            last = next(doc, None)
            if not last:
                self.stdout.write("Aucun run trouvé")
                return
            last["_id"] = str(last["_id"])  # jsonify
            logs = last.get("logs", [])[-3:]
            self.stdout.write("Dernier run:")
            self.stdout.write(str({k: v for k, v in last.items() if k != "logs"}))
            self.stdout.write("Derniers logs:")
            for l in logs:
                self.stdout.write(f"- {l.get('level')}: {l.get('message')}")
                if l.get("stderr"):
                    self.stdout.write(l["stderr"]) 
        finally:
            client.close()


