from datetime import datetime
import uuid

from _common import get_db_from_env


if __name__ == "__main__":
	client, db = get_db_from_env()
	batch_id = f"sample_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

	raw_doc = {
		"source_name": "sample_source",
		"event_type": "sale",
		"payload": {"customer_id": "C-DEMO", "service_id": "S-DEMO", "amount": 123.45},
		"received_at": datetime.utcnow().isoformat(),
		"ingested_at": datetime.utcnow().isoformat(),
		"batch_id": batch_id,
		"status": "processed",
	}
	db.raw_events.insert_one(raw_doc)

	fact = {
		"event_id": str(uuid.uuid4()),
		"event_type": "sale",
		"org_id": "ORG01",
		"customer_id": "C-DEMO",
		"service_id": "S-DEMO",
		"amounts": {"value": 123.45, "currency": "EUR"},
		"quantities": {"units": 1},
		"timestamps": {"occurred_at": datetime.utcnow().isoformat(), "recorded_at": datetime.utcnow().isoformat()},
		"dimensions_snapshot": {"service_category": "DEMO", "customer_segment": "DEMO", "period_month": datetime.utcnow().strftime('%Y-%m')},
	}
	db.fact_events.insert_one(fact)

	print("sample_extract: OK")
