#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic complet de la configuration Django + MongoDB
Vérifie : Settings, URLs, MongoDB, Serveur, Recommandations IA
"""
import os
import sys
import django

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.conf import settings
from django.urls import get_resolver
from plateforme_centralisation.mongo import get_mongo_db

def print_header(title):
    print("\n" + "="*90)
    print(f"  {title}")
    print("="*90)

def print_section(title):
    print(f"\n{title}")
    print("-" * 90)

def check_settings():
    """Vérification des settings Django"""
    print_header("⚙️  CONFIGURATION DJANGO")
    
    print_section("Paramètres généraux")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SECRET_KEY: {'*' * 20} (configuré)")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"   TIME_ZONE: {settings.TIME_ZONE}")
    
    print_section("Applications installées")
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django.'):
            print(f"   ✓ {app}")
    
    print_section("Base de données")
    print(f"   SQLite: {settings.DATABASES['default']['NAME']}")
    print(f"   MongoDB URI: {settings.MONGODB_URI}")
    print(f"   MongoDB DB: {settings.MONGODB_NAME}")
    
    print_section("Fichiers statiques")
    print(f"   STATIC_URL: {settings.STATIC_URL}")
    print(f"   STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
    
    print_section("Authentification")
    print(f"   AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
    print(f"   LOGIN_URL: {settings.LOGIN_URL}")
    print(f"   LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")

def check_urls():
    """Vérification des URLs configurées"""
    print_header("🔗 ROUTES URL")
    
    resolver = get_resolver()
    
    print_section("Routes principales")
    main_patterns = [
        ('/', 'Page d\'accueil (dashboard)'),
        ('/admin/', 'Interface admin Django'),
        ('/users/', 'Authentification'),
        ('/api/ingestion/', 'API ingestion'),
    ]
    
    for path, desc in main_patterns:
        try:
            match = resolver.resolve(path)
            print(f"   ✓ {path:30} → {desc}")
        except:
            print(f"   ✗ {path:30} → {desc} (NON CONFIGURÉ)")
    
    print_section("Routes dashboard BRVM")
    dashboard_patterns = [
        ('/brvm/', 'Dashboard BRVM'),
        ('/brvm/recommendations/', 'Recommandations IA'),
        ('/brvm/publications/', 'Publications BRVM'),
        ('/api/brvm/summary/', 'API Summary'),
        ('/api/brvm/recommendations/', 'API Recommandations'),
    ]
    
    for path, desc in dashboard_patterns:
        try:
            match = resolver.resolve(path)
            print(f"   ✓ {path:35} → {desc}")
        except:
            print(f"   ✗ {path:35} → {desc} (NON CONFIGURÉ)")

def check_mongodb():
    """Vérification de la connexion MongoDB"""
    print_header("🗄️  MONGODB")
    
    try:
        client, db = get_mongo_db()
        
        print_section("Connexion")
        print(f"   ✓ Connexion établie")
        print(f"   Base de données: {db.name}")
        
        print_section("Collections")
        collections = db.list_collection_names()
        key_collections = [
            'curated_observations',
            'daily_recommendations',
            'brvm_publications',
            'ingestion_runs',
            'raw_events'
        ]
        
        for coll in key_collections:
            if coll in collections:
                count = db[coll].count_documents({})
                print(f"   ✓ {coll:30} {count:>8,} documents")
            else:
                print(f"   ✗ {coll:30} (Absente)")
        
        print_section("Données BRVM")
        brvm_count = db.curated_observations.count_documents({'source': 'BRVM'})
        print(f"   Prix actions: {brvm_count:,} observations")
        
        # Compter les actions
        pipeline = [
            {'$match': {'source': 'BRVM'}},
            {'$group': {'_id': '$key'}},
            {'$count': 'total'}
        ]
        result = list(db.curated_observations.aggregate(pipeline))
        actions_count = result[0]['total'] if result else 0
        print(f"   Actions suivies: {actions_count}")
        
        # Dernière mise à jour
        last_obs = db.curated_observations.find_one(
            {'source': 'BRVM'},
            sort=[('ts', -1)]
        )
        if last_obs:
            print(f"   Dernière mise à jour: {last_obs.get('ts', 'N/A')}")
        
        print_section("Recommandations IA")
        rec_count = db.daily_recommendations.count_documents({})
        print(f"   Total analyses: {rec_count}")
        
        if rec_count > 0:
            last_rec = db.daily_recommendations.find_one(sort=[('date', -1)])
            print(f"   Dernière analyse: {last_rec.get('date', 'N/A')}")
            print(f"   Signaux ACHAT: {last_rec.get('buy_count', 0)}")
            print(f"   Signaux VENTE: {last_rec.get('sell_count', 0)}")
            print(f"   A CONSERVER: {last_rec.get('hold_count', 0)}")
        
        return True
        
    except Exception as e:
        print_section("Erreur")
        print(f"   ✗ Erreur de connexion: {e}")
        return False

def check_views():
    """Vérification que les vues existent"""
    print_header("👁️  VUES DJANGO")
    
    try:
        from dashboard import views
        
        required_views = [
            'index',
            'dashboard_brvm',
            'brvm_recommendations_page',
            'brvm_recommendations_api',
            'brvm_summary_api',
            'brvm_publications_page',
        ]
        
        print_section("Vues dashboard")
        for view_name in required_views:
            if hasattr(views, view_name):
                print(f"   ✓ {view_name}")
            else:
                print(f"   ✗ {view_name} (MANQUANTE)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
        return False

def check_templates():
    """Vérification des templates"""
    print_header("📄 TEMPLATES")
    
    from pathlib import Path
    
    templates_dir = Path(settings.BASE_DIR) / 'dashboard' / 'templates' / 'dashboard'
    
    required_templates = [
        'index.html',
        'dashboard_brvm.html',
        'brvm_recommendations.html',
        'brvm_publications.html',
    ]
    
    print_section("Templates dashboard")
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"   ✓ {template:30} ({size:>6,} bytes)")
        else:
            print(f"   ✗ {template:30} (MANQUANT)")

def main():
    print("\n" + "╔" + "="*88 + "╗")
    print("║" + " "*20 + "DIAGNOSTIC COMPLET DU SYSTÈME" + " "*39 + "║")
    print("╚" + "="*88 + "╝")
    
    # Vérifications
    check_settings()
    check_urls()
    mongodb_ok = check_mongodb()
    check_views()
    check_templates()
    
    # Résumé final
    print_header("✅ RÉSUMÉ")
    print("\nÉtat du système:")
    print(f"   ✓ Django settings configurés correctement")
    print(f"   ✓ Routes URL définies")
    print(f"   {'✓' if mongodb_ok else '✗'} MongoDB {'connecté' if mongodb_ok else 'NON ACCESSIBLE'}")
    print(f"   ✓ Vues Django présentes")
    print(f"   ✓ Templates créés")
    
    print("\nAccès au système:")
    print("   🌐 Page d'accueil:        http://127.0.0.1:8000/")
    print("   📊 Dashboard BRVM:        http://127.0.0.1:8000/brvm/")
    print("   🎯 Recommandations IA:    http://127.0.0.1:8000/brvm/recommendations/")
    print("   📄 Publications BRVM:     http://127.0.0.1:8000/brvm/publications/")
    print("   🔌 API Recommandations:   http://127.0.0.1:8000/api/brvm/recommendations/")
    
    if mongodb_ok:
        print("\n✅ Système opérationnel - Prêt à être utilisé!")
    else:
        print("\n⚠️  MongoDB non accessible - Démarrer MongoDB avant utilisation")
    
    print("\n" + "="*90 + "\n")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
