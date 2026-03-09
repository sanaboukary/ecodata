#!/usr/bin/env python3
# 📊 APERÇU SÉMANTIQUE FINANCIER – BRVM : Aperçu des tags, scores, risques
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
from plateforme_centralisation.mongo import get_mongo_db
django.setup()
def main():
    _, db = get_mongo_db()

    print("\n=== APERÇU SÉMANTIQUE FINANCIER BRVM ===\n")

    docs = list(db.curated_observations.find({
        "attrs.semantic_tags": {"$exists": True}
    }).sort("ts", -1).limit(20))

    if not docs:
        print("❌ Aucune publication analysée sémantiquement")
        print("👉 Lance d’abord le script d’extraction sémantique")
        return

    for i, doc in enumerate(docs, 1):
        attrs = doc.get("attrs", {})

        titre = attrs.get("titre", "Sans titre")
        emetteur = attrs.get("emetteur", "N/A")
        date = doc.get("ts", "N/A")

        short = attrs.get("semantic_score_short", 0)
        medium = attrs.get("semantic_score_medium", 0)
        long = attrs.get("semantic_score_long", 0)

        tags = attrs.get("semantic_tags", [])
        risk = attrs.get("semantic_risk", "N/A")
        conf = attrs.get("semantic_confidence", 0)

        print(f"{i}. {titre[:90]}")
        print(f"   📅 Date        : {date}")
        print(f"   🏢 Émetteur    : {emetteur}")
        print(f"   🧠 Tags        : {', '.join(tags) if tags else '—'}")
        print(f"   📊 Scores      : CT={short} | MT={medium} | LT={long}")
        print(f"   ⚠️  Risque      : {risk}")
        print(f"   🔎 Confiance   : {conf}")
        #!/usr/bin/env python3
        # 📊 APERÇU SÉMANTIQUE FINANCIER – BRVM : Aperçu des tags, scores, risques
        import django
        django.setup()

        print("-" * 80)

        short = attrs.get("semantic_score_short", 0)
        medium = attrs.get("semantic_score_medium", 0)
        long = attrs.get("semantic_score_long", 0)

        tags = attrs.get("semantic_tags", [])
        risk = attrs.get("semantic_risk", "N/A")
        conf = attrs.get("semantic_confidence", 0)

        print(f"{i}. {titre[:90]}")
        print(f"   📅 Date        : {date}")
        print(f"   🏢 Émetteur    : {emetteur}")
        print(f"   🧠 Tags        : {', '.join(tags) if tags else '—'}")
        print(f"   📊 Scores      : CT={short} | MT={medium} | LT={long}")
        print(f"   ⚠️  Risque      : {risk}")
        print(f"   🔎 Confiance   : {conf}")
        print("-" * 80)

    print("\n✅ Aperçu terminé\n")


if __name__ == "__main__":
    main()
