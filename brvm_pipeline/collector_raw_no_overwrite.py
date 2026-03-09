#!/usr/bin/env python3
"""
🔴 COLLECTEUR BRVM - NIVEAU 1 (RAW) - NE JAMAIS ÉCRASER

PRINCIPE ABSOLU :
- Chaque collecte = 1 INSERT (jamais UPDATE)
- Datetime avec heure/minute/seconde
- Index unique : (symbol, datetime)
- Jamais de suppression, jamais de modification

⚠️ CE FICHIER REMPLACE collecter_brvm_complet_maintenant.py
"""
import os, sys
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import uuid
from pymongo.errors import DuplicateKeyError

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# CONFIGURATION
# ============================================================================

URL_BRVM = "https://www.brvm.org/fr/cours-actions"
COLLECTION_RAW = "prices_intraday_raw"
SOURCE = "BRVM_INTRADAY"

# ============================================================================
# SCRAPING BRVM
# ============================================================================

def scrape_brvm():
    """
    Scraper la BRVM et retourner les données en temps réel
    Returns: list of dict
    """
    print(f"\n🌐 Scraping BRVM : {URL_BRVM}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(URL_BRVM, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le tableau des cours
        table = soup.find('table', class_='table')
        if not table:
            print("❌ Table non trouvée")
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 7:
                continue
            
            try:
                symbol = cols[0].text.strip()
                libelle = cols[1].text.strip()
                cours = cols[2].text.strip().replace(' ', '').replace(',', '.')
                variation = cols[3].text.strip().replace('%', '').replace(',', '.')
                ouverture = cols[4].text.strip().replace(' ', '').replace(',', '.')
                haut = cols[5].text.strip().replace(' ', '').replace(',', '.')
                bas = cols[6].text.strip().replace(' ', '').replace(',', '.')
                volume = cols[7].text.strip().replace(' ', '') if len(cols) > 7 else '0'
                
                # Nettoyer
                if not symbol or symbol == '-':
                    continue
                
                data.append({
                    'symbol': symbol,
                    'libelle': libelle,
                    'cours': float(cours) if cours and cours != '-' else None,
                    'variation_pct': float(variation) if variation and variation != '-' else None,
                    'ouverture': float(ouverture) if ouverture and ouverture != '-' else None,
                    'haut': float(haut) if haut and haut != '-' else None,
                    'bas': float(bas) if bas and bas != '-' else None,
                    'volume': int(volume) if volume and volume != '-' else 0
                })
            except Exception as e:
                print(f"⚠️  Erreur parsing ligne : {e}")
                continue
        
        return data
    
    except Exception as e:
        print(f"❌ Erreur scraping : {e}")
        return []

# ============================================================================
# INSERTION RAW (JAMAIS ÉCRASER)
# ============================================================================

def insert_raw(data):
    """
    Insérer dans prices_intraday_raw
    
    ❌ PAS DE UPDATE
    ✅ SEULEMENT INSERT avec datetime unique
    
    🔑 CORRECTION ANTI-CASSURE :
    - Session ID unique par collecte
    - DuplicateKeyError au lieu de find_one (100x plus rapide)
    - Index unique garantit unicité mathématique
    """
    if not data:
        print("⚠️  Aucune donnée à insérer")
        return 0
    
    now = datetime.now()
    datetime_str = now.isoformat()  # Format : 2026-02-10T14:35:22.123456
    date_str = now.strftime("%Y-%m-%d")
    
    # 🔑 SESSION ID unique pour cette collecte
    session_id = str(uuid.uuid4())
    
    print(f"\n📥 Insertion RAW - {datetime_str}")
    print(f"🔑 Session ID : {session_id}")
    print(f"📦 {len(data)} actions à insérer")
    
    inserted = 0
    skipped = 0
    
    for item in data:
        symbol = item['symbol']
        
        # Document RAW (INTANGIBLE)
        doc = {
            'symbol': symbol,
            'datetime': datetime_str,      # Heure exacte
            'date': date_str,              # Date seule (pour regroupement)
            'source': SOURCE,
            'collected_at': now,
            
            # 🔑 TRAÇABILITÉ COLLECTE (CORRECTION ANTI-CASSURE)
            'session_id': session_id,      # UUID unique par collecte
            'collector_version': 'v2.0',   # Version collector
            
            # Prix OHLC
            'open': item.get('ouverture'),
            'high': item.get('haut'),
            'low': item.get('bas'),
            'close': item.get('cours'),
            
            # Volume & Variation
            'volume': item.get('volume'),
            'variation_pct': item.get('variation_pct'),
            
            # Métadonnées
            'libelle': item.get('libelle'),
            
            # FLAGS (pour traçabilité)
            'level': 'RAW',               # Niveau 1
            'immutable': True,            # Jamais modifié
            'used_for_daily': False,      # Sera utilisé pour daily
            'used_for_weekly': False      # Sera utilisé pour weekly
        }
        
        # 🔑 INSERT avec DuplicateKeyError (CORRECTION ANTI-CASSURE)
        try:
            db[COLLECTION_RAW].insert_one(doc)
            inserted += 1
        except DuplicateKeyError:
            # Doublon = normal (index unique {symbol, datetime})
            skipped += 1
    
    print(f"✅ Inséré : {inserted}")
    print(f"⏭️  Skippé : {skipped} (doublons)")
    
    return inserted

# ============================================================================
# STATS RAPIDES
# ============================================================================

def show_stats():
    """Afficher stats de la collection RAW"""
    total = db[COLLECTION_RAW].count_documents({})
    
    # Dernière collecte
    last = db[COLLECTION_RAW].find_one(sort=[('datetime', -1)])
    last_dt = last['datetime'] if last else 'N/A'
    
    # Nombre de dates uniques
    dates = len(db[COLLECTION_RAW].distinct('date'))
    
    # Nombre de symboles uniques
    symbols = len(db[COLLECTION_RAW].distinct('symbol'))
    
    # Aujourd'hui
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = db[COLLECTION_RAW].count_documents({'date': today})
    
    print("\n" + "="*60)
    print("📊 STATS COLLECTION RAW (prices_intraday_raw)")
    print("="*60)
    print(f"Total observations  : {total:,}")
    print(f"Dernière collecte   : {last_dt}")
    print(f"Jours uniques       : {dates}")
    print(f"Actions uniques     : {symbols}")
    print(f"Collectes aujourd'hui : {today_count}")
    print("="*60 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Collecte principale"""
    print("\n" + "="*80)
    print("🔴 COLLECTEUR BRVM - NIVEAU 1 (RAW)")
    print("="*80)
    print("⚠️  PRINCIPE : Chaque collecte = 1 INSERT (JAMAIS UPDATE)")
    print("="*80 + "\n")
    
    # Scraper
    data = scrape_brvm()
    
    if not data:
        print("❌ Aucune donnée récupérée")
        return
    
    print(f"✅ {len(data)} actions scrapées")
    
    # Insérer (sans écraser)
    inserted = insert_raw(data)
    
    # Stats
    show_stats()
    
    print("✅ Collecte terminée\n")

if __name__ == "__main__":
    main()
