"""
Script simplifié pour créer un superutilisateur administrateur
Usage: python create_superuser.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    print("=" * 80)
    print("CRÉATION D'UN SUPERUTILISATEUR")
    print("=" * 80)
    
    # Vérifier si un superuser existe déjà
    existing_superusers = User.objects.filter(is_superuser=True)
    if existing_superusers.exists():
        print("\n⚠️  Des superutilisateurs existent déjà:")
        for user in existing_superusers:
            print(f"   - {user.username} ({user.email})")
        
        response = input("\nVoulez-vous en créer un autre ? (oui/non): ")
        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            print("Annulation.")
            return
    
    print("\n📝 Entrez les informations du superutilisateur:")
    print("-" * 80)
    
    # Nom d'utilisateur
    while True:
        username = input("\nSana: ").strip()
        if not username:
            print("❌ Le nom d'utilisateur est requis!")
            continue
        
        if User.objects.filter(username=username).exists():
            print(f"❌ Le nom d'utilisateur '{username}' existe déjà!")
            continue
        
        break
    
    # Email
    while True:
        email = input("sanaboukary79@gmail.com ").strip()
        if not email:
            print("❌ L'email est requis!")
            continue
        
        if User.objects.filter(email=email).exists():
            print(f"❌ L'email '{email}' est déjà utilisé!")
            continue
        
        break
    
    # Mot de passe
    while True:
        password = input("Boukary89@: ").strip()
        if len(password) < 8:
            print("❌ Le mot de passe doit contenir au moins 8 caractères!")
            continue
        
        password_confirm = input("Confirmer le mot de passe: ").strip()
        if password != password_confirm:
            print("❌ Les mots de passe ne correspondent pas!")
            continue
        
        break
    
    # Informations supplémentaires
    first_name = input("Boukary (optionnel): ").strip() or "Super"
    last_name = input("Sana (optionnel): ").strip() or "Admin"
    organization = input("Organisation (optionnel, ex: UEMOA): ").strip() or "UEMOA"
    
    # Création du superuser
    print("\n" + "=" * 80)
    print("CRÉATION EN COURS...")
    print("=" * 80)
    
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        # Ajouter l'organisation
        user.organization = organization
        user.is_staff = True
        user.is_active = True
        user.save()
        
        print("\n✅ SUPERUTILISATEUR CRÉÉ AVEC SUCCÈS!")
        print("=" * 80)
        print(f"\n📋 INFORMATIONS DE CONNEXION:")
        print("-" * 80)
        print(f"   Nom d'utilisateur : {username}")
        print(f"   Mot de passe      : {password}")
        print(f"   Email             : {email}")
        print(f"   Nom complet       : {first_name} {last_name}")
        print(f"   Organisation      : {organization}")
        print("-" * 80)
        print(f"\n🌐 URLS D'ACCÈS:")
        print("-" * 80)
        print(f"   Interface Admin : http://127.0.0.1:8000/admin/")
        print(f"   Page de login   : http://127.0.0.1:8000/users/login/")
        print(f"   Profil          : http://127.0.0.1:8000/users/profile/")
        print("-" * 80)
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print("-" * 80)
        print("   1. Démarrer le serveur : python manage.py runserver")
        print("   2. Aller sur http://127.0.0.1:8000/admin/")
        print(f"   3. Se connecter avec : {username} / {password}")
        print("   4. Créer les Permissions dans: /admin/users/permission/")
        print("   5. Créer les Rôles dans: /admin/users/role/")
        print("   6. Créer les Utilisateurs dans: /admin/users/user/")
        print("-" * 80)
        
        print(f"\n📖 DOCUMENTATION:")
        print("-" * 80)
        print("   Voir le guide complet : guide_configuration_acteurs.py")
        print("   Voir la doc acteurs   : CONFIGURATION_ACTEURS.md")
        print("   Voir le résumé        : ACTEURS_IMPLEMENTATION_SUMMARY.md")
        print("-" * 80)
        print()
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la création:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Proposer de créer un rôle admin pour ce user
    create_role = input("\nVoulez-vous créer un rôle 'Administrateur Plateforme' ? (oui/non): ")
    if create_role.lower() in ['oui', 'o', 'yes', 'y']:
        try:
            from users.models import Role
            
            role, created = Role.objects.get_or_create(
                code='admin_platform',
                defaults={
                    'name': 'Administrateur Plateforme',
                    'description': 'Accès complet au système - 31 permissions'
                }
            )
            
            user.role = role
            user.save()
            
            if created:
                print(f"✅ Rôle 'Administrateur Plateforme' créé")
            else:
                print(f"✅ Rôle 'Administrateur Plateforme' existant assigné")
            
            print(f"✅ Rôle assigné à {username}")
            
        except Exception as e:
            print(f"⚠️  Impossible de créer le rôle: {e}")
            print("   Vous pouvez le créer manuellement via /admin/users/role/")

if __name__ == "__main__":
    create_superuser()
