"""
Script pour réinitialiser proprement la base de données et configurer les acteurs
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.core.management import call_command
from plateforme_centralisation.mongo import get_mongo_db

def main():
    print("="*80)
    print("RÉINITIALISATION ET CONFIGURATION DES ACTEURS")
    print("="*80)
    
    # Nettoyer les collections Django dans MongoDB
    print("\n1️⃣ Nettoyage des collections Django...")
    client, db = get_mongo_db()
    
    # Supprimer uniquement les collections Django (pas les données métier)
    django_collections = [
        'django_migrations',
        'django_admin_log',
        'django_session',
        'auth_user',
        'auth_group',
        'auth_permission',
        'users_user',
        'users_role',
        'users_permission',
        'users_rolepermission',
        'users_auditlog',
        'users_datasourceaccess',
    ]
    
    for collection in django_collections:
        if collection in db.list_collection_names():
            db[collection].drop()
            print(f"   ✓ Collection {collection} supprimée")
    
    client.close()
    
    # Appliquer les migrations
    print("\n2️⃣ Application des migrations Django...")
    try:
        call_command('migrate', '--run-syncdb', verbosity=1)
        print("   ✓ Migrations appliquées")
    except Exception as e:
        print(f"   ⚠ Erreur migrations: {e}")
        print("   Continuons quand même...")
    
    # Initialiser les rôles
    print("\n3️⃣ Initialisation des rôles et permissions...")
    try:
        call_command('init_roles')
        print("   ✓ Rôles créés")
    except Exception as e:
        print(f"   ✗ Erreur init_roles: {e}")
        return
    
    # Créer des utilisateurs de démonstration
    print("\n4️⃣ Création des utilisateurs de démonstration...")
    create_demo_users()
    
    print("\n" + "="*80)
    print("✅ CONFIGURATION TERMINÉE")
    print("="*80)
    print("\nUtilisateurs créés:")
    print("  • admin / admin123 (Administrateur Plateforme)")
    print("  • engineer / engineer123 (Ingénieur Data)")
    print("  • analyst / analyst123 (Analyste/Économiste)")
    print("  • reader / reader123 (Lecteur)")
    print("  • api_client / api123 (Client API)")
    print("\nConnexion: http://localhost:8000/users/login/")
    print("="*80)


def create_demo_users():
    from users.models import User, Role
    
    users_config = [
        {
            'username': 'admin',
            'email': 'admin@platform.com',
            'password': 'admin123',
            'role_code': 'admin_platform',
            'first_name': 'Admin',
            'last_name': 'Plateforme',
            'organization': 'Direction Générale',
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'username': 'engineer',
            'email': 'engineer@platform.com',
            'password': 'engineer123',
            'role_code': 'data_engineer',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'organization': 'Équipe Data',
        },
        {
            'username': 'analyst',
            'email': 'analyst@platform.com',
            'password': 'analyst123',
            'role_code': 'analyst_economist',
            'first_name': 'Marie',
            'last_name': 'Martin',
            'organization': 'Service Études',
        },
        {
            'username': 'reader',
            'email': 'reader@platform.com',
            'password': 'reader123',
            'role_code': 'reader_stakeholder',
            'first_name': 'Paul',
            'last_name': 'Bernard',
            'organization': 'Investisseur',
        },
        {
            'username': 'api_client',
            'email': 'api@platform.com',
            'password': 'api123',
            'role_code': 'api_client',
            'first_name': 'API',
            'last_name': 'Client',
            'organization': 'External System',
        },
    ]
    
    for config in users_config:
        username = config['username']
        
        # Supprimer si existe
        User.objects.filter(username=username).delete()
        
        # Récupérer le rôle
        try:
            role = Role.objects.get(code=config['role_code'])
        except Role.DoesNotExist:
            print(f"   ⚠ Rôle {config['role_code']} non trouvé pour {username}")
            continue
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=config['email'],
            password=config['password'],
            first_name=config.get('first_name', ''),
            last_name=config.get('last_name', ''),
            is_staff=config.get('is_staff', False),
            is_superuser=config.get('is_superuser', False),
        )
        
        user.role = role
        user.organization = config.get('organization', '')
        user.save()
        
        print(f"   ✓ {username} créé ({role.name})")


if __name__ == '__main__':
    main()
