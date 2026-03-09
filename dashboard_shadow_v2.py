#!/usr/bin/env python3
"""Dashboard Shadow V2 - Comparaison rapide TOP 5 v1 vs v2"""

from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
db = client["centralisation_db"]  # Base Django (données daily existantes)

print("\n" + "=" * 80)
print(f"DASHBOARD SHADOW V2 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 80 + "\n")

# Compter collections
count_v1 = db.curated_observations.count_documents({"dataset": "DECISION_FINALE_BRVM"})
count_v2 = db.curated_observations.count_documents({"dataset": "ALPHA_V2_SHADOW"})

print(f"📊 DONNEES DISPONIBLES:")
print(f"   V1 (Production):  {count_v1} actions")
print(f"   V2 (Shadow):      {count_v2} actions")
print()

if count_v2 > 0:
    # TOP 5 V2
    print("🔥 TOP 5 ALPHA V2 (Shadow - Formule 4 Facteurs):")
    print("-" * 80)
    print(f"{'Rank':>4} | {'Symbol':<8} | {'Alpha':<8} | {'Categ':<8} | {'RS%':<8} | {'Details'}")
    print("-" * 80)
    
    top5_v2 = list(db.curated_observations.find({
        "dataset": "ALPHA_V2_SHADOW",
        "attrs.categorie": {"$ne": "REJECTED"}
    }).sort("value", -1).limit(5))
    
    for i, doc in enumerate(top5_v2, 1):
        symbol = doc["key"]
        alpha = doc["value"]
        attrs = doc.get("attrs", {})
        cat = attrs.get("categorie", "?")
        rs = attrs.get("rs_percentile", 0)
        
        # Details facteurs
        details = attrs.get("details", {})
        em_score = details.get("early_momentum", {}).get("score", 0)
        vs_score = details.get("volume_spike", {}).get("score", 0)
        ev_score = details.get("event", {}).get("score", 0)
        sent_score = details.get("sentiment", {}).get("score", 0)
        
        detail_str = f"EM:{em_score:.0f} VS:{vs_score:.0f} Ev:{ev_score:.0f} Sent:{sent_score:.0f}"
        
        print(f"{i:>4} | {symbol:<8} | {alpha:<8.1f} | {cat:<8} | P{rs:<7.0f} | {detail_str}")
    
    print()
    
    # Rejetes
    rejected = db.curated_observations.count_documents({
        "dataset": "ALPHA_V2_SHADOW",
        "attrs.categorie": "REJECTED"
    })
    
    if rejected > 0:
        print(f"❌ REJETES (filtres): {rejected} actions")
        
        rejetes_list = list(db.curated_observations.find({
            "dataset": "ALPHA_V2_SHADOW",
            "attrs.categorie": "REJECTED"
        }).limit(10))
        
        for doc in rejetes_list[:5]:
            symbol = doc["key"]
            raison = doc.get("attrs", {}).get("raison_rejet", "?")
            print(f"   {symbol:6s}: {raison}")
        
        if rejected > 5:
            print(f"   ... et {rejected - 5} autres")
    
    print()

else:
    print("⚠️  Aucune donnee V2 - Executer alpha_score_v2_shadow.py d'abord\n")

# Comparaison avec V1 si disponible
if count_v1 > 0 and count_v2 > 0:
    print("\n" + "=" * 80)
    print("📈 COMPARAISON V1 vs V2:")
    print("-" * 80)
    
    # TOP 5 V1
    top5_v1 = list(db.curated_observations.find({
        "dataset": "DECISION_FINALE_BRVM"
    }).sort("attrs.ALPHA_SCORE", -1).limit(5))
    
    symbols_v1 = [d["key"] for d in top5_v1]
    symbols_v2 = [d["key"] for d in top5_v2]
    
    common = set(symbols_v1).intersection(set(symbols_v2))
    turnover = len(set(symbols_v1).symmetric_difference(set(symbols_v2))) / 5.0
    
    print(f"\nTOP 5 V1 (Production): {', '.join(symbols_v1)}")
    print(f"TOP 5 V2 (Shadow):     {', '.join(symbols_v2)}")
    print(f"\nCommuns:   {len(common)}/5 {common if common else ''}")
    print(f"Turnover:  {turnover*100:.0f}% rotation")
    print()
    
elif count_v1 > 0:
    print("\n📊 TOP 5 V1 (Production uniquement):")
    print("-" * 80)
    top5_v1 = list(db.curated_observations.find({
        "dataset": "DECISION_FINALE_BRVM"
    }).sort("attrs.ALPHA_SCORE", -1).limit(5))
    
    for i, doc in enumerate(top5_v1, 1):
        symbol = doc["key"]
        alpha = doc.get("attrs", {}).get("ALPHA_SCORE", 0)
        signal = doc.get("attrs", {}).get("SIGNAL", "?")
        print(f"{i}. {symbol:6s} | Alpha: {alpha:5.1f} | {signal}")
    print()

print("=" * 80)
print("💡 Prochain: Executer comparaison_v1_v2.py pour validation quantitative")
print("=" * 80 + "\n")

client.close()
