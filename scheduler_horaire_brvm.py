#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler de Collecte Horaire BRVM
Collecte les cours BRVM toutes les heures pendant les heures de bourse

Heures de bourse BRVM: 9h00 - 16h30 (Lundi-Vendredi)
Collecte: Toutes les heures de 9h à 16h
"""

import os
import sys
import time
import schedule
from datetime import datetime, time as dt_time

# Fix encodage Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
import subprocess
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler_horaire.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SchedulerHoraireBRVM:
    """Collecte horaire des cours BRVM pendant heures de bourse"""
    
    def __init__(self):
        self.scraper_script = "scraper_brvm_robuste.py"
        
    def est_jour_ouvrable(self):
        """Vérifie si on est un jour de bourse (Lun-Ven)"""
        jour = datetime.now().weekday()
        return jour < 5  # 0-4 = Lun-Ven
    
    def est_heure_bourse(self):
        """Vérifie si on est pendant les heures de bourse (9h-16h30)"""
        maintenant = datetime.now().time()
        debut_bourse = dt_time(9, 0)
        fin_bourse = dt_time(16, 30)
        return debut_bourse <= maintenant <= fin_bourse
    
    def collecter_cours_horaire(self):
        """Collecte les cours BRVM (appelé toutes les heures)"""
        
        # Vérifier jour ouvrable
        if not self.est_jour_ouvrable():
            logger.info("⏸️  Week-end - Pas de collecte")
            return
        
        # Vérifier heures de bourse
        if not self.est_heure_bourse():
            logger.info("⏸️  Hors heures de bourse (9h-16h30) - Pas de collecte")
            return
        
        logger.info("="*80)
        logger.info("🕐 COLLECTE HORAIRE BRVM")
        logger.info("="*80)
        logger.info(f"Heure: {datetime.now().strftime('%H:%M')}")
        
        try:
            # Lancer scraper
            result = subprocess.run(
                [sys.executable, self.scraper_script, "--actions-only", "--apply"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode == 0:
                logger.info("✅ Collecte horaire réussie")
                
                # Extraire nombre d'actions collectées
                if "actions valides collectées" in result.stdout:
                    import re
                    match = re.search(r'(\d+) actions valides collectées', result.stdout)
                    if match:
                        nb_actions = match.group(1)
                        logger.info(f"   📊 {nb_actions} actions collectées")
                
                # Vérifier qualité
                self.verifier_qualite_donnees()
                
            else:
                logger.error(f"❌ Erreur collecte: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout - Collecte trop longue (>5 min)")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    def verifier_qualite_donnees(self):
        """Vérifie la qualité des données collectées"""
        try:
            client, db = get_mongo_db()
            
            # Compter observations aujourd'hui
            aujourd_hui = datetime.now().strftime('%Y-%m-%d')
            
            count = db.curated_observations.count_documents({
                'source': 'BRVM',
                'ts': aujourd_hui,
                'attrs.data_quality': 'REAL_SCRAPER'
            })
            
            logger.info(f"   ✅ {count} observations aujourd'hui")
            
            # Vérifier prix clés
            unlc = db.curated_observations.find_one({
                'source': 'BRVM',
                'key': 'UNLC',
                'ts': aujourd_hui
            })
            
            snts = db.curated_observations.find_one({
                'source': 'BRVM',
                'key': 'SNTS',
                'ts': aujourd_hui
            })
            
            if unlc:
                logger.info(f"   📌 UNLC: {unlc['value']:.0f} FCFA")
            if snts:
                logger.info(f"   📌 SNTS: {snts['value']:.0f} FCFA")
            
            client.close()
            
        except Exception as e:
            logger.error(f"   ⚠️  Erreur vérification: {e}")
    
    def configurer_planning(self):
        """Configure le planning de collecte horaire"""
        
        logger.info("="*80)
        logger.info("⚙️  CONFIGURATION PLANNING COLLECTE HORAIRE")
        logger.info("="*80)
        logger.info("")
        logger.info("📅 Jours: Lundi-Vendredi")
        logger.info("🕐 Heures: 9h, 10h, 11h, 12h, 13h, 14h, 15h, 16h")
        logger.info("⏰ Fréquence: Toutes les heures pendant heures de bourse")
        logger.info("")
        logger.info("="*80)
        
        # Planifier collecte toutes les heures de 9h à 16h
        heures_bourse = [9, 10, 11, 12, 13, 14, 15, 16]
        
        for heure in heures_bourse:
            schedule.every().day.at(f"{heure:02d}:00").do(self.collecter_cours_horaire)
            logger.info(f"   ✅ {heure:02d}:00 - Collecte programmée")
        
        logger.info("")
        logger.info("="*80)
        logger.info("🚀 SCHEDULER HORAIRE DÉMARRÉ")
        logger.info("="*80)
        logger.info("")
        logger.info("Prochaine collecte:")
        
        # Afficher prochaine collecte
        prochain = schedule.next_run()
        if prochain:
            logger.info(f"   🕐 {prochain.strftime('%d/%m/%Y %H:%M')}")
        
        logger.info("")
        logger.info("💡 Pour arrêter: Ctrl+C")
        logger.info("")
    
    def demarrer(self):
        """Démarre le scheduler"""
        
        # Configurer planning
        self.configurer_planning()
        
        # Collecte immédiate si on est pendant heures de bourse
        if self.est_jour_ouvrable() and self.est_heure_bourse():
            logger.info("🔥 Collecte immédiate (heures de bourse actuelles)")
            self.collecter_cours_horaire()
        
        # Boucle infinie
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
                
        except KeyboardInterrupt:
            logger.info("")
            logger.info("="*80)
            logger.info("⏹️  SCHEDULER ARRÊTÉ")
            logger.info("="*80)
            logger.info("")

def main():
    """Point d'entrée"""
    scheduler = SchedulerHoraireBRVM()
    scheduler.demarrer()

if __name__ == "__main__":
    main()
