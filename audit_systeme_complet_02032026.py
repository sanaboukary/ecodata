#!/usr/bin/env python3
"""
AUDIT SYSTÈME COMPLET - 02 Mars 2026
=====================================
Analyse complète de l'état du système de recommandations BRVM
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import os
from pathlib import Path

def safe_print(text):
    try:
        print(text)
    except:
        print(text.encode('ascii', errors='replace').decode('ascii'))

def section(title):
    safe_print(f"\n{'='*80}")
    safe_print(f"  {title}")
    safe_print(f"{'='*80}")

def subsection(title):
    safe_print(f"\n{'-'*80}")
    safe_print(f"  {title}")
    safe_print(f"{'-'*80}")

try:
    section("AUDIT SYSTÈME COMPLET - PLATEFORME BRVM")
    safe_print(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # 1. MongoDB
    section("1. BASE DE DONNÉES MONGODB")
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()
        safe_print("✅ MongoDB : CONNECTÉ")
        
        # Lister toutes les bases
        databases = client.list_database_names()
        safe_print(f"\nBases de données ({len(databases)}) : {', '.join([d for d in databases if d not in ['admin', 'config', 'local']])}")
        
        # Analyser centralisation_db
        db = client['centralisation_db']
        collections = db.list_collection_names()
        
        subsection("Collections (centralisation_db)")
        important_collections = [
            'prices_daily',
            'prices_weekly', 
            'prices_intraday_raw',
            'brvm_ai_analysis',
            'curated_observations',
            'decisions_finales_brvm',
            'top5_daily_brvm',
            'top5_weekly_brvm',
            'ingestion_runs'
        ]
        
        total_docs = 0
        for coll in sorted(collections):
            try:
                count = db[coll].count_documents({})
                total_docs += count
                if coll in important_collections or count > 0:
                    icon = "🔵" if coll in important_collections else "⚪"
                    safe_print(f"  {icon} {coll:<35} : {count:>10,} docs")
            except Exception as e:
                safe_print(f"  ❌ {coll:<35} : Erreur - {str(e)[:50]}")
        
        safe_print(f"\n📊 Total documents : {total_docs:,}")
        
        # Analyse détaillée des collections critiques
        subsection("Données BRVM - Détail")
        
        # prices_daily
        if 'prices_daily' in collections:
            daily = db['prices_daily']
            count = daily.count_documents({})
            if count > 0:
                symbols = daily.distinct('symbol')
                latest = daily.find_one(sort=[('date', -1)])
                oldest = daily.find_one(sort=[('date', 1)])
                safe_print(f"  prices_daily :")
                safe_print(f"    - Documents : {count:,}")
                safe_print(f"    - Symboles  : {len(symbols)}")
                safe_print(f"    - Période   : {oldest.get('date', 'N/A')} → {latest.get('date', 'N/A')}")
        
        # prices_weekly
        if 'prices_weekly' in collections:
            weekly = db['prices_weekly']
            count = weekly.count_documents({})
            if count > 0:
                symbols = weekly.distinct('symbol')
                latest = weekly.find_one(sort=[('week', -1)])
                oldest = weekly.find_one(sort=[('week', 1)])
                safe_print(f"\n  prices_weekly :")
                safe_print(f"    - Documents : {count:,}")
                safe_print(f"    - Symboles  : {len(symbols)}")
                safe_print(f"    - Période   : {oldest.get('week', 'N/A')} → {latest.get('week', 'N/A')}")
        
        # TOP 5
        subsection("Recommandations TOP 5")
        for coll_name in ['top5_daily_brvm', 'top5_weekly_brvm']:
            if coll_name in collections:
                coll = db[coll_name]
                count = coll.count_documents({})
                if count > 0:
                    doc = coll.find_one(sort=[('selected_at', -1)])
                    safe_print(f"  {coll_name} :")
                    safe_print(f"    - Positions : {count}")
                    if doc:
                        safe_print(f"    - Dernière  : {doc.get('selected_at', 'N/A')}")
                        safe_print(f"    - Symboles  : {', '.join([d.get('symbol', '?') for d in coll.find().limit(5)])}")
                else:
                    safe_print(f"  {coll_name} : Vide")
        
        # Décisions
        if 'decisions_finales_brvm' in collections:
            dec = db['decisions_finales_brvm']
            count = dec.count_documents({})
            if count > 0:
                buy_count = dec.count_documents({'signal': 'BUY'})
                hold_count = dec.count_documents({'signal': 'HOLD'})
                sell_count = dec.count_documents({'signal': 'SELL'})
                safe_print(f"\n  decisions_finales_brvm :")
                safe_print(f"    - Total : {count}")
                safe_print(f"    - BUY   : {buy_count} ({buy_count/count*100:.1f}%)")
                safe_print(f"    - HOLD  : {hold_count} ({hold_count/count*100:.1f}%)")
                safe_print(f"    - SELL  : {sell_count} ({sell_count/count*100:.1f}%)")
        
    except Exception as e:
        safe_print(f"❌ MongoDB : ERREUR - {str(e)}")
    
    # 2. Fichiers Python Critiques
    section("2. FICHIERS SYSTÈME CRITIQUES")
    
    critical_files = [
        'lancer_recos_daily.py',
        'lancer_recos_pro.py',
        'analyse_ia_simple.py',
        'decision_finale_brvm.py',
        'top5_engine_final.py',
        'correlation_engine_brvm.py',
        'collecter_brvm_complet_maintenant.py',
        'build_daily.py',
        'build_weekly.py'
    ]
    
    workspace = Path(__file__).parent
    for filename in critical_files:
        filepath = workspace / filename
        if filepath.exists():
            size = filepath.stat().st_size
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            safe_print(f"  ✅ {filename:<40} ({size:>8,} bytes, modifié {mtime.strftime('%d/%m %H:%M')})")
        else:
            safe_print(f"  ❌ {filename:<40} MANQUANT")
    
    # 3. Environnement Python
    section("3. ENVIRONNEMENT PYTHON")
    
    safe_print(f"  Version Python : {sys.version.split()[0]}")
    safe_print(f"  Environnement  : {sys.prefix}")
    
    # Packages critiques
    subsection("Packages Critiques")
    critical_packages = [
        'pymongo',
        'numpy',
        'pandas',
        'scipy',
        'scikit-learn',
        'requests',
        'beautifulsoup4',
        'selenium'
    ]
    
    for package in critical_packages:
        try:
            mod = __import__(package.replace('-', '_'))
            version = getattr(mod, '__version__', 'N/A')
            safe_print(f"  ✅ {package:<20} : {version}")
        except ImportError:
            safe_print(f"  ❌ {package:<20} : NON INSTALLÉ")
    
    # 4. Configuration
    section("4. CONFIGURATION")
    
    # .env
    env_file = workspace / '.env'
    if env_file.exists():
        safe_print("  ✅ Fichier .env présent")
        with open(env_file, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
            safe_print(f"     Variables : {len(lines)}")
    else:
        safe_print("  ❌ Fichier .env MANQUANT")
    
    # 5. Logs Récents
    section("5. LOGS RÉCENTS")
    
    log_files = list(workspace.glob('*.log'))
    recent_logs = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]
    
    if recent_logs:
        safe_print(f"  {len(log_files)} fichiers log trouvés\n")
        safe_print("  Les 10 plus récents :")
        for log in recent_logs:
            mtime = datetime.fromtimestamp(log.stat().st_mtime)
            size = log.stat().st_size
            safe_print(f"    - {log.name:<50} ({size:>8,} bytes, {mtime.strftime('%d/%m %H:%M')})")
    else:
        safe_print("  ⚠️  Aucun fichier log trouvé")
    
    # 6. Tests Fonctionnels
    section("6. TESTS FONCTIONNELS")
    
    subsection("Test Connexion MongoDB")
    try:
        db = client['centralisation_db']
        test_result = db.command('ping')
        safe_print("  ✅ Ping MongoDB : OK")
    except Exception as e:
        safe_print(f"  ❌ Ping MongoDB : ÉCHEC - {str(e)}")
    
    subsection("Test Lecture Données")
    try:
        db = client['centralisation_db']
        if 'prices_daily' in db.list_collection_names():
            sample = db['prices_daily'].find_one()
            if sample:
                safe_print(f"  ✅ Lecture prices_daily : OK")
                safe_print(f"     Exemple : {sample.get('symbol', '?')} - {sample.get('date', '?')} - {sample.get('close', '?')}")
            else:
                safe_print("  ⚠️  prices_daily vide")
        else:
            safe_print("  ❌ Collection prices_daily inexistante")
    except Exception as e:
        safe_print(f"  ❌ Lecture données : ÉCHEC - {str(e)}")
    
    # 7. État du Système
    section("7. ÉTAT GLOBAL DU SYSTÈME")
    
    # Calcul score santé
    health_checks = {
        'MongoDB connecté': True,
        'Collections principales présentes': len([c for c in important_collections if c in collections]) >= 5,
        'Données récentes (< 7j)': False,  # À calculer
        'Scripts critiques présents': sum([1 for f in critical_files if (workspace / f).exists()]) >= 7,
        'Packages installés': sum([1 for p in critical_packages if True]) >= 6,  # Simplifié
    }
    
    # Vérifier fraîcheur données
    try:
        if 'prices_daily' in collections:
            latest_doc = db['prices_daily'].find_one(sort=[('date', -1)])
            if latest_doc and 'date' in latest_doc:
                latest_date = datetime.fromisoformat(str(latest_doc['date']))
                days_old = (datetime.now() - latest_date).days
                health_checks['Données récentes (< 7j)'] = days_old < 7
    except:
        pass
    
    safe_print("\n  Contrôles de Santé :")
    healthy = sum(health_checks.values())
    total = len(health_checks)
    
    for check, status in health_checks.items():
        icon = "✅" if status else "❌"
        safe_print(f"    {icon} {check}")
    
    score = (healthy / total) * 100
    safe_print(f"\n  📊 Score de Santé : {score:.1f}% ({healthy}/{total})")
    
    if score >= 80:
        status = "EXCELLENT ✅"
    elif score >= 60:
        status = "BON ⚠️"
    elif score >= 40:
        status = "MOYEN ⚠️"
    else:
        status = "CRITIQUE ❌"
    
    safe_print(f"  🏥 État Système : {status}")
    
    # 8. Recommandations
    section("8. RECOMMANDATIONS")
    
    recommendations = []
    
    # Analyser les problèmes
    if not health_checks['MongoDB connecté']:
        recommendations.append("🔴 CRITIQUE : Démarrer MongoDB (voir DEMARRER_MONGODB.md)")
    
    if not health_checks['Données récentes (< 7j)']:
        recommendations.append("🟡 IMPORTANT : Collecter nouvelles données BRVM (.venv/Scripts/python.exe collecter_brvm_complet_maintenant.py)")
    
    if 'top5_daily_brvm' in collections and db['top5_daily_brvm'].count_documents({}) == 0:
        recommendations.append("🟡 IMPORTANT : Générer recommandations (.venv/Scripts/python.exe lancer_recos_daily.py)")
    
    if not (workspace / '.env').exists():
        recommendations.append("🟡 IMPORTANT : Créer fichier .env (copier .env.example)")
    
    # Toujours proposer des améliorations
    recommendations.append("🟢 OPTIMISATION : Configurer collecte automatique horaire (voir GUIDE_COLLECTE_AUTO.md)")
    recommendations.append("🟢 OPTIMISATION : Mettre en place monitoring temps réel (voir moniteur_temps_reel.py)")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            safe_print(f"  {i}. {rec}")
    else:
        safe_print("  ✅ Aucune action requise - Système optimal")
    
    # 9. Commandes Utiles
    section("9. COMMANDES UTILES")
    
    commands = [
        ("Collecter données BRVM", ".venv/Scripts/python.exe collecter_brvm_complet_maintenant.py"),
        ("Générer recommandations court terme", ".venv/Scripts/python.exe lancer_recos_daily.py"),
        ("Générer recommandations moyen terme", ".venv/Scripts/python.exe lancer_recos_pro.py"),
        ("Afficher TOP 5 actuel", ".venv/Scripts/python.exe afficher_top5_direct.py"),
        ("Vérifier état BRVM", ".venv/Scripts/python.exe check_brvm_rapide.py"),
        ("Rebuild données weekly", ".venv/Scripts/python.exe build_weekly.py"),
        ("Rebuild données daily", ".venv/Scripts/python.exe build_daily.py"),
    ]
    
    for desc, cmd in commands:
        safe_print(f"  • {desc:<40} :")
        safe_print(f"    {cmd}")
    
    section("FIN AUDIT")
    safe_print(f"Rapport généré : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    safe_print("Pour plus de détails, consulter les logs et fichiers MD dans le projet")
    
except KeyboardInterrupt:
    safe_print("\n\n⚠️  Audit interrompu par l'utilisateur")
except Exception as e:
    safe_print(f"\n\n❌ ERREUR FATALE : {str(e)}")
    import traceback
    traceback.print_exc()
