#!/usr/bin/env python3
"""
🔄 COLLECTEUR BRVM HORAIRE - TOUTES LES HEURES
===============================================
✅ Collecte automatique toutes les heures
✅ Tous les attributs des 47 actions
✅ Tourne en boucle jusqu'à Ctrl+C

USAGE:
    python collecter_brvm_horaire_fixe.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time
import logging
import signal

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration logging
log_file = BASE_DIR / 'collecte_brvm_horaire.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

# Signal handler pour arrêt propre
collecteur_actif = True

def signal_handler(sig, frame):
    """Gérer Ctrl+C pour arrêt propre"""
    global collecteur_actif
    logger.info("\n\n⏸️  Arrêt demandé - Fin après la collecte en cours...")
    collecteur_actif = False

signal.signal(signal.SIGINT, signal_handler)


class CollecteurHoraire:
    """Collecteur BRVM toutes les heures"""
    
    def __init__(self):
        self.collecte_count = 0
        
    def lancer_collecte(self):
        """Lance le script de collecte complet"""
        script = BASE_DIR / 'collecter_brvm_complet_maintenant.py'
        
        if not script.exists():
            logger.error(f"❌ Script non trouvé: {script}")
            return False
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 COLLECTE #{self.collecte_count + 1} - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'='*80}\n")
        
        try:
            # Lancer le script de collecte
            import subprocess
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=300  # 5 min max
            )
            
            if result.returncode == 0:
                logger.info("✅ Collecte réussie")
                self.collecte_count += 1
                
                # Afficher dernières lignes du résultat
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines[-10:]:
                    if line.strip():
                        logger.info(f"   {line}")
                
                return True
            else:
                logger.error(f"❌ Erreur collecte (code {result.returncode})")
                if result.stderr:
                    logger.error(f"   {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout - collecte trop longue (>5min)")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return False
    
    def boucle_horaire(self):
        """Boucle principale - collecte toutes les heures"""
        logger.info("\n" + "🔄"*40)
        logger.info("DÉMARRAGE COLLECTEUR BRVM HORAIRE")
        logger.info("🔄"*40 + "\n")
        logger.info("⏱️  Intervalle: Toutes les heures (60 minutes)")
        logger.info("⏸️  Arrêt: Ctrl+C\n")
        
        global collecteur_actif
        
        while collecteur_actif:
            try:
                # Lancer collecte
                self.lancer_collecte()
                
                if not collecteur_actif:
                    break
                
                # Attendre 1 heure
                logger.info(f"\n{'='*80}")
                logger.info(f"⏱️  PAUSE 1 HEURE - Prochaine collecte à {(datetime.now().hour + 1) % 24}h")
                logger.info(f"{'='*80}\n")
                
                # Attendre par tranches de 60s pour répondre rapidement à Ctrl+C
                for i in range(60):  # 60 minutes
                    if not collecteur_actif:
                        break
                    time.sleep(60)  # 1 minute
                    
                    if (i + 1) % 10 == 0:  # Log toutes les 10 min
                        logger.info(f"⏳ {60 - (i + 1)} minutes restantes...")
                
            except KeyboardInterrupt:
                logger.info("\n⏸️  Interruption clavier détectée")
                break
            except Exception as e:
                logger.error(f"❌ Erreur boucle: {e}")
                logger.info("⏱️  Retry dans 5 minutes...")
                time.sleep(300)
        
        logger.info("\n" + "🏁"*40)
        logger.info(f"FIN - {self.collecte_count} collectes effectuées")
        logger.info("🏁"*40 + "\n")


def main():
    """Point d'entrée principal"""
    try:
        collecteur = CollecteurHoraire()
        collecteur.boucle_horaire()
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
