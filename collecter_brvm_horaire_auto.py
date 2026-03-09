#!/usr/bin/env python3
"""
🔄 COLLECTE AUTOMATIQUE BRVM - HORAIRE
Collecte les cours BRVM toutes les heures (9h-16h) tous les jours ouvrables
Source: https://www.brvm.org/fr/cours-actions/investisseurs
Politique: TOLÉRANCE ZÉRO - Données réelles uniquement
"""

import os
import sys
from pathlib import Path
from datetime import datetime, time
import re
import time as time_module
import logging

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collecte_brvm_horaire.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    logger.error("Modules requis manquants. Installer: pip install requests beautifulsoup4")
    sys.exit(1)

BRVM_URL = "https://www.brvm.org/fr/cours-actions/investisseurs"
HEURES_COLLECTE = list(range(9, 17))  # 9h à 16h

class CollecteurBRVMHoraire:
    """Collecteur automatique horaire des cours BRVM"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        })
    
    def est_jour_ouvrable(self):
        """Vérifier si aujourd'hui est un jour ouvrable (lundi-vendredi)"""
        return datetime.now().weekday() < 5  # 0=lundi, 4=vendredi
    
    def est_heure_collecte(self):
        """Vérifier si l'heure actuelle est dans la plage de collecte"""
        heure_actuelle = datetime.now().hour
        return heure_actuelle in HEURES_COLLECTE
    
    def scraper_cours_brvm(self):
        """Scraper les cours BRVM depuis le site officiel"""
        logger.info(f"🌐 Connexion à {BRVM_URL}")
        
        try:
            response = self.session.get(BRVM_URL, verify=False, timeout=30)
            response.raise_for_status()
            logger.info(f"✅ Réponse HTTP {response.status_code}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher le tableau des actions
            actions_data = []
            
            # Stratégie 1: Chercher toutes les lignes avec symbole d'action
            # Sur le site BRVM, les lignes du tableau contiennent: Symbole | Nom | Volume | Cours veille | Cours ouverture | Cours clôture | Variation
            tables = soup.find_all('table')
            logger.info(f"📊 {len(tables)} tableaux trouvés")
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Chercher l'en-tête pour identifier les colonnes
                header_row = rows[0] if rows else None
                if not header_row:
                    continue
                
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                
                # Vérifier si c'est le tableau des cours (contient "symbole", "cours", "variation")
                if not any(kw in ' '.join(headers) for kw in ['symbole', 'cours', 'variation']):
                    continue
                
                logger.info(f"✅ Tableau de cours trouvé avec {len(rows)-1} lignes")
                
                # Parser les lignes de données (skip header)
                for row in rows[1:]:
                    cells = row.find_all('td')
                    if len(cells) < 6:
                        continue
                    
                    try:
                        # Format attendu: Symbole | Nom | Volume | Cours veille | Cours ouverture | Cours clôture | Variation
                        symbole = cells[0].get_text(strip=True).upper()
                        nom = cells[1].get_text(strip=True)
                        volume_text = cells[2].get_text(strip=True).replace(' ', '').replace(',', '')
                        cours_cloture_text = cells[5].get_text(strip=True).replace(' ', '').replace(',', '')
                        variation_text = cells[6].get_text(strip=True) if len(cells) > 6 else '0'
                        
                        # Nettoyer et convertir
                        if not symbole or len(symbole) < 3:
                            continue
                        
                        cours_cloture = float(cours_cloture_text) if cours_cloture_text else 0
                        if cours_cloture <= 0:
                            continue
                        
                        volume = int(volume_text) if volume_text and volume_text.isdigit() else 0
                        
                        # Extraire variation (peut être "+1,83%" ou "-0,49%")
                        variation = 0.0
                        if variation_text:
                            var_clean = re.sub(r'[^\d,.\-+]', '', variation_text)
                            var_clean = var_clean.replace(',', '.')
                            try:
                                variation = float(var_clean)
                            except:
                                pass
                        
                        actions_data.append({
                            'symbole': symbole,
                            'nom': nom,
                            'cours_cloture': cours_cloture,
                            'volume': volume,
                            'variation': variation
                        })
                        
                    except Exception as e:
                        logger.debug(f"Erreur parsing ligne: {e}")
                        continue
                
                if actions_data:
                    break  # On a trouvé le bon tableau
            
            if not actions_data:
                logger.warning("⚠️  Aucune donnée extraite du site BRVM")
                # Sauvegarder HTML pour debug
                debug_file = f'brvm_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"📄 HTML sauvegardé: {debug_file}")
                return []
            
            logger.info(f"✅ {len(actions_data)} actions extraites")
            return actions_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def sauvegarder_en_mongodb(self, actions_data):
        """Sauvegarder les cours dans MongoDB"""
        if not actions_data:
            logger.warning("⚠️  Aucune donnée à sauvegarder")
            return 0
        
        date_heure = datetime.now()
        date_str = date_heure.strftime('%Y-%m-%d')
        heure_str = date_heure.strftime('%H:%M:%S')
        
        logger.info(f"💾 Sauvegarde de {len(actions_data)} cours - {date_str} {heure_str}")
        
        inserted = 0
        updated = 0
        
        for action in actions_data:
            try:
                observation = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': action['symbole'],
                    'ts': date_str,
                    'value': action['cours_cloture'],
                    'attrs': {
                        'symbole': action['symbole'],
                        'nom': action['nom'],
                        'cours_cloture': action['cours_cloture'],
                        'volume': action['volume'],
                        'variation': action['variation'],
                        'data_quality': 'REAL_SCRAPER',
                        'source_url': BRVM_URL,
                        'collecte_datetime': date_heure.isoformat(),
                        'collecte_heure': heure_str,
                    }
                }
                
                result = self.db.curated_observations.update_one(
                    {
                        'source': 'BRVM',
                        'dataset': 'STOCK_PRICE',
                        'key': action['symbole'],
                        'ts': date_str
                    },
                    {'$set': observation},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count > 0:
                    updated += 1
                    
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde {action['symbole']}: {e}")
        
        logger.info(f"✅ Sauvegarde terminée: {inserted} nouvelles, {updated} mises à jour")
        
        # Log dans ingestion_runs
        self.log_ingestion_run(len(actions_data), inserted + updated)
        
        return inserted + updated
    
    def log_ingestion_run(self, obs_count, success_count):
        """Logger l'exécution dans ingestion_runs"""
        try:
            run_doc = {
                'source': 'BRVM',
                'run_datetime': datetime.now().isoformat(),
                'status': 'SUCCESS' if success_count > 0 else 'PARTIAL',
                'obs_count': obs_count,
                'duration_seconds': 0,
                'error_msg': None if success_count > 0 else 'Aucune donnée collectée'
            }
            self.db.ingestion_runs.insert_one(run_doc)
        except Exception as e:
            logger.error(f"❌ Erreur log ingestion: {e}")
    
    def collecter_maintenant(self):
        """Collecter les cours maintenant"""
        logger.info("=" * 100)
        logger.info("🔄 COLLECTE BRVM AUTOMATIQUE")
        logger.info("=" * 100)
        logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🌐 URL: {BRVM_URL}")
        logger.info(f"🎯 Politique: TOLÉRANCE ZÉRO - Données réelles uniquement")
        logger.info("=" * 100)
        
        # Vérifier si c'est un jour ouvrable
        if not self.est_jour_ouvrable():
            logger.info("⏭️  Week-end détecté - Pas de collecte")
            return
        
        # Scraper
        actions_data = self.scraper_cours_brvm()
        
        if actions_data:
            # Afficher aperçu
            logger.info(f"\n📊 APERÇU DES COURS COLLECTÉS:")
            logger.info(f"{'SYMBOLE':<8} {'NOM':<40} {'COURS':>12} {'VARIATION':>10}")
            logger.info(f"{'-'*8} {'-'*40} {'-'*12} {'-'*10}")
            
            for action in sorted(actions_data, key=lambda x: x['symbole'])[:10]:
                var_icon = "🟢" if action['variation'] > 0 else ("🔴" if action['variation'] < 0 else "⚪")
                logger.info(f"{action['symbole']:<8} {action['nom'][:40]:<40} {action['cours_cloture']:>12,.0f} {var_icon} {action['variation']:>8.2f}%")
            
            if len(actions_data) > 10:
                logger.info(f"... et {len(actions_data) - 10} autres actions")
            
            # Sauvegarder
            count = self.sauvegarder_en_mongodb(actions_data)
            
            logger.info("=" * 100)
            logger.info(f"✅ COLLECTE RÉUSSIE - {count} cours mis à jour")
            logger.info("=" * 100)
        else:
            logger.error("❌ ÉCHEC DE LA COLLECTE")
            logger.info("💡 Vérifier la connectivité et la structure du site BRVM")

def main():
    """Point d'entrée principal"""
    collecteur = CollecteurBRVMHoraire()
    collecteur.collecter_maintenant()

if __name__ == '__main__':
    main()
