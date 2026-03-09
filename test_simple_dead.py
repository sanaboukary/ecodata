import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from pymongo import MongoClient
    print("✅ MongoDB import OK")
    
    from brvm_pipeline.pipeline_weekly import is_dead_week
    print("✅ is_dead_week import OK")
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    print("✅ MongoDB connexion OK")
    
    obs = db.prices_weekly.find_one({'week': '2026-W06'})
    print(f"✅ Données trouvées: {obs['symbol']}")
    
    # Test is_dead_week
    is_dead = is_dead_week(obs)
    print(f"\nis_dead_week({obs['symbol']}): {is_dead}")
    
    # Détails
    h = obs.get('high', 0)
    l = obs.get('low', 0)
    c = obs.get('close', 0)
    vol = obs.get('volume', 0)
    
    print(f"\nDétails:")
    print(f"  High: {h}")
    print(f"  Low: {l}")
    print(f"  Close: {c}")
    print(f"  Volume: {vol}")
    
    if c > 0:
        range_pct = ((h - l) / c) * 100
        print(f"  Range%: {range_pct:.2f}%")
        
        if range_pct < 0.5:
            print("  → Range < 0.5% = DEAD")
        else:
            print("  → Range >= 0.5% = ACTIVE")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
