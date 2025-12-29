"""
═══════════════════════════════════════════════════════════════════════════════
  GUIDE COMPLET - CONFIGURATION DU SUPERUTILISATEUR ET DES ACTEURS
═══════════════════════════════════════════════════════════════════════════════

PARTIE 1 : CRÉER LE SUPERUTILISATEUR
═══════════════════════════════════════════════════════════════════════════════

Option A - Méthode Interactive (Recommandée)
────────────────────────────────────────────────────────────────────────────────
Exécutez le script interactif :

    python create_superuser.py

Le script vous demandera :
  • Nom d'utilisateur (ex: superadmin)
  • Email (ex: admin@plateforme.local)
  • Mot de passe (minimum 8 caractères)
  • Prénom, Nom, Organisation

────────────────────────────────────────────────────────────────────────────────

Option B - Commande Django Standard
────────────────────────────────────────────────────────────────────────────────
Utilisez la commande Django native :

    python manage.py createsuperuser

Répondez aux questions :
  Username: superadmin
  Email: admin@plateforme.local
  Password: super123 (ou autre mot de passe sécurisé)
  Password (again): super123

────────────────────────────────────────────────────────────────────────────────

Option C - Code Python Direct (pour script automatisé)
────────────────────────────────────────────────────────────────────────────────
"""

# create_super_admin.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Créer le superuser
superuser = User.objects.create_superuser(
    username='superadmin',
    email='admin@plateforme.local',
    password='super123',  # CHANGEZ CE MOT DE PASSE !
    first_name='Super',
    last_name='Admin'
)

superuser.organization = 'UEMOA'
superuser.is_staff = True
superuser.is_active = True
superuser.save()

print(f"✅ Superuser créé: {superuser.username}")
print(f"🌐 Connexion: http://127.0.0.1:8000/admin/")

"""
────────────────────────────────────────────────────────────────────────────────


═══════════════════════════════════════════════════════════════════════════════
  PARTIE 2 : CRÉER LES PERMISSIONS (31 au total)
═══════════════════════════════════════════════════════════════════════════════

Code Python pour créer toutes les permissions :
────────────────────────────────────────────────────────────────────────────────
"""

# create_permissions.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from users.models import Permission

# Définir toutes les permissions
permissions_data = [
    # Catégorie: Data Access (7 permissions)
    {"code": "view_all_data", "name": "Consulter toutes les données", 
     "category": "data_access", "description": "Accès en lecture à toutes les sources"},
    {"code": "view_brvm", "name": "Consulter données BRVM", 
     "category": "data_access", "description": "Accès BRVM uniquement"},
    {"code": "view_worldbank", "name": "Consulter World Bank", 
     "category": "data_access", "description": "Accès World Bank uniquement"},
    {"code": "view_imf", "name": "Consulter FMI", 
     "category": "data_access", "description": "Accès FMI uniquement"},
    {"code": "view_un_sdg", "name": "Consulter UN SDG", 
     "category": "data_access", "description": "Accès UN SDG uniquement"},
    {"code": "view_afdb", "name": "Consulter AfDB", 
     "category": "data_access", "description": "Accès AfDB uniquement"},
    {"code": "view_raw_events", "name": "Consulter événements bruts", 
     "category": "data_access", "description": "Accès aux raw_events"},
    
    # Catégorie: Data Export (3 permissions)
    {"code": "export_csv", "name": "Exporter en CSV", 
     "category": "data_export", "description": "Télécharger données en CSV"},
    {"code": "export_json", "name": "Exporter en JSON", 
     "category": "data_export", "description": "Télécharger données en JSON"},
    {"code": "export_excel", "name": "Exporter en Excel", 
     "category": "data_export", "description": "Télécharger données en Excel"},
    
    # Catégorie: Data Ingestion (5 permissions)
    {"code": "trigger_ingestion", "name": "Déclencher ingestion", 
     "category": "data_ingestion", "description": "Lancer collecte manuelle"},
    {"code": "schedule_ingestion", "name": "Planifier ingestion", 
     "category": "data_ingestion", "description": "Créer tâches automatiques"},
    {"code": "stop_ingestion", "name": "Arrêter ingestion", 
     "category": "data_ingestion", "description": "Stopper tâche en cours"},
    {"code": "view_ingestion_logs", "name": "Consulter logs ingestion", 
     "category": "data_ingestion", "description": "Voir historique ETL"},
    {"code": "debug_ingestion", "name": "Déboguer ingestion", 
     "category": "data_ingestion", "description": "Accès debug ETL"},
    
    # Catégorie: Source Management (4 permissions)
    {"code": "manage_data_sources", "name": "Gérer sources de données", 
     "category": "source_management", "description": "CRUD sources externes"},
    {"code": "test_source_connection", "name": "Tester connexion source", 
     "category": "source_management", "description": "Vérifier APIs externes"},
    {"code": "configure_source_api", "name": "Configurer API source", 
     "category": "source_management", "description": "Paramétrer connecteurs"},
    {"code": "view_source_credentials", "name": "Voir credentials sources", 
     "category": "source_management", "description": "Accès secrets APIs"},
    
    # Catégorie: Admin (6 permissions)
    {"code": "manage_users", "name": "Gérer utilisateurs", 
     "category": "admin", "description": "CRUD utilisateurs"},
    {"code": "manage_roles", "name": "Gérer rôles", 
     "category": "admin", "description": "Assigner permissions"},
    {"code": "view_audit_logs", "name": "Consulter audit logs", 
     "category": "admin", "description": "Voir journal complet"},
    {"code": "manage_api_tokens", "name": "Gérer tokens API", 
     "category": "admin", "description": "Créer/révoquer tokens"},
    {"code": "configure_system", "name": "Configurer système", 
     "category": "admin", "description": "Paramètres globaux"},
    {"code": "access_admin_panel", "name": "Accéder admin Django", 
     "category": "admin", "description": "Interface /admin"},
    
    # Catégorie: Monitoring (4 permissions)
    {"code": "view_dashboards", "name": "Consulter dashboards", 
     "category": "monitoring", "description": "Accès tableaux de bord"},
    {"code": "view_kpis", "name": "Consulter KPIs", 
     "category": "monitoring", "description": "Voir indicateurs"},
    {"code": "view_system_health", "name": "Voir santé système", 
     "category": "monitoring", "description": "Monitoring infrastructure"},
    {"code": "view_data_quality", "name": "Voir qualité données", 
     "category": "monitoring", "description": "Rapports qualité"},
    
    # Catégorie: Visualization (2 permissions)
    {"code": "create_charts", "name": "Créer graphiques", 
     "category": "visualization", "description": "Personnaliser visualisations"},
    {"code": "share_visualizations", "name": "Partager visualisations", 
     "category": "visualization", "description": "Exporter/diffuser graphiques"},
]

# Créer les permissions
created_count = 0
for perm_data in permissions_data:
    perm, created = Permission.objects.get_or_create(
        code=perm_data['code'],
        defaults=perm_data
    )
    if created:
        created_count += 1
        print(f"✅ Permission créée: {perm.code}")
    else:
        print(f"⚠️  Permission existante: {perm.code}")

print(f"\n✅ TOTAL: {created_count} permissions créées, {len(permissions_data) - created_count} existantes")

"""
────────────────────────────────────────────────────────────────────────────────


═══════════════════════════════════════════════════════════════════════════════
  PARTIE 3 : CRÉER LES RÔLES (5 rôles)
═══════════════════════════════════════════════════════════════════════════════

Code Python pour créer les 5 rôles avec leurs permissions :
────────────────────────────────────────────────────────────────────────────────
"""

# create_roles.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from users.models import Role, Permission

# Configuration des rôles avec leurs permissions
roles_config = {
    "admin_platform": {
        "name": "Administrateur Plateforme",
        "description": "Accès complet au système - Toutes les permissions",
        "permissions": [
            # TOUTES LES 31 PERMISSIONS
            "view_all_data", "view_brvm", "view_worldbank", "view_imf", 
            "view_un_sdg", "view_afdb", "view_raw_events",
            "export_csv", "export_json", "export_excel",
            "trigger_ingestion", "schedule_ingestion", "stop_ingestion", 
            "view_ingestion_logs", "debug_ingestion",
            "manage_data_sources", "test_source_connection", 
            "configure_source_api", "view_source_credentials",
            "manage_users", "manage_roles", "view_audit_logs", 
            "manage_api_tokens", "configure_system", "access_admin_panel",
            "view_dashboards", "view_kpis", "view_system_health", "view_data_quality",
            "create_charts", "share_visualizations",
        ],
    },
    "data_engineer": {
        "name": "Ingénieur Data/ETL",
        "description": "Gestion des pipelines d'ingestion - 17 permissions",
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
        "description": "Analyse des données économiques - 9 permissions",
        "permissions": [
            "view_all_data",
            "export_csv", "export_json", "export_excel",
            "view_dashboards", "view_kpis",
            "create_charts", "share_visualizations",
        ],
    },
    "reader_stakeholder": {
        "name": "Lecteur/Partie prenante",
        "description": "Consultation en lecture seule - 2 permissions",
        "permissions": [
            "view_dashboards", "view_kpis",
        ],
    },
    "api_client": {
        "name": "Client API Externe",
        "description": "Accès programmatique aux données - 2 permissions",
        "permissions": [
            "view_all_data",
            "export_json",
        ],
    },
}

# Créer les rôles
for code, config in roles_config.items():
    role, created = Role.objects.get_or_create(
        code=code,
        defaults={
            'name': config['name'],
            'description': config['description']
        }
    )
    
    if created:
        print(f"✅ Rôle créé: {config['name']}")
    else:
        print(f"⚠️  Rôle existant: {config['name']}")
        # Mettre à jour la description
        role.description = config['description']
        role.save()
    
    # Assigner les permissions
    for perm_code in config['permissions']:
        try:
            perm = Permission.objects.get(code=perm_code)
            role.permissions.add(perm)
        except Permission.DoesNotExist:
            print(f"   ❌ Permission '{perm_code}' non trouvée!")
    
    print(f"   → {role.permissions.count()} permissions assignées")

print("\n✅ TOUS LES RÔLES CRÉÉS!")

"""
────────────────────────────────────────────────────────────────────────────────


═══════════════════════════════════════════════════════════════════════════════
  PARTIE 4 : CRÉER LES UTILISATEURS DE DÉMONSTRATION
═══════════════════════════════════════════════════════════════════════════════

Code Python pour créer les 5 utilisateurs de test :
────────────────────────────────────────────────────────────────────────────────
"""

# create_demo_users.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Role

User = get_user_model()

# Définir les utilisateurs
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
    },
    {
        "username": "reader",
        "password": "reader123",
        "email": "reader@plateforme.local",
        "first_name": "Lecteur",
        "last_name": "Externe",
        "role_code": "reader_stakeholder",
        "organization": "Partenaire",
    },
    {
        "username": "api_client",
        "password": "api123",
        "email": "api@external.com",
        "first_name": "Client",
        "last_name": "API",
        "role_code": "api_client",
        "organization": "Externe",
    },
]

# Créer les utilisateurs
for user_data in users_data:
    role_code = user_data.pop("role_code")
    password = user_data.pop("password")
    
    # Vérifier si l'utilisateur existe
    if User.objects.filter(username=user_data['username']).exists():
        print(f"⚠️  Utilisateur '{user_data['username']}' existe déjà")
        continue
    
    # Récupérer le rôle
    try:
        role = Role.objects.get(code=role_code)
    except Role.DoesNotExist:
        print(f"❌ Rôle '{role_code}' non trouvé pour {user_data['username']}")
        continue
    
    # Créer l'utilisateur
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
    
    print(f"✅ Utilisateur créé: {user.username} → {role.name} ({role.permissions.count()} permissions)")

print("\n✅ TOUS LES UTILISATEURS CRÉÉS!")
print("\n📋 COMPTES DE DÉMONSTRATION:")
print("-" * 80)
print("  admin      / admin123      → Administrateur Plateforme (31 permissions)")
print("  engineer   / engineer123   → Ingénieur Data/ETL (17 permissions)")
print("  analyst    / analyst123    → Analyste/Économiste (9 permissions)")
print("  reader     / reader123     → Lecteur (2 permissions)")
print("  api_client / api123        → Client API (2 permissions)")
print("-" * 80)

"""
────────────────────────────────────────────────────────────────────────────────


═══════════════════════════════════════════════════════════════════════════════
  PARTIE 5 : SCRIPT TOUT-EN-UN (Recommandé)
═══════════════════════════════════════════════════════════════════════════════

Exécutez TOUS les scripts ci-dessus en une seule commande :
────────────────────────────────────────────────────────────────────────────────

    python setup_complete_actors.py

Ou créez ce fichier et exécutez-le :
────────────────────────────────────────────────────────────────────────────────
"""

# Voir le fichier: setup_complete_actors.py (créé ci-dessous)

"""
────────────────────────────────────────────────────────────────────────────────


═══════════════════════════════════════════════════════════════════════════════
  URLS IMPORTANTES
═══════════════════════════════════════════════════════════════════════════════

Après la configuration, accédez à :

  🔐 Interface Admin Django
     http://127.0.0.1:8000/admin/
     
  🔑 Page de connexion utilisateur
     http://127.0.0.1:8000/users/login/
     
  👤 Profil utilisateur
     http://127.0.0.1:8000/users/profile/
     
  📊 Dashboard BRVM
     http://127.0.0.1:8000/dashboard/brvm/

═══════════════════════════════════════════════════════════════════════════════
  COMMANDES UTILES
═══════════════════════════════════════════════════════════════════════════════

Démarrer le serveur :
    python manage.py runserver

Créer un superuser interactif :
    python manage.py createsuperuser

Vérifier les permissions d'un utilisateur :
    python -c "import django; django.setup(); from users.models import User; u = User.objects.get(username='admin'); print([p.code for p in u.role.permissions.all()])"

Afficher tous les utilisateurs :
    python manage.py shell
    >>> from users.models import User
    >>> for u in User.objects.all(): print(f"{u.username} - {u.role}")

═══════════════════════════════════════════════════════════════════════════════
"""

print(__doc__)
