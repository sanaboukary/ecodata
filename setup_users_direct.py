"""
Script de création directe des utilisateurs dans MongoDB
Sans passer par les migrations Django.
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from django.contrib.auth.hashers import make_password

# Configuration MongoDB
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "centralisation_db"

def main():
    print("=" * 80)
    print("CRÉATION DIRECTE DES UTILISATEURS DANS MONGODB")
    print("=" * 80)
    
    # Connexion MongoDB
    print("\n1️⃣ Connexion à MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    print(f"   ✓ Connecté à {MONGO_DB}")
    
    # Création de la collection users_user si elle n'existe pas
    if 'users_user' not in db.list_collection_names():
        db.create_collection('users_user')
        print("   ✓ Collection users_user créée")
    else:
        # Nettoyer la collection existante
        db.users_user.delete_many({})
        print("   ✓ Collection users_user nettoyée")
    
    # Création de la collection users_role
    if 'users_role' not in db.list_collection_names():
        db.create_collection('users_role')
        print("   ✓ Collection users_role créée")
    else:
        db.users_role.delete_many({})
        print("   ✓ Collection users_role nettoyée")
    
    # Création de la collection users_permission
    if 'users_permission' not in db.list_collection_names():
        db.create_collection('users_permission')
        print("   ✓ Collection users_permission créée")
    else:
        db.users_permission.delete_many({})
        print("   ✓ Collection users_permission nettoyée")
    
    print("\n2️⃣ Création des permissions...")
    permissions_data = [
        # Data Access (7 permissions)
        {"code": "view_all_data", "name": "Consulter toutes les données", "category": "data_access", "description": "Accès en lecture à toutes les sources"},
        {"code": "view_brvm", "name": "Consulter données BRVM", "category": "data_access", "description": "Accès BRVM uniquement"},
        {"code": "view_worldbank", "name": "Consulter World Bank", "category": "data_access", "description": "Accès World Bank uniquement"},
        {"code": "view_imf", "name": "Consulter FMI", "category": "data_access", "description": "Accès FMI uniquement"},
        {"code": "view_un_sdg", "name": "Consulter UN SDG", "category": "data_access", "description": "Accès UN SDG uniquement"},
        {"code": "view_afdb", "name": "Consulter AfDB", "category": "data_access", "description": "Accès AfDB uniquement"},
        {"code": "view_raw_events", "name": "Consulter événements bruts", "category": "data_access", "description": "Accès aux raw_events"},
        
        # Data Export (3 permissions)
        {"code": "export_csv", "name": "Exporter en CSV", "category": "data_export", "description": "Télécharger données en CSV"},
        {"code": "export_json", "name": "Exporter en JSON", "category": "data_export", "description": "Télécharger données en JSON"},
        {"code": "export_excel", "name": "Exporter en Excel", "category": "data_export", "description": "Télécharger données en Excel"},
        
        # Data Ingestion (5 permissions)
        {"code": "trigger_ingestion", "name": "Déclencher ingestion", "category": "data_ingestion", "description": "Lancer collecte manuelle"},
        {"code": "schedule_ingestion", "name": "Planifier ingestion", "category": "data_ingestion", "description": "Créer tâches automatiques"},
        {"code": "stop_ingestion", "name": "Arrêter ingestion", "category": "data_ingestion", "description": "Stopper tâche en cours"},
        {"code": "view_ingestion_logs", "name": "Consulter logs ingestion", "category": "data_ingestion", "description": "Voir historique ETL"},
        {"code": "debug_ingestion", "name": "Déboguer ingestion", "category": "data_ingestion", "description": "Accès debug ETL"},
        
        # Source Management (4 permissions)
        {"code": "manage_data_sources", "name": "Gérer sources de données", "category": "source_management", "description": "CRUD sources externes"},
        {"code": "test_source_connection", "name": "Tester connexion source", "category": "source_management", "description": "Vérifier APIs externes"},
        {"code": "configure_source_api", "name": "Configurer API source", "category": "source_management", "description": "Paramétrer connecteurs"},
        {"code": "view_source_credentials", "name": "Voir credentials sources", "category": "source_management", "description": "Accès secrets APIs"},
        
        # Admin (6 permissions)
        {"code": "manage_users", "name": "Gérer utilisateurs", "category": "admin", "description": "CRUD utilisateurs"},
        {"code": "manage_roles", "name": "Gérer rôles", "category": "admin", "description": "Assigner permissions"},
        {"code": "view_audit_logs", "name": "Consulter audit logs", "category": "admin", "description": "Voir journal complet"},
        {"code": "manage_api_tokens", "name": "Gérer tokens API", "category": "admin", "description": "Créer/révoquer tokens"},
        {"code": "configure_system", "name": "Configurer système", "category": "admin", "description": "Paramètres globaux"},
        {"code": "access_admin_panel", "name": "Accéder admin Django", "category": "admin", "description": "Interface /admin"},
        
        # Monitoring (4 permissions)
        {"code": "view_dashboards", "name": "Consulter dashboards", "category": "monitoring", "description": "Accès tableaux de bord"},
        {"code": "view_kpis", "name": "Consulter KPIs", "category": "monitoring", "description": "Voir indicateurs"},
        {"code": "view_system_health", "name": "Voir santé système", "category": "monitoring", "description": "Monitoring infrastructure"},
        {"code": "view_data_quality", "name": "Voir qualité données", "category": "monitoring", "description": "Rapports qualité"},
        
        # Visualization (2 permissions)
        {"code": "create_charts", "name": "Créer graphiques", "category": "visualization", "description": "Personnaliser visualisations"},
        {"code": "share_visualizations", "name": "Partager visualisations", "category": "visualization", "description": "Exporter/diffuser graphiques"},
    ]
    
    permission_ids = {}
    for i, perm in enumerate(permissions_data, start=1):
        perm['_id'] = i
        result = db.users_permission.insert_one(perm)
        permission_ids[perm['code']] = i
        
    print(f"   ✓ {len(permissions_data)} permissions créées")
    
    print("\n3️⃣ Création des rôles...")
    roles_config = {
        "admin_platform": {
            "name": "Administrateur Plateforme",
            "description": "Accès complet au système",
            "permissions": list(permission_ids.keys()),  # Toutes les permissions
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
    
    role_ids = {}
    role_id = 1
    for code, config in roles_config.items():
        role_doc = {
            "_id": role_id,
            "code": code,
            "name": config["name"],
            "description": config["description"],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "permission_ids": [permission_ids[p] for p in config["permissions"] if p in permission_ids]
        }
        db.users_role.insert_one(role_doc)
        role_ids[code] = role_id
        print(f"   ✓ Rôle '{config['name']}' créé ({len(role_doc['permission_ids'])} permissions)")
        role_id += 1
    
    print("\n4️⃣ Création des utilisateurs...")
    users_data = [
        {
            "username": "admin",
            "password": "admin123",
            "email": "admin@plateforme.local",
            "first_name": "Administrateur",
            "last_name": "Système",
            "role_code": "admin_platform",
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
            "role_code": "data_engineer",
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
            "role_code": "analyst_economist",
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
            "role_code": "reader_stakeholder",
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
            "role_code": "api_client",
            "organization": "Externe",
            "is_superuser": False,
            "is_staff": False,
        },
    ]
    
    for i, user_data in enumerate(users_data, start=1):
        role_code = user_data.pop("role_code")
        password = user_data.pop("password")
        
        user_doc = {
            "_id": i,
            "username": user_data["username"],
            "password": make_password(password),
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "role_id": role_ids[role_code],
            "organization": user_data["organization"],
            "is_active": True,
            "is_superuser": user_data["is_superuser"],
            "is_staff": user_data["is_staff"],
            "mfa_enabled": False,
            "date_joined": datetime.utcnow(),
            "last_login": None,
            "last_login_ip": None,
            "failed_login_attempts": 0,
        }
        
        db.users_user.insert_one(user_doc)
        print(f"   ✓ Utilisateur '{user_data['username']}' créé (rôle: {role_code})")
    
    print("\n" + "=" * 80)
    print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 80)
    print("\n📝 Comptes de démonstration créés:")
    print("-" * 80)
    for user in users_data:
        print(f"  • {user['username']:15} / {user['password']:15} ({roles_config[role_code]['name']})")
    print("-" * 80)
    print("\n🌐 Vous pouvez maintenant vous connecter sur:")
    print("   http://127.0.0.1:8000/users/login/")
    print("\n💡 Lancer le serveur Django:")
    print("   python manage.py runserver")
    print()
    
    client.close()

if __name__ == "__main__":
    main()
