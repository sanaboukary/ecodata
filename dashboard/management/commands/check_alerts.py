"""
Commande Django pour vérifier les alertes automatiquement
Usage: python manage.py check_alerts
"""
from django.core.management.base import BaseCommand
from dashboard.alert_service import alert_service


class Command(BaseCommand):
    help = 'Vérifie toutes les alertes actives et déclenche les notifications'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Démarrage de la vérification des alertes...'))
        
        triggered_alerts = alert_service.check_all_alerts()
        
        if triggered_alerts:
            self.stdout.write(self.style.WARNING(
                f'{len(triggered_alerts)} alerte(s) déclenchée(s):'
            ))
            for alert in triggered_alerts:
                self.stdout.write(f'  - {alert.name}')
        else:
            self.stdout.write(self.style.SUCCESS('Aucune alerte déclenchée'))
        
        self.stdout.write(self.style.SUCCESS('Vérification terminée'))
