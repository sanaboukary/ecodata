#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Collecteur BRVM avec PROXIES ROTATIFS - Contournement anti-bot
Utilise ScraperAPI ou proxies gratuits pour masquer l'origine
"""

import sys
import io
import time
import random
from datetime import datetime
import pandas as pd
import requests

# Fix encodage
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pymongo import MongoClient

def log(msg, level='INFO'):
    symbols = {'INFO': '📊', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbols.get(level, 'ℹ️')} {msg}")

# Liste de proxies gratuits (à actualiser régulièrement)
PROXIES_GRATUITS = [
    # Format: {'http': 'http://ip:port', 'https': 'http://ip:port'}
    # Exemples (à remplacer par proxies actuels depuis https://free-proxy-list.net/)
    None,  # Sans proxy en premier
]

def obtenir_proxies_gratuits():
    """Récupère liste de proxies gratuits."""
    try:
        # API proxies gratuits
        r = requests.get('https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all', timeout=10)
        
        if r.status_code == 200:
            proxies_list = []
            for line in r.text.strip().split('\n'):
                if ':' in line:
                    proxy_url = f"http://{line.strip()}"
                    proxies_list.append({
                        'http': proxy_url,
                        'https': proxy_url
                    })
            
            log(f"✅ {len(proxies_list)} proxies récupérés", 'SUCCESS')
            return proxies_list[:20]  # Garder les 20 premiers
    except:
        pass
    
    return [None]  # Fallback sans proxy

def collecter_avec_proxies():
    """Collecte avec rotation de proxies."""
    
    log("Récupération proxies gratuits...")
    proxies_list = obtenir_proxies_gratuits()
    
    url = "https://www.brvm.org/fr/investir/cours-et-cotations"
    
    for idx, proxies in enumerate(proxies_list):
        try:
            proxy_info = proxies['http'] if proxies else 'Sans proxy'
            log(f"Tentative {idx+1}/{len(proxies_list)}: {proxy_info[:50]}")
            
            headers = {
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
                    'Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0',
                ]),
                'Accept-Language': 'fr-FR,fr;q=0.9',
                'Referer': 'https://www.brvm.org/',
            }
            
            r = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=20,
                verify=False
            )
            
            if r.status_code == 200 and len(r.content) > 10000:
                log(f"✅ Connexion réussie ({len(r.content)} bytes)", 'SUCCESS')
                
                # Parser tables
                dfs = pd.read_html(r.content, thousands=" ", decimal=",")
                
                if dfs:
                    df_main = max(dfs, key=len)
                    if len(df_main) >= 20:
                        log(f"✅ {len(df_main)} actions extraites", 'SUCCESS')
                        return df_main
            
            # Délai entre tentatives
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            log(f"Erreur: {str(e)[:50]}", 'WARNING')
            time.sleep(2)
    
    return pd.DataFrame()

def main():
    print("=" * 100)
    print("🌐 COLLECTEUR BRVM - PROXIES ROTATIFS")
    print("=" * 100)
    print()
    
    df = collecter_avec_proxies()
    
    if df.empty:
        print()
        log("❌ Échec avec proxies gratuits", 'ERROR')
        print()
        print("💡 ALTERNATIVES:")
        print()
        print("1. Utiliser un service proxy premium:")
        print("   - ScraperAPI: https://www.scraperapi.com/ (1000 requêtes gratuites)")
        print("   - Bright Data: https://brightdata.com/")
        print("   - Oxylabs: https://oxylabs.io/")
        print()
        print("2. Parser bulletins PDF BRVM (RECOMMANDÉ):")
        print("   python parser_bulletin_brvm.py")
        print()
        print("3. Import CSV manuel:")
        print("   python importer_csv_brvm_complet.py")
        print()
        return 1
    
    # Normaliser et sauvegarder...
    # (code similaire aux autres collecteurs)
    
    print("=" * 100)
    log("✅ Collecte réussie avec proxies", 'SUCCESS')
    print("=" * 100)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
