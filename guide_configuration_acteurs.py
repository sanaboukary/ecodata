"""
Guide de configuration manuelle des acteurs.
À exécuter après avoir lancé le serveur Django.
"""

print("=" * 80)
print("GUIDE DE CONFIGURATION DES ACTEURS - CONFIGURATION MANUELLE")
print("=" * 80)

print("\n🚀 ÉTAPES À SUIVRE :")
print("-" * 80)

print("\n1️⃣ Démarrer le serveur Django :")
print("   python manage.py runserver")

print("\n2️⃣ Accéder à l'interface admin Django :")
print("   URL : http://127.0.0.1:8000/admin/")
print("   Note : Si aucun superuser n'existe, créer un avec:")
print("   python manage.py createsuperuser")

print("\n3️⃣ Créer les 31 permissions dans /admin/users/permission/add/ :")
print("-" * 80)

permissions = [
    ("Data Access", [
        ("view_all_data", "Consulter toutes les données"),
        ("view_brvm", "Consulter données BRVM"),
        ("view_worldbank", "Consulter World Bank"),
        ("view_imf", "Consulter FMI"),
        ("view_un_sdg", "Consulter UN SDG"),
        ("view_afdb", "Consulter AfDB"),
        ("view_raw_events", "Consulter événements bruts"),
    ]),
    ("Data Export", [
        ("export_csv", "Exporter en CSV"),
        ("export_json", "Exporter en JSON"),
        ("export_excel", "Exporter en Excel"),
    ]),
    ("Data Ingestion", [
        ("trigger_ingestion", "Déclencher ingestion"),
        ("schedule_ingestion", "Planifier ingestion"),
        ("stop_ingestion", "Arrêter ingestion"),
        ("view_ingestion_logs", "Consulter logs ingestion"),
        ("debug_ingestion", "Déboguer ingestion"),
    ]),
    ("Source Management", [
        ("manage_data_sources", "Gérer sources de données"),
        ("test_source_connection", "Tester connexion source"),
        ("configure_source_api", "Configurer API source"),
        ("view_source_credentials", "Voir credentials sources"),
    ]),
    ("Admin", [
        ("manage_users", "Gérer utilisateurs"),
        ("manage_roles", "Gérer rôles"),
        ("view_audit_logs", "Consulter audit logs"),
        ("manage_api_tokens", "Gérer tokens API"),
        ("configure_system", "Configurer système"),
        ("access_admin_panel", "Accéder admin Django"),
    ]),
    ("Monitoring", [
        ("view_dashboards", "Consulter dashboards"),
        ("view_kpis", "Consulter KPIs"),
        ("view_system_health", "Voir santé système"),
        ("view_data_quality", "Voir qualité données"),
    ]),
    ("Visualization", [
        ("create_charts", "Créer graphiques"),
        ("share_visualizations", "Partager visualisations"),
    ]),
]

for category, perms in permissions:
    print(f"\n   📁 Catégorie: {category}")
    for code, name in perms:
        print(f"      • Code: {code:25} | Nom: {name}")

print("\n4️⃣ Créer les 5 rôles dans /admin/users/role/add/ :")
print("-" * 80)

roles = {
    "admin_platform": {
        "name": "Administrateur Plateforme",
        "description": "Accès complet au système",
        "permissions_count": 31,
        "note": "✅ TOUTES les permissions (31/31)"
    },
    "data_engineer": {
        "name": "Ingénieur Data/ETL",
        "description": "Gestion des pipelines d'ingestion",
        "permissions_count": 17,
        "note": "🔧 17 permissions techniques (ingestion + sources + monitoring)"
    },
    "analyst_economist": {
        "name": "Analyste/Économiste",
        "description": "Analyse des données économiques",
        "permissions_count": 9,
        "note": "📊 9 permissions (lecture + export + visualisation)"
    },
    "reader_stakeholder": {
        "name": "Lecteur/Partie prenante",
        "description": "Consultation en lecture seule",
        "permissions_count": 2,
        "note": "👁️ 2 permissions (dashboards + KPIs uniquement)"
    },
    "api_client": {
        "name": "Client API Externe",
        "description": "Accès programmatique aux données",
        "permissions_count": 2,
        "note": "🔌 2 permissions (view_all_data + export_json)"
    },
}

for code, config in roles.items():
    print(f"\n   🏷️ Code: {code}")
    print(f"      Nom: {config['name']}")
    print(f"      Description: {config['description']}")
    print(f"      {config['note']}")

print("\n5️⃣ Créer les 5 utilisateurs de démonstration dans /admin/users/user/add/ :")
print("-" * 80)

users = [
    {
        "username": "admin",
        "password": "admin123",
        "email": "admin@plateforme.local",
        "first_name": "Administrateur",
        "last_name": "Système",
        "role": "admin_platform",
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
        "role": "data_engineer",
        "organization": "BCEAO",
        "is_staff": True,
    },
    {
        "username": "analyst",
        "password": "analyst123",
        "email": "analyst@plateforme.local",
        "first_name": "Analyste",
        "last_name": "Économiste",
        "role": "analyst_economist",
        "organization": "Ministère Économie",
    },
    {
        "username": "reader",
        "password": "reader123",
        "email": "reader@plateforme.local",
        "first_name": "Lecteur",
        "last_name": "Externe",
        "role": "reader_stakeholder",
        "organization": "Partenaire",
    },
    {
        "username": "api_client",
        "password": "api123",
        "email": "api@external.com",
        "first_name": "Client",
        "last_name": "API",
        "role": "api_client",
        "organization": "Externe",
    },
]

for user in users:
    print(f"\n   👤 Username: {user['username']} / Password: {user['password']}")
    print(f"      Email: {user['email']}")
    print(f"      Nom complet: {user['first_name']} {user['last_name']}")
    print(f"      Rôle: {user['role']}")
    print(f"      Organisation: {user['organization']}")
    if user.get('is_superuser'):
        print(f"      ⚠️ Cocher: is_superuser, is_staff, is_active")
    elif user.get('is_staff'):
        print(f"      ⚠️ Cocher: is_staff, is_active")
    else:
        print(f"      ⚠️ Cocher: is_active")

print("\n6️⃣ Tester la connexion :")
print("   URL : http://127.0.0.1:8000/users/login/")
print("   Essayer avec : admin / admin123")

print("\n7️⃣ Voir le profil utilisateur :")
print("   URL : http://127.0.0.1:8000/users/profile/")

print("\n" + "=" * 80)
print("✅ FIN DU GUIDE")
print("=" * 80)
print()
print("💡 ASTUCE: Pour automatiser la création, utilisez manage.py createsuperuser")
print("   puis créez manuellement un seul utilisateur dans l'admin Django pour tester.")
print()
