#!/usr/bin/env python3
"""
BOAKSDIRECT ORDERBOOK COLLECTOR
================================
Collecte le carnet d'ordres BRVM en temps réel via boaksdirect.com:9092.

Phase 1 — DÉCOUVERTE (mode par défaut) :
  Ouvre le navigateur, intercepte tous les messages WebSocket et requêtes XHR,
  les sauvegarde dans orderbook_discovery.json pour analyser la structure API.

Phase 2 — PRODUCTION (--collect) :
  Utilise la structure découverte pour collecter le carnet de tous les symboles
  BRVM et stocker dans MongoDB (collection: orderbook_live).

Usage :
  .venv\Scripts\python.exe scripts/connectors/boaksdirect_orderbook.py
  .venv\Scripts\python.exe scripts/connectors/boaksdirect_orderbook.py --collect
  .venv\Scripts\python.exe scripts/connectors/boaksdirect_orderbook.py --symbol SNTS
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

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
logger = logging.getLogger("BOA_ORDERBOOK")

# ─── Paramètres CLI ────────────────────────────────────────────────────────────
MODE_COLLECT  = "--collect" in sys.argv
FILTRE_SYMBOL = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == "--symbol"), None)
DISCOVERY_FILE = str(BASE_DIR / "orderbook_discovery.json")

BOAKSDIRECT_URL = "https://www.boaksdirect.com"
BOAKSDIRECT_API  = "https://www.boaksdirect.com:9092"
MARKET_PAGE      = f"{BOAKSDIRECT_URL}/marche.html"

# ─── Actions BRVM cibles ───────────────────────────────────────────────────────
ACTIONS_BRVM = [
    "ABJC", "BICB", "BICC", "BNBC", "BOAB", "BOABF", "BOAC", "BOAM", "BOAN", "BOAS",
    "CABC", "CBIBF", "CFAC", "CIEC", "ECOC", "ETIT", "FTSC", "LNBB", "NEIC", "NSBC",
    "NTLC", "ONTBF", "ORAC", "ORGT", "PALC", "PRSC", "SAFC", "SCRC", "SDCC", "SDSC",
    "SEMC", "SGBC", "SHEC", "SIBC", "SICC", "SIVC", "SLBC", "SMBC", "SNTS", "SOGC",
    "SPHC", "STAC", "STBC", "TTLC", "TTLS", "UNLC", "UNXC",
]

# ─── Tentative d'import Selenium ───────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    logger.error("[IMPORT] selenium non disponible — pip install selenium")


# ─── Phase 1 : Découverte automatique ─────────────────────────────────────────

def creer_driver_avec_capture():
    """
    Crée un ChromeDriver avec Chrome DevTools Protocol activé.
    Intercepte WebSocket frames + XHR requests pendant la navigation.
    """
    opts = Options()
    # Pas de headless : le site peut avoir des protections anti-bot
    # opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=opts)
    # Supprimer le flag navigator.webdriver
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    return driver


def extraire_messages_performance(driver) -> List[Dict]:
    """
    Extrait tous les messages WebSocket et XHR depuis les logs de performance Chrome.
    """
    messages = []
    try:
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                msg = json.loads(entry.get("message", "{}"))
                method = msg.get("message", {}).get("method", "")
                # WebSocket frames
                if method in (
                    "Network.webSocketFrameSent",
                    "Network.webSocketFrameReceived",
                    "Network.webSocketCreated",
                    "Network.webSocketHandshakeResponseReceived",
                ):
                    messages.append({
                        "type":    "websocket",
                        "method":  method,
                        "params":  msg.get("message", {}).get("params", {}),
                        "ts":      entry.get("timestamp"),
                    })
                # XHR / Fetch
                elif method in ("Network.requestWillBeSent", "Network.responseReceived"):
                    params = msg.get("message", {}).get("params", {})
                    req    = params.get("request", params.get("response", {}))
                    url    = req.get("url", "")
                    if "9092" in url or "boaksdirect" in url.lower():
                        messages.append({
                            "type":   "xhr",
                            "method": method,
                            "url":    url,
                            "params": params,
                            "ts":     entry.get("timestamp"),
                        })
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"[LOG] Extraction logs perf: {e}")
    return messages


def run_discovery():
    """
    Phase 1 : Ouvre le navigateur, navigue sur le carnet d'ordres,
    enregistre tous les échanges réseau dans orderbook_discovery.json.
    """
    if not HAS_SELENIUM:
        logger.error("[DISCOVERY] Selenium requis. pip install selenium")
        return

    logger.info("=" * 60)
    logger.info("  PHASE 1 — DÉCOUVERTE API BOAKSDIRECT")
    logger.info("=" * 60)
    logger.info(f"  URL cible  : {MARKET_PAGE}")
    logger.info(f"  API server : {BOAKSDIRECT_API}")
    logger.info(f"  Sortie     : {DISCOVERY_FILE}")
    logger.info("")
    logger.info("  >>> La page va s'ouvrir dans Chrome.")
    logger.info("  >>> Connecte-toi à ton compte BOA Direct.")
    logger.info("  >>> Le script capture automatiquement tous les échanges réseau.")
    logger.info("  >>> Navigue vers différentes actions si possible.")
    logger.info("  >>> Appuie sur ENTRÉE dans ce terminal pour terminer la capture.")
    logger.info("")

    driver = creer_driver_avec_capture()
    all_messages = []
    capture_active = True

    def capture_loop():
        while capture_active:
            msgs = extraire_messages_performance(driver)
            all_messages.extend(msgs)
            time.sleep(2)

    t = threading.Thread(target=capture_loop, daemon=True)
    t.start()

    try:
        driver.get(MARKET_PAGE)
        input("\n  [Appuie sur ENTRÉE une fois connecté et après avoir vu le carnet...]\n")
    except KeyboardInterrupt:
        pass
    finally:
        capture_active = False
        time.sleep(1)

    # Dernière capture
    all_messages.extend(extraire_messages_performance(driver))
    driver.quit()

    # Déduplication
    seen = set()
    unique = []
    for m in all_messages:
        key = json.dumps(m, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            unique.append(m)

    # Sauvegarde
    result = {
        "capture_at":   datetime.now().isoformat(),
        "total_events": len(unique),
        "websocket_events": [m for m in unique if m["type"] == "websocket"],
        "xhr_events":       [m for m in unique if m["type"] == "xhr"],
        "raw":              unique,
    }

    with open(DISCOVERY_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"\n  [OK] {len(unique)} événements capturés → {DISCOVERY_FILE}")
    logger.info(f"       WebSocket : {len(result['websocket_events'])}")
    logger.info(f"       XHR/Fetch : {len(result['xhr_events'])}")

    # Analyse rapide
    logger.info("\n  [ANALYSE] Endpoints détectés :")
    urls_vus = set()
    for m in result["xhr_events"]:
        url = m.get("url", "")
        if url not in urls_vus:
            urls_vus.add(url)
            logger.info(f"    XHR  : {url}")
    for m in result["websocket_events"]:
        url = m.get("params", {}).get("url", "")
        if url and url not in urls_vus:
            urls_vus.add(url)
            logger.info(f"    WS   : {url}")

    analyser_discovery(result)


def analyser_discovery(result: Dict = None):
    """
    Analyse le fichier de découverte et extrait la structure du carnet.
    Peut être appelé séparément sur un fichier existant.
    """
    if result is None:
        if not Path(DISCOVERY_FILE).exists():
            logger.error(f"[ANALYSE] Fichier {DISCOVERY_FILE} introuvable — lancer sans --collect d'abord")
            return
        with open(DISCOVERY_FILE, "r", encoding="utf-8") as f:
            result = json.load(f)

    ws_events = result.get("websocket_events", [])
    xhr_events = result.get("xhr_events", [])

    print("\n" + "=" * 60)
    print("  ANALYSE STRUCTURE CARNET D'ORDRES")
    print("=" * 60)
    print(f"  WebSocket frames : {len(ws_events)}")
    print(f"  XHR/Fetch calls  : {len(xhr_events)}")

    # Extraire les payloads WebSocket
    ws_created = [m for m in ws_events if "Created" in m.get("method", "")]
    ws_data    = [m for m in ws_events if "Frame" in m.get("method", "")]

    if ws_created:
        print("\n  [WebSocket URLs]")
        for m in ws_created:
            url = m.get("params", {}).get("url", "?")
            print(f"    → {url}")

    if ws_data:
        print(f"\n  [WebSocket Frames — {len(ws_data)} messages]")
        for m in ws_data[:10]:  # Afficher les 10 premiers
            payload = m.get("params", {}).get("response", {}).get("payloadData", "")
            if not payload:
                payload = m.get("params", {}).get("request", {}).get("payloadData", "")
            if payload:
                print(f"    [{m['method'][-4:]}] {payload[:120]}")

    # Endpoints XHR
    if xhr_events:
        print(f"\n  [Endpoints XHR/REST]")
        for m in xhr_events[:20]:
            url = m.get("url", "?")
            print(f"    → {url}")

    print("\n  [GUIDE] Chercher dans les frames WebSocket :")
    print("    - champ 'symbol' ou 'valeur' ou 'titre'")
    print("    - tableaux 'bid'/'offre' et 'ask'/'demande'")
    print("    - champs 'qty'/'qte'/'quantite' et 'price'/'cours'")
    print("=" * 60)


# ─── Phase 2 : Collecteur de production ───────────────────────────────────────

def calculer_pressure_score(bids: List[Dict], asks: List[Dict]) -> Dict:
    """
    Calcule le score de pression achat/vente depuis le carnet d'ordres.

    Métriques :
      pressure_ratio  = vol_bid_top3 / vol_ask_top3
      pressure_score  = 0-100 (50=neutre, >70=pression achat, <30=pression vente)
      bid_wall        = True si 1 niveau > 3x la moyenne des autres niveaux bid
      liquidity_gap   = % entre meilleur ask et ask+1 (espace de hausse rapide)
    """
    # Volumes cumulés top 3 niveaux
    bid_vols = [b.get("qty", b.get("quantite", b.get("volume", 0))) for b in bids[:3]]
    ask_vols = [a.get("qty", a.get("quantite", a.get("volume", 0))) for a in asks[:3]]

    total_bid = sum(v for v in bid_vols if v)
    total_ask = sum(v for v in ask_vols if v)

    pressure_ratio = round(total_bid / total_ask, 3) if total_ask > 0 else 1.0

    # Score 0-100 : ratio 0.3→0, 1.0→50, 3.0→100
    pressure_score = max(0.0, min(100.0, (pressure_ratio - 0.3) / (3.0 - 0.3) * 100))

    # Bid wall : un niveau > 3x la moyenne
    bid_wall = False
    if len(bid_vols) >= 2:
        avg = sum(bid_vols) / len(bid_vols)
        bid_wall = any(v > 3 * avg for v in bid_vols) if avg > 0 else False

    # Liquidity gap entre meilleur ask et ask+1
    liquidity_gap_pct = 0.0
    if len(asks) >= 2:
        p1 = asks[0].get("price", asks[0].get("cours", 0))
        p2 = asks[1].get("price", asks[1].get("cours", 0))
        if p1 and p1 > 0 and p2 and p2 > 0:
            liquidity_gap_pct = round((p2 - p1) / p1 * 100, 2)

    # Signal
    if pressure_ratio >= 2.0:
        signal = "ACCUMULATION"
    elif pressure_ratio >= 1.5:
        signal = "PRESSION_ACHAT"
    elif pressure_ratio <= 0.5:
        signal = "DISTRIBUTION"
    elif pressure_ratio <= 0.7:
        signal = "PRESSION_VENTE"
    else:
        signal = "NEUTRE"

    return {
        "pressure_ratio":    pressure_ratio,
        "pressure_score":    round(pressure_score, 1),
        "signal":            signal,
        "bid_wall":          bid_wall,
        "liquidity_gap_pct": liquidity_gap_pct,
        "total_bid_vol":     total_bid,
        "total_ask_vol":     total_ask,
    }


def sauvegarder_orderbook(symbol: str, bids: List[Dict], asks: List[Dict],
                           spread: float, db) -> bool:
    """
    Sauvegarde le carnet d'ordres + métriques dans MongoDB (orderbook_live).
    Upsert par symbol — 1 document par action (dernière capture).
    """
    pressure = calculer_pressure_score(bids, asks)
    now = datetime.utcnow()

    doc = {
        "symbol":           symbol,
        "ts":               now.isoformat(),
        "bids":             bids[:5],   # top 5 niveaux
        "asks":             asks[:5],
        "spread":           spread,
        "pressure_ratio":   pressure["pressure_ratio"],
        "pressure_score":   pressure["pressure_score"],
        "signal":           pressure["signal"],
        "bid_wall":         pressure["bid_wall"],
        "liquidity_gap_pct": pressure["liquidity_gap_pct"],
        "total_bid_vol":    pressure["total_bid_vol"],
        "total_ask_vol":    pressure["total_ask_vol"],
    }

    try:
        db.orderbook_live.update_one(
            {"symbol": symbol},
            {"$set": doc},
            upsert=True
        )

        # Historique compressé (dernier point par heure)
        db.orderbook_history.update_one(
            {"symbol": symbol, "hour": now.strftime("%Y-%m-%dT%H")},
            {"$set": {
                "pressure_ratio":  pressure["pressure_ratio"],
                "pressure_score":  pressure["pressure_score"],
                "signal":          pressure["signal"],
                "ts":              now.isoformat(),
            }},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"[SAVE] {symbol}: {e}")
        return False


def run_collector_selenium(db):
    """
    Collecteur Selenium : navigue sur la page marché, parse le DOM directement
    pour extraire les carnets. Utile si l'API nécessite une session authentifiée.
    """
    if not HAS_SELENIUM:
        logger.error("[COLLECT] Selenium requis")
        return

    opts = Options()
    # opts.add_argument("--headless=new")  # Activer si pas d'interface
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=opts)
    symbols = [FILTRE_SYMBOL] if FILTRE_SYMBOL else ACTIONS_BRVM
    total_ok = 0

    try:
        driver.get(MARKET_PAGE)
        logger.info("  Connecte-toi puis appuie sur ENTRÉE...")
        input()

        logger.info(f"  Démarrage collecte {len(symbols)} symboles...")

        for sym in symbols:
            logger.info(f"  [{sym}] Chargement carnet...")

            # À adapter selon la structure réelle du site (révélée par la découverte)
            # Exemple générique — MODIFIER après analyse de orderbook_discovery.json
            try:
                # Chercher un champ de sélection de symbole
                field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='symbol'], select.symbol-select, [ng-model*='symbol']")
                field.clear()
                field.send_keys(sym)
                time.sleep(1.5)

                # Extraire les lignes du carnet
                bids = extraire_niveaux_dom(driver, "bid,achat,buy,offre")
                asks = extraire_niveaux_dom(driver, "ask,vente,sell,demande")

                if bids or asks:
                    saved = sauvegarder_orderbook(sym, bids, asks, 0.0, db)
                    if saved:
                        total_ok += 1
                        pres = calculer_pressure_score(bids, asks)
                        logger.info(f"  [{sym}] bid={len(bids)} ask={len(asks)} | pressure={pres['pressure_ratio']}x | {pres['signal']}")
                else:
                    logger.debug(f"  [{sym}] Aucun niveau d'ordre trouvé")

                time.sleep(1.0)

            except Exception as e:
                logger.debug(f"  [{sym}] Erreur DOM: {e}")
                continue

    finally:
        driver.quit()

    logger.info(f"\n  [OK] {total_ok}/{len(symbols)} carnets collectés")


def extraire_niveaux_dom(driver, keywords_css: str) -> List[Dict]:
    """
    Tente d'extraire les niveaux du carnet depuis le DOM.
    Stratégie générique — adaptée après découverte.
    """
    niveaux = []
    keywords = [k.strip() for k in keywords_css.split(",")]

    for kw in keywords:
        try:
            rows = driver.find_elements(
                By.CSS_SELECTOR,
                f"tr[class*='{kw}'], .{kw}-row, [data-side='{kw}'], "
                f"table.{kw} tr, .orders-{kw} tr"
            )
            for row in rows[:5]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    try:
                        price = float(cells[0].text.replace(" ", "").replace(",", ".") or 0)
                        qty   = float(cells[1].text.replace(" ", "").replace(",", ".") or 0)
                        if price > 0 and qty > 0:
                            niveaux.append({"price": price, "qty": qty})
                    except (ValueError, IndexError):
                        pass
            if niveaux:
                break
        except Exception:
            pass

    return niveaux


# ─── Injection dans decisions_finales_brvm ────────────────────────────────────

def injecter_orderbook_dans_decisions(db):
    """
    Lit les carnets MongoDB et enrichit decisions_finales_brvm
    avec pressure_score + signal orderbook.
    À appeler après chaque collecte de carnets.
    """
    carnets = list(db.orderbook_live.find())
    updated = 0
    for c in carnets:
        sym = c.get("symbol")
        if not sym:
            continue
        db.decisions_finales_brvm.update_many(
            {"symbol": sym, "archived": {"$ne": True}},
            {"$set": {
                "ob_pressure_ratio":  c.get("pressure_ratio"),
                "ob_pressure_score":  c.get("pressure_score"),
                "ob_signal":          c.get("signal"),
                "ob_bid_wall":        c.get("bid_wall"),
                "ob_liquidity_gap":   c.get("liquidity_gap_pct"),
                "ob_ts":              c.get("ts"),
            }}
        )
        updated += 1
    if updated:
        logger.info(f"  [INJECT] {updated} décisions enrichies avec orderbook pressure")
    return updated


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  BOAKSDIRECT ORDERBOOK COLLECTOR")
    print("=" * 60)

    if MODE_COLLECT:
        # Phase 2 — collecte de production
        print("  Mode : COLLECTE PRODUCTION\n")

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
        import django
        django.setup()
        from plateforme_centralisation.mongo import get_mongo_db
        _, db = get_mongo_db()

        # Vérifier si la structure a été découverte
        if not Path(DISCOVERY_FILE).exists():
            logger.warning("  [AVERT] orderbook_discovery.json introuvable")
            logger.warning("  Lancer d'abord sans --collect pour découvrir la structure API")

        run_collector_selenium(db)
        injecter_orderbook_dans_decisions(db)

    else:
        # Phase 1 — découverte
        print("  Mode : DÉCOUVERTE API\n")
        print("  Ce script va ouvrir Chrome et capturer les échanges réseau.")
        print("  Résultat → orderbook_discovery.json\n")

        if not HAS_SELENIUM:
            print("  [ERREUR] Selenium requis :")
            print("    .venv\\Scripts\\pip install selenium webdriver-manager")
            print("\n  Alternative : analyser manuellement via F12 → Réseau → WS")
            return

        run_discovery()


if __name__ == "__main__":
    main()
