import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pymongo import MongoClient
c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
db = c["centralisation_db"]

print("=== A. FILTRE ENTREE AGREGATEUR ===")
total = db.curated_observations.count_documents(
    {"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}}
)
with_score = db.curated_observations.count_documents({
    "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]},
    "$or": [
        {"attrs.semantic_score_base": {"$exists": True, "$ne": 0}},
        {"attrs.has_catalyseur": True},
    ]
})
with_symbol = db.curated_observations.count_documents({
    "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]},
    "$or": [
        {"attrs.emetteur": {"$exists": True, "$ne": None}},
        {"attrs.symboles": {"$exists": True, "$ne": []}},
    ]
})
qualifying = db.curated_observations.count_documents({
    "$and": [
        {"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}},
        {"$or": [
            {"attrs.semantic_score_base": {"$exists": True, "$ne": 0}},
            {"attrs.has_catalyseur": True},
        ]},
        {"$or": [
            {"attrs.emetteur": {"$exists": True, "$ne": None}},
            {"attrs.symboles": {"$exists": True, "$ne": []}},
        ]}
    ]
})
print(f"  Total publications          : {total}")
print(f"  Avec score!=0 OU catalyseur : {with_score}")
print(f"  Avec emetteur OU symboles   : {with_symbol}")
print(f"  QUALIFIANTS agregateur      : {qualifying}  <- ce que l'agregateur voit")

print()
print("=== B. ETAT ATTRS SUR 5 SAMPLES ===")
sample = list(db.curated_observations.find(
    {"source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]}},
    {"source": 1, "ts": 1, "attrs": 1}
).limit(5))
for d in sample:
    a = d.get("attrs") or {}
    print(f"  {str(d.get('source',''))[:20]} ts={str(d.get('ts',''))[:10]}")
    print(f"    emetteur={a.get('emetteur','ABSENT')}  score_base={a.get('semantic_score_base','ABSENT')}  has_cat={a.get('has_catalyseur','ABSENT')}  sent_score={a.get('sentiment_score','ABSENT')}")

print()
print("=== C. SCORE REEL DANS AGREGATION (value au top level) ===")
agg_docs = list(db.curated_observations.find(
    {"dataset": "AGREGATION_SEMANTIQUE_ACTION"},
    {"key": 1, "value": 1, "attrs": 1}
).sort("value", -1).limit(15))
print(f"  Docs agregation : {len(agg_docs)}")
for d in agg_docs:
    a = d.get("attrs") or {}
    sym = a.get("symbol") or d.get("key") or "?"
    score_val   = d.get("value") or 0
    score_attrs = (a.get("score_semantique_7j") or 0)
    expl = "[EXPL]" if a.get("signal_explosion") else ""
    print(f"  {str(sym):<8s} value={float(score_val):+6.2f}  attrs.score_7j={float(score_attrs):+6.2f} {expl}")

print()
print("=== D. DOCS AVEC attrs.sentiment_score ===")
with_sent = db.curated_observations.count_documents(
    {"attrs.sentiment_score": {"$exists": True, "$ne": None}}
)
nonzero_sent = db.curated_observations.count_documents(
    {"attrs.sentiment_score": {"$exists": True, "$ne": 0}}
)
print(f"  Avec attrs.sentiment_score : {with_sent}")
print(f"  Avec sentiment_score != 0  : {nonzero_sent}")
if nonzero_sent > 0:
    ssample = list(db.curated_observations.find(
        {"attrs.sentiment_score": {"$exists": True, "$ne": 0}},
        {"attrs.emetteur": 1, "attrs.sentiment_score": 1, "attrs.sentiment_impact": 1, "ts": 1}
    ).limit(10))
    for d in ssample:
        a = d.get("attrs") or {}
        print(f"  {str(a.get('emetteur','?')):<8s} sent={a.get('sentiment_score',0):+5.0f}  impact={a.get('sentiment_impact','?')}  ts={str(d.get('ts',''))[:10]}")

print()
print("=== E. DOCS analyse_semantique (V3/V4 - storent semantic_score_base) ===")
sem_v4 = db.curated_observations.count_documents({"attrs.semantic_version": "v4"})
sem_v3 = db.curated_observations.count_documents({"attrs.semantic_version": {"$exists": True}})
any_base = db.curated_observations.count_documents({"attrs.semantic_score_base": {"$exists": True}})
nonzero_base = db.curated_observations.count_documents({"attrs.semantic_score_base": {"$gt": 0}})
print(f"  Docs avec semantic_version=v4    : {sem_v4}")
print(f"  Docs avec semantic_version       : {sem_v3}")
print(f"  Docs avec semantic_score_base    : {any_base}")
print(f"  Docs avec semantic_score_base > 0: {nonzero_base}")
