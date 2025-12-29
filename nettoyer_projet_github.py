#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NETTOYAGE COMPLET DU PROJET POUR GITHUB
Supprime tous les fichiers obsolètes, temporaires et de test
"""
import os
import shutil
from pathlib import Path

# Dossier racine du projet
ROOT = Path("e:/DISQUE C/Desktop/Implementation plateforme")

# Catégories de fichiers à supprimer
PATTERNS_TO_DELETE = {
    # Fichiers de test
    'test_*.py': 'Tests',
    'verif_*.py': 'Vérifications',
    'check_*.py': 'Checks',
    'debug_*.py': 'Debug',
    'diagnostic_*.py': 'Diagnostics',
    'explore_*.py': 'Exploration',
    'analyze_*.py': 'Analyses',
    'analyser_*.py': 'Analyses FR',
    
    # Fichiers temporaires
    '*.log': 'Logs',
    '*.txt': 'Fichiers texte temporaires',
    'backup_*.json': 'Backups JSON',
    'backup_*.csv': 'Backups CSV',
    '*.html': 'HTML de scraping',
    'brvm_scrape_*.html': 'Scraping HTML',
    'brvm_selenium_*.html': 'Selenium HTML',
    
    # JSON temporaires
    '*_20251*.json': 'JSON datés',
    'rapport_*.json': 'Rapports JSON',
    'top5_*.json': 'Top5 JSON',
    'recommandations_*.json': 'Recommandations JSON',
    
    # CSV temporaires
    'cours_brvm_*.csv': 'CSV cours temporaires',
    'historique_brvm_*.csv': 'CSV historiques temporaires',
    'donnees_reelles_*.csv': 'CSV données temporaires',
    
    # Scripts de collecte obsolètes/doublons
    'collecter_brvm_*.py': 'Collecteurs BRVM multiples',
    'collecter_cours_*.py': 'Collecteurs cours',
    'collecter_simple_*.py': 'Collecteurs simples',
    'collecter_csv_*.py': 'Collecteurs CSV (garder automatique)',
    'collecter_quotidien_*.py': 'Collecteurs quotidiens (garder intelligent)',
    
    # Scripts d'affichage/debug
    'afficher_*.py': 'Scripts affichage',
    'lister_*.py': 'Scripts listing',
    'show_*.py': 'Scripts show',
    'voir_*.py': 'Scripts voir',
    
    # Scripts de mise à jour obsolètes
    'mettre_a_jour_*.py': 'Scripts MAJ',
    'corriger_*.py': 'Scripts correction',
    'purger_*.py': 'Scripts purge',
    'nettoyer_*.py': 'Scripts nettoyage',
    
    # Scripts d'import multiples
    'importer_*.py': 'Scripts import',
    'import_*.py': 'Scripts import',
    
    # Scripts de génération temporaires
    'generer_*.py': 'Scripts génération',
    'generate_*.py': 'Scripts generation EN',
    
    # Scripts divers obsolètes
    'saisie_*.py': 'Scripts saisie manuelle',
    'sauv_*.py': 'Scripts sauvegarde',
    'sauvegarder_*.py': 'Scripts sauvegarde',
    'comparer_*.py': 'Scripts comparaison',
    'completer_*.py': 'Scripts complément',
    
    # BAT files (Windows scripts)
    '*.bat': 'Scripts batch Windows',
    
    # Fichiers PDF de documentation
    '*.pdf': 'PDFs temporaires',
}

# Fichiers spécifiques à garder
KEEP_FILES = {
    # Core
    'manage.py',
    'requirements.txt',
    'Dockerfile',
    'docker-compose.yml',
    'nginx.conf',
    '.gitignore',
    '.dockerignore',
    '.env.example',
    'README.md',
    'LICENSE',
    'Makefile',
    
    # Scripts essentiels
    'collecter_quotidien_intelligent.py',  # Collecteur principal
    'collecter_csv_automatique.py',  # Import CSV
    'collecter_toutes_47_actions.py',  # Collecteur complet
    
    # Documentation principale
    'PROJECT_STRUCTURE.md',
    'PIPELINE_STRUCTURE.txt',
    'CHANGELOG.md',
    'DEPLOYMENT_GUIDE.md',
    'GUIDE_UTILISATION_COMPLET.md',
}

# Dossiers à nettoyer complètement
DIRS_TO_CLEAN = [
    'bulletins_brvm',
    'logs',
    'csv',
    'csv_brvm',
]

# Dossiers à garder intacts
KEEP_DIRS = [
    '.venv',
    '.git',
    'dashboard',
    'ingestion',
    'plateforme_centralisation',
    'users',
    'static',
    'media',
    'templates',
    'scripts/connectors',  # Connecteurs essentiels
    'airflow/dags',  # DAGs Airflow
    'docs',  # Documentation
    '.github',  # GitHub workflows
]

def should_delete_file(file_path):
    """Détermine si un fichier doit être supprimé"""
    file_name = file_path.name
    
    # Ne jamais supprimer les fichiers à garder
    if file_name in KEEP_FILES:
        return False
    
    # Ne jamais supprimer les fichiers dans certains dossiers
    for keep_dir in KEEP_DIRS:
        if keep_dir in str(file_path.relative_to(ROOT)).split(os.sep):
            return False
    
    # Vérifier les patterns
    for pattern in PATTERNS_TO_DELETE.keys():
        if file_path.match(pattern):
            return True
    
    return False

def clean_project():
    """Nettoie le projet"""
    print("="*80)
    print("NETTOYAGE DU PROJET POUR GITHUB")
    print("="*80)
    
    stats = {
        'files_deleted': 0,
        'dirs_deleted': 0,
        'space_freed': 0,
    }
    
    deleted_by_category = {}
    
    # 1. Supprimer les fichiers
    print("\n📁 SUPPRESSION DES FICHIERS...")
    for file_path in ROOT.rglob('*'):
        if file_path.is_file() and should_delete_file(file_path):
            try:
                size = file_path.stat().st_size
                category = "Autres"
                
                # Trouver la catégorie
                for pattern, cat in PATTERNS_TO_DELETE.items():
                    if file_path.match(pattern):
                        category = cat
                        break
                
                deleted_by_category[category] = deleted_by_category.get(category, 0) + 1
                
                file_path.unlink()
                stats['files_deleted'] += 1
                stats['space_freed'] += size
                
                if stats['files_deleted'] % 10 == 0:
                    print(f"   Supprimés: {stats['files_deleted']} fichiers...")
                    
            except Exception as e:
                print(f"   ⚠️  Erreur suppression {file_path.name}: {e}")
    
    # 2. Nettoyer les dossiers temporaires
    print("\n📂 NETTOYAGE DES DOSSIERS...")
    for dir_name in DIRS_TO_CLEAN:
        dir_path = ROOT / dir_name
        if dir_path.exists():
            try:
                # Compter fichiers avant
                file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
                
                # Supprimer tout le contenu mais garder le dossier
                for item in dir_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                
                print(f"   ✅ {dir_name}/: {file_count} fichiers supprimés")
                stats['files_deleted'] += file_count
                
            except Exception as e:
                print(f"   ⚠️  Erreur nettoyage {dir_name}: {e}")
    
    # 3. Supprimer les dossiers vides
    print("\n🗑️  SUPPRESSION DES DOSSIERS VIDES...")
    for dir_path in list(ROOT.rglob('*')):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            # Ne pas supprimer les dossiers à garder
            skip = False
            for keep_dir in KEEP_DIRS:
                if keep_dir in str(dir_path.relative_to(ROOT)).split(os.sep):
                    skip = True
                    break
            
            if not skip:
                try:
                    dir_path.rmdir()
                    stats['dirs_deleted'] += 1
                except:
                    pass
    
    # 4. Rapport final
    print("\n" + "="*80)
    print("RÉSULTAT DU NETTOYAGE")
    print("="*80)
    
    print(f"\n📊 Statistiques:")
    print(f"   • Fichiers supprimés: {stats['files_deleted']}")
    print(f"   • Dossiers supprimés: {stats['dirs_deleted']}")
    print(f"   • Espace libéré: {stats['space_freed'] / (1024*1024):.2f} MB")
    
    print(f"\n📋 Détails par catégorie:")
    for category, count in sorted(deleted_by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {category}: {count} fichiers")
    
    print("\n" + "="*80)
    print("✅ NETTOYAGE TERMINÉ")
    print("="*80)
    
    # 5. Fichiers essentiels conservés
    print("\n🔒 FICHIERS ESSENTIELS CONSERVÉS:")
    for file_name in sorted(KEEP_FILES):
        if (ROOT / file_name).exists():
            print(f"   ✓ {file_name}")
    
    print("\n💡 PROCHAINES ÉTAPES:")
    print("   1. Vérifier le .gitignore")
    print("   2. Tester que l'application fonctionne")
    print("   3. git add .")
    print("   4. git commit -m 'Nettoyage projet pour production'")
    print("   5. git push origin main")

if __name__ == '__main__':
    response = input("\n⚠️  ATTENTION: Cette opération va supprimer des centaines de fichiers.\nContinuer? (o/N): ")
    if response.lower() == 'o':
        clean_project()
    else:
        print("\n❌ Nettoyage annulé")
