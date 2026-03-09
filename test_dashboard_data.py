"""Test rapide : Simuler ce que le dashboard va afficher"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

print("=" * 90)
print("🎯 SIMULATION DU DASHBOARD - DONNÉES QUI SERONT AFFICHÉES")
print("=" * 90)

# 1. Données BRVM (comme dans le dashboard)
print("\n1️⃣ Section BRVM du dashboard:")
brvm_count = db.curated_observations.count_documents({'source': 'BRVM'})
brvm_latest = db.curated_observations.find_one(
    {'source': 'BRVM'},
    sort=[('ts', -1)]
)
brvm_keys = db.curated_observations.distinct('key', {'source': 'BRVM'})

print(f"   Total observations: {brvm_count:,}")
print(f"   Nombre d'actions: {len(brvm_keys)}")
if brvm_latest:
    print(f"   Dernière mise à jour: {brvm_latest.get('ts', 'N/A')}")
    print(f"   Dernière action: {brvm_latest.get('key', 'N/A')}")
    print(f"   Dernier prix: {brvm_latest.get('value', 'N/A')} FCFA")

# 2. Les 10 actions les plus récemment mises à jour
print("\n2️⃣ 10 actions les plus récentes (ce qui apparaîtra en haut du dashboard):")
recent_actions = list(db.curated_observations.find({
    'source': 'BRVM'
}).sort('ts', -1).limit(10))

for i, action in enumerate(recent_actions, 1):
    symbol = action.get('key', 'N/A')
    name = action.get('attrs', {}).get('name', symbol)
    price = action.get('value', 0)
    date = action.get('ts', 'N/A')
    
    # Marquer SNTS
    mark = "🎯" if symbol == 'SNTS' else "  "
    print(f"   {mark} {i:2d}. {symbol:8s} - {name:30s} | {price:>10,.0f} FCFA | {date}")

# 3. Vérifier Sonatel spécifiquement
print("\n3️⃣ Zoom sur Sonatel (SNTS):")
snts_all = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': 'SNTS'
}).sort('ts', -1).limit(3))

if snts_all:
    for i, snts in enumerate(snts_all, 1):
        price = snts.get('value', 0)
        date = snts.get('ts', 'N/A')
        quality = snts.get('attrs', {}).get('data_quality', 'N/A')
        
        status = ""
        if price == 25500:
            status = "✅ CORRECT"
        elif price in [3475, 3405]:
            status = "❌ ANCIEN (données simulées)"
        else:
            status = f"⚠️ Vérifier ({price:,} FCFA)"
        
        print(f"   {i}. Date: {date} | Prix: {price:>10,.0f} FCFA | Qualité: {quality:20s} | {status}")
else:
    print("   ❌ Aucune donnée Sonatel trouvée")

# 4. Test du moteur de recommandations
print("\n4️⃣ Test du moteur de recommandations:")
try:
    from dashboard.correlation_engine import generate_trading_recommendations
    
    print("   📊 Génération des recommandations (7 derniers jours)...")
    recos = generate_trading_recommendations(days=7)
    
    if recos:
        print(f"   ✅ {len(recos)} recommandations générées")
        for reco in recos[:5]:  # Afficher les 5 premières
            print(f"      - {reco.get('action')}: {reco.get('recommandation')}")
    else:
        print("   ℹ️ Aucune recommandation générée (normal si pas de publications corrélées)")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n" + "=" * 90)
print("💡 Pour voir ces données dans le dashboard:")
print("   1. Démarrez le serveur: python manage.py runserver")
print("   2. Ouvrez: http://127.0.0.1:8000/")
print("=" * 90)
