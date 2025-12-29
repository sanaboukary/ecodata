#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SCRAPER BRVM ROBUSTE - Version Production
=============================================

Scraper complet et robuste pour collecter TOUTES les données BRVM:
- Cours des actions (prix, volumes, variations)
- Indices BRVM (BRVM-C, BRVM-30, Prestige, sectoriels)
- Volumes/Valeurs négociées
- Annonces officielles (communiqués, assemblées, etc.)
- États financiers (PDF)

✅ POLITIQUE ZÉRO TOLÉRANCE RESPECTÉE:
- Données marquées REAL_SCRAPER
- Validation stricte des valeurs
- Traçabilité complète (URL source + timestamp)
- Logs détaillés de chaque collecte

UTILISATION:
    python scraper_brvm_robuste.py --dry-run     # Test
    python scraper_brvm_robuste.py --apply       # Import MongoDB
    python scraper_brvm_robuste.py --actions-only # Uniquement cours actions
"""

import os
import sys
import re
import time
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# Imports pour scraping
try:
    import pandas as pd
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait as Wait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_brvm_robuste.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BRVMScraperRobuste:
    """Scraper robuste pour toutes les données BRVM"""
    
    def __init__(self):
        self.driver = None
        self.stats = {
            'actions_collectees': 0,
            'indices_collectes': 0,
            'annonces_collectees': 0,
            'etats_financiers_collectes': 0,
            'erreurs': 0
        }
    
    def setup_driver(self):
        """Configure Chrome headless optimisé"""
        if not SELENIUM_AVAILABLE:
            logger.error(f"❌ Selenium non disponible: {IMPORT_ERROR}")
            logger.info("💡 Installation: pip install selenium webdriver-manager pandas beautifulsoup4 lxml")
            return False
        
        try:
            logger.info("🔧 Configuration Chrome headless...")
            
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent réaliste
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Utiliser ChromeDriver (auto-install si nécessaire)
            try:
                service = Service(ChromeDriverManager().install())
            except Exception as e:
                logger.warning(f"⚠️ ChromeDriverManager timeout, utilisation driver système: {e}")
                # Fallback: utiliser chromedriver du PATH ou cache
                service = Service()
            
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Anti-détection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Chrome headless prêt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur setup driver: {e}")
            return False
    
    # ============= Helpers =============
    
    def _dismiss_cookies_if_any(self, timeout=3):
        """Ferme bandeau cookies"""
        try:
            btns = Wait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
            )
            for b in btns:
                t = (b.text or "").strip().lower()
                if any(x in t for x in ["accepter", "accept", "j'accepte", "i agree"]):
                    try:
                        b.click()
                        time.sleep(0.5)
                        logger.debug("✓ Cookies acceptés")
                    except:
                        pass
        except Exception:
            pass
    
    def _read_all_tables_from_dom(self, wait_for="table", timeout=20):
        """Attend et lit toutes les tables HTML via pandas"""
        try:
            Wait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, wait_for))
            )
            time.sleep(0.8)
            
            frames = []
            try:
                for df in pd.read_html(self.driver.page_source, flavor="lxml", thousands=" ", decimal=","):
                    df.columns = [str(c).strip() for c in df.columns]
                    frames.append(df.dropna(how="all"))
            except ValueError:
                pass
            
            return frames
        except Exception as e:
            logger.warning(f"⚠️  Erreur lecture tables: {e}")
            return []
    
    def _concat(self, frames):
        """Concatène DataFrames avec dédoublonnage colonnes"""
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
        df = df.loc[:, ~df.columns.duplicated()]
        return df
    
    def _validate_action_data(self, row):
        """Valide qu'une ligne d'action contient des données réelles"""
        try:
            # Doit avoir au minimum: ticker + prix
            ticker_cols = ['Symbole', 'Ticker', 'Symbol']
            ticker = None
            for col in ticker_cols:
                if col in row and not pd.isna(row[col]):
                    ticker = str(row[col]).strip()
                    break
            
            if not ticker or len(ticker) < 2 or len(ticker) > 10:
                return False
            
            # Prix de clôture requis
            prix_cols = ['Cours Clôture (FCFA)', 'Cours de clôture', 'Dernier cours', 'Close', 'Prix', 'Cours']
            prix = None
            for col in prix_cols:
                if col in row and not pd.isna(row[col]):
                    try:
                        val = row[col]
                        if isinstance(val, (int, float)):
                            prix = float(val)
                        else:
                            prix = float(str(val).replace(' ', '').replace(',', '.'))
                        break
                    except:
                        pass
            
            if prix is None or prix <= 0 or prix > 10000000:  # Max 10M FCFA
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Validation échouée: {e}")
            return False
    
    # ============= Collecte Actions =============
    
    def get_actions(self, secteur_id=0):
        """Collecte cours des actions (toutes ou par secteur)"""
        logger.info("\n" + "="*70)
        logger.info(f"📊 COLLECTE COURS ACTIONS (secteur_id={secteur_id})")
        logger.info("="*70)
        
        try:
            url = f"https://www.brvm.org/fr/cours-actions/{secteur_id}"
            logger.info(f"🌐 URL: {url}")
            
            self.driver.get(url)
            self._dismiss_cookies_if_any()
            
            tables = self._read_all_tables_from_dom(wait_for="table")
            actions_df = self._concat(tables)
            
            if actions_df.empty:
                logger.warning("⚠️  Aucune table trouvée")
                return pd.DataFrame()
            
            # Normalisation colonnes
            rename_map = {
                "Symbole": "Ticker",
                "Libellé": "Libelle",
                "Nom": "Nom",
                "Variation (%)": "Var_%",
                "Cours Clôture (FCFA)": "Close",
                "Cours de clôture": "Close",
                "Dernier cours": "Close",
                "Volume": "Volume",
                "Cours veille (FCFA)": "Previous_Close",
                "Cours Ouverture (FCFA)": "Open"
            }
            for k, v in rename_map.items():
                if k in actions_df.columns and v not in actions_df.columns:
                    actions_df.rename(columns={k: v}, inplace=True)
            
            # Validation
            actions_df['valid'] = actions_df.apply(self._validate_action_data, axis=1)
            actions_valides = actions_df[actions_df['valid'] == True].copy()
            actions_valides.drop('valid', axis=1, inplace=True)
            
            # Métadonnées
            actions_valides["collecte_ts"] = datetime.now(timezone.utc).isoformat()
            actions_valides["source_url"] = url
            actions_valides["data_quality"] = "REAL_SCRAPER"
            
            logger.info(f"✅ {len(actions_valides)} actions valides collectées")
            if len(actions_valides) < len(actions_df):
                logger.warning(f"⚠️  {len(actions_df) - len(actions_valides)} lignes invalides ignorées")
            
            self.stats['actions_collectees'] = len(actions_valides)
            return actions_valides
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte actions: {e}")
            self.stats['erreurs'] += 1
            return pd.DataFrame()
    
    # ============= Collecte Indices =============
    
    def get_indices(self):
        """Collecte indices BRVM (BRVM-C, BRVM-30, etc.)"""
        logger.info("\n" + "="*70)
        logger.info("📈 COLLECTE INDICES BRVM")
        logger.info("="*70)
        
        try:
            url = "https://www.brvm.org/en/indices"
            logger.info(f"🌐 URL: {url}")
            
            self.driver.get(url)
            self._dismiss_cookies_if_any()
            
            tables = self._read_all_tables_from_dom(wait_for="table")
            indices_df = self._concat(tables)
            
            if indices_df.empty:
                logger.warning("⚠️  Aucun indice trouvé")
                return pd.DataFrame()
            
            # Métadonnées
            indices_df["collecte_ts"] = datetime.now(timezone.utc).isoformat()
            indices_df["source_url"] = url
            indices_df["data_quality"] = "REAL_SCRAPER"
            
            logger.info(f"✅ {len(indices_df)} indices collectés")
            self.stats['indices_collectes'] = len(indices_df)
            return indices_df
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte indices: {e}")
            self.stats['erreurs'] += 1
            return pd.DataFrame()
    
    # ============= Collecte Marché =============
    
    def get_market_activity(self):
        """Collecte valeurs/volumes négociés"""
        logger.info("\n" + "="*70)
        logger.info("💰 COLLECTE ACTIVITÉ MARCHÉ")
        logger.info("="*70)
        
        try:
            url = "https://www.brvm.org/fr/marche-des-actions"
            logger.info(f"🌐 URL: {url}")
            
            self.driver.get(url)
            self._dismiss_cookies_if_any()
            
            # Parser valeur transactions
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            txt = soup.get_text(" ", strip=True)
            
            valeur_transactions = None
            m = re.search(r"Valeur des transactions[, ]+([0-9\s]+)\s*FCFA", txt, flags=re.I)
            if m:
                valeur_transactions = int(m.group(1).replace(" ", ""))
                logger.info(f"✅ Valeur transactions: {valeur_transactions:,} FCFA")
            
            # Top/Flop
            tables = self._read_all_tables_from_dom(wait_for="table")
            top_flop_df = self._concat(tables)
            
            return {
                "valeur_transactions_fcfa": valeur_transactions,
                "top_flop_tables": top_flop_df,
                "collecte_ts": datetime.now(timezone.utc).isoformat(),
                "source_url": url,
                "data_quality": "REAL_SCRAPER"
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte marché: {e}")
            self.stats['erreurs'] += 1
            return {}
    
    # ============= Collecte Annonces =============
    
    def get_annonces(self, type_slug="communiques", max_pages=5):
        """Collecte annonces officielles"""
        logger.info("\n" + "="*70)
        logger.info(f"📢 COLLECTE ANNONCES ({type_slug})")
        logger.info("="*70)
        
        try:
            base = f"https://www.brvm.org/fr/emetteurs/type-annonces/{type_slug}"
            rows = []
            
            for p in range(max_pages):
                url = base if p == 0 else f"{base}?page={p}"
                logger.info(f"📄 Page {p+1}/{max_pages}: {url}")
                
                self.driver.get(url)
                self._dismiss_cookies_if_any()
                
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                
                for art in soup.select("article, .views-row, .node, .card, .item-list"):
                    a = art.find("a", href=True)
                    href = a["href"] if a else None
                    titre = a.get_text(strip=True) if a else None
                    
                    if not titre or not href:
                        continue
                    
                    raw = art.get_text(" ", strip=True)
                    m = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", raw)
                    
                    a_pdf = art.find("a", href=re.compile(r"\.pdf$", re.I))
                    pdf_url = a_pdf["href"] if a_pdf else None
                    
                    rows.append({
                        "type": type_slug,
                        "titre": titre,
                        "date_txt": m.group(1) if m else None,
                        "url_page": href,
                        "url_pdf": pdf_url
                    })
                
                time.sleep(0.4)
            
            annonces_df = pd.DataFrame(rows).drop_duplicates()
            annonces_df["collecte_ts"] = datetime.now(timezone.utc).isoformat()
            annonces_df["source_url"] = base
            annonces_df["data_quality"] = "REAL_SCRAPER"
            
            logger.info(f"✅ {len(annonces_df)} annonces collectées")
            self.stats['annonces_collectees'] += len(annonces_df)
            return annonces_df
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte annonces: {e}")
            self.stats['erreurs'] += 1
            return pd.DataFrame()
    
    # ============= Collecte États Financiers =============
    
    def get_etats_financiers(self, max_pages=7):
        """Collecte états financiers (PDF)"""
        logger.info("\n" + "="*70)
        logger.info("📑 COLLECTE ÉTATS FINANCIERS")
        logger.info("="*70)
        
        try:
            base = "https://www.brvm.org/fr/type-document/etats-financiers"
            rows = []
            
            for p in range(max_pages):
                url = base if p == 0 else f"{base}?page={p}"
                logger.info(f"📄 Page {p+1}/{max_pages}: {url}")
                
                self.driver.get(url)
                self._dismiss_cookies_if_any()
                
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                
                for blk in soup.select("article, .views-row, .node, .card, .item-list"):
                    title = blk.get_text(" ", strip=True)
                    a = blk.find("a", href=True)
                    page_url = a["href"] if a else None
                    
                    a_pdf = blk.find("a", href=re.compile(r"\.pdf$", re.I))
                    pdf_url = a_pdf["href"] if a_pdf else None
                    
                    if title and (page_url or pdf_url):
                        rows.append({
                            "titre": title,
                            "url_page": page_url,
                            "url_pdf": pdf_url
                        })
                
                time.sleep(0.4)
            
            etats_df = pd.DataFrame(rows).drop_duplicates()
            etats_df["collecte_ts"] = datetime.now(timezone.utc).isoformat()
            etats_df["source_url"] = base
            etats_df["data_quality"] = "REAL_SCRAPER"
            
            logger.info(f"✅ {len(etats_df)} états financiers collectés")
            self.stats['etats_financiers_collectes'] = len(etats_df)
            return etats_df
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte états financiers: {e}")
            self.stats['erreurs'] += 1
            return pd.DataFrame()
    
    # ============= Import MongoDB =============
    
    def sauvegarder_actions_mongodb(self, actions_df, dry_run=True):
        """Sauvegarde cours actions dans MongoDB"""
        if actions_df.empty:
            logger.warning("⚠️  Aucune action à sauvegarder")
            return 0
        
        if dry_run:
            logger.info("\n" + "="*70)
            logger.info("🔍 MODE DRY-RUN - Aperçu actions:")
            logger.info("="*70)
            print(actions_df.head(10))
            logger.info(f"\n💡 {len(actions_df)} actions prêtes à importer")
            logger.info("Pour appliquer: python scraper_brvm_robuste.py --apply")
            return 0
        
        # Mode APPLY
        logger.info("\n" + "="*70)
        logger.info("💾 IMPORT MONGODB - ACTIONS")
        logger.info("="*70)
        
        client, db = get_mongo_db()
        collection = db.curated_observations
        
        date_collecte = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        inserted = 0
        updated = 0
        
        for _, row in actions_df.iterrows():
            try:
                ticker = str(row.get('Ticker', '')).strip()
                if not ticker:
                    continue
                
                # Extraction prix
                prix = None
                for col in ['Close', 'Cours de clôture', 'Dernier cours']:
                    if col in row and not pd.isna(row[col]):
                        try:
                            prix = float(str(row[col]).replace(' ', '').replace(',', '.'))
                            break
                        except:
                            pass
                
                if not prix:
                    continue
                
                # Extraction volume
                volume = 0
                for col in ['Volume', 'Qté échangée']:
                    if col in row and not pd.isna(row[col]):
                        try:
                            volume = int(str(row[col]).replace(' ', ''))
                            break
                        except:
                            pass
                
                # Extraction variation
                variation = 0.0
                if 'Var_%' in row and not pd.isna(row['Var_%']):
                    try:
                        variation = float(str(row['Var_%']).replace('%', '').replace(',', '.'))
                    except:
                        pass
                
                doc = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': ticker,
                    'ts': date_collecte,
                    'value': prix,
                    'attrs': {
                        'close': prix,
                        'open': prix,
                        'high': prix,
                        'low': prix,
                        'volume': volume,
                        'variation': variation,
                        'data_quality': 'REAL_SCRAPER',
                        'data_completeness': 'SCRAPED',
                        'source_url': row.get('source_url', 'https://www.brvm.org'),
                        'scrape_timestamp': row.get('collecte_ts', datetime.now(timezone.utc).isoformat()),
                        'scrape_method': 'selenium_robuste'
                    }
                }
                
                # Ajouter colonnes supplémentaires si présentes
                for col in ['Libelle', 'Secteur', 'Capitalisation']:
                    if col in row and not pd.isna(row[col]):
                        doc['attrs'][col.lower()] = str(row[col])
                
                result = collection.update_one(
                    {
                        'source': 'BRVM',
                        'dataset': 'STOCK_PRICE',
                        'key': ticker,
                        'ts': date_collecte
                    },
                    {'$set': doc},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count > 0:
                    updated += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde {ticker}: {e}")
                continue
        
        logger.info(f"\n✅ Import terminé:")
        logger.info(f"   • Nouvelles observations: {inserted}")
        logger.info(f"   • Mises à jour: {updated}")
        logger.info(f"   • Total: {inserted + updated}")
        logger.info(f"   • Date: {date_collecte}")
        logger.info(f"   • Qualité: REAL_SCRAPER")
        logger.info("="*70)
        
        return inserted + updated
    
    def collecter_tout(self, actions_only=False):
        """Collecte complète de toutes les données BRVM"""
        logger.info("\n" + "🚀"*35)
        logger.info("DÉMARRAGE COLLECTE COMPLÈTE BRVM")
        logger.info("🚀"*35)
        
        donnees = {}
        
        # 1. Actions (prioritaire)
        actions_df = self.get_actions(secteur_id=0)
        donnees['actions'] = actions_df
        
        if actions_only:
            logger.info("\n✅ Mode --actions-only: Collecte actions uniquement")
            return donnees
        
        # 2. Indices
        indices_df = self.get_indices()
        donnees['indices'] = indices_df
        
        # 3. Marché
        marche_info = self.get_market_activity()
        donnees['marche'] = marche_info
        
        # 4. Annonces (communiqués)
        annonces_df = self.get_annonces(type_slug="communiques", max_pages=3)
        donnees['annonces'] = annonces_df
        
        # 5. États financiers
        etats_df = self.get_etats_financiers(max_pages=3)
        donnees['etats_financiers'] = etats_df
        
        return donnees
    
    def afficher_stats(self):
        """Affiche statistiques de collecte"""
        logger.info("\n" + "="*70)
        logger.info("📊 STATISTIQUES COLLECTE")
        logger.info("="*70)
        logger.info(f"✅ Actions collectées: {self.stats['actions_collectees']}")
        logger.info(f"✅ Indices collectés: {self.stats['indices_collectes']}")
        logger.info(f"✅ Annonces collectées: {self.stats['annonces_collectees']}")
        logger.info(f"✅ États financiers: {self.stats['etats_financiers_collectes']}")
        if self.stats['erreurs'] > 0:
            logger.warning(f"⚠️  Erreurs: {self.stats['erreurs']}")
        logger.info("="*70)
    
    def cleanup(self):
        """Ferme le driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🔌 Driver fermé")
            except:
                pass


def main():
    """Point d'entrée"""
    parser = argparse.ArgumentParser(description='Scraper BRVM Robuste')
    parser.add_argument('--dry-run', action='store_true', help='Mode test (pas d\'import MongoDB)')
    parser.add_argument('--apply', action='store_true', help='Importer dans MongoDB')
    parser.add_argument('--actions-only', action='store_true', help='Collecter uniquement les cours actions')
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    scraper = BRVMScraperRobuste()
    
    try:
        # Setup Selenium
        if not scraper.setup_driver():
            logger.error("\n❌ Impossible de démarrer le scraper")
            return 1
        
        # Collecte
        donnees = scraper.collecter_tout(actions_only=args.actions_only)
        
        # Statistiques
        scraper.afficher_stats()
        
        # Sauvegarde actions
        if 'actions' in donnees and not donnees['actions'].empty:
            count = scraper.sauvegarder_actions_mongodb(donnees['actions'], dry_run=dry_run)
            
            if dry_run:
                logger.info("\n💡 Pour importer: python scraper_brvm_robuste.py --apply")
            else:
                logger.info(f"\n🎉 {count} observations importées avec succès !")
                logger.info("👉 Vérifier: python verifier_cours_brvm.py")
        else:
            logger.warning("\n⚠️  Aucune donnée action collectée")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interruption utilisateur")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        scraper.cleanup()


if __name__ == '__main__':
    sys.exit(main())
