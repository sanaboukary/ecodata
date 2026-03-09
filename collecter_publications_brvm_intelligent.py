#!/usr/bin/env python3
"""
📰 COLLECTEUR INTELLIGENT - PUBLICATIONS OFFICIELLES BRVM
=========================================================

Collecte automatique et intelligente de TOUTES les publications BRVM :
✅ Bulletins Officiels de la Cote (quotidiens)
✅ Communiqués des sociétés cotées (résultats, dividendes, AG)
✅ Rapports financiers annuels
✅ Actualités et annonces BRVM
✅ Avis de suspension/cotation

🎯 OBJECTIF : Analyse de sentiment pour trading intelligent
📊 SORTIE : MongoDB curated_observations (source='BRVM_PUBLICATION')
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import urllib3
import logging
from pathlib import Path
import sys
import hashlib
from typing import List, Dict, Optional
import json
import time

# Configuration
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire racine au path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


# 📌 CATÉGORIES DE PUBLICATIONS
CATEGORIES = {
    'BULLETIN_OFFICIEL': {
        'url': 'https://www.brvm.org/fr/bulletins-officiels-de-la-cote',
        'description': 'Bulletins quotidiens de la cote',
        'selectors': ['article', 'div.publication', 'div.bulletin', 'tr'],
        'priority': 1
    },
    'COMMUNIQUE_RESULTATS': {
        'url': 'https://www.brvm.org/fr/emetteurs/type-annonces/communiques-financiers',
        'description': 'Résultats financiers des sociétés',
        'selectors': ['article', 'div.communique', 'tr'],
        'keywords': ['résultat', 'chiffre d\'affaires', 'CA', 'bénéfice', 'perte'],
        'priority': 2
    },
    'COMMUNIQUE_DIVIDENDE': {
        'url': 'https://www.brvm.org/fr/emetteurs/type-annonces/dividendes',
        'description': 'Annonces de dividendes',
        'selectors': ['article', 'div.communique', 'tr'],
        'keywords': ['dividende', 'distribution', 'détachement'],
        'priority': 2
    },
    'COMMUNIQUE_AG': {
        'url': 'https://www.brvm.org/fr/emetteurs/type-annonces/convocations-assemblees-generales',
        'description': 'Convocations AG',
        'selectors': ['article', 'div.communique', 'tr'],
        'keywords': ['assemblée générale', 'AG', 'convocation', 'AGO', 'AGE'],
        'priority': 3
    },
    'RAPPORT_SOCIETE': {
        'url': 'https://www.brvm.org/fr/rapports-societes-cotees',
        'description': 'Rapports annuels',
        'selectors': ['article', 'div.rapport', 'tr', 'a[href$=".pdf"]'],
        'keywords': ['rapport annuel', 'rapport financier', 'états financiers'],
        'priority': 3
    },
    'ACTUALITE': {
        'url': 'https://www.brvm.org/fr/actualites',
        'description': 'Actualités BRVM',
        'selectors': ['article', 'div.actualite', 'div.news'],
        'priority': 4
    },
    'COMMUNIQUE_SUSPENSION': {
        'url': 'https://www.brvm.org/fr/emetteurs/type-annonces/suspensions',
        'description': 'Suspensions de cotation',
        'selectors': ['article', 'tr'],
        'keywords': ['suspension', 'reprise', 'cotation'],
        'priority': 2
    }
}


class BRVMPublicationCollector:
    """Collecteur intelligent de publications BRVM"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.media_dir = BASE_DIR / 'media' / 'publications'
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Connexion MongoDB
        _, self.db = get_mongo_db()
        
        self.stats = {
            'total_scraped': 0,
            'total_inserted': 0,
            'total_duplicates': 0,
            'by_category': {}
        }
    
    def scrape_category(self, category: str, config: dict) -> List[Dict]:
        """
        Scrape une catégorie de publications
        
        Stratégies intelligentes :
        1. Tester plusieurs sélecteurs CSS
        2. Parser les tableaux HTML
        3. Extraire les PDF
        4. Analyse de contenu avec keywords
        """
        logger.info(f"\n🔍 Scraping {category}: {config['url']}")
        publications = []
        
        try:
            response = self.session.get(config['url'], timeout=20, verify=False)
            
            if response.status_code != 200:
                logger.warning(f"   ❌ HTTP {response.status_code}")
                return publications
            
            logger.info(f"   ✅ Réponse reçue: {len(response.content):,} bytes")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Stratégie 1 : Liens PDF directs
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
            if pdf_links:
                logger.info(f"   📄 {len(pdf_links)} liens PDF trouvés")
                for link in pdf_links[:20]:  # Limiter à 20 plus récents
                    pub = self._extract_from_pdf_link(link, category, config['url'])
                    if pub:
                        publications.append(pub)
            
            # Stratégie 2 : Parser selon sélecteurs
            for selector in config.get('selectors', []):
                elements = soup.select(selector)
                if elements:
                    logger.info(f"   ✅ {len(elements)} éléments trouvés avec sélecteur '{selector}'")
                    for elem in elements[:30]:  # Limiter à 30 plus récents
                        pub = self._extract_from_element(elem, category, config)
                        if pub and pub not in publications:
                            publications.append(pub)
                    break  # Utiliser le premier sélecteur qui fonctionne
            
            # Stratégie 3 : Tableaux (très fréquent sur BRVM.org)
            tables = soup.find_all('table')
            if tables:
                logger.info(f"   📊 {len(tables)} tableau(x) trouvé(s)")
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:31]:  # Skip header, limiter à 30
                        pub = self._extract_from_table_row(row, category, config)
                        if pub and pub not in publications:
                            publications.append(pub)
            
            logger.info(f"   ✅ {len(publications)} publication(s) extraite(s)")
            
        except Exception as e:
            logger.error(f"   ❌ Erreur: {e}")
        
        return publications
    
    def _extract_from_pdf_link(self, link, category, source_url) -> Optional[Dict]:
        """Extraire métadonnées d'un lien PDF"""
        try:
            titre = link.get_text(strip=True) or link.get('title', '') or 'Publication'
            url_pdf = link.get('href', '')
            
            if not url_pdf:
                return None
            
            # Compléter URL relative
            if url_pdf.startswith('/'):
                url_pdf = f"https://www.brvm.org{url_pdf}"
            
            # Extraire date (plusieurs patterns)
            date = self._extract_date(titre + ' ' + url_pdf)
            
            # Extraire société/emetteur
            emetteur = self._extract_emetteur(titre)
            
            # Hash unique pour détecter duplicatas
            hash_id = hashlib.md5((titre + url_pdf).encode()).hexdigest()[:16]
            
            return {
                'title': titre,
                'url': url_pdf,
                'date': date,
                'emetteur': emetteur,
                'category': category,
                'source_url': source_url,
                'file_type': 'PDF',
                'hash': hash_id,
                'scraped_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.debug(f"Erreur extraction PDF: {e}")
            return None
    
    def _extract_from_element(self, element, category, config) -> Optional[Dict]:
        """Extraire métadonnées d'un élément HTML (article, div)"""
        try:
            # Chercher titre
            title_elem = (element.find('h1') or element.find('h2') or 
                          element.find('h3') or element.find('h4') or
                          element.find('strong') or element.find('b'))
            
            titre = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)[:200]
            
            if not titre or len(titre) < 5:
                return None
            
            # Filtrer par keywords si configurés
            keywords = config.get('keywords', [])
            if keywords:
                if not any(kw.lower() in titre.lower() for kw in keywords):
                    return None
            
            # Chercher lien
            link = element.find('a')
            url = link.get('href', '') if link else ''
            if url and url.startswith('/'):
                url = f"https://www.brvm.org{url}"
            
            # Extraire date
            date = self._extract_date(titre + ' ' + element.get_text())
            
            # Extraire emetteur
            emetteur = self._extract_emetteur(titre)
            
            # Description/snippet
            description = element.get_text(strip=True)[:500]
            
            hash_id = hashlib.md5((titre + url).encode()).hexdigest()[:16]
            
            return {
                'title': titre,
                'url': url or config['url'],
                'date': date,
                'emetteur': emetteur,
                'category': category,
                'source_url': config['url'],
                'description': description,
                'hash': hash_id,
                'scraped_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.debug(f"Erreur extraction element: {e}")
            return None
    
    def _extract_from_table_row(self, row, category, config) -> Optional[Dict]:
        """Extraire métadonnées d'une ligne de tableau"""
        try:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 2:
                return None
            
            # Format typique : Date | Titre | Lien/PDF
            date_text = cells[0].get_text(strip=True)
            titre = cells[1].get_text(strip=True)
            
            if not titre or len(titre) < 5:
                return None
            
            # Chercher lien dans n'importe quelle cellule
            link = row.find('a')
            url = link.get('href', '') if link else ''
            if url and url.startswith('/'):
                url = f"https://www.brvm.org{url}"
            
            # Parser date
            date = self._extract_date(date_text + ' ' + titre)
            
            emetteur = self._extract_emetteur(titre)
            
            hash_id = hashlib.md5((titre + url).encode()).hexdigest()[:16]
            
            return {
                'title': titre,
                'url': url or config['url'],
                'date': date,
                'emetteur': emetteur,
                'category': category,
                'source_url': config['url'],
                'hash': hash_id,
                'scraped_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.debug(f"Erreur extraction table row: {e}")
            return None
    
    def _extract_date(self, text: str) -> str:
        """
        Extraire date intelligemment avec multiples patterns
        """
        # Pattern 1 : JJ/MM/AAAA ou JJ-MM-AAAA
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
            except:
                pass
        
        # Pattern 2 : AAAA-MM-JJ
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
        if match:
            return match.group(0)
        
        # Pattern 3 : Année seule (pour rapports annuels)
        match = re.search(r'20\d{2}', text)
        if match:
            year = match.group(0)
            return f"{year}-12-31"  # Fin d'année par défaut
        
        # Default : aujourd'hui
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_emetteur(self, text: str) -> str:
        """
        Extraire symbole/nom de société
        
        Patterns :
        - Codes ticker : SNTS, BOABF, BICC, ECOC, etc.
        - Noms complets : Sonatel, BOA, BICICI
        """
        # Liste des symboles BRVM connus (47 actions)
        tickers = [
            'ABJC', 'BICC', 'BNBC', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'CABC', 'CBIBF',
            'CFAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'NEIC', 'NSBC', 'NTLC', 'ONAC',
            'ORAC', 'ORGT', 'PALC', 'PRSC', 'SCRC', 'SDCC', 'SDSC', 'SEMC', 'SGBC',
            'SHEC', 'SIBC', 'SICC', 'SICB', 'SLBC', 'SMBC', 'SNTS', 'SOGC', 'SPHC',
            'STAC', 'STBC', 'SVOC', 'TTLC', 'TTRC', 'UNXC', 'ABJC', 'BOAC', 'CIEC',
            'NEIC', 'TTLC'
        ]
        
        # Chercher ticker
        for ticker in tickers:
            if re.search(rf'\b{ticker}\b', text, re.I):
                return ticker
        
        # Chercher noms complets
        noms_societes = {
            'Sonatel': 'SNTS',
            'BICICI': 'BICC',
            'Ecobank': 'ECOC',
            'BOA': 'BOA',
            'SGCI': 'SGBC',
            'NSIA': 'NSBC'
        }
        
        for nom, ticker in noms_societes.items():
            if nom.lower() in text.lower():
                return ticker
        
        return 'BRVM'  # Émetteur par défaut
    
    def insert_to_mongodb(self, publications: List[Dict]):
        """
        Insérer publications dans MongoDB (curated_observations)
        
        Schema :
        {
            'source': 'BRVM_PUBLICATION',
            'dataset': category (BULLETIN_OFFICIEL, COMMUNIQUE_RESULTATS, etc.),
            'key': titre + hash (pour unicité),
            'ts': date ISO,
            'value': 1,
            'attrs': {
                'url': lien,
                'emetteur': symbole,
                'category': label,
                'file_type': PDF/HTML,
                'hash': identifiant unique,
                'title': titre original,
                ...
            }
        }
        """
        logger.info(f"\n💾 Insertion dans MongoDB...")
        
        inserted = 0
        duplicates = 0
        
        for pub in publications:
            # Vérifier si déjà existe (par hash)
            existing = self.db.curated_observations.find_one({
                'source': 'BRVM_PUBLICATION',
                'attrs.hash': pub.get('hash')
            })
            
            if existing:
                duplicates += 1
                continue
            
            # Créer clé unique (titre + hash court pour éviter collisions)
            title = pub.get('title', 'Publication sans titre')
            hash_short = pub.get('hash', '')[:8]  # 8 premiers caractères du hash
            unique_key = f"{title[:100]}-{hash_short}" if len(title) > 5 else f"Publication-{hash_short}"
            
            # Construire observation
            observation = {
                'source': 'BRVM_PUBLICATION',
                'dataset': pub.get('category', 'ACTUALITE'),
                'key': unique_key,  # Clé unique
                'ts': pub.get('date', datetime.now().strftime('%Y-%m-%d')),
                'value': 1,  # Compteur
                'attrs': {
                    'title': title,  # Titre original
                    'url': pub.get('url', ''),
                    'emetteur': pub.get('emetteur', 'BRVM'),
                    'category': pub.get('category', 'ACTUALITE'),
                    'source_url': pub.get('source_url', ''),
                    'file_type': pub.get('file_type', 'HTML'),
                    'hash': pub.get('hash', ''),
                    'description': pub.get('description', ''),
                    'scraped_at': pub.get('scraped_at', datetime.now().isoformat()),
                    'data_quality': 'REAL_SCRAPER'
                }
            }
            
            # Insérer avec gestion d'erreur
            try:
                self.db.curated_observations.insert_one(observation)
                inserted += 1
            except Exception as e:
                logger.warning(f"Erreur insertion (skip): {str(e)[:100]}")
                duplicates += 1
        
        logger.info(f"   ✅ {inserted} nouvelles publications insérées")
        logger.info(f"   ⏭️  {duplicates} duplicatas ignorés")
        
        return inserted, duplicates
    
    def collect_all(self, limit_per_category: Optional[int] = None):
        """
        Collecter TOUTES les catégories intelligemment
        
        Args:
            limit_per_category: Limiter nombre par catégorie (None = illimité)
        """
        logger.info("=" * 80)
        logger.info("🚀 COLLECTEUR INTELLIGENT PUBLICATIONS BRVM")
        logger.info("=" * 80)
        
        all_publications = []
        
        # Trier par priorité
        sorted_categories = sorted(
            CATEGORIES.items(),
            key=lambda x: x[1].get('priority', 99)
        )
        
        for category, config in sorted_categories:
            pubs = self.scrape_category(category, config)
            
            if limit_per_category:
                pubs = pubs[:limit_per_category]
            
            all_publications.extend(pubs)
            
            self.stats['by_category'][category] = len(pubs)
            
            # Pause entre requêtes (politesse)
            time.sleep(2)
        
        self.stats['total_scraped'] = len(all_publications)
        
        # Insertion dans MongoDB
        if all_publications:
            inserted, duplicates = self.insert_to_mongodb(all_publications)
            self.stats['total_inserted'] = inserted
            self.stats['total_duplicates'] = duplicates
        
        # Rapport final
        self._print_report()
    
    def _print_report(self):
        """Afficher rapport détaillé"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 RAPPORT FINAL")
        logger.info("=" * 80)
        logger.info(f"Total scrapé      : {self.stats['total_scraped']:,}")
        logger.info(f"Nouvelles insérées: {self.stats['total_inserted']:,}")
        logger.info(f"Duplicatas ignorés: {self.stats['total_duplicates']:,}")
        logger.info("\n📂 Par catégorie:")
        
        for category, count in sorted(self.stats['by_category'].items(), key=lambda x: -x[1]):
            config = CATEGORIES.get(category, {})
            desc = config.get('description', category)
            logger.info(f"   {category:30s} : {count:4d} - {desc}")
        
        logger.info("=" * 80)
        logger.info("\n✅ Collecte terminée avec succès!")
        logger.info("🔍 Vérifiez : http://127.0.0.1:8000/brvm/publications/")


def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collecteur intelligent publications BRVM')
    parser.add_argument('--limit', type=int, help='Limiter par catégorie', default=None)
    parser.add_argument('--category', help='Collecter une seule catégorie', default=None)
    parser.add_argument('--dry-run', action='store_true', help='Test sans insertion')
    
    args = parser.parse_args()
    
    collector = BRVMPublicationCollector()
    
    if args.category:
        # Collecter une seule catégorie
        if args.category in CATEGORIES:
            config = CATEGORIES[args.category]
            pubs = collector.scrape_category(args.category, config)
            
            if not args.dry_run:
                collector.insert_to_mongodb(pubs)
        else:
            print(f"❌ Catégorie inconnue: {args.category}")
            print(f"Disponibles: {', '.join(CATEGORIES.keys())}")
    else:
        # Collecter toutes
        collector.collect_all(limit_per_category=args.limit)


if __name__ == '__main__':
    main()
