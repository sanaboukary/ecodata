#!/usr/bin/env python3
"""
🎯 MASTER ORCHESTRATOR - PIPELINE COMPLET BRVM

Exécution ordonnée de toute la chaîne :
1. Vérification architecture
2. Collecte RAW (optionnel)
3. Agrégation DAILY
4. Agrégation WEEKLY
5. Calcul indicateurs
6. Génération TOP5
7. Auto-learning (si données RichBourse disponibles)

USAGE :
  python master_orchestrator.py --full             # Pipeline complet
  python master_orchestrator.py --collect-only     # Collecte uniquement
  python master_orchestrator.py --top5-only        # TOP5 uniquement
  python master_orchestrator.py --rebuild          # Reconstruction totale
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPTS_DIR = BASE_DIR / "brvm_pipeline"

SCRIPTS = {
    'architecture': SCRIPTS_DIR / "architecture_3_niveaux.py",
    'collector': SCRIPTS_DIR / "collector_raw_no_overwrite.py",
    'daily': SCRIPTS_DIR / "pipeline_daily.py",
    'weekly': SCRIPTS_DIR / "pipeline_weekly.py",
    'top5': SCRIPTS_DIR / "top5_engine.py",
    'learning': SCRIPTS_DIR / "autolearning_engine.py",
    'opportunity': SCRIPTS_DIR / "opportunity_engine.py",
    'dashboard_opp': SCRIPTS_DIR / "dashboard_opportunities.py",
    'notifications': SCRIPTS_DIR / "notifications_opportunites.py"
}

PYTHON = sys.executable

# ============================================================================
# EXÉCUTION DES SCRIPTS
# ============================================================================

def run_script(script_path, *args):
    """Exécuter un script Python avec arguments"""
    cmd = [PYTHON, str(script_path)] + list(args)
    
    print(f"\n🚀 Exécution : {script_path.name} {' '.join(args)}")
    print("-" * 80)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"❌ Erreur dans {script_path.name}")
        return False
    
    print(f"✅ {script_path.name} terminé")
    return True

# ============================================================================
# PIPELINES
# ============================================================================

def pipeline_collect():
    """Pipeline collecte RAW"""
    print("\n" + "="*80)
    print("🔴 ÉTAPE 1 - COLLECTE RAW")
    print("="*80)
    
    return run_script(SCRIPTS['collector'])

def pipeline_daily(date=None, rebuild=False):
    """Pipeline DAILY"""
    print("\n" + "="*80)
    print("🟢 ÉTAPE 2 - AGRÉGATION DAILY")
    print("="*80)
    
    args = []
    if rebuild:
        args.append('--rebuild')
    elif date:
        args.extend(['--date', date])
    
    return run_script(SCRIPTS['daily'], *args)

def pipeline_weekly(week=None, rebuild=False):
    """Pipeline WEEKLY"""
    print("\n" + "="*80)
    print("🔵 ÉTAPE 3 - AGRÉGATION WEEKLY + INDICATEURS")
    print("="*80)
    
    args = []
    if rebuild:
        args.append('--rebuild')
    elif week:
        args.extend(['--week', week])
    
    return run_script(SCRIPTS['weekly'], *args)

def pipeline_top5(week=None):
    """Génération TOP5"""
    print("\n" + "="*80)
    print("⭐ ÉTAPE 4 - GÉNÉRATION TOP5")
    print("="*80)
    
    args = []
    if week:
        args.extend(['--week', week])
    
    return run_script(SCRIPTS['top5'], *args)

def pipeline_learning():
    """Auto-learning"""
    print("\n" + "="*80)
    print("🧠 ÉTAPE 5 - AUTO-LEARNING")
    print("="*80)
    
    # Analyser performance
    success = run_script(SCRIPTS['learning'], '--analyze')
    
    if success:
        # Optionnel : ajuster poids si assez de données
        run_script(SCRIPTS['learning'], '--history')
    
    return success

def pipeline_opportunity(date=None, level='OBSERVATION'):
    """Scan opportunités"""
    print("\n" + "="*80)
    print("🔴 OPPORTUNITY ENGINE - DÉTECTION PRÉCOCE")
    print("="*80)
    
    args = []
    if date:
        args.extend(['--date', date])
    
    args.extend(['--level', level])
    
    return run_script(SCRIPTS['opportunity'], *args)

def pipeline_opportunity_dashboard():
    """Dashboard opportunités"""
    print("\n" + "="*80)
    print("📊 DASHBOARD OPPORTUNITÉS")
    print("="*80)
    
    # Opportunités du jour + conversion
    return run_script(SCRIPTS['dashboard_opp'], '--today', '--conversion')

# ============================================================================
# WORKFLOWS
# ============================================================================

def workflow_full(collect=True, rebuild=False):
    """Workflow complet"""
    print("\n" + "="*100)
    print(" " * 35 + "🎯 PIPELINE COMPLET BRVM")
    print("="*100)
    print(f"Démarré : {datetime.now()}")
    print("="*100 + "\n")
    
    # 0. Architecture
    run_script(SCRIPTS['architecture'])
    
    # 1. Collecte (optionnel)
    if collect:
        if not pipeline_collect():
            print("\n⚠️  Collecte échouée, mais on continue")
    
    # 2. DAILY
    if not pipeline_daily(rebuild=rebuild):
        print("\n❌ DAILY échoué, arrêt")
        return False
    
    # 3. WEEKLY
    if not pipeline_weekly(rebuild=rebuild):
        print("\n❌ WEEKLY échoué, arrêt")
        return False
    
    # 4. TOP5
    if not pipeline_top5():
        print("\n❌ TOP5 échoué, arrêt")
        return False
    
    # 🔑 CORRECTION ANTI-CASSURE : Auto-learning retiré du pipeline
    # → Utiliser workflow_calibration() manuellement
    
    print("\n" + "="*100)
    print("✅ PIPELINE COMPLET TERMINÉ")
    print(f"Terminé : {datetime.now()}")
    print("="*100 + "\n")
    
    return True

def workflow_daily_update():
    """
    Workflow quotidien (à exécuter à 17h après clôture BRVM)
    
    1. Agrégation DAILY
    2. Scan OPPORTUNITÉS (détection précoce)
    3. NOTIFICATIONS si opportunités FORTES
    4. Si lundi : WEEKLY + TOP5
    """
    print("\n🕐 MISE À JOUR QUOTIDIENNE")
    
    # Agréger hier (données complètes)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if not pipeline_daily(date=yesterday):
        return False
    
    # NOUVEAU : Scan opportunités (détection précoce J+1 à J+7)
    print("\n🔴 Scan opportunités...")
    pipeline_opportunity(date=yesterday, level='OBSERVATION')
    
    # NOUVEAU : Notifications si opportunités FORTES
    print("\n📢 Vérification notifications...")
    run_script(SCRIPTS['notifications'], '--date', yesterday)
    
    # Si c'est lundi, calculer semaine précédente
    if datetime.now().weekday() == 0:  # Lundi
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-W%V")
        pipeline_weekly(week=last_week)
        pipeline_top5(week=last_week)
    
    return True

def workflow_weekly_update():
    """
    Workflow hebdomadaire (lundi matin)
    Génère le TOP5 de la nouvelle semaine
    
    🔑 CORRECTION ANTI-CASSURE : Auto-learning retiré
    → Utiliser workflow_calibration() manuellement (1x/mois max)
    """
    print("\n📅 MISE À JOUR HEBDOMADAIRE (LUNDI)")
    
    # Semaine précédente (complète)
    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-W%V")
    
    pipeline_weekly(week=last_week)
    pipeline_top5(week=last_week)
    
    # 🔑 PAS de pipeline_learning() ici (hors pipeline)
    
    return True

def workflow_calibration(weeks=8, dry_run=True, apply=False):
    """
    🧠 CALIBRATION OFFLINE (AUTO-LEARNING)
    
    ⚠️  CORRECTION ANTI-CASSURE (EXPERT BRVM) :
    - Exécution MANUELLE uniquement (jamais automatique)
    - Minimum 8 semaines de données
    - Dry-run par défaut (affiche sans appliquer)
    - Confirmation explicite requise pour appliquer
    
    Règle d'or : Pipeline = exécution / Auto-learning = calibration OFFLINE
    
    Args:
        weeks: Nombre de semaines à analyser (min 8)
        dry_run: Si True, affiche sans appliquer
        apply: Si True, applique après confirmation
    """
    print("\n" + "="*80)
    print("🧠 CALIBRATION OFFLINE (AUTO-LEARNING)")
    print("⚠️  EXÉCUTION MANUELLE UNIQUEMENT - JAMAIS AUTOMATIQUE")
    print("="*80)
    print(f"Semaines à analyser : {weeks}")
    print(f"Mode : {'DRY-RUN (affichage)' if dry_run else 'APPLICATION'}")
    print("="*80 + "\n")
    
    if weeks < 8:
        print("❌ ERREUR : Minimum 8 semaines requis")
        print("   Vous avez besoin de plus d'historique pour calibrer")
        return False
    
    # 1. Analyser performances
    print("📊 Analyse performances TOP5...")
    if not run_script(SCRIPTS['learning'], '--analyze', f'--weeks={weeks}'):
        print("❌ Analyse échouée")
        return False
    
    # 2. Dry-run (affichage)
    if dry_run and not apply:
        print("\n" + "="*80)
        print("📋 AJUSTEMENTS PROPOSÉS (DRY-RUN)")
        print("="*80)
        print("✅ Analyse terminée sans modification")
        print("\n💡 Pour appliquer :")
        print("   python master_orchestrator.py --calibration --apply")
        print("="*80)
        return True
    
    # 3. Application (avec confirmation)
    if apply:
        print("\n" + "="*80)
        print("⚠️  CONFIRMATION REQUISE")
        print("="*80)
        print("Vous allez MODIFIER les poids du TOP5 Engine.")
        print("Ceci affectera les prochaines recommandations.")
        print("="*80)
        
        response = input("\nTaper 'YES' en majuscules pour confirmer : ")
        
        if response != "YES":
            print("\n❌ Calibration annulée (sécurité)")
            return False
        
        print("\n🔧 Application ajustements poids...")
        if not run_script(SCRIPTS['learning'], '--adjust', f'--weeks={weeks}'):
            print("❌ Ajustement échoué")
            return False
        
        print("\n" + "="*80)
        print("✅ POIDS AJUSTÉS AVEC SUCCÈS")
        print("="*80)
        print("⚠️  REDÉMARRER le pipeline pour appliquer les nouveaux poids")
        print("   python master_orchestrator.py --weekly-update")
        print("="*80)
        
        return True

def workflow_rebuild_all():
    """Reconstruction complète depuis RAW"""
    print("\n🔄 RECONSTRUCTION TOTALE")
    
    return workflow_full(collect=False, rebuild=True)

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Master Orchestrator - Pipeline BRVM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python master_orchestrator.py --full                 # Pipeline complet
  python master_orchestrator.py --full --no-collect    # Sans collecte
  python master_orchestrator.py --rebuild              # Reconstruction totale
  python master_orchestrator.py --daily-update         # Mise à jour quotidienne
  python master_orchestrator.py --weekly-update        # Mise à jour hebdo
  python master_orchestrator.py --top5-only            # TOP5 uniquement
        """
    )
    
    parser.add_argument('--full', action='store_true', help='Pipeline complet')
    parser.add_argument('--no-collect', action='store_true', help='Skip la collecte')
    parser.add_argument('--rebuild', action='store_true', help='Reconstruction totale')
    parser.add_argument('--daily-update', action='store_true', help='Mise à jour quotidienne')
    parser.add_argument('--weekly-update', action='store_true', help='Mise à jour hebdo')
    parser.add_argument('--top5-only', action='store_true', help='TOP5 uniquement')
    parser.add_argument('--collect-only', action='store_true', help='Collecte uniquement')
    parser.add_argument('--opportunity-scan', action='store_true', help='Scan opportunités uniquement')
    parser.add_argument('--opportunity-dashboard', action='store_true', help='Dashboard opportunités')
    parser.add_argument('--calibration', action='store_true', help='Calibration AUTO-LEARNING (manuel)')
    parser.add_argument('--weeks', type=int, default=8, help='Nombre semaines pour calibration')
    parser.add_argument('--apply', action='store_true', help='Appliquer calibration (+ confirmation)')
    
    args = parser.parse_args()
    
    if args.full:
        workflow_full(collect=not args.no_collect, rebuild=False)
    
    elif args.rebuild:
        workflow_rebuild_all()
    
    elif args.daily_update:
        workflow_daily_update()
    
    elif args.weekly_update:
        workflow_weekly_update()
    
    elif args.top5_only:
        pipeline_top5()
    
    elif args.collect_only:
        pipeline_collect()
    
    elif args.opportunity_scan:
        pipeline_opportunity()
    
    elif args.opportunity_dashboard:
        pipeline_opportunity_dashboard()
    
    elif args.calibration:
        # 🔑 CORRECTION ANTI-CASSURE : Auto-learning MANUEL uniquement
        dry_run = not args.apply
        workflow_calibration(weeks=args.weeks, dry_run=dry_run, apply=args.apply)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
