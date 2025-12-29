#!/usr/bin/env python3
"""
Vérifier les données RÉELLES du 23/12/2025 dans MongoDB
"""
from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

print("=" * 80)
print("🔍 AUDIT DONNÉES BRVM - 23 DÉCEMBRE 2025")
print("=" * 80)

# Données du 23/12
today = '2025-12-23'
data_23dec = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': today
}).sort('value', -1))

print(f"\n📊 DONNÉES DU 23/12/2025: {len(data_23dec)} observations")
print("-" * 80)

if data_23dec:
    print(f"{'SYMBOL':<15} {'PRIX (FCFA)':<15} {'VARIATION':<12} {'QUALITÉ'}")
    print("-" * 80)
    for obs in data_23dec:
        symbol = obs['key']
        price = obs['value']
        var = obs['attrs'].get('variation', 0)
        quality = obs['attrs'].get('data_quality', 'UNKNOWN')
        var_emoji = "🟢" if var > 0 else "🔴" if var < 0 else "⚪"
        print(f"{symbol:<15} {price:<15,.0f} {var_emoji} {var:>6.2f}%    {quality}")
else:
    print("❌ AUCUNE DONNÉE DU 23/12/2025")

# Vérifier SNTS spécifiquement
print("\n" + "=" * 80)
print("🔍 RECHERCHE SNTS (Sonatel)")
print("=" * 80)

snts_all = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': {'$in': ['SNTS', 'SNTS.BC', 'Sonatel']}
}).sort('ts', -1).limit(5))

if snts_all:
    print(f"\n📊 {len(snts_all)} observations SNTS trouvées:")
    for obs in snts_all:
        print(f"   Date: {obs['ts']}, Prix: {obs['value']:,.0f} FCFA, Symbol: {obs['key']}")
else:
    print("❌ SNTS non trouvé dans la base")

# Liste des actions BRVM réelles (47 actions)
print("\n" + "=" * 80)
print("📋 ACTIONS BRVM MANQUANTES DU 23/12")
print("=" * 80)

actions_brvm_officielles = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOCIC',
    'CABC', 'CBIBF', 'CFAC', 'CGFC', 'CIEC', 'ETIT', 'FTSC', 'NEIC', 'NSBC',
    'NSIAC', 'NTLC', 'ONTBF', 'ORGT', 'PALC', 'PRSC', 'SAFAC', 'SAFC', 'SCRC',
    'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICC', 'SICBC', 'SIVC',
    'SLBC', 'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC', 'SVOC', 'TTLC', 'TTLS',
    'TTRC', 'UNXC'
]

collected_symbols = [obs['key'].replace('.BC', '') for obs in data_23dec]
missing = [action for action in actions_brvm_officielles if action not in collected_symbols]

if missing:
    print(f"\n⚠️  {len(missing)} actions manquantes sur 47:")
    for i, action in enumerate(missing[:20], 1):  # Afficher les 20 premières
        print(f"   {i}. {action}")
    if len(missing) > 20:
        print(f"   ... et {len(missing) - 20} autres")
else:
    print("✅ Toutes les 47 actions collectées")

# Statistiques par date
print("\n" + "=" * 80)
print("📅 HISTORIQUE 7 DERNIERS JOURS")
print("=" * 80)

for i in range(7):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date
    })
    status = "✅" if count >= 40 else "⚠️ " if count > 0 else "❌"
    print(f"{status} {date}: {count:>3} observations")

print("\n" + "=" * 80)
print("🎯 RECOMMANDATION")
print("=" * 80)
print("Pour un trading hebdomadaire précis, il faut:")
print("1. Collecter LES 47 ACTIONS chaque jour (actuellement: seulement 13)")
print("2. Utiliser les données des 7-14 derniers jours")
print("3. Analyser les publications de la semaine en cours")
print("4. Scraper le site BRVM COMPLET, pas seulement les top variations")
print("=" * 80)

client.close()
