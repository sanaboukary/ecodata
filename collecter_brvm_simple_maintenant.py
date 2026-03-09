#!/usr/bin/env python3
"""
COLLECTE BRVM SIMPLE - Sans enrichissement
Collecte uniquement les données essentielles de la table BRVM
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def safe_round(value, n=2):
    return round(value, n) if isinstance(value, (int, float)) else None

def parse_float(text):
    if not text:
        return 0.0
    text = text.strip().replace(' ', '').replace('\xa0', '').replace(',', '.')
    try:
        return float(text)
    except:
        return 0.0

def parse_int(text):
    if not text:
        return 0
    text = text.strip().replace(' ', '').replace('\xa0', '')
    try:
        return int(text)
    except:
        return 0

def collecter_brvm():
    print("\n" + "="*80)
    print("COLLECTE BRVM SIMPLE - SANS ENRICHISSEMENT")
    print("="*80)
    
    _, db = get_mongo_db()
    
    url = "https://www.brvm.org/fr/cours-actions/investisseurs"
    print(f"\n[1/3] Scraping BRVM : {url}")
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "fr-FR,fr;q=0.9"
    })
    
    try:
        response = session.get(url, timeout=30, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"ERREUR lors du scraping : {e}")
        return
    
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table")
    
    actions = []
    
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        if not any("symbole" in h or "titre" in h for h in headers):
            continue
        
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 6:
                continue
            
            try:
                symbole = cells[0].get_text(strip=True).upper()
                nom = cells[1].get_text(strip=True)
                volume = parse_int(cells[2].get_text())
                valeur = parse_float(cells[3].get_text()) if len(cells) > 3 else 0.0
                ouverture = parse_float(cells[4].get_text()) if len(cells) > 4 else 0.0
                prix = parse_float(cells[5].get_text())
                variation = parse_float(cells[6].get_text()) if len(cells) > 6 else 0.0
                haut = parse_float(cells[7].get_text()) if len(cells) > 7 else 0.0
                bas = parse_float(cells[8].get_text()) if len(cells) > 8 else 0.0
                precedent = parse_float(cells[9].get_text()) if len(cells) > 9 else 0.0
                nb_transactions = parse_int(cells[10].get_text()) if len(cells) > 10 else 0
                
                if prix <= 0 or not symbole:
                    continue
                
                actions.append({
                    "symbole": symbole,
                    "nom": nom,
                    "close": safe_round(prix, 2),
                    "open": safe_round(ouverture, 2),
                    "high": safe_round(haut, 2),
                    "low": safe_round(bas, 2),
                    "precedent": safe_round(precedent, 2),
                    "volume": volume,
                    "valeur": safe_round(valeur, 2),
                    "variation": safe_round(variation, 2),
                    "nb_transactions": nb_transactions
                })
                
            except Exception as e:
                print(f"  Erreur ligne : {e}")
                continue
        
        if actions:
            break
    
    print(f"\n[2/3] Actions collectées : {len(actions)}")
    
    if not actions:
        print("AUCUNE action collectée !")
        return
    
    # Sauvegarde
    date_str = datetime.now().strftime("%Y-%m-%d")
    count = 0
    
    for a in actions:
        doc = {
            "source": "BRVM",
            "dataset": "STOCK_PRICE",
            "key": a["symbole"],
            "ts": date_str,
            "timestamp": datetime.now(),
            "value": a["close"],
            "attrs": {
                "data_quality": "REAL_SCRAPER",
                "symbole": a["symbole"],
                "nom": a["nom"],
                "cours": a["close"],
                "ouverture": a["open"],
                "haut": a["high"],
                "bas": a["low"],
                "precedent": a["precedent"],
                "variation_pct": a["variation"],
                "volume": a["volume"],
                "valeur": a["valeur"],
                "nb_transactions": a["nb_transactions"]
            }
        }
        
        db.curated_observations.update_one(
            {
                "source": "BRVM",
                "dataset": "STOCK_PRICE",
                "key": a["symbole"],
                "ts": date_str
            },
            {"$set": doc},
            upsert=True
        )
        count += 1
    
    print(f"\n[3/3] Sauvegarde MongoDB : {count} actions")
    
    # Vérification totale
    total_brvm = db.curated_observations.count_documents({
        "source": "BRVM",
        "dataset": "STOCK_PRICE"
    })
    
    print("\n" + "="*80)
    print(f"✅ COLLECTE TERMINÉE")
    print(f"Total observations BRVM en base : {total_brvm}")
    print("="*80 + "\n")

if __name__ == "__main__":
    collecter_brvm()
