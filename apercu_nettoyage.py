#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APERÇU DU NETTOYAGE - MODE SIMULATION
Affiche ce qui SERAIT supprimé sans rien supprimer
"""
import os
from pathlib import Path
from collections import defaultdict

ROOT = Path("e:/DISQUE C/Desktop/Implementation plateforme")

# Patterns à rechercher
PATTERNS = [
    'test_*.py', 'verif_*.py', 'check_*.py', 'debug_*.py',
    'diagnostic_*.py', 'explore_*.py', 'analyze_*.py', 'analyser_*.py',
    '*.log', 'backup_*.json', '*.html', '*_2025*.json',
    'afficher_*.py', 'lister_*.py', 'show_*.py', 'voir_*.py',
    '*.bat', 'collecter_brvm_*.py', 'mettre_a_jour_*.py',
]

KEEP_FILES = {
    'manage.py', 'requirements.txt', 'README.md', 'LICENSE',
    'collecter_quotidien_intelligent.py', 'collecter_csv_automatique.py',
    'collecter_toutes_47_actions.py', 'PROJECT_STRUCTURE.md',
}

KEEP_DIRS = [
    '.venv', '.git', 'dashboard', 'ingestion', 'plateforme_centralisation',
    'users', 'static', 'media', 'templates', 'scripts/connectors', 'airflow/dags',
]

def scan_project():
    """Scanner le projet en mode simulation"""
    by_category = defaultdict(list)
    total_size = 0
    
    for file_path in ROOT.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Vérifier si à garder
        if file_path.name in KEEP_FILES:
            continue
        
        # Vérifier dossiers à garder
        skip = False
        for keep_dir in KEEP_DIRS:
            if keep_dir in str(file_path.relative_to(ROOT)).split(os.sep):
                skip = True
                break
        if skip:
            continue
        
        # Vérifier patterns
        for pattern in PATTERNS:
            if file_path.match(pattern):
                category = pattern
                by_category[category].append(file_path.name)
                total_size += file_path.stat().st_size
                break
    
    # Afficher résumé
    print("="*80)
    print("APERÇU DU NETTOYAGE (MODE SIMULATION)")
    print("="*80)
    
    total_files = sum(len(files) for files in by_category.values())
    print(f"\n📊 TOTAL: {total_files} fichiers seraient supprimés")
    print(f"💾 ESPACE: {total_size / (1024*1024):.2f} MB seraient libérés")
    
    print(f"\n📋 DÉTAILS PAR CATÉGORIE:")
    for pattern, files in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n   {pattern}: {len(files)} fichiers")
        # Afficher premiers fichiers
        for file_name in sorted(files)[:5]:
            print(f"      - {file_name}")
        if len(files) > 5:
            print(f"      ... et {len(files)-5} autres")
    
    print("\n" + "="*80)
    print("⚠️  CECI EST UNE SIMULATION - Aucun fichier supprimé")
    print("="*80)
    
    print("\n💡 Pour effectuer le nettoyage réel:")
    print("   python nettoyer_projet_github.py")

if __name__ == '__main__':
    scan_project()
