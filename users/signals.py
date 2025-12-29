"""
Signals pour automatiser les tâches liées aux utilisateurs
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, AuditLog


@receiver(post_save, sender=User)
def user_created_audit(sender, instance, created, **kwargs):
    """Créer un log d'audit lors de la création d'un utilisateur"""
    if created:
        AuditLog.objects.create(
            user=None,  # Créé par le système
            action=AuditLog.ACTION_PERMISSION_CHANGE,
            level=AuditLog.LEVEL_INFO,
            resource=f"User: {instance.username}",
            details={
                'event': 'user_created',
                'username': instance.username,
                'email': instance.email,
                'role': instance.role.code if instance.role else None
            }
        )
