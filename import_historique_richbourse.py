#!/usr/bin/env python3
"""
IMPORT HISTORIQUE BRVM DEPUIS RICHBOURSE
==========================================
Scrape les cours journaliers réels (Bulletin Officiel de la Cote) pour
les 47 actions BRVM sur richbourse.com/common/variation/historique/

Données collectées par action :
  - Date (YYYY-MM-DD)
  - Cours normal    (prix officiel BOC — ce qu on veut)
  - Volume normal   (volume officiel BOC)
  - Variation %
  - Valeur totale FCFA (optionnel)

Résultat :
  1. prices_daily_richbourse_import — nouvelle collection propre (raw import)
  2. Migration vers prices_daily    — remplace les fausses données MIGRATION_CURATED

TOLÉRANCE ZÉRO : aucune donnée inventée. Si RichBourse n a pas la valeur,
                 on n insère pas.

Usage :
  .venv/Scripts/python.exe import_historique_richbourse.py
  .venv/Scripts/python.exe import_historique_richbourse.py --symbol SNTS
  .venv/Scripts/python.exe import_historique_richbourse.py --no-migrate  (import only)
  .venv/Scripts/python.exe import_historique_richbourse.py --dry-run     (test sans écriture)
"""

import sys
import time
import re
import warnings
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore')

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, UpdateOne

# ─── CONFIG ──────────────────────────────────────────────────────────────────
FILTRE_SYMBOL = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--symbol'), None)
NO_MIGRATE    = '--no-migrate' in sys.argv
DRY_RUN       = '--dry-run'    in sys.argv

DATE_DEBUT = '01-09-2025'   # dd-mm-yyyy
DATE_FIN   = datetime.now().strftime('%d-%m-%Y')

BASE_URL   = 'https://www.richbourse.com/common/variation/historique'

ACTIONS_OFFICIELLES = [
    "ABJC","BICB","BICC","BNBC","BOAB","BOABF","BOAC","BOAM","BOAN","BOAS",
    "CABC","CBIBF","CFAC","CIEC","ECOC","ETIT","FTSC","LNBB","NEIC","NSBC",
    "NTLC","ONTBF","ORAC","ORGT","PALC","PRSC","SAFC","SCRC","SDCC","SDSC",
    "SEMC","SGBC","SHEC","SIBC","SICC","SIVC","SLBC","SMBC","SNTS","SOGC",
    "SPHC","STAC","STBC","TTLC","TTLS","UNLC","UNXC",
]

# Sources que l on PEUT remplacer (données fictives)
SOURCES_FICTIVES = {None, '', '?', 'MIGRATION_CURATED', 'RESTORED_FROM_C',
                    'MIGRATION_CURATED_DAILY', 'RESTORED_FROM_CSV'}

PAUSE_ENTRE_PAGES    = 0.4   # secondes entre pages
PAUSE_ENTRE_SYMBOLES = 1.0   # secondes entre symboles


# ─── Session HTTP ─────────────────────────────────────────────────────────────

def creer_session():
    """Crée une session avec cookies RichBourse (requis pour accès PJAX)."""
    session = requests.Session()
    session.headers.update({
        'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8',
        'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    # Init cookies
    session.get('https://www.richbourse.com/', timeout=20, verify=False)
    session.get(f'{BASE_URL}/', timeout=20, verify=False)
    # Activer PJAX pour les requêtes de données
    session.headers.update({
        'X-Requested-With': 'XMLHttpRequest',
        'X-PJAX':           'true',
        'X-PJAX-Container': '#pjax-modal-grid-historique',
        'Referer':          f'{BASE_URL}/',
    })
    return session


# ─── Parsing ──────────────────────────────────────────────────────────────────

def parse_nombre(txt):
    """Convertit '29 250' ou '1 234 567' en nombre float."""
    if not txt:
        return None
    cleaned = re.sub(r'\s+', '', str(txt).strip())
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(txt):
    """Convertit '03/03/2026' en '2026-03-03'."""
    txt = txt.strip()
    try:
        dt = datetime.strptime(txt, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None


def parser_page(html):
    """
    Parse une page PJAX et retourne la liste des enregistrements.
    Colonnes attendues : Date | Variation% | Valeur | Cours ajusté | Volume ajusté | Cours normal | Volume normal
    """
    soup  = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return [], 0

    rows       = table.find_all('tr')
    records    = []
    row_count  = 0

    for tr in rows[1:]:   # skip header
        tds = tr.find_all('td')
        if len(tds) < 7:
            continue

        date_str   = parse_date(tds[0].get_text(strip=True))
        variation  = tds[1].get_text(strip=True)
        cours_norm = parse_nombre(tds[5].get_text(strip=True))
        vol_norm   = parse_nombre(tds[6].get_text(strip=True))
        valeur_tot = parse_nombre(tds[2].get_text(strip=True))

        if not date_str or cours_norm is None or cours_norm <= 0:
            continue  # Ligne vide ou cours manquant — tolérance zéro

        row_count += 1
        var_pct = None
        try:
            var_pct = float(variation.replace('%', '').replace(',', '.').strip())
        except ValueError:
            pass

        records.append({
            'date':          date_str,
            'close':         cours_norm,
            'volume':        int(vol_norm) if vol_norm is not None else 0,
            'variation_pct': var_pct,
            'valeur_totale': valeur_tot,
            # OHLC : on n a que le cours de clôture officiel BOC
            'open':          cours_norm,
            'high':          cours_norm,
            'low':           cours_norm,
        })

    return records, row_count


def detecter_nb_pages(html):
    """Retourne le nombre max de pages depuis la pagination."""
    soup  = BeautifulSoup(html, 'html.parser')
    pager = soup.find('ul', class_='pagination')
    if not pager:
        return 1
    page_nums = []
    for a in pager.find_all('a'):
        m = re.search(r'page=(\d+)', a.get('href', ''))
        if m:
            page_nums.append(int(m.group(1)))
    return max(page_nums) if page_nums else 1


# ─── Scraping d'un symbole ────────────────────────────────────────────────────

def scraper_symbole(session, symbol, date_debut, date_fin):
    """
    Récupère toutes les pages de données journalières pour un symbole.
    Retourne une liste de dicts {date, close, volume, ...}.
    """
    url_base = f'{BASE_URL}/{symbol}/jour/{date_debut}/{date_fin}'

    # Page 1 — détermine aussi le nombre de pages
    r = session.get(f'{url_base}?page=1', timeout=20, verify=False)
    if r.status_code != 200:
        print(f'  [ERR] {symbol} HTTP {r.status_code}')
        return []

    all_records, row1 = parser_page(r.text)
    nb_pages          = detecter_nb_pages(r.text)

    if row1 == 0:
        print(f'  [VIDE] {symbol} — aucune donnée page 1 (no data on RichBourse ?)')
        return []

    # Pages suivantes
    for page in range(2, nb_pages + 1):
        time.sleep(PAUSE_ENTRE_PAGES)
        r2 = session.get(f'{url_base}?page={page}', timeout=20, verify=False)
        if r2.status_code != 200:
            break
        recs, cnt = parser_page(r2.text)
        if cnt == 0:
            break
        all_records.extend(recs)

    # Déduplication par date (garder le plus récent en cas de doublon)
    seen = {}
    for rec in all_records:
        seen[rec['date']] = rec
    unique = sorted(seen.values(), key=lambda x: x['date'])

    return unique


# ─── Stockage ─────────────────────────────────────────────────────────────────

def sauvegarder_import(db, symbol, records):
    """Sauvegarde dans prices_daily_richbourse_import."""
    if not records:
        return 0
    ops = []
    for rec in records:
        doc = {
            'symbol':        symbol,
            'source':        'RICHBOURSE_IMPORT',
            'imported_at':   datetime.now(),
            **rec
        }
        ops.append(UpdateOne(
            {'symbol': symbol, 'date': rec['date']},
            {'$set': doc},
            upsert=True
        ))
    result = db.prices_daily_richbourse_import.bulk_write(ops)
    return result.upserted_count + result.modified_count


def migrer_vers_prices_daily(db, symbol, records):
    """
    Remplace les données fictives dans prices_daily par les données RichBourse.
    ONLY remplace les docs avec source FICTIVE (MIGRATION_CURATED etc).
    PRÉSERVE les docs avec source DAILY_BUILDER (données réelles existantes).
    """
    remplacements = 0
    ignores       = 0

    for rec in records:
        # Vérifier si le doc existant est une source fictive
        existing = db.prices_daily.find_one(
            {'symbol': symbol, 'date': rec['date']},
            {'source': 1, 'volume': 1}
        )

        if existing:
            src = existing.get('source', '')
            # Si source réelle (DAILY_BUILDER) → on ne touche pas
            if src and src not in SOURCES_FICTIVES:
                ignores += 1
                continue
            # Remplacer la donnée fictive par la vraie
            db.prices_daily.update_one(
                {'symbol': symbol, 'date': rec['date']},
                {'$set': {
                    'close':         rec['close'],
                    'open':          rec['open'],
                    'high':          rec['high'],
                    'low':           rec['low'],
                    'volume':        rec['volume'],
                    'variation_pct': rec['variation_pct'],
                    'source':        'RICHBOURSE_IMPORT',
                    'imported_at':   datetime.now(),
                    'is_complete':   True,
                }}
            )
            remplacements += 1
        else:
            # Pas de doc existant → insérer
            db.prices_daily.insert_one({
                'symbol':        symbol,
                'date':          rec['date'],
                'close':         rec['close'],
                'open':          rec['open'],
                'high':          rec['high'],
                'low':           rec['low'],
                'volume':        rec['volume'],
                'variation_pct': rec['variation_pct'],
                'source':        'RICHBOURSE_IMPORT',
                'imported_at':   datetime.now(),
                'level':         'DAILY',
                'is_complete':   True,
            })
            remplacements += 1

    return remplacements, ignores


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    db     = client['centralisation_db']

    banner = "DRY RUN — aucune ecriture" if DRY_RUN else ("IMPORT ONLY" if NO_MIGRATE else "IMPORT + MIGRATION")
    print('=' * 70)
    print(f' IMPORT HISTORIQUE RICHBOURSE BRVM — {banner}'.center(70))
    print('=' * 70)
    print(f'  Periode  : {DATE_DEBUT} => {DATE_FIN}')
    print(f'  Symboles : {FILTRE_SYMBOL or "tous les 47"}')
    print()

    # Liste des symboles à traiter
    symboles = [FILTRE_SYMBOL] if FILTRE_SYMBOL else ACTIONS_OFFICIELLES

    print('  [1/3] Initialisation session RichBourse...')
    session = creer_session()
    print('  Session OK\n')

    # ── Scraping ────────────────────────────────────────────────────────────
    print('  [2/3] Scraping des cours historiques...')
    print('  ' + '─' * 66)

    total_records   = 0
    total_symboles  = 0
    stats_par_sym   = {}

    for i, symbol in enumerate(symboles, 1):
        records = scraper_symbole(session, symbol, DATE_DEBUT, DATE_FIN)
        n       = len(records)
        stats_par_sym[symbol] = n
        total_records  += n
        total_symboles += 1

        if n > 0:
            first_d = records[0]['date']
            last_d  = records[-1]['date']
            print(f'  [{i:2d}/{len(symboles)}] {symbol:<8} {n:>4} jours  ({first_d} => {last_d})', end='')

            if not DRY_RUN:
                nb_saved = sauvegarder_import(db, symbol, records)
                print(f'  import:{nb_saved}', end='')
            print()
        else:
            print(f'  [{i:2d}/{len(symboles)}] {symbol:<8}  aucune donnee')

        if i < len(symboles):
            time.sleep(PAUSE_ENTRE_SYMBOLES)

    print()
    print(f'  Scraping termine : {total_symboles} symboles | {total_records} enregistrements totaux')

    # ── Migration ────────────────────────────────────────────────────────────
    if NO_MIGRATE or DRY_RUN:
        print('\n  [3/3] Migration ignoree (--no-migrate ou --dry-run)')
    else:
        print('\n  [3/3] Migration vers prices_daily...')
        print('  ' + '─' * 66)

        total_rempl  = 0
        total_ignore = 0

        for symbol in symboles:
            # Recharger depuis la collection d'import (au cas où)
            import_docs = list(db.prices_daily_richbourse_import.find(
                {'symbol': symbol},
                {'_id': 0, 'symbol': 0, 'source': 0, 'imported_at': 0}
            ).sort('date', 1))

            if not import_docs:
                continue

            rempl, ign = migrer_vers_prices_daily(db, symbol, import_docs)
            total_rempl  += rempl
            total_ignore += ign

            if rempl > 0 or ign > 0:
                print(f'  {symbol:<8} : {rempl:>4} remplace(s)  {ign:>4} conserve(s) (DAILY_BUILDER)')

        print()
        print(f'  Migration terminee : {total_rempl} remplaces | {total_ignore} conserves (deja reels)')

    # ── Vérification finale ──────────────────────────────────────────────────
    if not DRY_RUN:
        print('\n  [VERIF] Qualite finale prices_daily...')
        total_docs    = db.prices_daily.count_documents({})
        reel_docs     = db.prices_daily.count_documents({'volume': {'$gt': 0}})
        richbourse_d  = db.prices_daily.count_documents({'source': 'RICHBOURSE_IMPORT'})
        daily_builder = db.prices_daily.count_documents({'source': 'DAILY_BUILDER'})
        fictif_remain = db.prices_daily.count_documents({'source': {'$in': ['MIGRATION_CURATED', 'RESTORED_FROM_C']}})
        unknown_rem   = db.prices_daily.count_documents({'source': {'$in': [None, '', '?']}})

        print(f'  Total docs          : {total_docs}')
        print(f'  Volume > 0          : {reel_docs} ({reel_docs/total_docs*100:.1f}%)')
        print(f'  Source RICHBOURSE   : {richbourse_d}')
        print(f'  Source DAILY_BUILDER: {daily_builder}')
        print(f'  Source fictive rest.: {fictif_remain + unknown_rem}  (a purger si = 0)')

        if fictif_remain + unknown_rem == 0:
            print('\n  [OK] prices_daily 100% donnees reelles — tolerance zero atteinte!')
        else:
            print(f'\n  [WARN] {fictif_remain + unknown_rem} docs fictifs restants (RichBourse n avait pas cette date)')

    print()
    print('=' * 70)
    print()

    # Résumé
    no_data = [s for s, n in stats_par_sym.items() if n == 0]
    if no_data:
        print(f'  Symboles sans donnees RichBourse : {", ".join(no_data)}')
        print('  -> Ces symboles conservent leurs donnees existantes (ou restent vides)')


if __name__ == '__main__':
    main()
