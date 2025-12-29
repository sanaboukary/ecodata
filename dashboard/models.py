from django.db import models
from django.conf import settings
from django.utils import timezone


class Alert(models.Model):
    """Modèle pour les alertes configurables"""
    
    ALERT_TYPES = [
        ('brvm_variation', 'Variation BRVM'),
        ('debt_gdp_ratio', 'Ratio Dette/PIB'),
        ('inflation_rate', 'Taux d\'Inflation'),
        ('gdp_growth', 'Croissance PIB'),
        ('custom', 'Personnalisé'),
    ]
    
    CONDITION_TYPES = [
        ('greater_than', 'Supérieur à'),
        ('less_than', 'Inférieur à'),
        ('equal_to', 'Égal à'),
        ('between', 'Entre'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('triggered', 'Déclenchée'),
    ]
    
    # Utilisateur (optionnel pour alertes globales)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    # Configuration de l'alerte
    name = models.CharField(max_length=200, help_text="Nom de l'alerte")
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    description = models.TextField(blank=True)
    
    # Paramètres de la condition
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES, default='greater_than')
    threshold_value = models.FloatField(help_text="Valeur seuil")
    threshold_value_max = models.FloatField(null=True, blank=True, help_text="Valeur seuil max (pour 'between')")
    
    # Filtres spécifiques
    country_code = models.CharField(max_length=3, blank=True, help_text="Code pays (ex: CIV, BEN)")
    stock_symbol = models.CharField(max_length=20, blank=True, help_text="Symbole action BRVM")
    indicator_code = models.CharField(max_length=100, blank=True, help_text="Code indicateur")
    
    # État et notifications
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notify_email = models.BooleanField(default=True)
    notify_dashboard = models.BooleanField(default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_alert_type_display()})"
    
    def check_condition(self, current_value):
        """Vérifie si la condition de l'alerte est remplie"""
        if self.condition_type == 'greater_than':
            return current_value > self.threshold_value
        elif self.condition_type == 'less_than':
            return current_value < self.threshold_value
        elif self.condition_type == 'equal_to':
            return abs(current_value - self.threshold_value) < 0.01
        elif self.condition_type == 'between':
            if self.threshold_value_max:
                return self.threshold_value <= current_value <= self.threshold_value_max
        return False


class AlertNotification(models.Model):
    """Historique des notifications d'alertes"""
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='notifications')
    triggered_at = models.DateTimeField(default=timezone.now)
    current_value = models.FloatField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.alert.name} - {self.triggered_at.strftime('%Y-%m-%d %H:%M')}"


class UserPreference(models.Model):
    """Préférences utilisateur pour dashboard personnalisable"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    dashboard_layout = models.JSONField(default=dict, help_text="Configuration widgets dashboard")
    favorite_countries = models.JSONField(default=list, help_text="Codes pays favoris")
    favorite_indicators = models.JSONField(default=list, help_text="Codes indicateurs favoris")
    favorite_stocks = models.JSONField(default=list, help_text="Symboles actions BRVM favoris")
    theme = models.CharField(max_length=20, default='dark', choices=[('light', 'Clair'), ('dark', 'Sombre')])
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Préférence Utilisateur"
        verbose_name_plural = "Préférences Utilisateurs"
    
    def __str__(self):
        return f"Préférences de {self.user.username}"
