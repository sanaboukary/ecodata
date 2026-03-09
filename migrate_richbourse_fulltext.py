#!/usr/bin/env python3
"""
Migration : copie attrs['contenu'] vers attrs['full_text'] pour tous les documents RICHBOURSE sans full_text
"""
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def migrate_richbourse_fulltext():
    _, db = get_mongo_db()
    count = 0
    cursor = db.curated_observations.find({
        "source": "RICHBOURSE",
        "attrs.contenu": {"$exists": True, "$type": "string"},
        "attrs.full_text": {"$exists": False}
    })
    for doc in cursor:
        contenu = doc.get("attrs", {}).get("contenu", "")
        if contenu and len(contenu) > 100:
            db.curated_observations.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "attrs.full_text": contenu,
                    "attrs.full_text_extracted_at": datetime.now().isoformat()
                }}
            )
            print(f"✅ Copié pour : {doc.get('attrs', {}).get('titre', doc.get('_id'))}")
            count += 1
    print(f"\nMigration terminée. {count} documents mis à jour.")

if __name__ == "__main__":
    migrate_richbourse_fulltext()
