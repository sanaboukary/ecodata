from pymongo import MongoClient
from datetime import datetime

db = MongoClient()['centralisation_db']

print("=== État des collections ===\n")

# decisions_finales_brvm
df_count = db.decisions_finales_brvm.count_documents({})
print(f"decisions_finales_brvm: {df_count} documents")
if df_count > 0:
    latest = db.decisions_finales_brvm.find_one(sort=[('_id', -1)])
    print(f"  Dernier: {latest.get('symbol')} - {latest.get('date_analyse', 'N/A')}")
    print(f"  RS: {latest.get('rs_4sem', 'N/A')}")

print()

# top5_weekly_brvm
t5_count = db.top5_weekly_brvm.count_documents({})
print(f"top5_weekly_brvm: {t5_count} documents")
if t5_count > 0:
    all_t5 = list(db.top5_weekly_brvm.find().sort("rank", 1))
    print(f"  TOP {len(all_t5)}:")
    for t in all_t5:
        print(f"    #{t.get('rank')}: {t.get('symbol')} - RS {t.get('rs_4sem', t.get('relative_strength_pct', 0)):.1f}%")
    
    # Check date
    latest_t5 = all_t5[0]
    if 'date_analyse' in latest_t5:
        print(f"\n  Date analyse: {latest_t5.get('date_analyse')}")
    if 'market_regime' in latest_t5:
        print(f"  Régime: {latest_t5.get('market_regime')}")
