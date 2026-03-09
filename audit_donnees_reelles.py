#!/usr/bin/env python3
"""
AUDIT TOLERANCE ZERO - 100% DONNEES REELLES
Vérifie chaque couche de données : intraday, daily, weekly, publications
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pymongo import MongoClient
from datetime import datetime
import statistics

c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
db = c["centralisation_db"]

ROUGE  = "[ALERTE]"
VERT   = "[OK]"
JAUNE  = "[AVERTISSEMENT]"

print("=" * 70)
print("  AUDIT DONNEES 100% REELLES — TOLERANCE ZERO")
print("=" * 70)

# ================================================================
# 1. PRICES_INTRADAY_RAW — source primaire
# ================================================================
print("\n[1] prices_intraday_raw — source primaire collecte horaire")
print("-" * 60)

# Vérifier les sources
sources_intra = db.prices_intraday_raw.distinct("source")
print(f"  Sources distinctes : {sources_intra}")

# Chercher flags mock/simul
n_mock = db.prices_intraday_raw.count_documents({"$or": [
    {"is_mock": True}, {"simulated": True}, {"source": "MOCK"},
    {"source": "SIMULATED"}, {"fake": True}
]})
print(f"  Documents mock/simul : {n_mock}")

# Vérifier structure d'un doc récent
last_intra = db.prices_intraday_raw.find_one(sort=[("datetime", -1)])
if last_intra:
    print(f"  Dernier doc : symbol={last_intra.get('symbol')} date={last_intra.get('date')} datetime={last_intra.get('datetime')}")
    print(f"    close={last_intra.get('close')} volume={last_intra.get('volume')} source={last_intra.get('source')}")
    prix_val = last_intra.get('close') or 0
    if prix_val > 0:
        print(f"  {VERT} Prix non nul ({prix_val})")
    else:
        print(f"  {ROUGE} Prix = 0 ou absent")
else:
    print(f"  {ROUGE} Aucun document intraday trouvé")

# Vérifier si volumes sont cohérents (dernière journée, 3-4 collectes, doit être monotone ou stable)
from collections import defaultdict
docs_today = list(db.prices_intraday_raw.find(
    {"symbol": "BOAN"},
    {"volume": 1, "datetime": 1, "date": 1}
).sort("datetime", 1).limit(20))

if docs_today:
    last_date = docs_today[-1].get("date")
    docs_last = [d for d in docs_today if d.get("date") == last_date]
    vols = [d.get("volume", 0) for d in docs_last]
    print(f"\n  BOAN — {len(docs_last)} collectes sur {last_date} : volumes={vols}")
    if len(vols) >= 2:
        # Vérifier si cumulatif (croissant) ou delta
        is_cumul = all(vols[i] >= vols[i-1] for i in range(1, len(vols)) if vols[i] and vols[i-1])
        if is_cumul:
            print(f"  {VERT} Volumes CUMULATIFS confirmés — build_daily utilise last.get() = correct")
        else:
            print(f"  {JAUNE} Volumes NON cumulatifs sur cette date")

# ================================================================
# 2. PRICES_DAILY — données agrégées
# ================================================================
print("\n[2] prices_daily — données journalières agrégées")
print("-" * 60)

n_daily = db.prices_daily.count_documents({})
syms_daily = db.prices_daily.distinct("symbol")
dates_daily = sorted(db.prices_daily.distinct("date"), reverse=True)[:5]
print(f"  Total : {n_daily} docs | {len(syms_daily)} symboles")
print(f"  Dernières dates : {dates_daily}")

# Chercher flags mock
n_mock_daily = db.prices_daily.count_documents({"$or": [
    {"is_mock": True}, {"simulated": True}, {"source": "MOCK"},
    {"generated": True}
]})
print(f"  Documents mock/générés : {n_mock_daily}")

# Vérifier les prix pour la dernière date disponible
last_date = dates_daily[0] if dates_daily else None
if last_date:
    docs_last = list(db.prices_daily.find({"date": last_date}, {"symbol": 1, "close": 1, "volume": 1, "source": 1}))
    prix_vals = [d.get("close") for d in docs_last if d.get("close")]
    prix_zero = [d["symbol"] for d in docs_last if not d.get("close") or d.get("close") == 0]
    print(f"  Date {last_date} : {len(docs_last)} actions | prix_zero={prix_zero}")
    if prix_vals:
        print(f"  Prix min={min(prix_vals):.0f} max={max(prix_vals):.0f} median={statistics.median(prix_vals):.0f} FCFA")

# Vérifier les sources distinctes
sources_daily = db.prices_daily.distinct("source")
print(f"  Sources : {sources_daily}")

# ================================================================
# 3. PRICES_WEEKLY — données hebdomadaires
# ================================================================
print("\n[3] prices_weekly — données hebdomadaires")
print("-" * 60)

n_weekly = db.prices_weekly.count_documents({})
weeks = sorted(db.prices_weekly.distinct("week"), reverse=True)[:5]
print(f"  Total : {n_weekly} docs | Dernières semaines : {weeks}")

# Vérifier une action
doc_w = db.prices_weekly.find_one({"symbol": "BOAN"}, sort=[("week", -1)])
if doc_w:
    print(f"  BOAN dernière semaine : week={doc_w.get('week')} close={doc_w.get('close')} volume={doc_w.get('volume')}")

sources_weekly = db.prices_weekly.distinct("source")
n_mock_weekly = db.prices_weekly.count_documents({"$or": [
    {"is_mock": True}, {"simulated": True}, {"source": "MOCK"}
]})
print(f"  Sources : {sources_weekly}")
print(f"  Documents mock : {n_mock_weekly}")

# ================================================================
# 4. CURATED_OBSERVATIONS (AGREGATION_SEMANTIQUE_ACTION)
# ================================================================
print("\n[4] curated_observations (AGREGATION_SEMANTIQUE_ACTION)")
print("-" * 60)

curated = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))
print(f"  Total : {len(curated)} documents")

# Vérifier les signaux anormaux (tous BUY/HOLD sans score?)
signaux = {}
for doc in curated:
    sig = doc.get("attrs", {}).get("signal", "?")
    signaux[sig] = signaux.get(sig, 0) + 1
print(f"  Distribution des signaux : {signaux}")

# Vérifier les scores nuls/identiques (signe de données mock)
scores = [doc.get("attrs", {}).get("score") for doc in curated if doc.get("attrs", {}).get("score") is not None]
if scores:
    unique_scores = len(set(scores))
    print(f"  Scores : min={min(scores):.0f} max={max(scores):.0f} valeurs_uniques={unique_scores}")
    if unique_scores < 5:
        print(f"  {ROUGE} Trop peu de valeurs uniques — suspicion données générées")
    else:
        print(f"  {VERT} Distribution variée des scores ({unique_scores} valeurs uniques)")

# Chercher symboles fantômes
symbs_cur = [doc.get("key") for doc in curated]
fantomes = [s for s in symbs_cur if s in ["BRVM", "BOA", "SVOC", "SGOC", "SAFH", None]]
print(f"  Symboles fantômes dans curated : {fantomes}")

# ================================================================
# 5. PUBLICATIONS BRVM
# ================================================================
print("\n[5] publications_brvm — publications officielles BRVM")
print("-" * 60)

n_pubs = db.publications_brvm.count_documents({})
print(f"  Total : {n_pubs} publications")
if n_pubs > 0:
    pub_sample = db.publications_brvm.find_one(sort=[("date_publication", -1)])
    if pub_sample:
        print(f"  Dernière pub : emetteur={pub_sample.get('emetteur')} titre={str(pub_sample.get('titre',''))[:60]}")
        print(f"    date={pub_sample.get('date_publication')} source={pub_sample.get('source')}")
    sources_pubs = db.publications_brvm.distinct("source")
    print(f"  Sources : {sources_pubs}")
    n_mock_pubs = db.publications_brvm.count_documents({"$or": [
        {"is_mock": True}, {"simulated": True}, {"source": "MOCK"}
    ]})
    print(f"  Documents mock : {n_mock_pubs}")

# ================================================================
# 6. DECISIONS_FINALES_BRVM — résultats pipeline
# ================================================================
print("\n[6] decisions_finales_brvm — résultats actifs")
print("-" * 60)

decisions_actives = list(db.decisions_finales_brvm.find(
    {"archived": {"$ne": True}},
    {"symbol": 1, "decision": 1, "confidence": 1, "prix_entree": 1, "gain_attendu": 1, "wos": 1}
))
print(f"  Décisions actives : {len(decisions_actives)}")
for d in sorted(decisions_actives, key=lambda x: x.get("confidence", 0), reverse=True)[:5]:
    print(f"    {d.get('symbol'):6s} | {d.get('decision'):4s} | conf={d.get('confidence'):.0f}% | prix={d.get('prix_entree'):.0f} | gain={d.get('gain_attendu'):.1f}% | wos={d.get('wos'):.1f}")

# ================================================================
# 7. TOP5 ACTIF
# ================================================================
print("\n[7] top5_daily_brvm — TOP5 actif")
print("-" * 60)

top5 = list(db.top5_daily_brvm.find({}, {"symbol": 1, "rank": 1, "prix_entree": 1, "gain_attendu": 1, "vsr": 1, "momentum_5j": 1}).sort("rank", 1))
print(f"  TOP5 en cours : {len(top5)} entrées")
for t in top5:
    print(f"    #{t.get('rank')} {t.get('symbol'):6s} | entrée={t.get('prix_entree',0):.0f} | gain={t.get('gain_attendu',0):.1f}% | vsr={t.get('vsr')} | mom5j={t.get('momentum_5j')}")

# ================================================================
# SYNTHÈSE
# ================================================================
print("\n" + "=" * 70)
print("  SYNTHÈSE AUDIT DONNEES REELLES")
print("=" * 70)
total_mock = n_mock + n_mock_daily + n_mock_weekly
if total_mock == 0:
    print(f"\n  {VERT} Aucun document mock/simulated détecté dans les collections principales")
else:
    print(f"\n  {ROUGE} {total_mock} documents mock/simulés détectés — CORRECTION URGENTE")

# Vérifier cohérence prix vs marché réel
prix_reels_connus = {"BOAN": 2700, "PRSC": 5255, "CABC": 3995, "SLBC": 44150, "SIVC": 2685}
print("\n  Vérification prix vs dernière session BRVM connue :")
for sym, prix_ref in prix_reels_connus.items():
    doc_p = db.prices_daily.find_one({"symbol": sym}, sort=[("date", -1)])
    prix_db = doc_p.get("close", 0) if doc_p else 0
    date_db = doc_p.get("date", "?") if doc_p else "?"
    ecart = abs(prix_db - prix_ref) / prix_ref * 100 if prix_ref > 0 else 100
    statut = VERT if ecart < 5 else (JAUNE if ecart < 20 else ROUGE)
    print(f"    {sym:6s}: DB={prix_db:.0f} | REF={prix_ref:.0f} | écart={ecart:.1f}% — {statut} ({date_db})")
