"""
Vérifier le format des timestamps dans la base BRVM
"""
import sys, os, django

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

_, db = get_mongo_db()

print("\n📊 VÉRIFICATION FORMAT TIMESTAMPS\n")

# Échantillon
sample = list(db.curated_observations.find({'source': 'BRVM'}).limit(5))

for obs in sample:
    symbol = obs.get('key')
    ts = obs.get('ts')
    print(f"   {symbol:8s} | ts type: {type(ts).__name__:15s} | value: {ts}")

# Test query avec datetime
threshold_date = datetime.now() - timedelta(days=60)
print(f"\n🔍 Test query avec datetime({threshold_date}):")

count_datetime = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': {'$gte': threshold_date}
})

print(f"   Résultats: {count_datetime} documents")

# Test avec string
threshold_str = threshold_date.strftime('%Y-%m-%d')
print(f"\n🔍 Test query avec string('{threshold_str}'):")

count_string = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': {'$gte': threshold_str}
})

print(f"   Résultats: {count_string} documents\n")

if count_datetime > 0:
    print("✅ Les timestamps sont en format datetime")
    print("❌ Le code recommendation_engine utilise des strings!")
    print("🔧 SOLUTION: Corriger la query dans _analyze_action\n")
elif count_string > 0:
    print("✅ Les timestamps sont en format string")
else:
    print("❌ Problème: Aucune donnée trouvée!\n")
