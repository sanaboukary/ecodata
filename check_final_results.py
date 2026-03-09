from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.centralisation_db

# Compter semantic_tags
avec_tags = db.curated_observations.count_documents({
    "source": "RICHBOURSE",
    "attrs.semantic_tags": {"$exists": True, "$ne": []}
})

# Compter agrégations
agg = db.curated_observations.count_documents({
    "dataset": "AGREGATION_SEMANTIQUE_ACTION"
})

# Voir exemples avec scores
samples = list(db.curated_observations.find({
    "dataset": "AGREGATION_SEMANTIQUE_ACTION"
}).limit(5))

with open("resultats_finaux.txt", "w") as f:
    f.write("RESULTATS FINAUX\n")
    f.write("="*60 + "\n\n")
    f.write(f"RICHBOURSE avec semantic_tags: {avec_tags}/116\n")
    f.write(f"AGREGATION_SEMANTIQUE_ACTION: {agg} actions\n\n")
    
    if agg > 0:
        f.write("SCORES (5 premiers):\n")
        for doc in samples:
            symbol = doc.get("key", "N/A")
            attrs = doc.get("attrs", {})
            ct = attrs.get("score_semantique_ct", 0)
            mt = attrs.get("score_semantique_mt", 0)
            lt = attrs.get("score_semantique_lt", 0)
            f.write(f"{symbol}: CT={ct:+.1f} | MT={mt:+.1f} | LT={lt:+.1f}\n")
    else:
        f.write("PAS D'AGREGATION!\n")

print("Resultats dans resultats_finaux.txt")
