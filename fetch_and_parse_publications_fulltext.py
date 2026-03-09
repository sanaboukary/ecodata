#!/usr/bin/env python3
"""
V2.2 — LECTURE COMPLÈTE DES ARTICLES RICHBOURSE & PDF BRVM
========================================================
- Ouvre chaque URL collectée (RichBourse et BRVM_PUBLICATION)
- Extrait le vrai contenu éditorial ou le texte PDF
- Nettoie le bruit HTML ou PDF
- Stocke le texte intégral en base
- Prêt pour analyse sémantique experte
"""
import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

# PDF extraction
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    print("[WARN] PyPDF2 n'est pas installé. Extraction PDF désactivée.")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BRVMAnalyzer/1.0)"
}

def extract_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    article = soup.find("div", class_="content") or soup.find("article")
    if not article:
        article = soup
    paragraphs = []
    for p in article.find_all(["p", "li"]):
        text = p.get_text(strip=True)
        if len(text) > 40:
            paragraphs.append(text)
    return "\n".join(paragraphs)

def extract_pdf_text(url: str) -> str:
    if not PyPDF2:
        return ""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        from io import BytesIO
        pdf = PyPDF2.PdfReader(BytesIO(response.content))
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        print(f"❌ Erreur extraction PDF {url} : {e}")
        return ""

def fetch_and_store_articles(days_back: int = 7):
    _, db = get_mongo_db()
    print("=" * 80)
    print("LECTURE COMPLÈTE DES ARTICLES RICHBOURSE & PDF BRVM – V2.2")
    print("=" * 80)
    # Inclure aussi les documents RICHBOURSE qui ont un texte dans attrs.contenu mais pas attrs.full_text
    pubs = list(db.curated_observations.find({
        "$or": [
            {"source": "RICHBOURSE", "url": {"$exists": True}, "attrs.full_text": {"$exists": False}},
            {"source": "BRVM_PUBLICATION", "url": {"$exists": True}, "attrs.full_text": {"$exists": False}},
            {"source": "RICHBOURSE", "url": {"$exists": True}, "attrs.contenu": {"$exists": True, "$type": "string"}, "attrs.full_text": {"$exists": False}}
        ]
    }))
    print(f"{len(pubs)} documents à analyser\n")
    for pub in pubs:
        url = pub.get("url")
        if not url:
            continue
        try:
            if pub["source"] == "RICHBOURSE":
                # Si attrs.contenu existe et est non vide, l'utiliser comme texte intégral
                contenu = pub.get("attrs", {}).get("contenu", "")
                if contenu and len(contenu) > 200:
                    full_text = contenu
                else:
                    response = requests.get(url, headers=HEADERS, timeout=15)
                    response.raise_for_status()
                    full_text = extract_clean_text(response.text)
            elif pub["source"] == "BRVM_PUBLICATION":
                full_text = extract_pdf_text(url)
            else:
                continue
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

if __name__ == "__main__":
    fetch_and_store_articles(days_back=7)
