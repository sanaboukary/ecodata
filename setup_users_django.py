"""
Script de création des utilisateurs via Django ORM
Compatible avec Djongo - pas besoin de migrations.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from users.models import User, Role, Permission
from datetime import datetime

def main():
    print("=" * 80)
    print("CRÉATION DES UTILISATEURS VIA DJANGO ORM")
    print("=" * 80)
    
    print("\n1️⃣ Nettoyage des données existantes...")
    try:
        User.objects.all().delete()
        print("   ✓ Utilisateurs supprimés")
    except Exception as e:
        print(f"   ⚠ Pas d'utilisateurs à supprimer: {e}")
    
    try:
        Role.objects.all().delete()
        print("   ✓ Rôles supprimés")
    except Exception as e:
        print(f"   ⚠ Pas de rôles à supprimer: {e}")
    
    try:
        Permission.objects.all().delete()
        print("   ✓ Permissions supprimées")
    except Exception as e:
        print(f"   ⚠ Pas de permissions à supprimer: {e}")
    
    print("\n2️⃣ Création des permissions...")
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
    
    permissions = {}
    for perm_data in permissions_data:
        perm = Permission.objects.create(**perm_data)
        permissions[perm.code] = perm
    
    print(f"   ✓ {len(permissions)} permissions créées")
    
    print("\n3️⃣ Création des rôles...")
    roles_config = {
        "admin_platform": {
            "name": "Administrateur Plateforme",
            "description": "Accès complet au système",
            "permissions": list(permissions.keys()),
        },
        "data_engineer": {
            "name": "Ingénieur Data/ETL",
            "description": "Gestion des pipelines d'ingestion",
            "permissions": [
                "view_all_data", "view_raw_events",
                "export_csv", "export_json", "export_excel",
                "trigger_ingestion", "schedule_ingestion", "stop_ingestion", 
                "view_ingestion_logs", "debug_ingestion",
                "manage_data_sources", "test_source_connection", 
                "configure_source_api", "view_source_credentials",
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
            "permissions": [
                "view_dashboards", "view_kpis",
            ],
        },
        "api_client": {
            "name": "Client API Externe",
            "description": "Accès programmatique aux données",
            "permissions": [
                "view_all_data",
                "export_json",
            ],
        },
    }
    
    roles = {}
    for code, config in roles_config.items():
        role = Role.objects.create(
            code=code,
            name=config["name"],
            description=config["description"],
            is_active=True
        )
        # Assigner les permissions
        for perm_code in config["permissions"]:
            if perm_code in permissions:
                role.permissions.add(permissions[perm_code])
        
        roles[code] = role
        print(f"   ✓ Rôle '{config['name']}' créé ({role.permissions.count()} permissions)")
    
    print("\n4️⃣ Création des utilisateurs...")
    users_data = [
        {
            "username": "admin",
            "password": "admin123",
            "email": "admin@plateforme.local",
            "first_name": "Administrateur",
            "last_name": "Système",
            "role": roles["admin_platform"],
            "organization": "UEMOA",
            "is_superuser": True,
            "is_staff": True,
        },
        {
            "username": "engineer",
            "password": "engineer123",
            "email": "engineer@plateforme.local",
            "first_name": "Ingénieur",
            "last_name": "Data",
            "role": roles["data_engineer"],
            "organization": "BCEAO",
            "is_superuser": False,
            "is_staff": True,
        },
        {
            "username": "analyst",
            "password": "analyst123",
            "email": "analyst@plateforme.local",
            "first_name": "Analyste",
            "last_name": "Économiste",
            "role": roles["analyst_economist"],
            "organization": "Ministère Économie",
            "is_superuser": False,
            "is_staff": False,
        },
        {
            "username": "reader",
            "password": "reader123",
            "email": "reader@plateforme.local",
            "first_name": "Lecteur",
            "last_name": "Externe",
            "role": roles["reader_stakeholder"],
            "organization": "Partenaire",
            "is_superuser": False,
            "is_staff": False,
        },
        {
            "username": "api_client",
            "password": "api123",
            "email": "api@external.com",
            "first_name": "Client",
            "last_name": "API",
            "role": roles["api_client"],
            "organization": "Externe",
            "is_superuser": False,
            "is_staff": False,
        },
    ]
    
    created_users = []
    for user_data in users_data:
        password = user_data.pop("password")
        user = User.objects.create(**user_data)
        user.set_password(password)
        user.save()
        created_users.append((user.username, password, user.role.name))
        print(f"   ✓ Utilisateur '{user.username}' créé (rôle: {user.role.code})")
    
    print("\n" + "=" * 80)
    print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 80)
    print("\n📝 Comptes de démonstration créés:")
    print("-" * 80)
    for username, password, role_name in created_users:
        print(f"  • {username:15} / {password:15} ({role_name})")
    print("-" * 80)
    print("\n🌐 Vous pouvez maintenant vous connecter sur:")
    print("   http://127.0.0.1:8000/users/login/")
    print("\n💡 Lancer le serveur Django:")
    print("   python manage.py runserver")
    print()

if __name__ == "__main__":
    main()
