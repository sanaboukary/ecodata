#!/usr/bin/env python3
"""
✅ VÉRIFICATION RAPIDE - SYSTÈME DOUBLE OBJECTIF

Vérifie que tous les fichiers sont présents et importables
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print("\n" + "="*80)
print("✅ VÉRIFICATION SYSTÈME DOUBLE OBJECTIF BRVM")
print("="*80 + "\n")

# Fichiers requis
FILES = {
    'Architecture': [
        'architecture_3_niveaux.py',
        'collector_raw_no_overwrite.py',
        'pipeline_daily.py',
        'pipeline_weekly.py'
    ],
    'Moteurs': [
        'top5_engine.py',
        'opportunity_engine.py',
        'autolearning_engine.py'
    ],
    'Dashboard & Notifications': [
        'dashboard_opportunities.py',
        'notifications_opportunites.py'
    ],
    'Orchestration': [
        'master_orchestrator.py'
    ],
    'Configuration & Tests': [
        'config_double_objectif.py',
        'test_opportunity_engine.py',
        'test_rapide.py'
    ],
    'Documentation': [
        'README_DOUBLE_OBJECTIF.md',
        'STRATEGIE_DOUBLE_OBJECTIF.md',
        'README_ARCHITECTURE_3_NIVEAUX.md'
    ]
}

total_files = 0
present_files = 0

for category, files in FILES.items():
    print(f"📁 {category}")
    for file in files:
        path = BASE_DIR / file
        total_files += 1
        if path.exists():
            size = path.stat().st_size
            present_files += 1
            print(f"   ✅ {file:<45} ({size:>8,} bytes)")
        else:
            print(f"   ❌ {file:<45} MANQUANT")
    print()

print("="*80)
print(f"RÉSULTAT : {present_files}/{total_files} fichiers présents ({present_files/total_files*100:.0f}%)")
print("="*80 + "\n")

if present_files == total_files:
    print("🎉 SYSTÈME COMPLET - Prêt à l'emploi !")
    print("\n📚 PROCHAINES ÉTAPES :")
    print("   1. Lire la documentation : README_DOUBLE_OBJECTIF.md")
    print("   2. Tester l'Opportunity Engine :")
    print("      python brvm_pipeline/opportunity_engine.py")
    print("   3. Lancer le workflow quotidien :")
    print("      python brvm_pipeline/master_orchestrator.py --daily-update")
else:
    print("⚠️  Certains fichiers manquent - Vérifier l'installation")

print()
