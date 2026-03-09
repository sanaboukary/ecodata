#!/usr/bin/env python3
"""Collecte BRVM et affichage immédiat - Version ultra-rapide"""
import os
import sys
from datetime import datetime

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("\n" + "="*70)
print("🚀 COLLECTE BRVM + AFFICHAGE IMMÉDIAT")
print("="*70)

client, db = get_mongo_db()
today = datetime.now().strftime('%Y-%m-%d')

# 1. Vérifier données existantes
print(f"\n📅 Date: {today}")
existing = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE',
    'ts': today
})

print(f"   Données existantes: {existing}")

if existing > 0:
    print(f"\n✅ {existing} observations déjà en base pour aujourd'hui")
    print("\n📊 AFFICHAGE DES DONNÉES:")
    print("-" * 70)
    
    data = list(db.curated_observations.find({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': today
    }).sort('key', 1))
    
    print(f"\n{'SYMBOLE':<8} | {'PRIX (FCFA)':>12} | {'VOLUME':>10} | {'VAR %':>8} | QUALITÉ")
    print("-" * 70)
    
    for obs in data:
        symbol = obs['key']
        price = obs['value']
        attrs = obs.get('attrs', {})
        volume = attrs.get('volume', 0)
        var = attrs.get('variation', 0)
        quality = attrs.get('data_quality', 'UNKNOWN')
        
        print(f"{symbol:<8} | {price:>12,.0f} | {volume:>10,} | {var:>+7.2f}% | {quality}")
    
    # Statistiques
    total_volume = sum(obs.get('attrs', {}).get('volume', 0) for obs in data)
    avg_var = sum(obs.get('attrs', {}).get('variation', 0) for obs in data) / len(data) if data else 0
    
    print("-" * 70)
    print(f"\n📈 STATISTIQUES:")
    print(f"   Total actions: {len(data)}")
    print(f"   Volume total: {total_volume:,} titres")
    print(f"   Variation moyenne: {avg_var:+.2f}%")
    
    # Top gainers/losers
    sorted_by_var = sorted(data, key=lambda x: x.get('attrs', {}).get('variation', 0), reverse=True)
    
    print(f"\n🔝 TOP 5 HAUSSES:")
    for obs in sorted_by_var[:5]:
        symbol = obs['key']
        var = obs.get('attrs', {}).get('variation', 0)
        price = obs['value']
        print(f"   {symbol:<8} | {var:>+7.2f}% | {price:>10,.0f} FCFA")
    
    print(f"\n🔻 TOP 5 BAISSES:")
    for obs in sorted_by_var[-5:]:
        symbol = obs['key']
        var = obs.get('attrs', {}).get('variation', 0)
        price = obs['value']
        print(f"   {symbol:<8} | {var:>+7.2f}% | {price:>10,.0f} FCFA")

else:
    print("\n⚠️  AUCUNE DONNÉE POUR AUJOURD'HUI")
    print("\n💡 OPTIONS:")
    print("   1. Collecte automatique:")
    print("      python collecter_brvm_horaire_auto.py")
    print("   2. Saisie manuelle:")
    print("      python mettre_a_jour_cours_brvm.py")
    print("   3. Import CSV:")
    print("      python collecter_csv_automatique.py")

client.close()
print("\n" + "="*70)
