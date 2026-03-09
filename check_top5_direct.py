#!/usr/bin/env python3
"""Vérification directe TOP5 sans Django"""
from pymongo import MongoClient

# Connexion MongoDB directe
client = MongoClient('mongodb://localhost:27017/')
db = client['brvm_db']

week = '2026-W02'

print(f"\n🔍 VÉRIFICATION TOP5 - {week}\n")

# 1. Compter docs avec indicateurs
total = db.prices_weekly.count_documents({'week': week})
with_ind = db.prices_weekly.count_documents({
    'week': week,
    'indicators_computed': True
})

print(f"📊 Total actions: {total}")
print(f"✅ Avec indicateurs: {with_ind}")

# 2. Échantillon avec indicateurs
sample = db.prices_weekly.find_one({
    'week': week,
    'indicators_computed': True
})

if sample:
    print(f"\n📝 Échantillon: {sample['symbol']}")
    print(f"   - RSI: {sample.get('rsi', 'N/A')}")
    print(f"   - Volume ratio: {sample.get('volume_ratio', 'N/A')}")
    print(f"   - Trend: {sample.get('trend', 'N/A')}")
    print(f"   - Close: {sample.get('close', 'N/A')}")
    print(f"   - Week open: {sample.get('open', 'N/A')}")
    
    # Calculer Expected Return simple
    if sample.get('close') and sample.get('open'):
        er = ((sample['close'] - sample['open']) / sample['open']) * 100
        print(f"   - Expected Return: {er:.2f}%")
else:
    print("\n❌ Aucune action avec indicateurs trouvée")

# 3. Lister quelques symboles avec indicateurs
print(f"\n🎯 Symboles avec indicateurs:")
actions_ok = list(db.prices_weekly.find({
    'week': week,
    'indicators_computed': True
}).limit(10))

for a in actions_ok:
    print(f"   - {a['symbol']}: RSI={a.get('rsi', 0):.1f}, Volume={a.get('volume_ratio', 0):.2f}x")

print(f"\n✅ {len(actions_ok)} actions affichées")
