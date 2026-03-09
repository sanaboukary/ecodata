#!/usr/bin/env python3
"""
EXTRACTION PDF BRVM — pdfplumber
=================================
Télécharge et extrait le texte des PDFs BRVM (bulletins, rapports, AG)
stockés dans curated_observations sans contenu.

Stratégie :
1. pdfplumber.extract_text() → meilleur rendu texte pour PDFs français
2. pdfplumber.extract_tables() → extraction tableaux (bulletins marché)
3. Mise à jour attrs.full_text + attrs.symboles (re-détection par texte)

Étape 1bis du pipeline (après collecte, avant analyse sémantique).
"""

import sys
import os
import tempfile
import requests
import urllib3

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")

import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

try:
    import pdfplumber
except ImportError:
    print("pdfplumber non installe. Lancer: pip install pdfplumber")
    sys.exit(1)

# ─── symboles BRVM (47 actions) ─────────────────────────────────────────────

ACTIONS_BRVM = {
    "ABJC": ["SERVAIR"],
    "BICB": ["BICI BENIN", "BICIB"],
    "BICC": ["BICI", "BANQUE INTERNATIONALE POUR LE COMMERCE"],
    "BNBC": ["BERNABE", "BERNABÉ"],
    "BOAB": ["BOA BENIN", "BANK OF AFRICA BENIN"],
    "BOABF": ["BOA BURKINA", "BANK OF AFRICA BURKINA"],
    "BOAC": ["BOA CI", "BOA COTE", "BANK OF AFRICA CI"],
    "BOAM": ["BOA MALI", "BANK OF AFRICA MALI"],
    "BOAN": ["BOA NIGER", "BANK OF AFRICA NIGER"],
    "BOAS": ["BOA SENEGAL", "BANK OF AFRICA SENEGAL"],
    "CABC": ["SICABLE"],
    "CBIBF": ["CORIS BANK", "CORIS"],
    "CFAC": ["CFAO"],
    "CIEC": ["CIE CI", "COMPAGNIE IVOIRIENNE ELECTRICITE"],
    "ECOC": ["ECOBANK CI", "ETI"],
    "ETIT": ["ECOBANK TOGO", "ECOBANK TG"],
    "FTSC": ["FILTISAC"],
    "LNBB": ["LONAB", "LOTERIE NATIONALE BENIN"],
    "NEIC": ["NEI CEDA", "NEI"],
    "NSBC": ["NSIA BANQUE"],
    "NTLC": ["NESTLE CI", "NESTLÉ"],
    "ONTBF": ["ONATEL"],
    "ORAC": ["ORANGE CI", "ORANGE COTE"],
    "ORGT": ["ORAGROUP"],
    "PALC": ["PALMCI", "PALM CI"],
    "PRSC": ["TRACTAFRIC"],
    "SAFC": ["SAFCA"],
    "SCRC": ["SUCRIVOIRE"],
    "SDCC": ["SODECI", "SODE CI"],
    "SDSC": ["AFRICA GLOBAL LOGISTICS", "AGL"],
    "SEMC": ["EVIOSYS", "SIEM CI"],
    "SGBC": ["SOCIETE GENERALE CI", "SG CI", "SGCI"],
    "SHEC": ["VIVO ENERGY", "SHELL CI"],
    "SIBC": ["SIB CI", "SOCIETE IVOIRIENNE DE BANQUE"],
    "SICC": ["SICOR"],
    "SIVC": ["ERIUM"],
    "SLBC": ["SOLIBRA"],
    "SMBC": ["SMB CI", "SMB"],
    "SNTS": ["SONATEL", "ORANGE SENEGAL"],
    "SOGC": ["SOGB"],
    "SPHC": ["SAPH"],
    "STAC": ["SETAO"],
    "STBC": ["SITAB"],
    "TTLC": ["TOTAL CI", "TOTALENERGIES CI"],
    "TTLS": ["TOTAL SN", "TOTALENERGIES SENEGAL"],
    "UNLC": ["UNILEVER CI", "UNILEVER"],
    "UNXC": ["UNIWAX"],
}

_NOM2SYM = {}
for sym, variantes in ACTIONS_BRVM.items():
    for v in variantes:
        _NOM2SYM[v.upper()] = sym
    _NOM2SYM[sym] = sym   # match direct sur le code


def extraire_symboles(texte: str) -> list:
    if not texte:
        return []
    t = texte.upper()
    found = set()
    for sym in ACTIONS_BRVM:
        if sym in t.split() or f" {sym} " in t or t.startswith(sym) or t.endswith(sym):
            found.add(sym)
    for nom, sym in _NOM2SYM.items():
        if nom in t:
            found.add(sym)
    return sorted(found)


# ─── téléchargement + extraction ─────────────────────────────────────────────

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})


def telecharger_pdf(url: str, timeout: int = 20) -> str | None:
    """Télécharge un PDF et retourne le chemin temporaire. None si échec."""
    try:
        r = SESSION.get(url, timeout=timeout, verify=False, stream=True)
        if r.status_code != 200:
            return None
        content_type = r.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
            # Accepter quand même — BRVM parfois renvoie application/octet-stream
            pass
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        for chunk in r.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"   [telecharger] erreur: {e}")
        return None


def extraire_texte_pdfplumber(path: str) -> str:
    """
    Extrait le texte via pdfplumber.
    Stratégie :
    1. extract_text() page par page (meilleur pour prose)
    2. Si une page ne donne rien → extract_tables() + conversion en texte
    """
    texte_pages = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:60]:   # max 60 pages
                # Essai 1 : texte brut
                txt = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                if len(txt.strip()) > 30:
                    texte_pages.append(txt)
                    continue

                # Essai 2 : tables → conversion ligne par ligne
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            cells = [str(c).strip() for c in row if c]
                            texte_pages.append(" | ".join(cells))

    except Exception as e:
        print(f"   [pdfplumber] erreur: {e}")

    return "\n".join(texte_pages).strip()


# ─── pipeline ────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("EXTRACTION PDF — pdfplumber (etape 1bis pipeline)")
    print("=" * 70)

    _, db = get_mongo_db()

    # PDFs officiels BRVM pas encore traités par pdfplumber
    # (pdf_extraction_status absent = jamais traité)
    query = {
        "source": "BRVM_PUBLICATION",
        "attrs.type_document": "PDF_OFFICIEL",
        "attrs.pdf_extraction_status": {"$exists": False},
    }

    docs = list(db.curated_observations.find(query).limit(50))
    print(f"\n{len(docs)} PDFs a traiter")

    if not docs:
        print("Rien a faire — tous les PDFs ont dejà du texte.")
        return

    ok, vide, erreur = 0, 0, 0

    for i, doc in enumerate(docs, 1):
        attrs = doc.get("attrs", {})
        url   = attrs.get("url", "")
        titre = attrs.get("titre", "?")[:60]

        print(f"\n[{i}/{len(docs)}] {titre}")
        print(f"   URL: {url}")

        if not url or not url.lower().endswith(".pdf"):
            print("   ignore (pas un PDF)")
            vide += 1
            continue

        # 1. Téléchargement
        path = telecharger_pdf(url)
        if not path:
            print("   echec telechargement")
            erreur += 1
            continue

        # 2. Extraction texte
        texte = extraire_texte_pdfplumber(path)

        # 3. Nettoyage fichier tmp
        try:
            os.unlink(path)
        except Exception:
            pass

        if not texte or len(texte) < 50:
            print(f"   texte vide apres extraction ({len(texte)} chars) — PDF scanné ou protégé")
            vide += 1
            db.curated_observations.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "attrs.pdf_extraction_status": "VIDE",
                    "attrs.pdf_extracted_at": datetime.now().isoformat(),
                }}
            )
            continue

        # 4. Re-détection symboles dans le texte extrait
        symboles = extraire_symboles(texte)
        emetteur = symboles[0] if symboles else attrs.get("emetteur")

        # 5. Mise à jour MongoDB
        db.curated_observations.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "attrs.full_text":            texte[:50000],
                "attrs.contenu":              texte[:50000],
                "attrs.symboles":             symboles,
                "attrs.emetteur":             emetteur,
                "attrs.nb_symboles":          len(symboles),
                "attrs.pdf_extraction_status": "OK",
                "attrs.pdf_extracted_at":     datetime.now().isoformat(),
                "attrs.pdf_text_length":      len(texte),
            }}
        )
        print(f"   OK — {len(texte)} chars | symboles: {symboles or '(aucun)'}")
        ok += 1

    print("\n" + "=" * 70)
    print(f"RESULTATS: {ok} OK | {vide} vides/ignores | {erreur} erreurs")
    print("=" * 70)


if __name__ == "__main__":
    main()
