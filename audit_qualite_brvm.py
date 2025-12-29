#!/usr/bin/env python3
"""
🔍 AUDIT QUALITÉ DES DONNÉES BRVM
Identifie les données RÉELLES vs SIMULÉES/INCONNUES
"""
import os
import sys
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("\n" + "="*80)
print("🔍 AUDIT QUALITÉ DONNÉES BRVM")
print("="*80)
print()

client, db = get_mongo_db()

# Compter par qualité
total = db.curated_observations.count_documents({'source': 'BRVM'})

real_manual = db.curated_observations.count_documents({
    'source': 'BRVM',
    'data_quality': 'REAL_MANUAL'
})

real_scraper = db.curated_observations.count_documents({
    'source': 'BRVM',
    'data_quality': 'REAL_SCRAPER'
})

simulated = db.curated_observations.count_documents({
    'source': 'BRVM',
    'data_quality': 'SIMULATED'
})

unknown = db.curated_observations.count_documents({
    'source': 'BRVM',
    'data_quality': 'UNKNOWN'
})

autres = total - (real_manual + real_scraper + simulated + unknown)

print(f"📊 RÉPARTITION DES {total:,} OBSERVATIONS BRVM:")
print()
print(f"  ✅ REAL_MANUAL  : {real_manual:>6,} ({real_manual/total*100:>5.1f}%)")
print(f"  ✅ REAL_SCRAPER : {real_scraper:>6,} ({real_scraper/total*100:>5.1f}%)")
print(f"  🔴 SIMULATED    : {simulated:>6,} ({simulated/total*100:>5.1f}%)")
print(f"  ⚠️  UNKNOWN      : {unknown:>6,} ({unknown/total*100:>5.1f}%)")
print(f"  ❓ AUTRES       : {autres:>6,} ({autres/total*100:>5.1f}%)")
print()

total_real = real_manual + real_scraper
pct_real = (total_real / total * 100) if total > 0 else 0

print(f"{'='*80}")
print(f"TOTAL DONNÉES RÉELLES: {total_real:,} / {total:,} ({pct_real:.1f}%)")
print(f"{'='*80}")
print()

if pct_real < 100:
    print("🔴 PROBLÈME: Des données NON RÉELLES détectées!")
    print()
    print("📋 ACTIONS REQUISES:")
    print()
    
    if simulated > 0:
        print(f"  1. PURGER {simulated:,} observations SIMULÉES:")
        print(f"     → python purger_donnees_simulees.py")
        print()
    
    if unknown > 0:
        print(f"  2. VÉRIFIER {unknown:,} observations UNKNOWN:")
        print(f"     → python analyser_donnees_unknown.py")
        print()
    
    print("  3. COLLECTER données RÉELLES:")
    print("     → python scraper_selenium_brvm.py (scraping site)")
    print("     → python mettre_a_jour_cours_REELS_22dec.py (saisie manuelle)")
    print()
    
else:
    print("✅ TOUTES LES DONNÉES SONT RÉELLES (100%)")
    print()
    print("📋 PROCHAINES ÉTAPES:")
    print("  → python generer_top5_simple.py")
    print("  → python afficher_dashboard_hebdo.py")
    print()

# Échantillon de données simulées
if simulated > 0:
    print(f"{'='*80}")
    print("🔍 ÉCHANTILLON DONNÉES SIMULÉES:")
    print(f"{'='*80}")
    print()
    
    samples = list(db.curated_observations.find({
        'source': 'BRVM',
        'data_quality': 'SIMULATED'
    }).limit(10))
    
    for s in samples:
        print(f"  {s['key']:<12} | {s['ts']} | {s['value']:,.0f} FCFA")
    
    print()

client.close()

print("="*80)
print()
