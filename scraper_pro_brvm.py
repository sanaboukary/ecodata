#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SCRAPER PRO BRVM - EXTRACTION COMPLÈTE
Collecte RICHBOURSE + BRVM avec texte intégral pour analyse sémantique

OBJECTIF: Résoudre le problème des scores sémantiques à 0
SOLUTION: Extraire le VRAI contenu des articles, pas juste les métadonnées

Sources:
- RICHBOURSE: Articles complets (actualités, news, analyses)
- BRVM: Bulletins officiels, rapports, communiqués
"""

import os
import sys
import requests
import logging
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib
import time
import re
import urllib3
urllib3.disable_warnings()

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("SCRAPER_PRO_BRVM")

class ScraperProBRVM:
    """Scraper professionnel avec extraction complète du contenu"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        self.db = client['centralisation_db']
        
        # Statistiques
        self.stats = {
            'richbourse_articles': 0,
            'richbourse_chars': 0,
            'brvm_bulletins': 0,
            'errors': 0
        }
    
    # =========================
    # RICHBOURSE - EXTRACTION COMPLÈTE
    # =========================
    
    def extraire_article_richbourse(self, url):
        """
        Extrait le contenu COMPLET d'un article Richbourse
        
        Returns:
            str: Texte complet de l'article
        """
        try:
            response = self.session.get(url, timeout=30, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Stratégie 1: Chercher dans <article>
            article = soup.find('article')
            if article:
                paragraphes = article.find_all('p')
                texte = ' '.join([p.get_text(strip=True) for p in paragraphes])
                if len(texte) > 100:
                    return texte
            
            # Stratégie 2: Chercher div avec classe content/article
            for class_name in ['article-content', 'content', 'post-content', 'entry-content']:
                div = soup.find('div', class_=re.compile(class_name, re.I))
                if div:
                    paragraphes = div.find_all('p')
                    texte = ' '.join([p.get_text(strip=True) for p in paragraphes])
                    if len(texte) > 100:
                        return texte
            
            # Stratégie 3: Tous les <p> de la page (fallback)
            paragraphes = soup.find_all('p')
            if len(paragraphes) > 3:
                texte = ' '.join([p.get_text(strip=True) for p in paragraphes])
                return texte
            
            return ""
            
        except Exception as e:
            logger.error(f"Erreur extraction article {url}: {e}")
            return ""
    
    def scraper_richbourse_actualites(self):
        """
        Scrappe les actualités Richbourse avec contenu complet
        """
        logger.info("📰 RICHBOURSE - Actualités (extraction complète)")
        
        url_base = "https://www.richbourse.com/common/actualite/index"
        articles_collectes = []
        
        try:
            response = self.session.get(url_base, timeout=30, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver tous les liens d'articles
            liens = soup.find_all('a', href=re.compile(r'/common/actualite/detail'))
            
            for lien in liens[:20]:  # Limiter à 20 articles récents
                titre = lien.get_text(strip=True)
                href = lien.get('href')
                
                if not href.startswith('http'):
                    href = f"https://www.richbourse.com{href}"
                
                # Vérifier si déjà en base
                hash_url = hashlib.md5(href.encode()).hexdigest()
                existe = self.db.curated_observations.find_one({
                    'source': 'RICHBOURSE',
                    'attrs.url_hash': hash_url
                })
                
                if existe:
                    continue
                
                # Extraire le contenu COMPLET
                logger.info(f"   📄 {titre[:60]}...")
                contenu = self.extraire_article_richbourse(href)
                
                if not contenu or len(contenu) < 50:
                    logger.warning(f"      ⚠️  Contenu vide ou trop court ({len(contenu)} chars)")
                    self.stats['errors'] += 1
                    continue
                
                logger.info(f"      ✅ {len(contenu)} caractères extraits")
                
                articles_collectes.append({
                    'titre': titre,
                    'url': href,
                    'url_hash': hash_url,
                    'contenu': contenu,
                    'type': 'ACTUALITE',
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                
                self.stats['richbourse_articles'] += 1
                self.stats['richbourse_chars'] += len(contenu)
                
                # Pause pour éviter surcharge
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"Erreur scraping Richbourse actualités: {e}")
            self.stats['errors'] += 1
        
        return articles_collectes
    
    def scraper_richbourse_news(self):
        """
        Scrappe les news Richbourse avec contenu complet
        """
        logger.info("📰 RICHBOURSE - News (extraction complète)")
        
        url_base = "https://www.richbourse.com/common/news/index"
        articles_collectes = []
        
        try:
            response = self.session.get(url_base, timeout=30, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver tous les liens d'articles
            liens = soup.find_all('a', href=re.compile(r'/common/news/detail'))
            
            for lien in liens[:15]:  # 15 news récentes
                titre = lien.get_text(strip=True)
                href = lien.get('href')
                
                if not href.startswith('http'):
                    href = f"https://www.richbourse.com{href}"
                
                hash_url = hashlib.md5(href.encode()).hexdigest()
                existe = self.db.curated_observations.find_one({
                    'source': 'RICHBOURSE',
                    'attrs.url_hash': hash_url
                })
                
                if existe:
                    continue
                
                logger.info(f"   📄 {titre[:60]}...")
                contenu = self.extraire_article_richbourse(href)
                
                if not contenu or len(contenu) < 50:
                    logger.warning(f"      ⚠️  Contenu vide ({len(contenu)} chars)")
                    self.stats['errors'] += 1
                    continue
                
                logger.info(f"      ✅ {len(contenu)} caractères")
                
                articles_collectes.append({
                    'titre': titre,
                    'url': href,
                    'url_hash': hash_url,
                    'contenu': contenu,
                    'type': 'NEWS',
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                
                self.stats['richbourse_articles'] += 1
                self.stats['richbourse_chars'] += len(contenu)
                
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"Erreur scraping Richbourse news: {e}")
            self.stats['errors'] += 1
        
        return articles_collectes
    
    def scraper_richbourse_analyses(self):
        """
        Scrappe les analyses/articles approfondis Richbourse
        """
        logger.info("📊 RICHBOURSE - Analyses (extraction complète)")
        
        url_base = "https://www.richbourse.com/common/apprendre/article"
        articles_collectes = []
        
        try:
            response = self.session.get(url_base, timeout=30, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            liens = soup.find_all('a', href=re.compile(r'/common/apprendre/article/detail'))
            
            for lien in liens[:10]:  # 10 analyses
                titre = lien.get_text(strip=True)
                href = lien.get('href')
                
                if not href.startswith('http'):
                    href = f"https://www.richbourse.com{href}"
                
                hash_url = hashlib.md5(href.encode()).hexdigest()
                existe = self.db.curated_observations.find_one({
                    'source': 'RICHBOURSE',
                    'attrs.url_hash': hash_url
                })
                
                if existe:
                    continue
                
                logger.info(f"   📊 {titre[:60]}...")
                contenu = self.extraire_article_richbourse(href)
                
                if not contenu or len(contenu) < 100:
                    logger.warning(f"      ⚠️  Contenu insuffisant ({len(contenu)} chars)")
                    self.stats['errors'] += 1
                    continue
                
                logger.info(f"      ✅ {len(contenu)} caractères")
                
                articles_collectes.append({
                    'titre': titre,
                    'url': href,
                    'url_hash': hash_url,
                    'contenu': contenu,
                    'type': 'ANALYSE',
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                
                self.stats['richbourse_articles'] += 1
                self.stats['richbourse_chars'] += len(contenu)
                
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"Erreur scraping Richbourse analyses: {e}")
            self.stats['errors'] += 1
        
        return articles_collectes
    
    # =========================
    # SAUVEGARDE MONGODB
    # =========================
    
    def sauvegarder_articles(self, articles):
        """
        Sauvegarde les articles dans MongoDB
        """
        saved = 0
        
        for article in articles:
            doc = {
                'source': 'RICHBOURSE',
                'dataset': f'RICHBOURSE_{article["type"]}',
                'key': article['url'],
                'ts': article['date'],
                'value': 1,
                'attrs': {
                    'titre': article['titre'],
                    'url': article['url'],
                    'url_hash': article['url_hash'],
                    'contenu': article['contenu'][:50000],  # Limiter à 50k chars
                    'type_document': article['type'],
                    'text_length': len(article['contenu']),
                    'data_quality': 'MEDIA_ANALYSIS',
                    'collecte_at': datetime.now().isoformat(),
                    'scraper_version': 'PRO_V1'
                }
            }
            
            self.db.curated_observations.update_one(
                {'source': 'RICHBOURSE', 'key': doc['key']},
                {'$set': doc},
                upsert=True
            )
            saved += 1
        
        return saved
    
    # =========================
    # PIPELINE COMPLET
    # =========================
    
    def executer(self):
        """
        Exécute la collecte complète
        """
        logger.info("="*100)
        logger.info("🚀 SCRAPER PRO BRVM - DÉMARRAGE")
        logger.info("="*100)
        
        tous_articles = []
        
        # RICHBOURSE
        logger.info("\n📰 PHASE 1: RICHBOURSE")
        logger.info("-"*100)
        
        tous_articles += self.scraper_richbourse_actualites()
        tous_articles += self.scraper_richbourse_news()
        tous_articles += self.scraper_richbourse_analyses()
        
        # Sauvegarde
        logger.info(f"\n💾 Sauvegarde de {len(tous_articles)} articles...")
        saved = self.sauvegarder_articles(tous_articles)
        
        # Statistiques finales
        logger.info("\n" + "="*100)
        logger.info("📊 STATISTIQUES FINALES")
        logger.info("="*100)
        logger.info(f"✅ Articles RICHBOURSE:    {self.stats['richbourse_articles']}")
        logger.info(f"✅ Caractères extraits:     {self.stats['richbourse_chars']:,}")
        logger.info(f"✅ Sauvegardés MongoDB:     {saved}")
        logger.info(f"⚠️  Erreurs:                {self.stats['errors']}")
        logger.info("="*100)
        
        if saved > 0:
            logger.info("\n🎯 PROCHAINES ÉTAPES:")
            logger.info("   1. python analyse_semantique_brvm_v3.py")
            logger.info("      → Analyser les nouveaux articles")
            logger.info("   2. python agregateur_semantique_actions.py")
            logger.info("      → Agréger par action")
            logger.info("   3. python pipeline_brvm.py")
            logger.info("      → Générer nouvelles recommandations!")
        
        return saved

if __name__ == "__main__":
    scraper = ScraperProBRVM()
    scraper.executer()
