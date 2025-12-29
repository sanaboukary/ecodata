from datetime import datetime
from typing import Optional

from django.core.management.base import BaseCommand, CommandParser

from plateforme_centralisation.mongo import get_mongo_db


class Command(BaseCommand):
    help = "Calcule des KPI simples et écrit dans kpi_snapshots"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--org-id", dest="org_id")
        parser.add_argument("--month", dest="month", help="YYYY-MM (période)")

    def handle(self, *args, **options):
        org_id: Optional[str] = options.get("org_id")
        month: Optional[str] = options.get("month")
        _, db = get_mongo_db()

        if not month:
            self.stderr.write("--month est requis, ex: 2025-10")
            return

        period = {
            "granularity": "month",
            "start": f"{month}-01",
            "end": None,
        }

        match = {"dimensions_snapshot.period_month": month}
        if org_id:
            match["org_id"] = org_id

        # CA_MENSUEL
        pipeline = [
            {"$match": match},
            {"$group": {"_id": None, "value": {"$sum": "$amounts.value"}}},
        ]
        result = list(db.fact_events.aggregate(pipeline))
        value = result[0]["value"] if result else 0
        db.kpi_snapshots.insert_one({
            "kpi_code": "CA_MENSUEL",
            "period": period,
            "scope": ({"org_id": org_id} if org_id else {}),
            "value": value,
            "unit": "EUR",
            "calc_method": "sum(amounts.value) over month",
            "inputs_signature": "compute_kpis:v1",
            "computed_at": datetime.utcnow(),
            "pipeline_version": "gold-1.0.0",
        })

        self.stdout.write(self.style.SUCCESS("KPI CA_MENSUEL calculé."))


