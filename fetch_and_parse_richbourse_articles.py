#!/usr/bin/env python3
"""
V2.1 — LECTURE COMPLÈTE DES ARTICLES RICHBOURSE
=============================================

- Ouvre chaque URL collectée
- Extrait le vrai contenu éditorial
- Nettoie le bruit HTML
- Stocke le texte intégral en base
- Prêt pour analyse sémantique experte
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

# ======================
# DJANGO / DB
# ======================
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BRVMAnalyzer/1.0)"
}

# ======================
# EXTRACTION TEXTE PRO
# ======================
def extract_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Supprimer scripts / styles
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()

    # Zone principale RichBourse
    article = soup.find("div", class_="content") or soup.find("article")

    if not article:
        article = soup

    paragraphs = []
    for p in article.find_all(["p", "li"]):
        text = p.get_text(strip=True)
        if len(text) > 40:  # filtre bruit
            paragraphs.append(text)

    return "\n".join(paragraphs)

# ======================
# PIPELINE
# ======================
def fetch_and_store_articles(days_back: int = 7):
    _, db = get_mongo_db()

    print("=" * 80)
    print("LECTURE COMPLÈTE DES ARTICLES RICHBOURSE – V2.1")
    print("=" * 80)

    pubs = list(db.curated_observations.find({
        "source": "RICHBOURSE",
        "url": {"$exists": True},
        "attrs.full_text": {"$exists": False}
    }))

    print(f"{len(pubs)} articles à analyser\n")

    for pub in pubs:
        url = pub.get("url")
        if not url:
            continue

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            full_text = extract_clean_text(response.text)

            if len(full_text) < 200:
                print(f"⚠️ Texte trop court ignoré : {url}")
                continue

            db.curated_observations.update_one(
                {"_id": pub["_id"]},
                {"$set": {
                    "attrs.full_text": full_text,
                    "attrs.full_text_extracted_at": datetime.now().isoformat()
                }}
            )

            print(f"✅ Texte extrait : {url[:80]}")

        except Exception as e:
            print(f"❌ Erreur lecture {url} : {e}")

    print("\n✅ Extraction complète terminée")

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    fetch_and_store_articles(days_back=7)
