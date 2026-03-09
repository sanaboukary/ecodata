#!/usr/bin/env python3
"""Check semantic aggregation in curated_observations"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.centralisation_db

print("="*70)
print("VÉRIFICATION SEMANTIC DATA")
print("="*70)

# 1. Articles RICHBOURSE avec semantic_tags
rich = db.curated_observations.find({"source": "RICHBOURSE"}).limit(5)
print("\n1️⃣  Sample RICHBOURSE (5 premiers):")
for doc in rich:
    attrs = doc.get("attrs", {})
    tags = attrs.get("semantic_tags", [])
    score = attrs.get("semantic_score_base", 0)
    contenu_len = len(attrs.get("contenu", ""))
    print(f"   {attrs.get('titre', 'N/A')[:50]}...")
    print(f"     contenu: {contenu_len} chars")
    print(f"     semantic_tags: {len(tags)} tags → {tags[:3] if tags else 'NONE'}")
    print(f"     semantic_score_base: {score}")
    print()

# 2. Compter combien ont des tags
avec_tags = db.curated_observations.count_documents({
    "source": "RICHBOURSE",
    "attrs.semantic_tags": {"$exists": True, "$ne": []}
})
print(f"2️⃣  RICHBOURSE avec semantic_tags non-vides: {avec_tags}/116")

# 3. Agrégation sémantique
agg_count = db.curated_observations.count_documents({
    "dataset": "AGREGATION_SEMANTIQUE_ACTION"
})
print(f"\n3️⃣  AGREGATION_SEMANTIQUE_ACTION: {agg_count} docs")

if agg_count > 0:
    print("\n   Exemples:")
    for doc in db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}).limit(5):
        symbol = doc.get("key", "N/A")
        attrs = doc.get("attrs", {})
        ct = attrs.get("score_semantique_ct", 0)
        mt = attrs.get("score_semantique_mt", 0)
        lt = attrs.get("score_semantique_lt", 0)
        print(f"   {symbol}: CT={ct:+.1f} | MT={mt:+.1f} | LT={lt:+.1f}")
else:
    print("   ⚠️  Aucune agrégation trouvée!")
    print("\n   DIAGNOSTIC: L'analyse sémantique n'a probablement PAS détecté de tags")
    print("   → Vérifier que semantic_tags contient des valeurs")

print("\n" + "="*70)
