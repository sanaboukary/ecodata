"""
Models pour la gestion des utilisateurs et des rôles (RBAC)
Basé sur le diagramme de cas d'utilisation de la plateforme
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets


class Role(models.Model):
    """
    Rôles disponibles dans la plateforme (RBAC - Role-Based Access Control)
    """
    # Constantes pour les rôles
    ADMIN_PLATFORM = 'admin_platform'
    DATA_ENGINEER = 'data_engineer'
    ANALYST_ECONOMIST = 'analyst_economist'
    READER_STAKEHOLDER = 'reader_stakeholder'
    API_CLIENT = 'api_client'
    
    ROLE_CHOICES = [
        (ADMIN_PLATFORM, 'Administrateur Plateforme'),
        (DATA_ENGINEER, 'Ingénieur Data/ETL'),
        (ANALYST_ECONOMIST, 'Analyste/Économiste'),
        (READER_STAKEHOLDER, 'Lecteur (Stakeholder)'),
        (API_CLIENT, 'Client API Externe'),
    ]
    
    code = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'users_role'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def permissions(self):
        """Retourne les permissions via RolePermission"""
        from django.db.models import Prefetch
        return Permission.objects.filter(permission_roles__role=self)


class Permission(models.Model):
    """
    Permissions granulaires associées aux rôles
    """
    # Catégories de permissions
    DATA_ACCESS = 'data_access'
    DATA_EXPORT = 'data_export'
    DATA_INGESTION = 'data_ingestion'
    ADMIN_CONFIG = 'admin_config'
    PIPELINE_MANAGE = 'pipeline_manage'
    API_CONSUME = 'api_consume'
    AUDIT_VIEW = 'audit_view'
    
    CATEGORY_CHOICES = [
        (DATA_ACCESS, 'Accès aux données'),
        (DATA_EXPORT, 'Export de données'),
        (DATA_INGESTION, 'Ingestion de données'),
        (ADMIN_CONFIG, 'Configuration admin'),
        (PIPELINE_MANAGE, 'Gestion pipelines'),
        (API_CONSUME, 'Consommation API'),
        (AUDIT_VIEW, 'Visualisation audit'),
    ]
    
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'users_permission'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.category} - {self.name}"


class RolePermission(models.Model):
    """
    Table de liaison Many-to-Many entre Roles et Permissions
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_role_permission'
        unique_together = ['role', 'permission']
    
    def __str__(self):
        return f"{self.role.code} → {self.permission.code}"


class User(AbstractUser):
    """
    Modèle utilisateur étendu avec support RBAC et MFA
    """
    # Informations complémentaires
    organization = models.CharField(max_length=200, blank=True, help_text="Organisation de l'utilisateur")
    phone = models.CharField(max_length=20, blank=True)
    
    # Rôle principal
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Multi-Factor Authentication (MFA)
    mfa_enabled = models.BooleanField(default=False, help_text="MFA activé")
    mfa_secret = models.CharField(max_length=32, blank=True, help_text="Secret TOTP pour MFA")
    mfa_backup_codes = models.JSONField(default=list, blank=True, help_text="Codes de secours MFA")
    
    # Token API (pour les clients API)
    api_token = models.CharField(max_length=64, blank=True, unique=True, null=True)
    api_token_created_at = models.DateTimeField(null=True, blank=True)
    api_rate_limit = models.IntegerField(default=1000, help_text="Requêtes API par heure")
    
    # Métadonnées
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_user'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_role_display(self):
        """Retourne le nom du rôle ou 'Aucun rôle'"""
        return self.role.name if self.role else "Aucun rôle"
    
    def has_permission(self, permission_code):
        """Vérifie si l'utilisateur a une permission spécifique"""
        if not self.role:
            return False
        return self.role.role_permissions.filter(permission__code=permission_code).exists()
    
    def get_permissions(self):
        """Retourne toutes les permissions de l'utilisateur"""
        if not self.role:
            return Permission.objects.none()
        return Permission.objects.filter(permission_roles__role=self.role)
    
    def generate_api_token(self):
        """Génère un nouveau token API"""
        self.api_token = secrets.token_urlsafe(48)
        self.api_token_created_at = timezone.now()
        self.save()
        return self.api_token
    
    def regenerate_mfa_secret(self):
        """Génère un nouveau secret MFA (TOTP)"""
        import pyotp
        self.mfa_secret = pyotp.random_base32()
        self.save()
        return self.mfa_secret
    
    def verify_mfa_token(self, token):
        """Vérifie un code MFA"""
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        import pyotp
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token, valid_window=1)
    
    def is_account_locked(self):
        """Vérifie si le compte est verrouillé"""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """Verrouille le compte temporairement"""
        from datetime import timedelta
        self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save()


class AuditLog(models.Model):
    """
    Journal d'audit pour toutes les actions importantes
    """
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_DATA_ACCESS = 'data_access'
    ACTION_DATA_EXPORT = 'data_export'
    ACTION_DATA_INGESTION = 'data_ingestion'
    ACTION_CONFIG_CHANGE = 'config_change'
    ACTION_PIPELINE_RUN = 'pipeline_run'
    ACTION_API_CALL = 'api_call'
    ACTION_PERMISSION_CHANGE = 'permission_change'
    
    ACTION_CHOICES = [
        (ACTION_LOGIN, 'Connexion'),
        (ACTION_LOGOUT, 'Déconnexion'),
        (ACTION_DATA_ACCESS, 'Accès aux données'),
        (ACTION_DATA_EXPORT, 'Export de données'),
        (ACTION_DATA_INGESTION, 'Ingestion de données'),
        (ACTION_CONFIG_CHANGE, 'Modification configuration'),
        (ACTION_PIPELINE_RUN, 'Exécution pipeline'),
        (ACTION_API_CALL, 'Appel API'),
        (ACTION_PERMISSION_CHANGE, 'Modification permissions'),
    ]
    
    LEVEL_INFO = 'info'
    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'
    LEVEL_CRITICAL = 'critical'
    
    LEVEL_CHOICES = [
        (LEVEL_INFO, 'Info'),
        (LEVEL_WARNING, 'Avertissement'),
        (LEVEL_ERROR, 'Erreur'),
        (LEVEL_CRITICAL, 'Critique'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=LEVEL_INFO)
    resource = models.CharField(max_length=200, blank=True, help_text="Ressource affectée (ex: source, indicateur)")
    details = models.JSONField(default=dict, blank=True, help_text="Détails supplémentaires")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'users_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'user']),
            models.Index(fields=['action', 'level']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else "Système"
        return f"{self.timestamp} - {user_str} - {self.get_action_display()}"


class DataSourceAccess(models.Model):
    """
    Contrôle d'accès granulaire par source de données
    Permet de restreindre l'accès à certaines sources (BRVM, WorldBank, etc.)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='source_access')
    source = models.CharField(max_length=50, choices=[
        ('BRVM', 'BRVM'),
        ('WorldBank', 'Banque Mondiale'),
        ('IMF', 'FMI'),
        ('UN_SDG', 'ONU - ODD'),
        ('AfDB', 'BAD'),
    ])
    can_read = models.BooleanField(default=True)
    can_export = models.BooleanField(default=False)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_access')
    
    class Meta:
        db_table = 'users_data_source_access'
        unique_together = ['user', 'source']
    
    def __str__(self):
        return f"{self.user.username} → {self.source}"
