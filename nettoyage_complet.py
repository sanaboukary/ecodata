#!/usr/bin/env python3
"""
Nettoyage complet du projet pour GitHub
Supprime tous les fichiers temporaires, tests, debug et obsolètes
"""

import os
import glob
from pathlib import Path

# Répertoire du projet
PROJECT_ROOT = Path(__file__).parent

# Fichiers ESSENTIELS à préserver absolument
PRESERVE_FILES = {
    'manage.py',
    'requirements.txt',
    'Dockerfile',
    'docker-compose.yml',
    '.env',
    '.env.example',
    '.gitignore',
    'Makefile',
    
    # Scripts de collecte ACTIFS (production)
    'collecter_quotidien_intelligent.py',
    'collecter_toutes_47_actions.py',
    'collecter_brvm_selenium_robuste.py',
    'mettre_a_jour_cours_brvm.py',
    'collecter_csv_automatique.py',
    
    # Scripts de monitoring ESSENTIELS
    'show_complete_data.py',
    'show_ingestion_history.py',
    'verifier_connexion_db.py',
    
    # Scripts de nettoyage (garder pour référence)
    'nettoyer_projet_github.py',
    'apercu_nettoyage.py',
    'nettoyage_complet.py',
    'GUIDE_NETTOYAGE_GITHUB.md',
}

# Dossiers ESSENTIELS à préserver
PRESERVE_DIRS = {
    'dashboard',
    'ingestion',
    'users',
    'plateforme_centralisation',
    'scripts',
    'airflow',
    '.venv',
    '.git',
    'staticfiles',
    'media',
}

def should_delete(filepath):
    """Détermine si un fichier doit être supprimé"""
    filename = os.path.basename(filepath)
    
    # Préserver les fichiers essentiels
    if filename in PRESERVE_FILES:
        return False
    
    # Préserver les dossiers essentiels
    for preserve_dir in PRESERVE_DIRS:
        if filepath.startswith(str(PROJECT_ROOT / preserve_dir)):
            return False
    
    # Préserver README et documentation Markdown
    if filename in ['README.md', 'PROJECT_STRUCTURE.md', 'AIRFLOW_SETUP.md', 'CHANGELOG.md']:
        return False
    
    # ===== FICHIERS À SUPPRIMER =====
    
    # 1. Fichiers de test
    if any(filename.startswith(prefix) for prefix in ['test_', 'check_', 'verif_', 'debug_', 'analyze_']):
        return True
    
    # 2. Scripts d'affichage/debug
    if any(filename.startswith(prefix) for prefix in ['afficher_', 'lister_', 'show_', 'display_']):
        # Exceptions : scripts essentiels déjà dans PRESERVE_FILES
        if filename not in PRESERVE_FILES:
            return True
    
    # 3. Scripts obsolètes de collecte (sauf ceux dans PRESERVE_FILES)
    if filename.startswith('collecter_') and filename not in PRESERVE_FILES:
        return True
    
    # 4. Scripts d'analyse
    if filename.startswith(('analyser_', 'analyse_', 'analyzer_')):
        return True
    
    # 5. Scripts de migration/purge/backup
    if any(word in filename for word in ['purge', 'backup', 'migration', 'cleanup']):
        if filename not in PRESERVE_FILES:
            return True
    
    # 6. Fichiers BAT Windows
    if filename.endswith('.bat'):
        return True
    
    # 7. Fichiers LOG
    if filename.endswith('.log'):
        return True
    
    # 8. Fichiers HTML de debug
    if filename.endswith('.html') and any(word in filename for word in ['brvm_', 'scrape', 'debug', 'test']):
        return True
    
    # 9. Fichiers JSON temporaires/datés
    if filename.endswith('.json'):
        # Garder seulement les JSON de config dans le root
        if any(word in filename for word in ['backup', '_202', '2024', '2025', 'temp']):
            return True
    
    # 10. Fichiers CSV temporaires
    if filename.endswith('.csv'):
        if any(word in filename for word in ['test', 'debug', 'temp', 'backup', '_202']):
            return True
    
    # 11. Anciens fichiers TXT
    if filename.endswith('.txt') and filename not in ['requirements.txt']:
        return True
    
    # 12. Fichiers Python de saisie manuelle obsolètes
    if filename.startswith('saisir_'):
        return True
    
    # 13. Scripts d'activation/désactivation temporaires
    if filename.startswith(('activer_', 'desactiver_')):
        return True
    
    # 14. Scripts de vérification
    if filename.startswith('verifier_') and filename not in PRESERVE_FILES:
        return True
    
    # 15. Scripts d'import temporaires
    if filename.startswith(('importer_', 'import_')):
        return True
    
    # 16. Scripts de parsing temporaires
    if filename.startswith('parser_'):
        return True
    
    # 17. Fichiers PID
    if filename.endswith('_pids.txt'):
        return True
    
    return False

def main():
    """Exécute le nettoyage complet"""
    
    print("🧹 NETTOYAGE COMPLET DU PROJET")
    print("=" * 80)
    
    # Collecter tous les fichiers à la racine
    all_files = [f for f in PROJECT_ROOT.iterdir() if f.is_file()]
    
    # Filtrer les fichiers à supprimer
    files_to_delete = [f for f in all_files if should_delete(str(f))]
    
    # Grouper par catégorie pour affichage
    categories = {
        'Tests': [],
        'Affichage/Debug': [],
        'Collecteurs obsolètes': [],
        'Analyses': [],
        'BAT Windows': [],
        'Logs': [],
        'HTML debug': [],
        'JSON temporaires': [],
        'CSV temporaires': [],
        'TXT anciens': [],
        'Autres': [],
    }
    
    for f in files_to_delete:
        name = f.name
        if name.startswith(('test_', 'check_', 'verif_', 'debug_')):
            categories['Tests'].append(f)
        elif name.startswith(('afficher_', 'lister_', 'show_', 'display_')):
            categories['Affichage/Debug'].append(f)
        elif name.startswith('collecter_'):
            categories['Collecteurs obsolètes'].append(f)
        elif name.startswith(('analyser_', 'analyse_', 'analyzer_')):
            categories['Analyses'].append(f)
        elif name.endswith('.bat'):
            categories['BAT Windows'].append(f)
        elif name.endswith('.log'):
            categories['Logs'].append(f)
        elif name.endswith('.html'):
            categories['HTML debug'].append(f)
        elif name.endswith('.json'):
            categories['JSON temporaires'].append(f)
        elif name.endswith('.csv'):
            categories['CSV temporaires'].append(f)
        elif name.endswith('.txt'):
            categories['TXT anciens'].append(f)
        else:
            categories['Autres'].append(f)
    
    # Afficher le résumé
    print(f"\n📊 RÉSUMÉ DES SUPPRESSIONS")
    print("-" * 80)
    total = 0
    for category, files in categories.items():
        if files:
            print(f"🗑️  {category}: {len(files)} fichiers")
            total += len(files)
    
    print(f"\n📦 TOTAL: {total} fichiers à supprimer")
    print("=" * 80)
    
    # Confirmation
    print("\n⚠️  ATTENTION: Cette opération est IRRÉVERSIBLE !")
    response = input("Continuer avec la suppression ? (oui/non): ").lower().strip()
    
    if response != 'oui':
        print("❌ Nettoyage annulé")
        return
    
    # Suppression
    print("\n🗑️  SUPPRESSION EN COURS...")
    deleted_count = 0
    errors = []
    
    for f in files_to_delete:
        try:
            f.unlink()
            deleted_count += 1
            print(f"  ✓ {f.name}")
        except Exception as e:
            errors.append((f.name, str(e)))
            print(f"  ✗ {f.name}: {e}")
    
    # Résultat final
    print("\n" + "=" * 80)
    print(f"✅ NETTOYAGE TERMINÉ")
    print(f"   • Fichiers supprimés: {deleted_count}/{total}")
    
    if errors:
        print(f"   • Erreurs: {len(errors)}")
        for name, err in errors:
            print(f"     - {name}: {err}")
    
    # Afficher ce qui reste
    remaining = [f.name for f in PROJECT_ROOT.iterdir() if f.is_file()]
    print(f"\n📁 Fichiers restants à la racine: {len(remaining)}")
    
    # Fichiers essentiels préservés
    preserved = [f for f in remaining if f in PRESERVE_FILES]
    print(f"   • Fichiers essentiels préservés: {len(preserved)}")
    
    print("\n🎯 Projet prêt pour GitHub !")
    print("=" * 80)

if __name__ == '__main__':
    main()
