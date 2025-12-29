"""
SCRIPT COMPLET - Configuration automatique de tous les acteurs
Exécute toutes les étapes en une seule commande.

Usage: python setup_complete_actors.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Role, Permission, RolePermission

User = get_user_model()

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_section(text):
    print(f"\n{text}")
    print("-" * 80)

def create_permissions():
    print_header("ÉTAPE 1/4 : CRÉATION DES 31 PERMISSIONS")
    
    permissions_data = [
        # Data Access (7)
        {"code": "view_all_data", "name": "Consulter toutes les données", "category": "data_access", "description": "Accès en lecture à toutes les sources"},
        {"code": "view_brvm", "name": "Consulter données BRVM", "category": "data_access", "description": "Accès BRVM uniquement"},
        {"code": "view_worldbank", "name": "Consulter World Bank", "category": "data_access", "description": "Accès World Bank uniquement"},
        {"code": "view_imf", "name": "Consulter FMI", "category": "data_access", "description": "Accès FMI uniquement"},
        {"code": "view_un_sdg", "name": "Consulter UN SDG", "category": "data_access", "description": "Accès UN SDG uniquement"},
        {"code": "view_afdb", "name": "Consulter AfDB", "category": "data_access", "description": "Accès AfDB uniquement"},
        {"code": "view_raw_events", "name": "Consulter événements bruts", "category": "data_access", "description": "Accès aux raw_events"},
        
        # Data Export (3)
        {"code": "export_csv", "name": "Exporter en CSV", "category": "data_export", "description": "Télécharger données en CSV"},
        {"code": "export_json", "name": "Exporter en JSON", "category": "data_export", "description": "Télécharger données en JSON"},
        {"code": "export_excel", "name": "Exporter en Excel", "category": "data_export", "description": "Télécharger données en Excel"},
        
        # Data Ingestion (5)
        {"code": "trigger_ingestion", "name": "Déclencher ingestion", "category": "data_ingestion", "description": "Lancer collecte manuelle"},
        {"code": "schedule_ingestion", "name": "Planifier ingestion", "category": "data_ingestion", "description": "Créer tâches automatiques"},
        {"code": "stop_ingestion", "name": "Arrêter ingestion", "category": "data_ingestion", "description": "Stopper tâche en cours"},
        {"code": "view_ingestion_logs", "name": "Consulter logs ingestion", "category": "data_ingestion", "description": "Voir historique ETL"},
        {"code": "debug_ingestion", "name": "Déboguer ingestion", "category": "data_ingestion", "description": "Accès debug ETL"},
        
        # Source Management (4)
        {"code": "manage_data_sources", "name": "Gérer sources de données", "category": "source_management", "description": "CRUD sources externes"},
        {"code": "test_source_connection", "name": "Tester connexion source", "category": "source_management", "description": "Vérifier APIs externes"},
        {"code": "configure_source_api", "name": "Configurer API source", "category": "source_management", "description": "Paramétrer connecteurs"},
        {"code": "view_source_credentials", "name": "Voir credentials sources", "category": "source_management", "description": "Accès secrets APIs"},
        
        # Admin (6)
        {"code": "manage_users", "name": "Gérer utilisateurs", "category": "admin", "description": "CRUD utilisateurs"},
        {"code": "manage_roles", "name": "Gérer rôles", "category": "admin", "description": "Assigner permissions"},
        {"code": "view_audit_logs", "name": "Consulter audit logs", "category": "admin", "description": "Voir journal complet"},
        {"code": "manage_api_tokens", "name": "Gérer tokens API", "category": "admin", "description": "Créer/révoquer tokens"},
        {"code": "configure_system", "name": "Configurer système", "category": "admin", "description": "Paramètres globaux"},
        {"code": "access_admin_panel", "name": "Accéder admin Django", "category": "admin", "description": "Interface /admin"},
        
        # Monitoring (4)
        {"code": "view_dashboards", "name": "Consulter dashboards", "category": "monitoring", "description": "Accès tableaux de bord"},
        {"code": "view_kpis", "name": "Consulter KPIs", "category": "monitoring", "description": "Voir indicateurs"},
        {"code": "view_system_health", "name": "Voir santé système", "category": "monitoring", "description": "Monitoring infrastructure"},
        {"code": "view_data_quality", "name": "Voir qualité données", "category": "monitoring", "description": "Rapports qualité"},
        
        # Visualization (2)
        {"code": "create_charts", "name": "Créer graphiques", "category": "visualization", "description": "Personnaliser visualisations"},
        {"code": "share_visualizations", "name": "Partager visualisations", "category": "visualization", "description": "Exporter/diffuser graphiques"},
    ]
    
    created = 0
    existing = 0
    
    for perm_data in permissions_data:
        perm, is_created = Permission.objects.get_or_create(
            code=perm_data['code'],
            defaults=perm_data
        )
        if is_created:
            created += 1
            print(f"  ✅ {perm.code}")
        else:
            existing += 1
    
    print(f"\n  📊 Résultat: {created} créées, {existing} existantes")
    return True

def create_roles():
    print_header("ÉTAPE 2/4 : CRÉATION DES 5 RÔLES")
    
    roles_config = {
        "admin_platform": {
            "name": "Administrateur Plateforme",
            "description": "Accès complet au système",
            "permissions": [
                "view_all_data", "view_brvm", "view_worldbank", "view_imf", "view_un_sdg", "view_afdb", "view_raw_events",
                "export_csv", "export_json", "export_excel",
                "trigger_ingestion", "schedule_ingestion", "stop_ingestion", "view_ingestion_logs", "debug_ingestion",
                "manage_data_sources", "test_source_connection", "configure_source_api", "view_source_credentials",
                "manage_users", "manage_roles", "view_audit_logs", "manage_api_tokens", "configure_system", "access_admin_panel",
                "view_dashboards", "view_kpis", "view_system_health", "view_data_quality",
                "create_charts", "share_visualizations",
            ],
        },
        "data_engineer": {
            "name": "Ingénieur Data/ETL",
            "description": "Gestion des pipelines d'ingestion",
            "permissions": [
                "view_all_data", "view_raw_events",
                "export_csv", "export_json", "export_excel",
                "trigger_ingestion", "schedule_ingestion", "stop_ingestion", "view_ingestion_logs", "debug_ingestion",
                "manage_data_sources", "test_source_connection", "configure_source_api", "view_source_credentials",
                "view_dashboards", "view_kpis", "view_system_health", "view_data_quality",
            ],
        },
        "analyst_economist": {
            "name": "Analyste/Économiste",
            "description": "Analyse des données économiques",
            "permissions": [
                "view_all_data",
                "export_csv", "export_json", "export_excel",
                "view_dashboards", "view_kpis",
                "create_charts", "share_visualizations",
            ],
        },
        "reader_stakeholder": {
            "name": "Lecteur/Partie prenante",
            "description": "Consultation en lecture seule",
            "permissions": ["view_dashboards", "view_kpis"],
        },
        "api_client": {
            "name": "Client API Externe",
            "description": "Accès programmatique aux données",
            "permissions": ["view_all_data", "export_json"],
        },
    }
    
    for code, config in roles_config.items():
        role, created = Role.objects.get_or_create(
            code=code,
            defaults={'name': config['name'], 'description': config['description']}
        )
        
        if not created:
            role.description = config['description']
            role.save()
        
        # Supprimer les anciennes permissions
        RolePermission.objects.filter(role=role).delete()
        
        # Assigner les permissions via RolePermission
        for perm_code in config['permissions']:
            try:
                perm = Permission.objects.get(code=perm_code)
                RolePermission.objects.get_or_create(role=role, permission=perm)
            except Permission.DoesNotExist:
                print(f"    ⚠️ Permission '{perm_code}' non trouvée")
        
        perm_count = RolePermission.objects.filter(role=role).count()
        status = "✅ Créé" if created else "🔄 Mis à jour"
        print(f"  {status}: {config['name']} ({perm_count} permissions)")
    
    return True

def create_demo_users():
    print_header("ÉTAPE 3/4 : CRÉATION DES 5 UTILISATEURS DE DÉMONSTRATION")
    
    users_data = [
        {"username": "admin", "password": "admin123", "email": "admin@plateforme.local",
         "first_name": "Administrateur", "last_name": "Système", "role_code": "admin_platform",
         "organization": "UEMOA", "is_superuser": True, "is_staff": True},
        
        {"username": "engineer", "password": "engineer123", "email": "engineer@plateforme.local",
         "first_name": "Ingénieur", "last_name": "Data", "role_code": "data_engineer",
         "organization": "BCEAO", "is_staff": True},
        
        {"username": "analyst", "password": "analyst123", "email": "analyst@plateforme.local",
         "first_name": "Analyste", "last_name": "Économiste", "role_code": "analyst_economist",
         "organization": "Ministère Économie"},
        
        {"username": "reader", "password": "reader123", "email": "reader@plateforme.local",
         "first_name": "Lecteur", "last_name": "Externe", "role_code": "reader_stakeholder",
         "organization": "Partenaire"},
        
        {"username": "api_client", "password": "api123", "email": "api@external.com",
         "first_name": "Client", "last_name": "API", "role_code": "api_client",
         "organization": "Externe"},
    ]
    
    created = 0
    existing = 0
    
    for user_data in users_data:
        role_code = user_data.pop("role_code")
        password = user_data.pop("password")
        
        if User.objects.filter(username=user_data['username']).exists():
            existing += 1
            print(f"  ⚠️ Existe déjà: {user_data['username']}")
            continue
        
        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            print(f"  ❌ Rôle '{role_code}' non trouvé pour {user_data['username']}")
            continue
        
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=password,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
        )
        
        user.organization = user_data['organization']
        user.role = role
        user.is_active = True
        user.is_staff = user_data.get('is_staff', False)
        user.is_superuser = user_data.get('is_superuser', False)
        user.save()
        
        created += 1
        print(f"  ✅ {user.username} → {role.name}")
    
    print(f"\n  📊 Résultat: {created} créés, {existing} existants")
    return True

def display_summary():
    print_header("ÉTAPE 4/4 : RÉSUMÉ DE LA CONFIGURATION")
    
    print("\n📋 COMPTES DE DÉMONSTRATION:")
    print("-" * 80)
    print("  Username       Password       Rôle                          Permissions")
    print("-" * 80)
    print("  admin          admin123       Administrateur Plateforme     31/31 ✅")
    print("  engineer       engineer123    Ingénieur Data/ETL            17/31 🔧")
    print("  analyst        analyst123     Analyste/Économiste            9/31 📊")
    print("  reader         reader123      Lecteur                        2/31 👁️")
    print("  api_client     api123         Client API                     2/31 🔌")
    print("-" * 80)
    
    print("\n🌐 URLS D'ACCÈS:")
    print("-" * 80)
    print("  Interface Admin   : http://127.0.0.1:8000/admin/")
    print("  Page de login     : http://127.0.0.1:8000/users/login/")
    print("  Profil utilisateur: http://127.0.0.1:8000/users/profile/")
    print("  Dashboard BRVM    : http://127.0.0.1:8000/dashboard/brvm/")
    print("-" * 80)
    
    print("\n💡 PROCHAINES ÉTAPES:")
    print("-" * 80)
    print("  1. Démarrer le serveur : python manage.py runserver")
    print("  2. Aller sur http://127.0.0.1:8000/users/login/")
    print("  3. Se connecter avec : admin / admin123")
    print("  4. Tester les différents rôles")
    print("-" * 80)
    
    print("\n✅ CONFIGURATION COMPLÈTE TERMINÉE!")
    print("=" * 80)

def main():
    print("=" * 80)
    print("  CONFIGURATION AUTOMATIQUE DE TOUS LES ACTEURS")
    print("  Plateforme de Centralisation des Données Économiques UEMOA")
    print("=" * 80)
    
    try:
        # Étape 1: Permissions
        if not create_permissions():
            print("❌ Échec de la création des permissions")
            return
        
        # Étape 2: Rôles
        if not create_roles():
            print("❌ Échec de la création des rôles")
            return
        
        # Étape 3: Utilisateurs
        if not create_demo_users():
            print("❌ Échec de la création des utilisateurs")
            return
        
        # Étape 4: Résumé
        display_summary()
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
