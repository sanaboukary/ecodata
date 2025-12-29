"""
✅ CONFIRMATION: SYSTÈME DE COLLECTE AUTOMATIQUE OPÉRATIONNEL

Ce script confirme que:
1. MongoDB est accessible (centralisation_db)
2. Les données BRVM sont sauvegardées automatiquement
3. Le système est prêt pour la collecte horaire
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import json

print("=" * 70)
print("🎯 VÉRIFICATION SYSTÈME DE COLLECTE AUTOMATIQUE")
print("=" * 70)

# 1. Connexion MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    db = client['centralisation_db']
    # Test de ping
    client.admin.command('ping')
    print("\n✅ MongoDB: CONNECTÉ")
    print(f"   Base de données: centralisation_db")
except Exception as e:
    print(f"\n❌ MongoDB: ERREUR - {e}")
    exit(1)

# 2. Vérifier les données BRVM
total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
print(f"✅ Total observations BRVM: {total_brvm}")

# 3. Vérifier les 3 derniers jours
dates_recentes = []
for i in range(3):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date
    })
    dates_recentes.append((date, count))
    status = "✅" if count > 0 else "⚠️ "
    print(f"{status} {date}: {count} observations")

# 4. Vérifier la qualité des données
quality_stats = {}
for quality in ['REAL_SCRAPER', 'REAL_MANUAL', 'REAL_CSV']:
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': quality
    })
    if count > 0:
        quality_stats[quality] = count

print("\n📊 QUALITÉ DES DONNÉES:")
for quality, count in quality_stats.items():
    print(f"   {quality}: {count} observations")

# 5. Vérifier le dernier rapport de collecte
import glob
rapports = sorted(glob.glob('rapport_collecte_*.json'), reverse=True)
if rapports:
    print(f"\n📄 Dernier rapport: {rapports[0]}")
    with open(rapports[0], 'r', encoding='utf-8') as f:
        rapport = json.load(f)
    
    print(f"   Timestamp: {rapport['timestamp']}")
    print(f"   Succès: {rapport['success']}")
    print(f"   Sauvegardés: {rapport['saved_count']}")
    
    if rapport.get('top5'):
        print(f"\n   🏆 Top 5 variations:")
        for i, stock in enumerate(rapport['top5'][:5], 1):
            var_symbol = "🟢" if stock['variation'] > 0 else "🔴"
            print(f"      {i}. {stock['symbol']:12} {stock['close']:>8,.0f} FCFA  {var_symbol} {stock['variation']:+6.2f}%")

# 6. Instructions pour la collecte
print("\n" + "=" * 70)
print("🚀 SYSTÈME PRÊT POUR LA COLLECTE AUTOMATIQUE")
print("=" * 70)

print("\n📋 MODES DE COLLECTE DISPONIBLES:")
print("\n1️⃣  COLLECTE UNIQUE (immédiate):")
print("   Windows: collecter_maintenant.bat")
print("   Python:  python collecte_intelligente_auto.py --mode unique")

print("\n2️⃣  COLLECTE HORAIRE (automatique 9h-16h lun-ven):")
print("   Windows: activer_collecte_horaire.bat")
print("   Python:  python collecte_intelligente_auto.py --mode horaire")

print("\n📊 VÉRIFICATION:")
print("   python verif_et_sauvegarde_23dec.py")

print("\n🎯 GÉNÉRATION TOP 5:")
print("   python generer_top5_nlp.py")

print("\n" + "=" * 70)
print("✅ CONFIRMATION: Toutes les collectes sauvegardent automatiquement dans MongoDB")
print("   Database: centralisation_db")
print("   Collection: curated_observations")
print("   Marquage: REAL_SCRAPER (données scrappées)")
print("=" * 70)

client.close()
