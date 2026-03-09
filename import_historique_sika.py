#!/usr/bin/env python3
"""
IMPORT HISTORIQUE BRVM DEPUIS SIKA FINANCE
==========================================
Utilise l'API JSON interne de Sika Finance :
  POST /api/general/GetHistos
  Body: {"ticker": "SNTS.sn", "datedeb": "DD/MM/YYYY", "datefin": "DD/MM/YYYY", "xperiod": "0"}
  xperiod=0  → données journalières avec filtre de dates exact
  Max 3 mois par requête → découpage automatique en fenêtres trimestrielles

TOLÉRANCE ZÉRO :
  - Aucune donnée inventée : close=0 → rejeté
  - DAILY_BUILDER et RICHBOURSE_IMPORT jamais écrasés
  - Seules les dates absentes ou fictives sont complétées

Usage :
  python import_historique_sika.py                        # tous les 47 symboles
  python import_historique_sika.py --symbol SNTS          # 1 symbole
  python import_historique_sika.py --from 2020-01-01 --to 2022-12-31
  python import_historique_sika.py --dry-run              # test sans écriture MongoDB
  python import_historique_sika.py --no-migrate           # import buffer seul
"""

import sys
import time
import json
import warnings
from datetime import datetime, timedelta, date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore')

import requests
from pymongo import MongoClient, UpdateOne

# ─── CONFIG ───────────────────────────────────────────────────────────────────

FILTRE_SYMBOL = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--symbol'), None)
DRY_RUN       = '--dry-run'    in sys.argv
NO_MIGRATE    = '--no-migrate' in sys.argv

_from_arg = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--from'), None)
_to_arg   = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--to'),   None)

DATE_DEBUT = _from_arg or '2020-01-01'
DATE_FIN   = _to_arg   or datetime.now().strftime('%Y-%m-%d')

API_URL  = 'https://www.sikafinance.com/api/general/GetHistos'
BASE_REF = 'https://www.sikafinance.com/marches/historiques'

# Fenêtre max autorisée par l'API Sika Finance (3 mois = ~91 jours)
WINDOW_DAYS = 88

# Pauses pour ne pas surcharger le serveur
PAUSE_ENTRE_FENETRES  = 0.8   # secondes entre 2 fenêtres d'un même symbole
PAUSE_ENTRE_SYMBOLES  = 2.0   # secondes entre symboles
MAX_RETRIES           = 3

# Sources réelles — NE JAMAIS écraser
SOURCES_REELLES  = {'DAILY_BUILDER', 'RICHBOURSE_IMPORT', 'SIKA_IMPORT'}

# Sources fictives — remplaçables
SOURCES_FICTIVES = {
    None, '', '?', 'MIGRATION_CURATED', 'RESTORED_FROM_C',
    'MIGRATION_CURATED_DAILY', 'RESTORED_FROM_CSV',
}

# ─── MAPPING 47 SYMBOLES → TICKER SIKA FINANCE ────────────────────────────────

SIKA_TICKERS = {
    # Côte d'Ivoire
    "ABJC": "ABJC.ci", "BICC": "BICC.ci", "BOAC": "BOAC.ci",
    "CABC": "CABC.ci", "CFAC": "CFAC.ci", "CIEC": "CIEC.ci",
    "ECOC": "ECOC.ci", "FTSC": "FTSC.ci", "NEIC": "NEIC.ci",
    "NSBC": "NSBC.ci", "NTLC": "NTLC.ci", "ORAC": "ORAC.ci",
    "PALC": "PALC.ci", "PRSC": "PRSC.ci", "SAFC": "SAFC.ci",
    "SCRC": "SCRC.ci", "SDCC": "SDCC.ci", "SDSC": "SDSC.ci",
    "SEMC": "SEMC.ci", "SGBC": "SGBC.ci", "SHEC": "SHEC.ci",
    "SIBC": "SIBC.ci", "SICC": "SICC.ci", "SIVC": "SIVC.ci",
    "SLBC": "SLBC.ci", "SMBC": "SMBC.ci", "SOGC": "SOGC.ci",
    "SPHC": "SPHC.ci", "STAC": "STAC.ci", "STBC": "STBC.ci",
    "TTLC": "TTLC.ci", "UNLC": "UNLC.ci", "UNXC": "UNXC.ci",
    # Sénégal
    "BOAS": "BOAS.sn", "SNTS": "SNTS.sn", "TTLS": "TTLS.sn",
    # Burkina Faso
    "BICB": "BICB.bf", "BNBC": "BNBC.bf", "BOABF": "BOABF.bf",
    "CBIBF": "CBIBF.bf", "LNBB": "LNBB.bf", "ONTBF": "ONTBF.bf",
    # Bénin
    "BOAB": "BOAB.bj",
    # Togo
    "ETIT": "ETIT.tg", "ORGT": "ORGT.tg",
    # Mali
    "BOAM": "BOAM.ml",
    # Niger
    "BOAN": "BOAN.ne",
}

ACTIONS_OFFICIELLES = sorted(SIKA_TICKERS.keys())


# ─── SESSION HTTP ──────────────────────────────────────────────────────────────

def creer_session():
    """Session HTTP avec headers navigateur et warm-up cookies Sika Finance."""
    s = requests.Session()
    s.headers.update({
        'User-Agent':     ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/123.0.0.0 Safari/537.36'),
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8',
        'Accept':          'application/json, text/plain, */*',
        'Content-Type':    'application/json;charset=UTF-8',
        'Origin':          'https://www.sikafinance.com',
        'Connection':      'keep-alive',
    })
    # Warm-up : établir les cookies de session
    try:
        s.get('https://www.sikafinance.com/', timeout=20, verify=False)
    except Exception:
        pass
    return s


def appel_api(session, ticker, datedeb_str, datefin_str):
    """
    Appel POST /api/general/GetHistos pour une fenêtre de dates.
    datedeb_str, datefin_str : format 'DD/MM/YYYY'

    Retourne (list[dict], error_code) :
      - list[dict] avec clés 'Date','Open','High','Low','Close','Volume'
      - error_code : '' | 'toolong' | 'baddt' | 'nodata' | 'http_err' | 'exception'
    """
    payload = {
        'ticker':  ticker,
        'datedeb': datedeb_str,
        'datefin': datefin_str,
        'xperiod': '0',          # 0 = journalier avec dates exactes
    }

    session.headers.update({
        'Referer': f'{BASE_REF}/{ticker}',
    })

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.post(
                API_URL,
                data=json.dumps(payload),
                timeout=30,
                verify=False,
            )
            if r.status_code != 200:
                if attempt == MAX_RETRIES:
                    return [], f'http_{r.status_code}'
                time.sleep(2 ** attempt)
                continue

            data = r.json()
            error = data.get('error', '')
            lst   = data.get('lst') or []

            return lst, error

        except Exception as e:
            if attempt == MAX_RETRIES:
                return [], f'exception:{e}'
            time.sleep(2 ** attempt)

    return [], 'max_retries'


# ─── DÉCOUPAGE EN FENÊTRES TRIMESTRIELLES ─────────────────────────────────────

def decouper_fenetres(date_debut_ymd, date_fin_ymd, window_days=WINDOW_DAYS):
    """
    Découpe [date_debut, date_fin] en fenêtres de window_days jours max.
    Retourne list[(debut_str_fr, fin_str_fr)] au format 'DD/MM/YYYY'.
    """
    dt_debut = datetime.strptime(date_debut_ymd, '%Y-%m-%d').date()
    dt_fin   = datetime.strptime(date_fin_ymd,   '%Y-%m-%d').date()

    fenetres = []
    current  = dt_debut

    while current <= dt_fin:
        fin_fenetre = min(current + timedelta(days=window_days - 1), dt_fin)
        fenetres.append((
            current.strftime('%d/%m/%Y'),
            fin_fenetre.strftime('%d/%m/%Y'),
        ))
        current = fin_fenetre + timedelta(days=1)

    return fenetres


# ─── PARSING DES RECORDS API ──────────────────────────────────────────────────

def normaliser_record(record_api):
    """
    Convertit un record JSON Sika Finance en dict compatible prices_daily.
    Format API : {'Date': 'DD/MM/YYYY', 'Open': int, 'High': int,
                  'Low': int, 'Close': int, 'Volume': int}
    TOLÉRANCE ZÉRO : retourne None si Close manquant ou <= 0.
    """
    try:
        close = float(record_api.get('Close', 0) or 0)
        if close <= 0:
            return None   # tolérance zéro

        # Convertir la date DD/MM/YYYY → YYYY-MM-DD
        date_raw = str(record_api.get('Date', '')).strip()
        try:
            date_ymd = datetime.strptime(date_raw, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            return None

        open_  = float(record_api.get('Open',   0) or 0) or close
        high   = float(record_api.get('High',   0) or 0) or close
        low    = float(record_api.get('Low',    0) or 0) or close
        volume = int(record_api.get('Volume',   0) or 0)

        # Calculer variation_pct si possible (nécessite contexte — pas disponible ici)
        return {
            'date':          date_ymd,
            'open':          open_,
            'high':          max(open_, high, close),   # cohérence OHLC
            'low':           min(open_, low,  close),
            'close':         close,
            'volume':        volume,
            'variation_pct': None,   # calculé en post-traitement si nécessaire
        }
    except Exception:
        return None


# ─── SCRAPING D'UN SYMBOLE ────────────────────────────────────────────────────

def scraper_symbole(session, symbol, date_debut_ymd, date_fin_ymd):
    """
    Scrape l'historique complet pour un symbole sur la plage demandée
    en découpant automatiquement en fenêtres de 88 jours.

    Retourne list[dict] dédupliqué, trié par date ASC.
    """
    ticker = SIKA_TICKERS.get(symbol)
    if not ticker:
        print(f'  [SKIP] {symbol} — ticker Sika non défini')
        return []

    fenetres = decouper_fenetres(date_debut_ymd, date_fin_ymd)
    all_records = {}   # date → record (déduplication)

    for i_w, (deb_fr, fin_fr) in enumerate(fenetres, 1):
        lst, err = appel_api(session, ticker, deb_fr, fin_fr)

        if err == 'nodata':
            pass   # fenêtre sans données (normal pour certaines périodes)
        elif err == 'toolong':
            print(f'    [WARN] {symbol} fenetre {deb_fr}→{fin_fr} : toolong (réduire WINDOW_DAYS)')
        elif err.startswith('http') or err.startswith('exception'):
            print(f'    [ERR] {symbol} fenetre {i_w}/{len(fenetres)} : {err}')

        for rec_raw in lst:
            rec = normaliser_record(rec_raw)
            if rec:
                all_records[rec['date']] = rec

        if i_w < len(fenetres):
            time.sleep(PAUSE_ENTRE_FENETRES)

    return sorted(all_records.values(), key=lambda x: x['date'])


# ─── GESTION DES DATES MANQUANTES ─────────────────────────────────────────────

def obtenir_couverture_reelle(db, symbol):
    """
    Retourne l'ensemble des dates avec données RÉELLES dans prices_daily.
    (ignore les sources fictives)
    """
    docs = db.prices_daily.find(
        {
            'symbol': symbol,
            'source': {'$in': list(SOURCES_REELLES)},
            'close':  {'$gt': 0},
        },
        {'date': 1, '_id': 0}
    )
    return {doc['date'] for doc in docs}


def calculer_plage_manquante(date_debut, date_fin, dates_reelles):
    """
    Retourne (premiere_date_manquante, derniere_date_manquante)
    en ne considérant que les jours ouvrables (lun-ven).
    Retourne (None, None) si toutes les dates ouvrables sont couvertes.
    """
    dt_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    dt_fin   = datetime.strptime(date_fin,   '%Y-%m-%d').date()

    manquantes = []
    current    = dt_debut
    while current <= dt_fin:
        if current.weekday() < 5:   # lun=0 … ven=4
            ds = current.strftime('%Y-%m-%d')
            if ds not in dates_reelles:
                manquantes.append(ds)
        current += timedelta(days=1)

    if not manquantes:
        return None, None
    return manquantes[0], manquantes[-1]


# ─── STOCKAGE ─────────────────────────────────────────────────────────────────

def sauvegarder_buffer(db, symbol, records):
    """Upsert dans prices_daily_sika_import (buffer intermédiaire)."""
    if not records:
        return 0
    now = datetime.now()
    ops = [
        UpdateOne(
            {'symbol': symbol, 'date': rec['date']},
            {'$set': {'symbol': symbol, 'source': 'SIKA_IMPORT',
                      'imported_at': now, **rec}},
            upsert=True,
        )
        for rec in records
    ]
    result = db.prices_daily_sika_import.bulk_write(ops)
    return result.upserted_count + result.modified_count


def migrer_vers_prices_daily(db, symbol, records):
    """
    Insère / remplace dans prices_daily en respectant la priorité des sources.

    Règles :
      PRÉSERVE  → DAILY_BUILDER, RICHBOURSE_IMPORT, SIKA_IMPORT (données réelles)
      REMPLACE  → sources fictives (MIGRATION_CURATED, RESTORED_FROM_C, etc.)
      INSÈRE    → dates absentes de prices_daily

    Retourne (inseres, remplaces, ignores).
    """
    inseres = remplaces = ignores = 0
    now = datetime.now()

    for rec in records:
        existing = db.prices_daily.find_one(
            {'symbol': symbol, 'date': rec['date']},
            {'source': 1, '_id': 0}
        )

        if existing:
            src = existing.get('source', '')
            if src in SOURCES_REELLES:
                ignores += 1
                continue   # données réelles existantes : INTOUCHABLES

            # Source fictive → remplacer
            db.prices_daily.update_one(
                {'symbol': symbol, 'date': rec['date']},
                {'$set': {
                    'open':          rec['open'],
                    'high':          rec['high'],
                    'low':           rec['low'],
                    'close':         rec['close'],
                    'volume':        rec['volume'],
                    'variation_pct': rec['variation_pct'],
                    'source':        'SIKA_IMPORT',
                    'imported_at':   now,
                    'is_complete':   True,
                    'data_quality':  'REAL_HISTORICAL',
                }}
            )
            remplaces += 1

        else:
            # Date absente → insérer
            db.prices_daily.insert_one({
                'symbol':        symbol,
                'date':          rec['date'],
                'open':          rec['open'],
                'high':          rec['high'],
                'low':           rec['low'],
                'close':         rec['close'],
                'volume':        rec['volume'],
                'variation_pct': rec['variation_pct'],
                'source':        'SIKA_IMPORT',
                'imported_at':   now,
                'level':         'DAILY',
                'is_complete':   True,
                'data_quality':  'REAL_HISTORICAL',
            })
            inseres += 1

    return inseres, remplaces, ignores


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    db     = client['centralisation_db']

    banner = ('DRY RUN — aucune ecriture' if DRY_RUN else
             ('IMPORT ONLY'               if NO_MIGRATE else
              'IMPORT + MIGRATION'))

    # Compter les fenêtres totales pour estimer l'avancement
    nb_fenetres_exemple = len(decouper_fenetres(DATE_DEBUT, DATE_FIN))

    print('=' * 72)
    print(f'  IMPORT HISTORIQUE SIKA FINANCE BRVM — {banner}'.center(72))
    print('=' * 72)
    print(f'  API           : POST /api/general/GetHistos (xperiod=0 daily)')
    print(f'  Plage         : {DATE_DEBUT} -> {DATE_FIN}')
    print(f'  Symboles      : {FILTRE_SYMBOL or f"tous les {len(ACTIONS_OFFICIELLES)}"}')
    print(f'  Fenetres/sym  : ~{nb_fenetres_exemple} fenetres de {WINDOW_DAYS}j')
    print(f'  Protection    : DAILY_BUILDER + RICHBOURSE_IMPORT preserves')
    print()

    symboles = [FILTRE_SYMBOL] if FILTRE_SYMBOL else ACTIONS_OFFICIELLES

    # ── Session ──────────────────────────────────────────────────────────────
    print('  [1/3] Initialisation session Sika Finance...')
    session = creer_session()
    print('  Session OK\n')

    # ── Scraping ─────────────────────────────────────────────────────────────
    print('  [2/3] Collecte des cours historiques...')
    print('  ' + '-' * 68)

    stats         = {}
    records_cache = {}
    total_recolte = 0

    for i, symbol in enumerate(symboles, 1):

        # Calcul de la plage manquante pour ce symbole
        if not DRY_RUN:
            dates_reelles = obtenir_couverture_reelle(db, symbol)
        else:
            dates_reelles = set()

        debut_manq, fin_manq = calculer_plage_manquante(
            DATE_DEBUT, DATE_FIN, dates_reelles
        )

        if debut_manq is None:
            couverts = len(dates_reelles)
            print(f'  [{i:2d}/{len(symboles)}] {symbol:<8} OK donnees completes ({couverts} jours reels)')
            stats[symbol] = 0
            continue

        nb_fenetres = len(decouper_fenetres(debut_manq, fin_manq))
        couverts    = len(dates_reelles)
        print(f'  [{i:2d}/{len(symboles)}] {symbol:<8} '
              f'{nb_fenetres} fenetres ({debut_manq}->{fin_manq}) '
              f'[existants:{couverts}]', end=' ', flush=True)

        records = scraper_symbole(session, symbol, debut_manq, fin_manq)
        n       = len(records)
        stats[symbol]         = n
        records_cache[symbol] = records
        total_recolte        += n

        if n > 0:
            first_d = records[0]['date']
            last_d  = records[-1]['date']
            msg = f'-> {n} jours ({first_d}..{last_d})'
            if not DRY_RUN:
                nb_buf = sauvegarder_buffer(db, symbol, records)
                msg += f' buf:{nb_buf}'
            print(msg)
        else:
            print('-> 0 (Sika sans donnees sur cette periode)')

        if i < len(symboles):
            time.sleep(PAUSE_ENTRE_SYMBOLES)

    print()
    print(f'  Collecte terminee : {len(symboles)} symboles | '
          f'{total_recolte} nouvelles entrees')

    # ── Migration ────────────────────────────────────────────────────────────
    if NO_MIGRATE or DRY_RUN:
        print(f'\n  [3/3] Migration ignoree ({banner})')
    else:
        print('\n  [3/3] Migration vers prices_daily...')
        print('  ' + '-' * 68)

        total_ins = total_repl = total_ign = 0

        for symbol in symboles:
            records = records_cache.get(symbol, [])
            if not records:
                continue
            ins, repl, ign = migrer_vers_prices_daily(db, symbol, records)
            total_ins  += ins
            total_repl += repl
            total_ign  += ign
            if ins + repl > 0:
                print(f'  {symbol:<8} : +{ins} inseres  ~{repl} remplaces  ={ign} conserves')

        print()
        print(f'  Migration : +{total_ins} inseres | '
              f'~{total_repl} remplaces (fictifs) | '
              f'={total_ign} conserves (reels)')

    # ── Vérification finale ───────────────────────────────────────────────────
    if not DRY_RUN:
        print('\n  [VERIF] Etat prices_daily apres import Sika Finance...')
        total  = db.prices_daily.count_documents({})
        reels  = db.prices_daily.count_documents(
            {'source': {'$in': ['DAILY_BUILDER', 'RICHBOURSE_IMPORT', 'SIKA_IMPORT']}}
        )
        sika   = db.prices_daily.count_documents({'source': 'SIKA_IMPORT'})
        richb  = db.prices_daily.count_documents({'source': 'RICHBOURSE_IMPORT'})
        daily  = db.prices_daily.count_documents({'source': 'DAILY_BUILDER'})
        fictif = db.prices_daily.count_documents(
            {'source': {'$in': list(SOURCES_FICTIVES - {None})}}
        ) + db.prices_daily.count_documents({'source': {'$exists': False}})

        pct = reels / total * 100 if total else 0
        print(f'  Total prices_daily   : {total:,}')
        print(f'  Sources reelles      : {reels:,}  ({pct:.1f}%)')
        print(f'    DAILY_BUILDER      : {daily:,}')
        print(f'    RICHBOURSE_IMPORT  : {richb:,}')
        print(f'    SIKA_IMPORT        : {sika:,}')
        print(f'  Sources fictives rest: {fictif:,}')
        if fictif == 0:
            print()
            print('  [OK] prices_daily 100% donnees reelles — TOLERANCE ZERO atteinte!')
        else:
            print(f'\n  [WARN] {fictif} docs fictifs restants')

    print()
    print('=' * 72)

    vides = [s for s, n in stats.items() if n == 0 and s in records_cache]
    if vides:
        print(f'\n  Symboles sans donnees Sika : {", ".join(vides)}')


if __name__ == '__main__':
    main()
