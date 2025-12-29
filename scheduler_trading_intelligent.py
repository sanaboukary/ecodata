"""
SCHEDULER INTELLIGENT - TRADING HEBDOMADAIRE AUTOMATISÉ
========================================================

Collecte quotidienne : 17h00 lun-ven (après clôture BRVM 16h30)
Analyse hebdo : Lundi 8h00 (historique semaine précédente)
Alertes : Temps réel si franchissement seuils

Politique ZERO TOLERANCE :
- Scraping → Saisie manuelle → AUCUNE collecte
- Jamais de données simulées/estimées
- Validation 100% avant analyse
"""

import schedule
import time
import os
import sys
import django
from datetime import datetime, timedelta
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from scraper_brvm_robuste import BRVMScraperRobuste
from systeme_trading_hebdo_auto import SystemeTradingHebdo
from plateforme_centralisation.mongo import get_mongo_db

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler_trading_hebdo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SchedulerTradingIntelligent:
    """Scheduler intelligent pour trading hebdomadaire"""
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
        self.dernier_succes_collecte = None
        self.dernier_succes_analyse = None
    
    # ============= COLLECTE QUOTIDIENNE =============
    
    def collecte_quotidienne_intelligente(self):
        """Collecte intelligente : Scraping → Saisie → Rien"""
        logger.info("="*70)
        logger.info("🔄 COLLECTE QUOTIDIENNE INTELLIGENTE")
        logger.info("="*70)
        
        today = datetime.now()
        
        # Vérifier si déjà collecté aujourd'hui
        count_today = self.db.curated_observations.count_documents({
            'source': 'BRVM',
            'ts': str(today.date()),
            'attrs.data_quality': 'REAL_SCRAPER'
        })
        
        if count_today >= 40:
            logger.info(f"✅ Collecte aujourd'hui déjà effectuée ({count_today}/47 actions)")
            return True
        
        # STRATÉGIE 1 : Scraping BRVM.org
        logger.info("\n📡 STRATÉGIE 1 : Scraping BRVM.org")
        try:
            scraper = BRVMScraperRobuste()
            if scraper.setup_driver():
                actions = scraper.get_actions()
                scraper.driver.quit()
                
                if not actions.empty and len(actions) >= 40:
                    # Import MongoDB
                    logger.info(f"✅ Scraping réussi : {len(actions)} actions")
                    result = scraper.sauvegarder_actions_mongodb(actions, dry_run=False)
                    
                    if result:
                        logger.info("✅ Import MongoDB réussi")
                        self.dernier_succes_collecte = datetime.now()
                        self.envoyer_notification_succes('collecte_scraping', len(actions))
                        return True
        
        except Exception as e:
            logger.warning(f"⚠️  Scraping échoué : {e}")
        
        # STRATÉGIE 2 : Saisie manuelle
        logger.info("\n✋ STRATÉGIE 2 : Saisie manuelle requise")
        logger.info("➡️  Exécuter : python mettre_a_jour_cours_brvm.py")
        logger.info("➡️  Ou : python importer_donnees_brvm_manuel.py")
        
        self.envoyer_notification_action_requise('saisie_manuelle')
        
        # STRATÉGIE 3 : AUCUNE collecte (pas d'estimation)
        logger.info("\n🛑 STRATÉGIE 3 : AUCUNE collecte")
        logger.info("Politique ZERO TOLERANCE : Pas de données simulées")
        logger.info("➡️  Système reste inactif jusqu'à données réelles")
        
        return False
    
    def verifier_qualite_collecte(self):
        """Vérifie qualité des données collectées"""
        today = str(datetime.now().date())
        
        # Compter par qualité
        stats = {
            'REAL_SCRAPER': self.db.curated_observations.count_documents({
                'source': 'BRVM', 'ts': today, 'attrs.data_quality': 'REAL_SCRAPER'
            }),
            'REAL_MANUAL': self.db.curated_observations.count_documents({
                'source': 'BRVM', 'ts': today, 'attrs.data_quality': 'REAL_MANUAL'
            }),
            'UNKNOWN': self.db.curated_observations.count_documents({
                'source': 'BRVM', 'ts': today, 'attrs.data_quality': {'$exists': False}
            })
        }
        
        total_real = stats['REAL_SCRAPER'] + stats['REAL_MANUAL']
        
        logger.info(f"\n📊 Qualité collecte {today} :")
        logger.info(f"  REAL_SCRAPER : {stats['REAL_SCRAPER']}")
        logger.info(f"  REAL_MANUAL  : {stats['REAL_MANUAL']}")
        logger.info(f"  UNKNOWN      : {stats['UNKNOWN']}")
        logger.info(f"  TOTAL RÉEL   : {total_real}/47")
        
        if stats['UNKNOWN'] > 0:
            logger.warning(f"⚠️  {stats['UNKNOWN']} observations de qualité inconnue détectées")
        
        return total_real >= 40  # 85% minimum
    
    # ============= ANALYSE HEBDOMADAIRE =============
    
    def analyse_hebdomadaire(self):
        """Analyse technique complète chaque lundi"""
        logger.info("="*70)
        logger.info("📈 ANALYSE HEBDOMADAIRE")
        logger.info("="*70)
        
        # Vérifier si c'est lundi
        if datetime.now().weekday() != 0:
            logger.info("⏭️  Analyse uniquement le lundi")
            return False
        
        # Vérifier si déjà analysé cette semaine
        today = datetime.now().date()
        if self.dernier_succes_analyse:
            if (today - self.dernier_succes_analyse.date()).days < 7:
                logger.info("✅ Analyse hebdo déjà effectuée cette semaine")
                return True
        
        # Lancer analyse complète
        try:
            systeme = SystemeTradingHebdo()
            success = systeme.executer_analyse_complete()
            
            if success:
                self.dernier_succes_analyse = datetime.now()
                
                # Statistiques recommandations
                recs = systeme.recommandations
                count_buy = len([r for r in recs if r['recommandation'] == 'BUY'])
                count_sell = len([r for r in recs if r['recommandation'] == 'SELL'])
                count_hold = len([r for r in recs if r['recommandation'] == 'HOLD'])
                
                logger.info(f"\n✅ Analyse terminée :")
                logger.info(f"  BUY  : {count_buy}")
                logger.info(f"  HOLD : {count_hold}")
                logger.info(f"  SELL : {count_sell}")
                
                self.envoyer_notification_succes('analyse_hebdo', len(recs))
                return True
            else:
                logger.error("❌ Analyse échouée")
                self.envoyer_notification_erreur('analyse_hebdo')
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur analyse : {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ============= ALERTES & NOTIFICATIONS =============
    
    def envoyer_notification_succes(self, type_operation, count):
        """Enregistre succès dans MongoDB"""
        self.db.scheduler_logs.insert_one({
            'type': type_operation,
            'status': 'success',
            'count': count,
            'timestamp': datetime.now(),
            'message': f"{type_operation} réussie : {count} éléments"
        })
    
    def envoyer_notification_action_requise(self, action):
        """Enregistre action manuelle requise"""
        self.db.scheduler_logs.insert_one({
            'type': 'action_requise',
            'action': action,
            'timestamp': datetime.now(),
            'message': f"Action manuelle requise : {action}"
        })
    
    def envoyer_notification_erreur(self, operation):
        """Enregistre erreur"""
        self.db.scheduler_logs.insert_one({
            'type': 'error',
            'operation': operation,
            'timestamp': datetime.now(),
            'message': f"Erreur lors de {operation}"
        })
    
    def verifier_alertes_prix(self):
        """Vérifie franchissement seuils prix (support/résistance)"""
        # À implémenter : alertes temps réel
        pass
    
    # ============= NETTOYAGE & MAINTENANCE =============
    
    def nettoyer_donnees_anciennes(self):
        """Supprime données > 90 jours (sauf pour backtests)"""
        logger.info("\n🧹 Nettoyage données anciennes")
        
        date_limite = datetime.now() - timedelta(days=90)
        
        result = self.db.curated_observations.delete_many({
            'source': 'BRVM',
            'ts': {'$lt': str(date_limite.date())}
        })
        
        if result.deleted_count > 0:
            logger.info(f"✅ {result.deleted_count} observations supprimées (> 90 jours)")
        else:
            logger.info("✅ Aucune donnée à supprimer")
    
    def verifier_integrite_base(self):
        """Vérifie intégrité de la base MongoDB"""
        logger.info("\n🔍 Vérification intégrité base")
        
        # Vérifier doublons
        pipeline = [
            {
                '$group': {
                    '_id': {'source': '$source', 'key': '$key', 'ts': '$ts'},
                    'count': {'$sum': 1}
                }
            },
            {'$match': {'count': {'$gt': 1}}}
        ]
        
        doublons = list(self.db.curated_observations.aggregate(pipeline))
        
        if doublons:
            logger.warning(f"⚠️  {len(doublons)} doublons détectés")
            for d in doublons[:5]:
                logger.warning(f"  {d['_id']}")
        else:
            logger.info("✅ Aucun doublon détecté")
    
    # ============= ORCHESTRATION =============
    
    def configurer_schedule(self):
        """Configure tous les jobs schedulés"""
        logger.info("⚙️  Configuration scheduler...")
        
        # Collecte quotidienne : 17h00 lun-ven
        schedule.every().monday.at("17:00").do(self.collecte_quotidienne_intelligente)
        schedule.every().tuesday.at("17:00").do(self.collecte_quotidienne_intelligente)
        schedule.every().wednesday.at("17:00").do(self.collecte_quotidienne_intelligente)
        schedule.every().thursday.at("17:00").do(self.collecte_quotidienne_intelligente)
        schedule.every().friday.at("17:00").do(self.collecte_quotidienne_intelligente)
        
        # Vérification qualité : 17h30 lun-ven
        schedule.every().monday.at("17:30").do(self.verifier_qualite_collecte)
        schedule.every().tuesday.at("17:30").do(self.verifier_qualite_collecte)
        schedule.every().wednesday.at("17:30").do(self.verifier_qualite_collecte)
        schedule.every().thursday.at("17:30").do(self.verifier_qualite_collecte)
        schedule.every().friday.at("17:30").do(self.verifier_qualite_collecte)
        
        # Analyse hebdo : Lundi 8h00
        schedule.every().monday.at("08:00").do(self.analyse_hebdomadaire)
        
        # Nettoyage : Dimanche 2h00
        schedule.every().sunday.at("02:00").do(self.nettoyer_donnees_anciennes)
        
        # Vérification intégrité : Dimanche 3h00
        schedule.every().sunday.at("03:00").do(self.verifier_integrite_base)
        
        logger.info("✅ Scheduler configuré :")
        logger.info("  - Collecte quotidienne : 17h00 lun-ven")
        logger.info("  - Analyse hebdo : Lundi 8h00")
        logger.info("  - Nettoyage : Dimanche 2h00")
    
    def demarrer(self):
        """Démarre le scheduler en boucle infinie"""
        logger.info("="*70)
        logger.info("🚀 DÉMARRAGE SCHEDULER TRADING HEBDOMADAIRE")
        logger.info("="*70)
        
        self.configurer_schedule()
        
        logger.info("\n▶️  Scheduler actif - En attente des tâches planifiées...")
        logger.info("   Ctrl+C pour arrêter\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier chaque minute
                
        except KeyboardInterrupt:
            logger.info("\n⏹️  Arrêt scheduler")
            sys.exit(0)


def main():
    """Point d'entrée"""
    scheduler = SchedulerTradingIntelligent()
    
    # Test immédiat (mode dev)
    if '--test' in sys.argv:
        logger.info("🧪 MODE TEST")
        scheduler.collecte_quotidienne_intelligente()
        scheduler.verifier_qualite_collecte()
        # scheduler.analyse_hebdomadaire()  # Décommenter pour tester
    else:
        # Mode production : scheduler continu
        scheduler.demarrer()


if __name__ == "__main__":
    main()
