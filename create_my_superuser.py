"""
Script pour créer un superutilisateur rapidement
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Paramètres du superuser - MODIFIEZ ICI
USERNAME = "sana"
EMAIL = "sana@plateforme.local"
PASSWORD = "Boukary89@"
FIRST_NAME = "Sana"
LAST_NAME = "Boukary"
ORGANIZATION = "UEMOA"

print("=" * 80)
print("CRÉATION DU SUPERUTILISATEUR")
print("=" * 80)

# Vérifier si l'utilisateur existe déjà
if User.objects.filter(username=USERNAME).exists():
    print(f"\n⚠️  L'utilisateur '{USERNAME}' existe déjà!")
    user = User.objects.get(username=USERNAME)
    print(f"   Email: {user.email}")
    print(f"   Superuser: {'Oui' if user.is_superuser else 'Non'}")
    
    # Mettre à jour le mot de passe
    response = input(f"\nVoulez-vous mettre à jour le mot de passe ? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        user.set_password(PASSWORD)
        user.save()
        print(f"✅ Mot de passe mis à jour pour '{USERNAME}'")
else:
    # Créer le superuser
    try:
        user = User.objects.create_superuser(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
        )
        
        # Ajouter l'organisation
        user.organization = ORGANIZATION
        user.is_staff = True
        user.is_active = True
        user.save()
        
        print(f"\n✅ SUPERUTILISATEUR CRÉÉ AVEC SUCCÈS!")
        print("=" * 80)
        print(f"\n📋 INFORMATIONS DE CONNEXION:")
        print("-" * 80)
        print(f"   Nom d'utilisateur : {USERNAME}")
        print(f"   Mot de passe      : {PASSWORD}")
        print(f"   Email             : {EMAIL}")
        print(f"   Nom complet       : {FIRST_NAME} {LAST_NAME}")
        print(f"   Organisation      : {ORGANIZATION}")
        print("-" * 80)
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la création:")
        print(f"   {str(e)}")
        sys.exit(1)

print(f"\n🌐 URLS D'ACCÈS:")
print("-" * 80)
print(f"   Interface Admin : http://127.0.0.1:8000/admin/")
print(f"   Page de login   : http://127.0.0.1:8000/users/login/")
print("-" * 80)
print(f"\n✅ Vous pouvez maintenant vous connecter avec: {USERNAME} / {PASSWORD}")
print()
