from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Gestion des Utilisateurs et Rôles'
    
    def ready(self):
        """Import des signals lors du démarrage de l'app"""
        import users.signals
