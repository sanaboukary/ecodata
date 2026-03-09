#!/usr/bin/env python3
"""
SCRAPER PUBLICATIONS BRVM PAR EMETTEUR
=======================================
Collecte les publications officielles BRVM en filtrant par société (emetteur).

Contrairement au collecteur générique (bulletins globaux avec 47 symboles),
ce script utilise le filtre `og_group_ref_target_id` du site BRVM pour
récupérer les publications SPECIFIQUES à chaque action cotée.

Types collectés :
  - Convocations / Compte-rendu AG
  - Dividendes et coupons
  - Resultats et rapports financiers
  - Communications officielles

Chaque publication est stockée dans `curated_observations` avec :
  emetteur  = CODE_SYMBOLE (ex: 'UNLC', 'SNTS') -- JAMAIS tous les 47
  symboles  = [CODE_SYMBOLE]                     -- liste a 1 element
  full_text = texte extrait du PDF (pdfplumber)
  type_event = DIVIDENDE | RESULTATS | AG | COMMUNIQUE

Usage :
  .venv/Scripts/python.exe scripts/connectors/brvm_publications_par_emetteur.py
  .venv/Scripts/python.exe scripts/connectors/brvm_publications_par_emetteur.py --symbol SNTS
  .venv/Scripts/python.exe scripts/connectors/brvm_publications_par_emetteur.py --recent 90
"""

import os
import sys
import re
import time
import logging
import hashlib
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("BRVM_PUB_EMETTEUR")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.warning("[PDF] pdfplumber non disponible -- texte PDF non extrait")

# ─── Parametres CLI ────────────────────────────────────────────────────────────
FILTRE_SYMBOL = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--symbol'), None)
JOURS_RECENT  = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--recent'), 365))

BRVM_BASE = "https://www.brvm.org"

SESSION_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
    "Referer":         "https://www.brvm.org/fr/",
}

# Types d'annonces BRVM : (url_slug, code_evenement)
TYPES_ANNONCES = [
    ("convocations-assemblees-generales",  "AG"),
    ("dividendes-et-coupons",              "DIVIDENDE"),
    ("resultats-et-rapports",              "RESULTATS"),
    ("communications-officielles",         "COMMUNIQUE"),
]

# ─── Dictionnaire des 47 actions BRVM ──────────────────────────────────────────
ACTIONS_BRVM = {
    "ABJC": ["SERVAIR ABIDJAN", "SERVAIR CI", "SAGA CI", "SERVAIR"],
    "BICB": ["BICI BENIN", "BICIB", "BANQUE INTERNATIONALE COMMERCE BENIN"],
    "BICC": ["BICI CI", "BICI", "BANQUE INTERNATIONALE POUR LE COMMERCE ET L'INDUSTRIE"],
    "BNBC": ["BERNABE", "BERNABE CI"],
    "BOAB": ["BOA BENIN", "BANK OF AFRICA BENIN"],
    "BOABF": ["BOA BURKINA", "BANK OF AFRICA BURKINA", "BANK OF AFRICA BURKINA FASO"],
    "BOAC": ["BOA COTE D'IVOIRE", "BANK OF AFRICA CI", "BOA CI"],
    "BOAM": ["BOA MALI", "BANK OF AFRICA MALI"],
    "BOAN": ["BOA NIGER", "BANK OF AFRICA NIGER"],
    "BOAS": ["BOA SENEGAL", "BANK OF AFRICA SENEGAL"],
    "BOAT": ["BOA TOGO", "BANK OF AFRICA TOGO"],
    "CABC": ["SICABLE", "SICABLE CI"],
    "CBIBF": ["CORIS BANK", "CORIS BANK INTERNATIONAL", "CORIS BANK BURKINA"],
    "CFAC": ["CFAO", "CFAO CI", "CFAO MOTORS"],
    "CIEC": ["ECOBANK CI", "ECOBANK COTE D'IVOIRE", "CIE ECOBANK"],
    "ECOC": ["ETI CI", "ECOBANK TI CI"],
    "ETIT": ["ECOBANK TRANSNATIONAL", "ETI", "ECOBANK GROUP", "ECOBANK TRANSNATIONAL INCORPORATED"],
    "FTSC": ["FILTISAC", "FILTISAC CI"],
    "LNBB": ["LONACI", "LOTERIE NATIONALE DE COTE D'IVOIRE"],
    "NEIC": ["NESTLE CI", "NESTLE COTE D'IVOIRE"],
    "NSBC": ["NSIA BANQUE", "NSIA BANQUE CI"],
    "NTLC": ["NESTLE CI", "NESTLE"],
    "ONTBF": ["ONATEL", "ONATEL BURKINA", "OFFICE NATIONAL DES TELECOMMUNICATIONS"],
    "ORAC": ["ORANGE CI", "ORANGE COTE D'IVOIRE"],
    "ORGT": ["ORANGE CI", "ORANGE COTE D'IVOIRE"],
    "PALC": ["PALMCI", "PALM CI", "PALM COTE D'IVOIRE"],
    "PRSC": ["PRESTIGE CI", "PRESTIGE"],
    "SAFC": ["SAFCA", "SAFCA CI"],
    "SCRC": ["SICOR", "SICOR CI"],
    "SDCC": ["SODECI", "SOCIETE DE DISTRIBUTION D'EAU"],
    "SDSC": ["BOLLORE", "BOLLORE TRANSPORT", "BOLLORE CI"],
    "SEMC": ["SETAO", "SETAO CI"],
    "SGBC": ["SOCIETE GENERALE CI", "SG CI", "SGCI", "SOCIETE GENERALE COTE D'IVOIRE"],
    "SHEC": ["SHELL CI", "VIVO ENERGY CI", "VIVO ENERGY"],
    "SIBC": ["SIB", "SIB CI", "SOCIETE IVOIRIENNE DE BANQUE"],
    "SICC": ["SICOGI", "SOCIETE IVOIRIENNE DE CONSTRUCTION"],
    "SIVC": ["AIR LIQUIDE CI", "AIR LIQUIDE COTE D'IVOIRE"],
    "SLBC": ["SOLIBRA", "BRASSERIE"],
    "SMBC": ["SMB", "SMB CI"],
    "SNTS": ["SONATEL", "ORANGE SENEGAL", "ORANGE SN"],
    "SOGC": ["SOGB"],
    "SPHC": ["SAPH", "SOCIETE AFRICAINE DE PLANTATIONS"],
    "STAC": ["SITAB", "SOCIETE IVOIRIENNE DE TABACS"],
    "STBC": ["SITAB"],
    "TTLC": ["TOTAL CI", "TOTAL COTE D'IVOIRE", "TRACTAFRIC"],
    "TTLS": ["TOTAL SENEGAL"],
    "UNLC": ["UNILEVER CI", "UNILEVER COTE D'IVOIRE", "UNILEVER"],
    "UNXC": ["UNIWAX", "UNIWAX CI"],
}


# ─── Session HTTP ──────────────────────────────────────────────────────────────
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(SESSION_HEADERS)
    return s


# ─── Mapping societe → node_id BRVM ──────────────────────────────────────────
def charger_mapping_emetteurs(session: requests.Session) -> Dict[str, int]:
    """
    Extrait le mapping {nom_societe_lower: node_id} depuis le dropdown
    du filtre og_group_ref_target_id sur la page AGs du site BRVM.
    """
    url = f"{BRVM_BASE}/fr/emetteurs/type-annonces/convocations-assemblees-generales"
    logger.info(f"[MAPPING] Chargement dropdown emetteurs depuis {url}")
    mapping: Dict[str, int] = {}
    try:
        r = session.get(url, timeout=30, verify=False)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        select = soup.find("select", id="edit-og-group-ref-target-id")
        if not select:
            logger.warning("[MAPPING] Dropdown #edit-og-group-ref-target-id introuvable")
            return {}
        for opt in select.find_all("option"):
            val  = opt.get("value", "").strip()
            name = opt.get_text(strip=True)
            if val.isdigit() and name and "Acces" not in name and "Tout" not in name:
                mapping[name.lower()] = int(val)
        logger.info(f"[MAPPING] {len(mapping)} societes dans le dropdown")
    except Exception as e:
        logger.error(f"[MAPPING] Erreur: {e}")
    return mapping


def resoudre_node_id(symbol: str, mapping_noms: Dict[str, int]) -> Optional[int]:
    """Trouve le node_id BRVM pour un symbole en matchant les alias connus."""
    noms = ACTIONS_BRVM.get(symbol, [])
    for nom in noms:
        nl = nom.lower()
        if nl in mapping_noms:
            return mapping_noms[nl]
        for key, nid in mapping_noms.items():
            if nl in key or key in nl:
                return nid
    # Dernier recours : 4 premieres lettres du symbole dans le nom
    sym4 = symbol.lower()[:4]
    for key, nid in mapping_noms.items():
        if sym4 in key:
            return nid
    return None


# ─── Extraction texte PDF ──────────────────────────────────────────────────────
def extraire_texte_pdf(url: str, session: requests.Session, max_chars: int = 8000) -> str:
    """Telecharge un PDF et extrait le texte via pdfplumber."""
    if not HAS_PDFPLUMBER or not url:
        return ""
    try:
        r = session.get(url, timeout=45, verify=False)
        if r.status_code != 200:
            return ""
        # Verifier que c'est bien un PDF (par content-type ou extension)
        ctype = r.headers.get("content-type", "").lower()
        if "pdf" not in ctype and ".pdf" not in url.lower():
            return ""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(r.content)
            tmp_path = tmp.name
        try:
            pages_text = []
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages[:12]:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t.strip())
            return " ".join(pages_text)[:max_chars]
        except Exception:
            return ""
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"[PDF] Erreur {url}: {e}")
        return ""


# ─── Detection type evenement ──────────────────────────────────────────────────
def detecter_type_evenement(titre: str, texte: str, url_slug: str = "") -> str:
    """Classe l'evenement depuis le contenu textuel."""
    txt = (titre + " " + texte[:500] + " " + url_slug).lower()
    if any(k in txt for k in ["dividende", "coupon", "distribution", "detachement",
                                "dividendes-et-coupons"]):
        return "DIVIDENDE"
    if any(k in txt for k in ["resultat", "benefice", "chiffre d'affaires",
                                "rapport annuel", "rapport financier", "bilan",
                                "resultats-et-rapports"]):
        return "RESULTATS"
    if any(k in txt for k in ["assemblee", "convocation", "ag ordinaire",
                                "ag extraordinaire", "ordre du jour",
                                "convocations-assemblees"]):
        return "AG"
    if any(k in txt for k in ["notation", "rating", "upgrade", "downgrade"]):
        return "NOTATION"
    if any(k in txt for k in ["partenariat", "accord", "convention", "signature"]):
        return "PARTENARIAT"
    return "COMMUNIQUE"


# ─── Scraping par type d'annonce pour un emetteur ─────────────────────────────
def scraper_annonces_emetteur(
    symbol: str,
    node_id: int,
    url_slug: str,
    event_type: str,
    session: requests.Session,
    jours_max: int = 365,
) -> List[Dict]:
    """
    Scrape toutes les publications d'un type pour un emetteur specifique.
    Utilise og_group_ref_target_id pour filtrer par societe.
    Pagine jusqu'a la derniere page ou la date limite.
    """
    publications = []
    date_limite  = datetime.now() - timedelta(days=jours_max)
    base_url     = f"{BRVM_BASE}/fr/emetteurs/type-annonces/{url_slug}"
    page         = 0

    while True:
        url = f"{base_url}?og_group_ref_target_id={node_id}&page={page}"
        try:
            r = session.get(url, timeout=30, verify=False)
            if r.status_code != 200:
                break
            soup  = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", class_="views-table")
            if not table:
                break
            rows = table.find_all("tr")[1:]  # ignorer l'en-tete
            if not rows:
                break

            found_on_page = False
            stop_pagination = False

            for row in rows:
                # Date
                date_cell = row.find("td", class_=re.compile(r"field-date"))
                date_str  = date_cell.get_text(strip=True) if date_cell else ""
                pub_date  = None
                for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        pub_date = datetime.strptime(date_str, fmt)
                        break
                    except Exception:
                        pass

                # Si trop ancien, inutile de paginer plus loin
                if pub_date and pub_date < date_limite:
                    stop_pagination = True
                    continue

                # Nom societe (confirmation)
                soc_cell  = row.find("td", class_=re.compile(r"og-group-ref"))
                nom_soc   = soc_cell.get_text(strip=True) if soc_cell else ""

                # Titre de la publication
                titre_cell = row.find("td", class_=re.compile(r"views-field-title"))
                titre      = titre_cell.get_text(strip=True) if titre_cell else ""

                # Lien PDF / telechargement
                fichier_cell = row.find("td", class_=re.compile(r"field-fichier"))
                pdf_url      = ""
                if fichier_cell:
                    a = fichier_cell.find("a", href=True)
                    if a:
                        href    = a["href"]
                        pdf_url = href if href.startswith("http") else BRVM_BASE + href

                if titre or pdf_url:
                    found_on_page = True
                    publications.append({
                        "symbol":      symbol,
                        "titre":       titre,
                        "date_pub":    pub_date.strftime("%Y-%m-%d") if pub_date else date_str,
                        "pdf_url":     pdf_url,
                        "event_type":  event_type,
                        "nom_societe": nom_soc,
                        "page_url":    url,
                    })

            if stop_pagination or not found_on_page:
                break

            # Verifier presence d'une page suivante
            has_next = (
                soup.find("li", class_="pager-next") or
                soup.find("a", string=re.compile(r"suivant|next", re.I))
            )
            if not has_next:
                break

            page += 1
            time.sleep(0.6)

        except Exception as e:
            logger.error(f"[SCRAPE] {symbol}/{url_slug} page={page}: {e}")
            break

    return publications


# ─── Sauvegarde MongoDB ────────────────────────────────────────────────────────
def sauvegarder_publication(pub: Dict, full_text: str, db) -> bool:
    """
    Sauvegarde une publication dans curated_observations avec le bon emetteur.
    Cle unique : hash(symbol + titre + date_pub) -- evite les doublons.
    """
    symbol   = pub["symbol"]
    titre    = pub.get("titre", "")
    pdf_url  = pub.get("pdf_url", pub.get("page_url", ""))
    date_pub = pub.get("date_pub", datetime.now().strftime("%Y-%m-%d"))
    event_t  = pub.get("event_type", "COMMUNIQUE")

    key = hashlib.md5(f"{symbol}_{titre}_{date_pub}".encode()).hexdigest()

    # Score semantique basique depuis le titre (sera affine par analyse_semantique_brvm_v3)
    sem_score = 0
    mots_pos  = ["hausse", "benefice", "dividende", "croissance", "progression",
                 "positif", "distribution", "excedent", "amelioration"]
    mots_neg  = ["perte", "baisse", "deficit", "recul", "difficultes", "redressement"]
    txt_sc    = (titre + " " + full_text[:500]).lower()
    for m in mots_pos:
        if m in txt_sc:
            sem_score += 10
    for m in mots_neg:
        if m in txt_sc:
            sem_score -= 15

    dataset_map = {
        "AG":         "COMMUNIQUE_AG",
        "DIVIDENDE":  "DIVIDENDE",
        "RESULTATS":  "RAPPORT_SOCIETE",
        "NOTATION":   "COMMUNIQUE",
        "PARTENARIAT":"COMMUNIQUE",
        "COMMUNIQUE": "COMMUNIQUE",
    }

    doc = {
        "source":  "BRVM_PUBLICATION",
        "dataset": dataset_map.get(event_t, "COMMUNIQUE"),
        "key":     key,
        "ts":      date_pub,
        "value":   1,
        "attrs": {
            # Identification societe -- SPECIFIQUE (1 seule action)
            "emetteur":           symbol,
            "symboles":           [symbol],
            "is_multi_action":    False,
            "nom_societe":        pub.get("nom_societe", ""),

            # Contenu
            "titre":              titre,
            "url":                pdf_url,
            "source_url":         pub.get("page_url", ""),
            "description":        titre,
            "full_text":          full_text[:8000] if full_text else "",
            "contenu":            full_text[:3000] if full_text else "",
            "text_length":        len(full_text),

            # Classification
            "type_event":         event_t,
            "category":           event_t,
            "data_quality":       "OFFICIAL",

            # Semantique basique (sera recalcule par analyse_semantique_brvm_v3)
            "semantic_score_base": sem_score,
            "semantic_scores": {
                "SEMAINE":    float(sem_score) * 2.0,
                "MOIS":       float(sem_score) * 1.5,
                "TRIMESTRE":  float(sem_score) * 1.2,
                "ANNUEL":     float(sem_score),
            },
            "semantic_tags":    [event_t] if sem_score > 0 else [],
            "semantic_reasons": [f"type:{event_t}"],

            # Metadata
            "date_publication":  date_pub,
            "collecte_at":       datetime.utcnow().isoformat(),
            "collecte_par":      "brvm_publications_par_emetteur",
        },
    }

    try:
        db.curated_observations.update_one(
            {"source": "BRVM_PUBLICATION", "key": key},
            {"$set": doc},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"[SAVE] {symbol} / {titre[:50]}: {e}")
        return False


# ─── Entree principale ─────────────────────────────────────────────────────────
def main():
    _, db   = get_mongo_db()
    session = make_session()

    print("=" * 70)
    print(" COLLECTEUR PUBLICATIONS BRVM PAR EMETTEUR ".center(70))
    print("=" * 70)
    print(f"\n  Horizon    : {JOURS_RECENT} jours")
    print(f"  PDF        : {'pdfplumber OK' if HAS_PDFPLUMBER else 'ABSENT -- texte vide'}")
    if FILTRE_SYMBOL:
        print(f"  Filtre     : {FILTRE_SYMBOL} seulement")
    print()

    # 1. Charger mapping nom_societe → node_id
    mapping_noms = charger_mapping_emetteurs(session)
    if not mapping_noms:
        print("[ERREUR] Impossible de charger le mapping emetteurs. Verifier la connexion.")
        return

    # 2. Resoudre node_ids pour chaque symbole cible
    symboles = [FILTRE_SYMBOL] if FILTRE_SYMBOL else list(ACTIONS_BRVM.keys())
    sym_to_nid: Dict[str, int] = {}
    non_resolus = []
    for sym in symboles:
        nid = resoudre_node_id(sym, mapping_noms)
        if nid:
            sym_to_nid[sym] = nid
        else:
            non_resolus.append(sym)

    print(f"  Symboles resolus    : {len(sym_to_nid)}/{len(symboles)}")
    if non_resolus:
        print(f"  Non resolus         : {non_resolus}")
    print()

    # 3. Scraper chaque symbole
    total_new  = 0
    total_skip = 0
    stats_type: Dict[str, int] = {}

    for sym, nid in sym_to_nid.items():
        sym_new = 0
        logger.info(f"[{sym}] node_id={nid}")

        for url_slug, event_type in TYPES_ANNONCES:
            pubs = scraper_annonces_emetteur(
                sym, nid, url_slug, event_type, session, JOURS_RECENT
            )
            if not pubs:
                continue

            logger.info(f"  [{sym}] {event_type}: {len(pubs)} pub(s)")

            for pub in pubs:
                # Extraction PDF
                full_text = ""
                if pub["pdf_url"]:
                    full_text = extraire_texte_pdf(pub["pdf_url"], session)
                    time.sleep(0.3)

                # Affiner le type d'evenement avec le texte PDF
                pub["event_type"] = detecter_type_evenement(
                    pub["titre"], full_text, url_slug
                )

                saved = sauvegarder_publication(pub, full_text, db)
                if saved:
                    sym_new += 1
                    et = pub["event_type"]
                    stats_type[et] = stats_type.get(et, 0) + 1
                else:
                    total_skip += 1

            time.sleep(1.0)  # politesse entre types

        total_new += sym_new
        if sym_new:
            print(f"  [{sym}] +{sym_new} publication(s)")

        time.sleep(1.5)  # politesse entre emetteurs

    # 4. Resume
    print(f"\n{'='*70}")
    print(f"  Publications sauvegardees : +{total_new}")
    print(f"  Doublons ignores          : {total_skip}")
    if stats_type:
        print(f"  Par type                  : " + " | ".join(f"{k}={v}" for k, v in stats_type.items()))
    print(f"\n  Prochaine etape : analyse_semantique_brvm_v3.py")
    print(f"                  + agregateur_semantique_actions.py")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
