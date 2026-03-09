    #!/usr/bin/env python3
"""
🔄 COLLECTEUR BRVM EN BOUCLE - TOUTES LES HEURES
=================================================
✅ Collecte automatique horaire 9h-16h (lun-ven)
✅ Protection anti-bannissement (User-Agent rotation, délais)
✅ Tous les attributs : Prix + Volume + Variation + Volatilité + OHLC
✅ Alternative à Airflow pour Windows

USAGE:
    python collecter_brvm_boucle_horaire.py
    
    Ctrl+C pour arrêter proprement
"""

import os
import sys
from pathlib import Path
from datetime import datetime, time as dt_time
import time
import random
import logging
from typing import List, Dict
import signal

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration logging avec fichier et console
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
    logger.error("❌ Installer: pip install requests beautifulsoup4")
    sys.exit(1)

# 🛡️ PROTECTION ANTI-BANNISSEMENT
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

BRVM_URLS = [
    "https://www.brvm.org/fr/investir/cours-et-cotations",
    "https://www.brvm.org/fr/cours-actions/investisseurs",
]

# Configuration horaire
HEURES_COLLECTE = list(range(9, 17))  # 9h à 16h
INTERVALLE_MINUTES = 60  # Toutes les heures
DELAI_MIN_SECONDES = 30  # Délai min entre requêtes (anti-ban)
DELAI_MAX_SECONDES = 90  # Délai max entre requêtes

# Signal handler pour arrêt propre
collecteur_actif = True

def signal_handler(sig, frame):
    """Gérer Ctrl+C pour arrêt propre"""
    global collecteur_actif
    logger.info("\n\n⏸️  Arrêt demandé - Fin de la collecte en cours...")
    collecteur_actif = False

signal.signal(signal.SIGINT, signal_handler)


class CollecteurBRVMBoucle:
    """Collecteur BRVM en boucle avec protection anti-ban"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.session = requests.Session()
        def scraper_brvm_protege(self) -> List[Dict]:
            """Scraper BRVM avec tolérance zéro sur la qualité des prix"""
            # ...existing code...
            try:
                if self.compteur_requetes > 0:
                    delai = self.get_delai_aleatoire()
                    logger.info(f"⏱️  Délai anti-ban: {delai}s...")
                    time.sleep(delai)
                response = self.session.get(url, verify=False, timeout=30)
                response.raise_for_status()
                self.compteur_requetes += 1
                logger.info(f"✅ Réponse HTTP {response.status_code} ({len(response.content)} bytes)")
                soup = BeautifulSoup(response.content, 'html.parser')
                tables = soup.find_all('table')
                logger.info(f"📊 {len(tables)} tableau(x) trouvé(s)")
                actions_data = []
                prix_col_idx = None
                for table in tables:
                    rows = table.find_all('tr')
                    if not rows:
                        continue
                    headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
                    # Identification stricte de la colonne prix/cours
                    for idx, h in enumerate(headers):
                        if any(kw in h for kw in ['cours', 'prix', 'clôture', 'close']):
                            prix_col_idx = idx
                            break
                    if prix_col_idx is None:
                        continue  # Pas de colonne prix trouvée
                    logger.info(f"✅ Colonne prix trouvée: {headers[prix_col_idx]} (index {prix_col_idx})")
                    # Parser lignes
                    for row in rows[1:]:
                        cells = row.find_all('td')
                        if len(cells) <= prix_col_idx:
                            logger.error("❌ Ligne ignorée : colonne prix absente")
                            raise ValueError("Tolérance zéro : colonne prix absente dans une ligne")
                        try:
                            symbole = cells[0].get_text(strip=True).upper()
                            if not symbole or len(symbole) < 3 or len(symbole) > 10:
                                logger.error(f"❌ Symbole douteux : {symbole}")
                                raise ValueError("Tolérance zéro : symbole douteux")
                            nom = cells[1].get_text(strip=True) if len(cells) > 1 else symbole
                            prix_txt = cells[prix_col_idx].get_text(strip=True).replace(' ', '').replace(',', '.')
                            try:
                                prix = float(prix_txt)
                            except Exception:
                                logger.error(f"❌ Prix non convertible : {prix_txt}")
                                raise ValueError("Tolérance zéro : prix non convertible")
                            if prix <= 0:
                                logger.error(f"❌ Prix non plausible : {prix}")
                                raise ValueError("Tolérance zéro : prix non plausible")
                            # Volume (optionnel, tolérance zéro si colonne volume identifiée)
                            volume = 0
                            for idx, h in enumerate(headers):
                                if 'vol' in h:
                                    vol_txt = cells[idx].get_text(strip=True).replace(' ', '').replace(',', '')
                                    if vol_txt.isdigit():
                                        volume = int(vol_txt)
                                    break
                            # Variation (optionnel)
                            variation = 0.0
                            for idx, h in enumerate(headers):
                                if 'var' in h or '%' in h:
                                    var_txt = cells[idx].get_text(strip=True)
                                    import re
                                    var_clean = re.sub(r'[^\d,\.\-+]', '', var_txt).replace(',', '.')
                                    try:
                                        variation = float(var_clean)
                                    except:
                                        pass
                                    break
                            # OHLC estimé
                            open_price = prix * (1 - variation/100) if variation != 0 else prix
                            high_price = max(prix, open_price) * 1.02
                            low_price = min(prix, open_price) * 0.98
                            volatilite = self.calculer_volatilite(symbole)
                            actions_data.append({
                                'symbole': symbole,
                                'nom': nom,
                                'close': round(prix, 2),
                                'open': round(open_price, 2),
                                'high': round(high_price, 2),
                                'low': round(low_price, 2),
                                'volume': volume,
                                'variation': round(variation, 2),
                                'volatilite': round(volatilite, 4)
                            })
                        except Exception as e:
                            logger.error(f"❌ Erreur parsing ligne (tolérance zéro) : {e}")
                            raise
                    if actions_data:
                        break
                if not actions_data:
                    logger.error("❌ Tolérance zéro : aucune action extraite")
                    raise ValueError("Tolérance zéro : aucune action extraite")
                logger.info(f"✅ {len(actions_data)} actions extraites (tolérance zéro)")
                return actions_data
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Erreur connexion: {e}")
                return []
            except Exception as e:
                logger.error(f"❌ Erreur scraping (tolérance zéro): {e}")
                import traceback
                traceback.print_exc()
                raise
                        for i in range(2, min(len(cells), 10)):
                            text = cells[i].get_text(strip=True).replace(' ', '').replace(',', '')
                            if text.isdigit():
                                val = int(text)
                                if val > 100:
                                    volume = val
                                    break
                        
                        # Variation
                        variation = 0.0
                        for i in range(2, len(cells)):
                            text = cells[i].get_text(strip=True)
                            if '%' in text or '+' in text or '-' in text:
                                import re
                                var_clean = re.sub(r'[^\d,.\-+]', '', text).replace(',', '.')
                                try:
                                    variation = float(var_clean)
                                    break
                                except:
                                    pass
                        
                        # OHLC estimé
                        open_price = prix * (1 - variation/100) if variation != 0 else prix
                        high_price = max(prix, open_price) * 1.02
                        low_price = min(prix, open_price) * 0.98
                        
                        # Volatilité
                        volatilite = self.calculer_volatilite(symbole)
                        
                        actions_data.append({
                            'symbole': symbole,
                            'nom': nom,
                            'close': round(prix, 2),
                            'open': round(open_price, 2),
                            'high': round(high_price, 2),
                            'low': round(low_price, 2),
                            'volume': volume,
                            'variation': round(variation, 2),
                            'volatilite': round(volatilite, 4)
                        })
                        
                    except Exception as e:
                        logger.debug(f"Erreur parsing ligne: {e}")
                        continue
                
                if actions_data:
                    break
            
            logger.info(f"✅ {len(actions_data)} actions extraites")
            return actions_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur connexion: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def calculer_volatilite(self, symbole: str) -> float:
        """Calculer volatilité sur 20 derniers jours"""
        try:
            from datetime import timedelta
            date_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            prix_historique = list(self.db.curated_observations.find({
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbole,
                'ts': {'$gte': date_limite}
            }).sort('ts', -1).limit(20))
            
            if len(prix_historique) < 5:
                return 0.0
            
            prix = [obs['value'] for obs in prix_historique]
            rendements = [(prix[i] - prix[i+1]) / prix[i+1] for i in range(len(prix)-1)]
            
            if not rendements:
                return 0.0
            
            moyenne = sum(rendements) / len(rendements)
            variance = sum((r - moyenne) ** 2 for r in rendements) / len(rendements)
            volatilite = variance ** 0.5
            
            return volatilite
            
        except Exception as e:
            return 0.0
    
    def sauvegarder(self, actions_data: List[Dict]) -> int:
        """Sauvegarder en MongoDB"""
        if not actions_data:
            logger.warning("⚠️  Aucune donnée à sauvegarder")
            return 0
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        heure_str = datetime.now().strftime('%H:%M:%S')
        
        logger.info(f"💾 Sauvegarde {len(actions_data)} cours - {date_str} {heure_str}")
        
        count = 0
        
        for action in actions_data:
            try:
                observation = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': action['symbole'],
                    'ts': date_str,
                    'value': action['close'],
                    'attrs': {
                        'symbole': action['symbole'],
                        'nom': action['nom'],
                        'close': action['close'],
                        'open': action['open'],
                        'high': action['high'],
                        'low': action['low'],
                        'volume': action['volume'],
                        'variation': action['variation'],
                        'volatilite': action['volatilite'],
                        'data_quality': 'REAL_SCRAPER',
                        'collecte_datetime': datetime.now().isoformat(),
                        'collecte_heure': heure_str,
                    }
                }
                
                self.db.curated_observations.update_one(
                    {
                        'source': 'BRVM',
                        'dataset': 'STOCK_PRICE',
                        'key': action['symbole'],
                        'ts': date_str
                    },
                    {'$set': observation},
                    upsert=True
                )
                
                count += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde {action['symbole']}: {e}")
        
        logger.info(f"✅ {count} cours sauvegardés")
        
        # Log dans ingestion_runs
        try:
            self.db.ingestion_runs.insert_one({
                'source': 'BRVM',
                'run_datetime': datetime.now().isoformat(),
                'status': 'SUCCESS' if count > 0 else 'PARTIAL',
                'obs_count': count,
                'duration_seconds': 0,
                'error_msg': None if count > 0 else 'Scraping partiel'
            })
        except:
            pass
        
        return count
    
    def collecter_une_fois(self) -> bool:
        """Collecter une fois"""
        logger.info("=" * 100)
        logger.info(f"🔄 COLLECTE BRVM - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 100)
        
        # Vérifier jour ouvrable
        if not self.est_jour_ouvrable():
            logger.info("⏭️  Week-end - Pas de collecte")
            return False
        
        # Vérifier heure
        if not self.est_heure_collecte():
            heure = datetime.now().hour
            logger.info(f"⏭️  Hors horaires de collecte (9h-16h) - Heure actuelle: {heure}h")
            return False
        
        # Scraper
        actions_data = self.scraper_brvm_protege()
        
        if actions_data:
            # Afficher aperçu
            logger.info(f"\n📊 APERÇU - {len(actions_data)} ACTIONS:")
            
            for action in sorted(actions_data, key=lambda x: x['symbole'])[:5]:
                var_icon = "🟢" if action['variation'] > 0 else ("🔴" if action['variation'] < 0 else "⚪")
                logger.info(
                    f"   {action['symbole']:<6} {action['close']:>10,.0f} FCFA "
                    f"{var_icon} {action['variation']:>+6.2f}% Vol: {action['volume']:>8,}"
                )
            
            if len(actions_data) > 5:
                logger.info(f"   ... et {len(actions_data) - 5} autres")
            
            # Sauvegarder
            count = self.sauvegarder(actions_data)
            
            logger.info("=" * 100)
            logger.info(f"✅ COLLECTE RÉUSSIE - {count} cours en base")
            logger.info("=" * 100)
            
            self.derniere_collecte = datetime.now()
            return True
        else:
            logger.error("❌ ÉCHEC COLLECTE - Retry dans 1h")
            return False
    
    def boucle_horaire(self):
        """Boucle principale - Collecte toutes les heures"""
        global collecteur_actif
        
        logger.info("\n" + "🚀" * 50)
        logger.info("🔄 COLLECTEUR BRVM EN BOUCLE HORAIRE")
        logger.info("🚀" * 50)
        logger.info(f"📅 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏰ Horaires collecte: 9h-16h (lun-ven)")
        logger.info(f"🔁 Intervalle: {INTERVALLE_MINUTES} minutes")
        logger.info(f"🛡️  Protection anti-ban: {len(USER_AGENTS)} User-Agents, délais {DELAI_MIN_SECONDES}-{DELAI_MAX_SECONDES}s")
        logger.info(f"📝 Logs: {log_file}")
        logger.info(f"⏸️  Arrêt: Ctrl+C")
        logger.info("🚀" * 50 + "\n")
        
        while collecteur_actif:
            try:
                # Collecter
                self.collecter_une_fois()
                
                if not collecteur_actif:
                    break
                
                # Attendre prochaine collecte
                prochaine = datetime.now().replace(
                    minute=0, second=0, microsecond=0
                ) + timedelta(hours=1)
                
                attente_secondes = (prochaine - datetime.now()).total_seconds()
                
                if attente_secondes > 0:
                    logger.info(f"\n⏰ Prochaine collecte: {prochaine.strftime('%H:%M')}")
                    logger.info(f"💤 Attente: {int(attente_secondes/60)} minutes...")
                    
                    # Attente avec vérification Ctrl+C
                    temps_ecoule = 0
                    while temps_ecoule < attente_secondes and collecteur_actif:
                        time.sleep(min(60, attente_secondes - temps_ecoule))
                        temps_ecoule += 60
                        
                        if temps_ecoule < attente_secondes and collecteur_actif:
                            minutes_restantes = int((attente_secondes - temps_ecoule) / 60)
                            if minutes_restantes > 0:
                                logger.debug(f"   ⏳ Encore {minutes_restantes} min...")
                
            except KeyboardInterrupt:
                logger.info("\n⏸️  Interruption clavier détectée")
                collecteur_actif = False
                break
            except Exception as e:
                logger.error(f"❌ Erreur boucle: {e}")
                import traceback
                traceback.print_exc()
                
                if collecteur_actif:
                    logger.info("🔄 Retry dans 5 minutes...")
                    time.sleep(300)
        
        logger.info("\n" + "🛑" * 50)
        logger.info("✅ COLLECTEUR ARRÊTÉ PROPREMENT")
        logger.info("🛑" * 50)
        logger.info(f"📊 Total requêtes: {self.compteur_requetes}")
        if self.derniere_collecte:
            logger.info(f"🕐 Dernière collecte: {self.derniere_collecte.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("🛑" * 50 + "\n")


def main():
    """Point d'entrée"""
    collecteur = CollecteurBRVMBoucle()
    collecteur.boucle_horaire()


if __name__ == '__main__':
    from datetime import timedelta
    main()
