from datetime import datetime
from typing import List, Dict

from django.conf import settings
from django.core.management.base import BaseCommand

from pymongo import MongoClient, ASCENDING, DESCENDING


def get_mongo_client_and_db():
    client = MongoClient(settings.DATABASES["default"]["CLIENT"]["host"])  # type: ignore
    db_name = settings.DATABASES["default"]["NAME"]  # type: ignore
    return client, client[db_name]


def ensure_indexes(db) -> None:
    # raw_events indexes
    db.raw_events.create_index([("source_name", ASCENDING), ("received_at", DESCENDING)])
    db.raw_events.create_index([("batch_id", ASCENDING)])
    db.raw_events.create_index([("status", ASCENDING)])

    # bronze_records indexes
    db.bronze_records.create_index([("record_type", ASCENDING), ("record_key", ASCENDING)], unique=False)
    db.bronze_records.create_index([("processed_at", DESCENDING)])

    # entities_* indexes
    db.entities_organization.create_index([("organization_id", ASCENDING)], unique=True)
    db.entities_organization.create_index([("external_refs.system", ASCENDING), ("external_refs.ref", ASCENDING)])

    db.entities_customer.create_index([("customer_id", ASCENDING)], unique=True)
    db.entities_customer.create_index([("email", ASCENDING)], unique=False)
    db.entities_customer.create_index([("org_id", ASCENDING)])

    db.entities_service.create_index([("service_id", ASCENDING)], unique=True)
    db.entities_service.create_index([("category", ASCENDING)])

    # fact_events indexes
    db.fact_events.create_index([("occurred_at", DESCENDING)])
    db.fact_events.create_index([("org_id", ASCENDING), ("occurred_at", DESCENDING)])
    db.fact_events.create_index([("customer_id", ASCENDING)])
    db.fact_events.create_index([("service_id", ASCENDING)])

    # kpi_snapshots indexes
    db.kpi_snapshots.create_index([("kpi_code", ASCENDING), ("period.start", DESCENDING), ("scope", ASCENDING)])
    db.kpi_snapshots.create_index([("computed_at", DESCENDING)])

    # ingestion_runs indexes
    db.ingestion_runs.create_index([("source_name", ASCENDING), ("started_at", DESCENDING)])
    db.ingestion_runs.create_index([("status", ASCENDING)])

    # data_lineage indexes
    db.data_lineage.create_index([("target_collection", ASCENDING), ("target_id", ASCENDING)])


def base_kpi_definitions() -> List[Dict]:
    now = datetime.utcnow()
    return [
        {
            "kpi_code": "CA_MENSUEL",
            "name": "Chiffre d'affaires mensuel",
            "unit": "EUR",
            "granularity": "month",
            "description": "Somme des montants sur fact_events par mois et par organisation",
            "formula": {
                "collection": "fact_events",
                "aggregation": "sum(amounts.value)",
                "filters": ["org_id", "period.month"],
            },
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "kpi_code": "NB_CLIENTS_ACTIFS",
            "name": "Nombre de clients actifs",
            "unit": "count",
            "granularity": "month",
            "description": "Nombre de clients avec au moins un événement dans la période",
            "formula": {
                "collection": "fact_events",
                "aggregation": "count_distinct(customer_id)",
                "filters": ["org_id", "period.month"],
            },
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "kpi_code": "TAUX_CONVERSION",
            "name": "Taux de conversion",
            "unit": "%",
            "granularity": "month",
            "description": "Conversions / opportunités sur la période",
            "formula": {
                "collection": "fact_events",
                "aggregation": "count(event_type=='conversion') / count(event_type=='opportunity')",
                "filters": ["org_id", "period.month"],
            },
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "kpi_code": "DELAI_MOYEN",
            "name": "Délai moyen de traitement",
            "unit": "seconds",
            "granularity": "month",
            "description": "Délai moyen entre occurred_at et recorded_at",
            "formula": {
                "collection": "fact_events",
                "aggregation": "avg(recorded_at - occurred_at)",
                "filters": ["org_id", "period.month"],
            },
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "kpi_code": "CA_MENSUEL_PAR_SERVICE",
            "name": "CA mensuel par service",
            "unit": "EUR",
            "granularity": "month",
            "description": "Somme des montants groupée par service",
            "formula": {
                "collection": "fact_events",
                "aggregation": "sum(amounts.value) group by service_id",
                "filters": ["org_id", "period.month"],
            },
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]


class Command(BaseCommand):
    help = "Initialise les collections MongoDB, index et KPI de base"

    def handle(self, *args, **options):
        client, db = get_mongo_client_and_db()
        try:
            # Touch collections (création implicite en écriture au besoin)
            for name in [
                "raw_events",
                "bronze_records",
                "entities_organization",
                "entities_customer",
                "entities_service",
                "fact_events",
                "kpi_snapshots",
                "kpi_definitions",
                "ingestion_runs",
                "data_lineage",
            ]:
                db[name].insert_one({"_created_for": name, "ts": datetime.utcnow()})
                db[name].delete_one({"_created_for": name})

            ensure_indexes(db)

            # Seed KPI definitions (upsert par code)
            for kpi in base_kpi_definitions():
                db.kpi_definitions.update_one(
                    {"kpi_code": kpi["kpi_code"]},
                    {"$set": {**kpi, "updated_at": datetime.utcnow()}},
                    upsert=True,
                )

            self.stdout.write(self.style.SUCCESS("MongoDB initialisé: collections, index et KPI de base"))
        finally:
            client.close()


