#!/usr/bin/env python3
"""
REBUILD ALL DAILY
Reconstruit prices_daily pour TOUS les jours depuis prices_intraday_raw
"""
import os, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("="*70)
print("REBUILD ALL DAILY - VRAIS HIGH/LOW 9h-16h")
print("="*70)

# Charger TOUTES les collectes intraday
print("\n[1/4] Chargement collectes intraday...")
all_intraday = list(db.prices_intraday_raw.find({}, {
    "symbol": 1, "date": 1, "datetime": 1,
    "open": 1, "high": 1, "low": 1, "close": 1,
    "volume": 1, "valeur": 1, "nb_transactions": 1,
    "precedent": 1, "variation_pct": 1,
    "nom": 1, "sector": 1, "secteur_officiel": 1,
    "capitalisation": 1, "market_cap": 1, "pe_ratio": 1,
    "dividend_yield": 1, "nombre_titres": 1, "flottant_pct": 1,
    "data_quality": 1
}))

print(f"  Total collectes: {len(all_intraday)}")

# Grouper par (symbol, date)
print("\n[2/4] Groupement par (symbol, date)...")
grouped = defaultdict(list)
for doc in all_intraday:
    key = (doc.get("symbol"), doc.get("date"))
    grouped[key].append(doc)

print(f"  Groupes (symbol,date): {len(grouped)}")

multi = [(k,v) for k,v in grouped.items() if len(v) > 1]
print(f"  Avec collectes multiples: {len(multi)}")

# Calculer OHLC pour chaque groupe
print("\n[3/4] Calcul OHLC daily...")
daily_docs = []
created = 0
updated = 0

for (symbol, date), collectes in grouped.items():
    if not symbol or not date:
        continue
    
    # Trier par datetime
    collectes_sorted = sorted(collectes, key=lambda x: x.get("datetime", ""))
    
    first = collectes_sorted[0]
    last = collectes_sorted[-1]
    
    # VRAI OHLC
    open_price = first.get("open") or first.get("close")
    
    all_highs = [c.get("high") or c.get("close") or 0 for c in collectes_sorted]
    high_price = max(all_highs) if all_highs else 0
    
    all_lows = [c.get("low") or c.get("close") for c in collectes_sorted if c.get("low") or c.get("close")]
    low_price = min(all_lows) if all_lows else 0
    
    close_price = last.get("close")
    
    # Volume/valeur/transactions du jour
    volume_total = sum([c.get("volume") or 0 for c in collectes_sorted])
    valeur_totale = sum([c.get("valeur") or 0 for c in collectes_sorted])
    nb_tx_total = sum([c.get("nb_transactions") or 0 for c in collectes_sorted])
    
    # Variation
    precedent = first.get("precedent")
    if precedent and close_price:
        variation_pct = ((close_price - precedent) / precedent) * 100
    else:
        variation_pct = last.get("variation_pct")
    
    # Document daily
    daily_doc = {
        "symbol": symbol,
        "date": date,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "precedent": precedent,
        "variation_pct": variation_pct,
        "volume": volume_total,
        "valeur": valeur_totale,
        "nb_transactions": nb_tx_total,
        "nb_collectes_intraday": len(collectes_sorted),
        "nom": last.get("nom"),
        "sector": last.get("sector"),
        "secteur_officiel": last.get("secteur_officiel"),
        "capitalisation": last.get("capitalisation"),
        "market_cap": last.get("market_cap"),
        "pe_ratio": last.get("pe_ratio"),
        "dividend_yield": last.get("dividend_yield"),
        "nombre_titres": last.get("nombre_titres"),
        "flottant_pct": last.get("flottant_pct"),
        "data_quality": last.get("data_quality"),
        "first_collect_time": first.get("datetime"),
        "last_collect_time": last.get("datetime"),
        "built_at": datetime.now(),
        "source": "DAILY_REBUILD_ALL"
    }
    
    daily_docs.append(daily_doc)

print(f"  Documents à sauvegarder: {len(daily_docs)}")

# Sauvegarder
print("\n[4/4] Sauvegarde dans prices_daily...")

for doc in daily_docs:
    result = db.prices_daily.update_one(
        {"symbol": doc["symbol"], "date": doc["date"]},
        {"$set": doc},
        upsert=True
    )
    
    if result.matched_count > 0:
        updated += 1
    else:
        created += 1

print(f"  Crees: {created}")
print(f"  MAJ: {updated}")

# Vérification précision
with_multi = db.prices_daily.count_documents({"nb_collectes_intraday": {"$gt": 1}})
print(f"\n  Jours avec collectes multiples: {with_multi}")

print("\n" + "="*70)
print("OK REBUILD DAILY - Lancer rebuild_weekly_direct.py")
print("="*70)
