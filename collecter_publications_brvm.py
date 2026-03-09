#!/usr/bin/env python3
"""
📰 COLLECTEUR BRVM + RICHBOURSE (OFFICIEL + ANALYSES)
===================================================

Sources :
- BRVM officielle (PDF)
- RichBourse Actualités
- RichBourse News
- RichBourse Palmarès

Objectif :
- Alimenter l'IA (sentiment + événements)
- Multi-horizon : semaine / mois / trimestre / annuel
"""

import os
import sys
import re
import logging
import hashlib
import time
import tempfile
import unicodedata
from pathlib import Path
from datetime import datetime, timedelta

# =========================
# ENV & LOGS
# =========================
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("COLLECTEUR_BRVM_RICHBOURSE")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# =========================
# DEPENDANCES
# =========================
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# =========================
# DICTIONNAIRE ACTIONS BRVM (47 ACTIONS)
# =========================

ACTIONS_BRVM = {
    # ── Mise à jour 27/02/2026 : +5 ajouts (BICB, LNBB, ORAC, SCRC, UNLC)
    # ── -5 suppressions (BOAG, SAFH, SGOC, SVOC, TTRC) — suspendus / symboles erronés
    "ABJC": ["SERVAIR ABIDJAN", "SERVAIR CI"],
    "BICB": ["BICI BENIN", "BICI-B", "BICIB", "BANQUE INTERNATIONALE DU COMMERCE ET DE L'INDUSTRIE DU BENIN", "BICI B"],
    "BICC": ["BIC", "BICI", "BANQUE INTERNATIONALE POUR LE COMMERCE"],
    "BNBC": ["BERNABE", "BERNABÉ"],
    "BOAB": ["BANK OF AFRICA BN", "BOA BN", "BOA BENIN", "BANK OF AFRICA BENIN"],
    "BOABF": ["BANK OF AFRICA BF", "BOA BF", "BOA BURKINA", "BANK OF AFRICA BURKINA"],
    "BOAC": ["BOA CI", "BOA COTE D'IVOIRE", "BOA CÔTE D'IVOIRE", "BANK OF AFRICA CI"],
    "BOAM": ["BANK OF AFRICA ML", "BOA ML", "BOA MALI", "BANK OF AFRICA MALI"],
    "BOAN": ["BANK OF AFRICA NG", "BOA NE", "BOA NIGER", "BANK OF AFRICA NIGER"],
    "BOAS": ["BANK OF AFRICA SN", "BOA SN", "BOA SENEGAL", "BANK OF AFRICA SENEGAL"],
    "CABC": ["SICABLE", "SICABLE CI", "CABLES ELECTRIQUES"],
    "CBIBF": ["CORIS BANK", "CORIS BF", "CORIS BURKINA"],
    "CFAC": ["CFAO", "CFAO MOTORS"],
    "CIEC": ["CIE", "COMPAGNIE IVOIRIENNE ELECTRICITE", "CIE CI"],
    "ECOC": ["ECOBANK CI", "ETI", "ECOBANK TRANSNATIONAL"],
    "ETIT": ["ECOBANK TG", "ECOBANK TOGO"],
    "FTSC": ["FILTISAC", "SACS INDUSTRIELS"],
    "LNBB": ["LNB", "LOTERIE NATIONALE DU BENIN", "LOTERIE NATIONALE BENIN", "LNB BENIN", "LOTERIE BENIN"],
    "NEIC": ["NEI", "NEI CEDA"],
    "NSBC": ["NSIA BANQUE", "NSIA BANQUE CI", "NSIA CI"],
    "NTLC": ["NESTLE", "NESTLE CI", "NESTLÉ"],
    "ONTBF": ["ONATEL", "ONATEL BF", "ONATEL BURKINA"],
    "ORAC": ["ORANGE CI", "ORANGE COTE IVOIRE", "ORANGE CÔTE D'IVOIRE"],
    "ORGT": ["ORAGROUP TOGO", "ORAGROUP TG"],
    "PALC": ["PALM CI", "PALMCI", "PALM COTE D'IVOIRE"],
    "PRSC": ["TRACTAFRIC", "TRACTAFRIC MOTORS"],
    "SAFC": ["SAFCA", "SAFCA CI"],
    "SCRC": ["SUCRIVOIRE", "SUCRIVOIRE CI", "SUCRE COTE IVOIRE"],
    "SDCC": ["SODE CI", "SODECI", "SOCIETE DISTRIBUTION EAU"],
    "SDSC": ["AFRICA GLOBAL LOGISTICS", "AFRICA GLOBAL LOGISTICS CI", "AGL CI", "BOLLORE TRANSPORT", "SDV CI", "BOLLORE CI"],
    "SEMC": ["EVIOSYS", "SIEM CI", "PACKAGING SIEM"],
    "SGBC": ["SGB CI", "SOCIETE GENERALE DE BANQUES", "SOCIETE GENERALE DE BANQUES EN COTE D'IVOIRE", "SGBCI", "SOCIETE GENERALE CI", "SG CI", "SGCI"],
    "SHEC": ["VIVO ENERGY", "SHELL CI"],
    "SIBC": ["SIB", "SOCIETE IVOIRIENNE DE BANQUE"],
    "SICC": ["SICOR CI", "SICOR"],
    "SIVC": ["ERIUM CI", "ERIUM", "AIR LIQUIDE CI", "AIR LIQUIDE COTE D'IVOIRE", "AIR LIQUIDE"],
    "SLBC": ["SOLIBRA", "SOLIBRA CI"],
    "SMBC": ["SMB", "SMB CI"],
    "SNTS": ["SONATEL", "ORANGE SENEGAL", "ORANGE SN"],
    "SOGC": ["SOGB", "SOGB CI"],
    "SPHC": ["SAPH", "SAPH CI", "PALMAFRIQUE"],
    "STAC": ["SETAO", "SETAO CI"],
    "STBC": ["SITAB", "SITAB CI"],
    "TTLC": ["TOTAL CI", "TOTALENERGIES CI"],
    "TTLS": ["TOTAL SN", "TOTALENERGIES SENEGAL"],
    "UNLC": ["UNILEVER CI", "UNILEVER COTE IVOIRE", "UNILEVER"],
    "UNXC": ["UNIWAX", "UNIWAX CI", "TEXTILE"],
}

# Mapping inverse : nom complet → symbole
NOM_VERS_SYMBOLE = {}
for symbole, variantes in ACTIONS_BRVM.items():
    for variante in variantes:
        NOM_VERS_SYMBOLE[variante.upper()] = symbole

# =========================
# EXTRACTION SYMBOLES & ÉVÉNEMENTS
# =========================

def extraire_symboles(texte: str) -> list:
    """
    Extrait les symboles d'actions BRVM mentionnés dans un texte.
    
    Stratégie :
    1. Recherche des codes boursiers (SNTS, SGBC, etc.)
    2. Recherche des noms d'entreprises (Sonatel, Société Générale, etc.)
    3. Retourne la liste unique des symboles trouvés
    """
    if not texte:
        return []
    
    texte_upper = texte.upper()
    symboles_trouves = set()
    
    # 1. Recherche directe des codes boursiers (4 lettres)
    import re
    codes_pattern = r'\b(' + '|'.join(ACTIONS_BRVM.keys()) + r')\b'
    for match in re.finditer(codes_pattern, texte_upper):
        symboles_trouves.add(match.group(1))
    
    # 2. Recherche des noms d'entreprises
    for nom, symbole in NOM_VERS_SYMBOLE.items():
        if nom in texte_upper:
            symboles_trouves.add(symbole)
    
    return sorted(list(symboles_trouves))


def detecter_type_event(texte: str) -> str:
    """
    Détecte le type d'événement financier dans une publication.
    
    Types :
    - DIVIDENDE : annonce ou distribution de dividendes
    - RESULTATS : publication de résultats (T1, S1, annuels)
    - NOTATION : notation financière
    - AG : assemblée générale
    - COMMUNIQUE : communiqué général
    - AUTRE : non catégorisé
    """
    if not texte:
        return "AUTRE"
    
    texte_lower = texte.lower()
    
    # Ordre de priorité
    if any(kw in texte_lower for kw in ["dividende", "distribution", "coupon"]):
        return "DIVIDENDE"
    
    if any(kw in texte_lower for kw in ["résultat", "resultat", "bénéfice", "benefice", "chiffre d'affaires", "ca ", "trimestre", "semestriel", "annuel"]):
        return "RESULTATS"
    
    if any(kw in texte_lower for kw in ["notation", "rating", "note", "dégradation", "amélioration note"]):
        return "NOTATION"
    
    if any(kw in texte_lower for kw in ["assemblée générale", "assemblee generale", "ag ", "convocation", "ago", "age"]):
        return "AG"
    
    if any(kw in texte_lower for kw in ["communiqué", "communique", "annonce"]):
        return "COMMUNIQUE"
    
    return "AUTRE"

# =========================
# COLLECTEUR PAR EMETTEUR — Helpers
# =========================

# Types d'annonces BRVM avec filtre emetteur (og_group_ref_target_id)
TYPES_ANNONCES_EMETTEUR = [
    ("convocations-assemblees-generales",  "AG"),
    ("dividendes-et-coupons",              "DIVIDENDE"),
    ("resultats-et-rapports",              "RESULTATS"),
    ("communications-officielles",         "COMMUNIQUE"),
]

BRVM_BASE = "https://www.brvm.org"


def _strip_accents(s: str) -> str:
    """Supprime les accents : 'bénin' → 'benin', 'côte' → 'cote'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def _norm(s: str) -> str:
    """Lowercase + supprime accents pour matching robuste."""
    return _strip_accents(s.lower())


def charger_mapping_emetteurs(session):
    """
    Extrait le mapping {nom_societe_normalise: node_id} depuis le dropdown
    og_group_ref_target_id sur la page AGs du site BRVM.
    Les clés sont normalisées (lowercase, sans accents) pour un matching robuste.
    """
    url = f"{BRVM_BASE}/fr/emetteurs/type-annonces/convocations-assemblees-generales"
    logger.info(f"[MAPPING EMETTEURS] Chargement dropdown depuis {url}")
    mapping = {}
    try:
        r = session.get(url, timeout=30, verify=False)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        select = soup.find("select", id="edit-og-group-ref-target-id")
        if not select:
            logger.warning("[MAPPING EMETTEURS] Dropdown #edit-og-group-ref-target-id introuvable")
            return {}
        for opt in select.find_all("option"):
            val  = opt.get("value", "").strip()
            name = opt.get_text(strip=True)
            if val.isdigit() and name and "Acces" not in name and "Tout" not in name:
                mapping[_norm(name)] = int(val)
        logger.info(f"[MAPPING EMETTEURS] {len(mapping)} societes trouvees")
    except Exception as e:
        logger.error(f"[MAPPING EMETTEURS] Erreur: {e}")
    return mapping


def resoudre_node_id(symbol, mapping_noms):
    """
    Trouve le node_id BRVM pour un symbole via les alias du dictionnaire ACTIONS_BRVM.
    Tous les comparaisons sont normalisées (lowercase, sans accents).
    """
    noms = ACTIONS_BRVM.get(symbol, [])
    for nom in noms:
        nl = _norm(nom)
        if nl in mapping_noms:           # correspondance exacte normalisée
            return mapping_noms[nl]
        for key, nid in mapping_noms.items():
            if nl in key or key in nl:   # correspondance partielle
                return nid
    # Dernier recours : 4 premieres lettres du symbole (normalisées)
    sym4 = _norm(symbol)[:4]
    for key, nid in mapping_noms.items():
        if sym4 in key:
            return nid
    return None


def extraire_texte_pdf_emetteur(url, session, max_chars=8000):
    """Telecharge un PDF et extrait le texte via pdfplumber (si disponible)."""
    if not HAS_PDFPLUMBER or not url:
        return ""
    try:
        r = session.get(url, timeout=45, verify=False)
        if r.status_code != 200:
            return ""
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
        logger.debug(f"[PDF EMETTEUR] Erreur {url}: {e}")
        return ""


def detecter_type_evenement_emetteur(titre, texte, url_slug=""):
    """Classification evenement améliorée (titre + texte + slug URL)."""
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


# =========================
# COLLECTEUR
# =========================

class CollecteurBRVMRichBourse:
    def scraper_richbourse_palmares_semaine(self, url, dataset):
        """
        Collecte les résumés de la semaine/palmarès hebdomadaires RichBourse depuis la page des articles 'Apprendre'.
        """
        logger.info(f"🗞️ RICHBOURSE PALMARES | {dataset} | SEMAINE PASSEE (mode ARTICLES)")
        pubs = []
        # Nouvelle URL pour la page des articles 'Apprendre'
        articles_url = "https://www.richbourse.com/common/apprendre/article/"
        r = self.session.get(articles_url, timeout=30, verify=False)
        soup = BeautifulSoup(r.content, "html.parser")
        # Cherche tous les liens d'articles
        articles = soup.find_all("a", href=lambda x: x and "/common/apprendre/article/" in x)
        now = datetime.now()
        for a in articles:
            titre = a.get_text(strip=True)
            href = self._abs_url("https://www.richbourse.com", a.get("href"))
            logger.info(f"[PALMARES-ARTICLES] Titre détecté : {titre} | URL : {href}")
            if not titre or self._en_base(href):
                continue
            # On cible les titres contenant 'résumé de la semaine' ou 'palmarès hebdomadaire'
            if not re.search(r"résumé de la semaine|palmarès hebdomadaire|palmares hebdomadaire", titre, re.IGNORECASE):
                continue
            # Lire le contenu de l'article
            try:
                r2 = self.session.get(href, timeout=30, verify=False)
                s2 = BeautifulSoup(r2.content, "html.parser")
                paragraphs = s2.find_all("p")
                contenu = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
                # Recherche de la date dans le contenu ou le titre (format attendu : 2026-01-24 ou similaire)
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", contenu + " " + titre)
                if date_match:
                    pub_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                else:
                    pub_date = now
            except Exception:
                contenu = ""
                pub_date = now
            # Ne garder que les publications des 7 derniers jours
            if (now - pub_date).days > 7:
                continue
            pubs.append({
                "source": "RICHBOURSE",
                "dataset": dataset,
                "titre": titre,
                "url": href,
                "contenu": contenu[:10000],
                "date": pub_date.strftime("%Y-%m-%d"),
                "type": "ARTICLE"
            })
        return pubs

    MAX_DAYS = 180  # on garde large pour analyses long terme

    URLS = {
        # BRVM
        "BRVM_BULLETIN": "https://www.brvm.org/fr/bulletins-officiels-de-la-cote",
        "BRVM_RAPPORT": "https://www.brvm.org/fr/rapports-societes-cotees",
        "BRVM_AG": "https://www.brvm.org/fr/emetteurs/type-annonces/convocations-assemblees-generales",

        # RichBourse
        "RICH_ACTUALITE": "https://www.richbourse.com/common/actualite/index",
        "RICH_NEWS": "https://www.richbourse.com/common/news/index",
        "RICH_PALMARES": "https://www.richbourse.com/common/palmares/index",
    }

    def __init__(self):
        _, self.db = get_mongo_db()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "fr-FR,fr;q=0.9",
        })

    # =========================
    # OUTILS
    # =========================

    def _en_base(self, url):
        return self.db.curated_observations.count_documents({
            "source": {"$in": ["BRVM_PUBLICATION", "RICHBOURSE"]},
            "key": url
        }) > 0

    def _date_valide(self, dt):
        return (datetime.now() - dt).days <= self.MAX_DAYS

    def _abs_url(self, base, href):
        return href if href.startswith("http") else f"{base}{href}"

    # =========================
    # SCRAPER BRVM PAR EMETTEUR (publications specifiques)
    # =========================

    def _sauvegarder_emetteur_pub(self, symbol, titre, date_pub, pdf_url, page_url, event_type, full_text):
        """
        Sauvegarde une publication emetteur-specifique.
        Cle unique : hash(symbol + titre + date_pub) pour eviter les doublons.
        emetteur=SYMBOL et symboles=[SYMBOL] -- jamais les 47 actions.
        """
        key = hashlib.md5(f"{symbol}_{titre}_{date_pub}".encode()).hexdigest()

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
            "dataset": dataset_map.get(event_type, "COMMUNIQUE"),
            "key":     key,
            "ts":      date_pub,
            "value":   1,
            "attrs": {
                "emetteur":        symbol,
                "symboles":        [symbol],
                "is_multi_action": False,
                "titre":           titre,
                "url":             pdf_url,
                "source_url":      page_url,
                "description":     titre,
                "full_text":       full_text[:8000] if full_text else "",
                "contenu":         full_text[:3000] if full_text else "",
                "text_length":     len(full_text),
                "type_event":      event_type,
                "category":        event_type,
                "data_quality":    "OFFICIAL",
                "date_publication":date_pub,
                "collecte_at":     datetime.utcnow().isoformat(),
                "collecte_par":    "collecter_publications_brvm",
            },
        }

        self.db.curated_observations.update_one(
            {"source": "BRVM_PUBLICATION", "key": key},
            {"$set": doc},
            upsert=True
        )

    def scraper_brvm_par_emetteur(self, jours_max=365, filtre_symbol=None):
        """
        Scrape les publications officelles BRVM specifiques PAR SOCIETE.
        Utilise og_group_ref_target_id pour filtrer par emetteur.
        Stocke emetteur=SYMBOL (1 seul) au lieu de emetteur=ABJC (47 symboles).
        """
        logger.info("=" * 60)
        logger.info("[PAR EMETTEUR] Collecte publications specifiques BRVM")
        logger.info("=" * 60)

        # 1. Charger le mapping nom_societe → node_id depuis le dropdown BRVM
        mapping_noms = charger_mapping_emetteurs(self.session)
        if not mapping_noms:
            logger.warning("[PAR EMETTEUR] Mapping vide — collecte specifique ignoree")
            return 0

        # 2. Resoudre node_ids
        symboles_cibles = [filtre_symbol] if filtre_symbol else list(ACTIONS_BRVM.keys())
        sym_to_nid = {}
        non_resolus = []
        for sym in symboles_cibles:
            nid = resoudre_node_id(sym, mapping_noms)
            if nid:
                sym_to_nid[sym] = nid
            else:
                non_resolus.append(sym)

        logger.info(f"[PAR EMETTEUR] {len(sym_to_nid)}/{len(symboles_cibles)} symboles resolus")
        if non_resolus:
            logger.info(f"[PAR EMETTEUR] Non resolus: {non_resolus}")

        total_new  = 0
        date_limite = datetime.now() - timedelta(days=jours_max)

        for sym, nid in sym_to_nid.items():
            sym_new = 0

            for url_slug, event_type in TYPES_ANNONCES_EMETTEUR:
                base_url = f"{BRVM_BASE}/fr/emetteurs/type-annonces/{url_slug}"
                page = 0

                while True:
                    url = f"{base_url}?og_group_ref_target_id={nid}&page={page}"
                    try:
                        r = self.session.get(url, timeout=30, verify=False)
                        if r.status_code != 200:
                            break
                        soup  = BeautifulSoup(r.text, "html.parser")
                        table = soup.find("table", class_="views-table")
                        if not table:
                            break
                        rows = table.find_all("tr")[1:]
                        if not rows:
                            break

                        found_on_page   = False
                        stop_pagination = False

                        for row in rows:
                            date_cell = row.find("td", class_=re.compile(r"field-date"))
                            date_str  = date_cell.get_text(strip=True) if date_cell else ""
                            pub_date  = None
                            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
                                try:
                                    pub_date = datetime.strptime(date_str, fmt)
                                    break
                                except Exception:
                                    pass

                            if pub_date and pub_date < date_limite:
                                stop_pagination = True
                                continue

                            titre_cell = row.find("td", class_=re.compile(r"views-field-title"))
                            titre      = titre_cell.get_text(strip=True) if titre_cell else ""

                            fichier_cell = row.find("td", class_=re.compile(r"field-fichier"))
                            pdf_url = ""
                            if fichier_cell:
                                a = fichier_cell.find("a", href=True)
                                if a:
                                    href = a["href"]
                                    pdf_url = href if href.startswith("http") else BRVM_BASE + href

                            if not titre and not pdf_url:
                                continue

                            found_on_page = True
                            date_str_out  = pub_date.strftime("%Y-%m-%d") if pub_date else date_str

                            # Extraction texte PDF
                            full_text = ""
                            if pdf_url:
                                full_text = extraire_texte_pdf_emetteur(pdf_url, self.session)
                                time.sleep(0.3)

                            # Affiner le type depuis le contenu
                            ev_type = detecter_type_evenement_emetteur(titre, full_text, url_slug)

                            self._sauvegarder_emetteur_pub(
                                sym, titre, date_str_out, pdf_url, url, ev_type, full_text
                            )
                            sym_new += 1
                            logger.info(f"   [EMETTEUR] {sym} | {ev_type} | {titre[:60]}")

                        if stop_pagination or not found_on_page:
                            break

                        has_next = (
                            soup.find("li", class_="pager-next") or
                            soup.find("a", string=re.compile(r"suivant|next", re.I))
                        )
                        if not has_next:
                            break

                        page += 1
                        time.sleep(0.6)

                    except Exception as e:
                        logger.error(f"[EMETTEUR] {sym}/{url_slug} page={page}: {e}")
                        break

                time.sleep(0.8)  # politesse entre types d'annonce

            total_new += sym_new
            if sym_new:
                logger.info(f"[PAR EMETTEUR] {sym} : +{sym_new} publication(s)")

            time.sleep(1.2)  # politesse entre emetteurs

        logger.info(f"[PAR EMETTEUR] Total sauvegarde : +{total_new}")
        return total_new

    # =========================
    # SCRAPER BRVM (PDF)
    # =========================

    def scraper_brvm_pdfs(self, url, dataset):
        logger.info(f"📄 BRVM | {dataset}")
        pubs = []

        r = self.session.get(url, timeout=30, verify=False)
        soup = BeautifulSoup(r.content, "html.parser")

        for a in soup.find_all("a", href=lambda x: x and ".pdf" in x.lower()):
            titre = a.get_text(strip=True)
            href = self._abs_url("https://www.brvm.org", a.get("href"))

            if self._en_base(href):
                continue

            pubs.append({
                "source": "BRVM_PUBLICATION",
                "dataset": dataset,
                "titre": titre,
                "url": href,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "PDF_OFFICIEL"
            })

        return pubs

    # =========================
    # SCRAPER RICHBOURSE (TEXTE)
    # =========================

    def scraper_richbourse(self, url, dataset):
        logger.info(f"🗞️ RICHBOURSE | {dataset}")
        pubs = []

        r = self.session.get(url, timeout=30, verify=False)
        soup = BeautifulSoup(r.content, "html.parser")

        articles = soup.find_all("a", href=lambda x: x and "/common/" in x)

        for a in articles:
            titre = a.get_text(strip=True)
            href = self._abs_url("https://www.richbourse.com", a.get("href"))

            if not titre or self._en_base(href):
                continue

            # Lire le contenu de l'article
            try:
                r2 = self.session.get(href, timeout=30, verify=False)
                s2 = BeautifulSoup(r2.content, "html.parser")
                paragraphs = s2.find_all("p")
                contenu = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            except Exception:
                contenu = ""

            pubs.append({
                "source": "RICHBOURSE",
                "dataset": dataset,
                "titre": titre,
                "url": href,
                "contenu": contenu[:10000],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "ARTICLE"
            })

        return pubs

    # =========================
    # SAUVEGARDE (ENRICHIE AVEC EXTRACTION SYMBOLES)
    # =========================

    def sauvegarder(self, pubs):
        count = 0
        for p in pubs:
            # 1. Texte complet pour analyse
            texte_complet = f"{p['titre']} {p.get('contenu', '')}"
            
            # 2. Extraction des symboles d'actions mentionnés
            symboles = extraire_symboles(texte_complet)
            
            # 3. Détection du type d'événement
            type_event = detecter_type_event(texte_complet)
            
            # 4. Symbole principal (le premier trouvé, ou None)
            emetteur = symboles[0] if symboles else None
            
            doc = {
                "source": p["source"],
                "dataset": p["dataset"],
                "key": p["url"],
                "ts": p["date"],
                "value": 1,
                "attrs": {
                    "titre": p["titre"],
                    "url": p["url"],
                    "type_document": p["type"],
                    "contenu": p.get("contenu"),
                    "data_quality": "OFFICIAL" if p["source"] == "BRVM_PUBLICATION" else "MEDIA_ANALYSIS",
                    "collecte_at": datetime.now().isoformat(),
                    # === NOUVEAUX CHAMPS POUR PIPELINE IA ===
                    "symboles": symboles,              # Liste des actions mentionnées
                    "emetteur": emetteur,              # Symbole principal
                    "nb_symboles": len(symboles),      # Nombre d'actions
                    "type_event": type_event,          # Type d'événement (DIVIDENDE, RESULTATS, etc.)
                    "is_multi_action": len(symboles) > 1,  # Publication multi-actions
                    # Alias pour compatibilité avec analyse_semantique_brvm_v3.py
                    "full_text": texte_complet[:10000],
                    "description": p["titre"]
                }
            }

            self.db.curated_observations.update_one(
                {"source": doc["source"], "key": doc["key"]},
                {"$set": doc},
                upsert=True
            )
            count += 1
            
            # Log pour visibilité (trading hebdomadaire)
            if symboles:
                logger.info(f"   ✓ {emetteur} | {type_event} | {p['titre'][:60]}")

        return count

    # =========================
    # PIPELINE GLOBAL
    # =========================

    def collecter(self):
        logger.info("=" * 100)
        logger.info("COLLECTE BRVM + RICHBOURSE")
        logger.info("=" * 100)

        toutes = []

        # BRVM — bulletins généraux (tous symboles)
        toutes += self.scraper_brvm_pdfs(self.URLS["BRVM_BULLETIN"], "BULLETIN_COTE")
        toutes += self.scraper_brvm_pdfs(self.URLS["BRVM_RAPPORT"], "RAPPORT_SOCIETE")
        toutes += self.scraper_brvm_pdfs(self.URLS["BRVM_AG"], "CONVOCATION_AG")

        # RichBourse
        toutes += self.scraper_richbourse(self.URLS["RICH_ACTUALITE"], "ACTUALITE")
        toutes += self.scraper_richbourse(self.URLS["RICH_NEWS"], "NEWS")
        # Collecte Palmares : uniquement la publication de la semaine passée
        toutes += self.scraper_richbourse_palmares_semaine(self.URLS["RICH_PALMARES"], "PALMARES_SEMAINE")

        logger.info(f"Total documents collectés (generaux) : {len(toutes)}")
        nb_general = self.sauvegarder(toutes)
        logger.info(f"Enregistrés (generaux) : {nb_general}")

        # BRVM — publications spécifiques par émetteur (emetteur=SYMBOL)
        nb_emetteur = self.scraper_brvm_par_emetteur()
        logger.info(f"Enregistrés (par emetteur) : {nb_emetteur}")
        logger.info(f"Total enregistré : {nb_general + nb_emetteur}")

# =========================
# MAIN
# =========================

def main():
    CollecteurBRVMRichBourse().collecter()

if __name__ == "__main__":
    main()
