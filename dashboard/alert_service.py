# =====================
# Création rapide d'alerte sur action BRVM (variation de prix)
# =====================
from dashboard.models import Alert
def create_brvm_price_alert(user, stock_symbol, threshold_pct=5):
    """
    Crée une alerte sur variation de prix d'une action BRVM (ex: +5% ou -5%).
    """
    alert = Alert.objects.create(
        user=user,
        alert_type='brvm_variation',
        stock_symbol=stock_symbol,
        threshold=threshold_pct,
        status='active'
    )
    return alert
"""
Service de vérification et déclenchement des alertes
"""
from datetime import datetime, timedelta
from django.utils import timezone
from plateforme_centralisation.mongo import get_mongo_db
from dashboard.models import Alert, AlertNotification
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service pour gérer les alertes"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
    
    def check_all_alerts(self):
        """Vérifie toutes les alertes actives"""
        alerts = Alert.objects.filter(status='active')
        triggered_alerts = []
        
        for alert in alerts:
            try:
                if self._check_alert(alert):
                    triggered_alerts.append(alert)
            except Exception as e:
                logger.error(f"Erreur lors de la vérification de l'alerte {alert.id}: {e}")
        
        return triggered_alerts
    
    def _check_alert(self, alert):
        """Vérifie une alerte spécifique"""
        if alert.alert_type == 'brvm_variation':
            return self._check_brvm_variation(alert)
        elif alert.alert_type == 'debt_gdp_ratio':
            return self._check_debt_gdp_ratio(alert)
        elif alert.alert_type == 'inflation_rate':
            return self._check_inflation_rate(alert)
        elif alert.alert_type == 'gdp_growth':
            return self._check_gdp_growth(alert)
        return False
    
    def _check_brvm_variation(self, alert):
        """Vérifie la variation journalière d'une action BRVM"""
        # Récupérer les 2 dernières observations pour calculer la variation
        query = {"source": "BRVM"}
        if alert.stock_symbol:
            query["key"] = alert.stock_symbol
        
        recent_obs = list(self.db.curated_observations.find(query).sort("ts", -1).limit(2))
        
        if len(recent_obs) >= 2:
            current_price = recent_obs[0].get('value', 0)
            previous_price = recent_obs[1].get('value', 1)
            
            if previous_price > 0:
                variation_pct = ((current_price - previous_price) / previous_price) * 100
                
                if alert.check_condition(abs(variation_pct)):
                    self._trigger_alert(alert, variation_pct, 
                        f"Variation de {variation_pct:.2f}% détectée pour {alert.stock_symbol or 'BRVM'}")
                    return True
        
        return False
    
    def _check_debt_gdp_ratio(self, alert):
        """Vérifie le ratio dette/PIB"""
        query = {
            "source": "AfDB",
            "dataset": {"$regex": "debt", "$options": "i"}
        }
        if alert.country_code:
            query["key"] = {"$regex": f"^{alert.country_code}", "$options": "i"}
        
        recent_obs = list(self.db.curated_observations.find(query).sort("ts", -1).limit(1))
        
        if recent_obs:
            debt_ratio = recent_obs[0].get('value', 0)
            
            if alert.check_condition(debt_ratio):
                self._trigger_alert(alert, debt_ratio,
                    f"Ratio Dette/PIB de {debt_ratio:.1f}% atteint pour {alert.country_code or 'pays ciblé'}")
                return True
        
        return False
    
    def _check_inflation_rate(self, alert):
        """Vérifie le taux d'inflation"""
        query = {
            "source": "IMF",
            "dataset": {"$regex": "PCPI", "$options": "i"}  # Consumer Price Index
        }
        if alert.country_code:
            query["key"] = {"$regex": f"{alert.country_code}", "$options": "i"}
        
        recent_obs = list(self.db.curated_observations.find(query).sort("ts", -1).limit(2))
        
        if len(recent_obs) >= 2:
            current_cpi = recent_obs[0].get('value', 0)
            previous_cpi = recent_obs[1].get('value', 1)
            
            if previous_cpi > 0:
                inflation_rate = ((current_cpi - previous_cpi) / previous_cpi) * 100
                
                if alert.check_condition(inflation_rate):
                    self._trigger_alert(alert, inflation_rate,
                        f"Taux d'inflation de {inflation_rate:.2f}% pour {alert.country_code or 'pays ciblé'}")
                    return True
        
        return False
    
    def _check_gdp_growth(self, alert):
        """Vérifie la croissance du PIB"""
        query = {
            "source": "WorldBank",
            "dataset": "NY.GDP.MKTP.KD.ZG"  # GDP growth
        }
        if alert.country_code:
            query["key"] = {"$regex": f"^{alert.country_code}", "$options": "i"}
        
        recent_obs = list(self.db.curated_observations.find(query).sort("ts", -1).limit(1))
        
        if recent_obs:
            gdp_growth = recent_obs[0].get('value', 0)
            
            if alert.check_condition(gdp_growth):
                self._trigger_alert(alert, gdp_growth,
                    f"Croissance PIB de {gdp_growth:.2f}% pour {alert.country_code or 'pays ciblé'}")
                return True
        
        return False
    
    def _trigger_alert(self, alert, current_value, message):
        """Déclenche une alerte"""
        # Créer la notification
        notification = AlertNotification.objects.create(
            alert=alert,
            current_value=current_value,
            message=message
        )
        
        # Mettre à jour l'alerte
        alert.last_triggered = timezone.now()
        alert.trigger_count += 1
        alert.status = 'triggered'
        alert.save()
        
        logger.info(f"Alerte déclenchée: {alert.name} - {message}")
        
        # TODO: Envoyer email si alert.notify_email
        # TODO: Envoyer notification push si configuré
        
        return notification
    
    def get_unread_notifications(self, user=None):
        """Récupère les notifications non lues"""
        query = AlertNotification.objects.filter(is_read=False)
        if user:
            query = query.filter(alert__user=user)
        return query.order_by('-triggered_at')[:10]
    
    def mark_notification_read(self, notification_id):
        """Marque une notification comme lue"""
        try:
            notification = AlertNotification.objects.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return True
        except AlertNotification.DoesNotExist:
            return False


# Instance globale du service
alert_service = AlertService()
