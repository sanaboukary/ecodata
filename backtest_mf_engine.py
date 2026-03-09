#!/usr/bin/env python3
"""
BACKTEST MULTI-FACTOR ENGINE — BRVM
=====================================
Deux modes de validation :

MODE A — RANKING PREDICTIF (recommandé)
  Pour chaque fenêtre historique, le moteur MF classe les 47 actions.
  On mesure si les actions EXPLOSION/SWING_FORT surperforment réellement
  les actions IGNORER sur J+5, J+10, J+15 => validation de la hiérarchie.
  Ne dépend pas du placement du stop.

MODE B — SIMULATION TP/STOP (avec capping ATR)
  Entrée au close, stop capé à 8% max (indépendamment de l'ATR),
  cibles étagées TP1+7.5% / TP2+15% / Runner+27.5%.
  Stop trop large => remplacé par stop fixe 5%.

DIAGNOSTIC DE DONNÉES
  Affiche la qualité des données disponibles pour informer l'utilisateur.

Usage :
  .venv/Scripts/python.exe backtest_mf_engine.py
  .venv/Scripts/python.exe backtest_mf_engine.py --horizon 10
  .venv/Scripts/python.exe backtest_mf_engine.py --mode A   (ranking seulement)
  .venv/Scripts/python.exe backtest_mf_engine.py --mode B   (TP/Stop seulement)
"""

import sys
import csv
import statistics
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pymongo import MongoClient
from scipy.stats import percentileofscore

# ─── CLI ─────────────────────────────────────────────────────────────────────
HORIZON   = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--horizon'), 10))
MODE_CLI  = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--mode'), 'AB')
TOP_N     = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--top'), 5))
STEP      = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--step'), 1))

# ─── Paramètres ──────────────────────────────────────────────────────────────
MIN_WINDOW      = 20      # jours min pour calculer les facteurs MF
STOP_MAX_PCT    = 8.0     # stop capé à 8% max (protection data quality)
STOP_DEFAULT    = 5.0     # stop fixe si ATR indisponible ou aberrant
ATR_MAX_PCT     = 30.0    # filtre: rejeter les fenêtres où ATR > 30% du prix

INDICES_BRVM = {"BRVM-PRESTIGE","BRVM-COMPOSITE","BRVM-10","BRVM-30","BRVMC","BRVM10"}

ACTIONS_OFFICIELLES = {
    "ABJC","BICB","BICC","BNBC","BOAB","BOABF","BOAC","BOAM","BOAN","BOAS",
    "CABC","CBIBF","CFAC","CIEC","ECOC","ETIT","FTSC","LNBB","NEIC","NSBC",
    "NTLC","ONTBF","ORAC","ORGT","PALC","PRSC","SAFC","SCRC","SDCC","SDSC",
    "SEMC","SGBC","SHEC","SIBC","SICC","SIVC","SLBC","SMBC","SNTS","SOGC",
    "SPHC","STAC","STBC","TTLC","TTLS","UNLC","UNXC",
}


# ─── Helpers MF ──────────────────────────────────────────────────────────────

def _perf(closes, n):
    if len(closes) < n + 1 or not closes[-(n+1)] or closes[-(n+1)] <= 0:
        return None
    return (closes[-1] - closes[-(n+1)]) / closes[-(n+1)] * 100


def calculer_facteurs(closes, highs, volumes):
    """Retourne les facteurs bruts pour les percentiles cross-sectionnels."""
    if len(closes) < MIN_WINDOW:
        return None

    trs = [abs(closes[i] - closes[i-1]) for i in range(1, len(closes))
           if closes[i] and closes[i-1]]

    if len(trs) < 5:
        return None

    atr_20 = statistics.mean(trs[-min(20, len(trs)):])
    close  = closes[-1]

    # Filtre qualité : rejeter si ATR > ATR_MAX_PCT du prix (données aberrantes)
    if close and close > 0 and atr_20 / close * 100 > ATR_MAX_PCT:
        return None

    p10 = _perf(closes, 10)
    p20 = _perf(closes, 20)

    breakout = None
    if len(highs) >= 20:
        highs_v = [h for h in highs[-20:] if h and h > 0]
        if highs_v and atr_20 > 0:
            breakout = (close - max(highs_v)) / atr_20

    volume_ratio = None
    if len(volumes) >= 20:
        v5  = [v for v in volumes[-5:]  if v and v > 0]
        v20 = [v for v in volumes[-20:] if v and v > 0]
        if v5 and v20:
            m5  = statistics.mean(v5)
            m20 = statistics.mean(v20)
            if m20 > 0:
                volume_ratio = m5 / m20

    compression = None
    if len(trs) >= 20:
        delayed = trs[-11:-6] if len(trs) >= 11 else []
        if len(delayed) == 5 and atr_20 > 0:
            compression = 1.0 - (statistics.mean(delayed) / atr_20)

    p5 = _perf(closes, 5)
    acceleration = (p5 - p20) if p5 is not None and p20 is not None else None

    # Stop capé
    atr_pct = atr_20 / close * 100 if close and close > 0 else None
    if atr_pct and atr_pct <= STOP_MAX_PCT:
        stop_pct = atr_pct
    else:
        stop_pct = STOP_DEFAULT

    return {
        "close":         close,
        "momentum":      p10,
        "breakout":      breakout,
        "rs":            p20,
        "volume_ratio":  volume_ratio,
        "compression":   compression,
        "acceleration":  acceleration,
        "stop_pct":      stop_pct,
        "atr_20_abs":    atr_20,
    }


def normaliser_cross(all_factors):
    """Percentile cross-sectionnel sur l'ensemble des symboles présents."""
    factor_map = {
        "momentum":     "momentum_score",
        "breakout":     "breakout_score",
        "rs":           "rs_score",
        "volume_ratio": "volume_ratio_score",
        "compression":  "compression_score",
        "acceleration": "acceleration_score",
    }
    for fname, sname in factor_map.items():
        vals = [d[fname] for d in all_factors if d.get(fname) is not None]
        for d in all_factors:
            if d.get(fname) is not None and vals:
                d[sname] = round(percentileofscore(vals, d[fname], kind="rank"), 1)
            else:
                d[sname] = 50.0
    return all_factors


def score_total(d):
    sc = (
        0.30 * d.get("rs_score",            50.0)
        + 0.25 * d.get("breakout_score",    50.0)
        + 0.20 * d.get("volume_ratio_score", 50.0)
        + 0.15 * d.get("momentum_score",    50.0)
        + 0.10 * d.get("compression_score", 50.0)
    )
    if d.get("acceleration_score", 0) >= 80:
        sc = min(100.0, sc + 5.0)
    return round(sc, 1)


def get_label(sc):
    if sc >= 85: return "EXPLOSION"
    if sc >= 70: return "SWING_FORT"
    if sc >= 55: return "SWING_MOYEN"
    return "IGNORER"


# ─── MODE B : simulation TP/Stop ─────────────────────────────────────────────

def simuler_tp_stop(closes_futur, prix_entree, stop_pct):
    """Sortie étagée TP1 40% / TP2 40% / Runner 20% + Stop fixe."""
    if not prix_entree or prix_entree <= 0 or not closes_futur:
        return 0.0, "HORIZON", {}

    tp1    = prix_entree * 1.075
    tp2    = prix_entree * 1.150
    runner = prix_entree * 1.275
    stop   = prix_entree * (1 - stop_pct / 100)

    poids   = [0.40, 0.40, 0.20]
    paliers = [tp1, tp2, runner]
    sorties = [None, None, None]
    motif   = "HORIZON"

    for close in closes_futur:
        if not close or close <= 0:
            continue
        if close <= stop:
            for k in range(3):
                if sorties[k] is None:
                    sorties[k] = stop
            motif = "STOP"
            break
        for k in range(3):
            if sorties[k] is None and close >= paliers[k]:
                sorties[k] = paliers[k]
                motif = ["TP1", "TP2", "RUNNER"][k]
                break
        if all(s is not None for s in sorties):
            break

    close_final = closes_futur[-1] if closes_futur[-1] else prix_entree
    for k in range(3):
        if sorties[k] is None:
            sorties[k] = close_final

    rendement = sum(poids[k] * (sorties[k] - prix_entree) / prix_entree * 100 for k in range(3))

    details = {
        "tp1_hit":    sorties[0] >= tp1,
        "tp2_hit":    sorties[1] >= tp2,
        "runner_hit": sorties[2] >= runner,
    }
    return round(rendement, 2), motif, details


# ─── Chargement données ───────────────────────────────────────────────────────

def charger_donnees(db):
    """Charge tout prices_daily en mémoire, indexé par (symbol, date_str)."""
    symbols_db = {s for s in db.prices_daily.distinct("symbol") if s not in INDICES_BRVM}
    symbols    = sorted(ACTIONS_OFFICIELLES & symbols_db)

    # data[symbol] = liste de {"date": str, "close", "high", "volume"}
    data = {}
    all_dates_set = set()

    for sym in symbols:
        docs = list(db.prices_daily.find({"symbol": sym}).sort("date", 1))
        if len(docs) < MIN_WINDOW + HORIZON + 2:
            continue
        rows = []
        for d in docs:
            ds = str(d.get("date", ""))[:10]
            rows.append({
                "date":   ds,
                "close":  d.get("close"),
                "high":   d.get("high"),
                "volume": d.get("volume", 0),
            })
            all_dates_set.add(ds)
        data[sym] = rows

    all_dates = sorted(all_dates_set)
    return data, all_dates


def get_window(rows, date_idx, lookback):
    """Retourne les dernières closes/highs/volumes jusqu'à date_idx (inclus)."""
    subset = rows[max(0, date_idx - lookback + 1): date_idx + 1]
    closes  = [r["close"]  for r in subset]
    highs   = [r["high"]   for r in subset]
    volumes = [r["volume"] for r in subset]
    return closes, highs, volumes


def get_future_closes(rows, date_idx, horizon):
    """Retourne les closes des HORIZON prochains jours."""
    subset = rows[date_idx + 1: date_idx + 1 + horizon]
    return [r["close"] for r in subset if r.get("close") and r["close"] > 0]


# ─── DIAGNOSTIC données ──────────────────────────────────────────────────────

def diagnostic_donnees(data, all_dates):
    # Compter les jours avec volume > 0 par symbole
    sym_clean = {}
    for sym, rows in data.items():
        clean = sum(1 for r in rows if r.get("volume", 0) and r["volume"] > 0)
        sym_clean[sym] = clean

    n_ok   = sum(1 for v in sym_clean.values() if v >= 15)
    n_poor = sum(1 for v in sym_clean.values() if v < 15)
    vol_total = sum(sym_clean.values())
    vol_mean  = vol_total / len(sym_clean) if sym_clean else 0

    print(f"\n{'─'*70}")
    print(f" DIAGNOSTIC QUALITE DONNEES")
    print(f"{'─'*70}")
    print(f"  Dates totales disponibles : {len(all_dates)} ({all_dates[0]} => {all_dates[-1]})")
    print(f"  Symboles charges          : {len(data)}")
    print(f"  Jours vol>0 (moy/symb)    : {vol_mean:.1f}")
    print(f"  Symboles >=15j vol>0      : {n_ok}")
    print(f"  Symboles <15j vol>0       : {n_poor} (donnees simulees)")
    print(f"")
    if vol_mean < 10:
        print(f"  [AVERT] <10 jours de donnees reelles en moyenne par symbole.")
        print(f"  Les resultats du backtest sont INDICATIFS, pas definitifs.")
        print(f"  Pour un backtest fiable, il faut minimum 60 jours de donnees reelles.")
    print(f"{'─'*70}\n")

    return vol_mean


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run_backtest():
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db     = client["centralisation_db"]

    print("=" * 70)
    print(f" BACKTEST MF ENGINE — Mode {MODE_CLI} | Horizon J+{HORIZON} | TOP{TOP_N}".center(70))
    print("=" * 70)

    print("\n  [1/4] Chargement donnees...")
    data, all_dates = charger_donnees(db)
    print(f"  {len(data)} symboles | {len(all_dates)} dates")

    vol_mean = diagnostic_donnees(data, all_dates)
    fiable   = vol_mean >= 30

    # Index: date_str -> position dans la liste rows de chaque symbole
    # Construire un index date -> index par symbole
    sym_date_idx = {}
    for sym, rows in data.items():
        sym_date_idx[sym] = {r["date"]: i for i, r in enumerate(rows)}

    # Fenêtres de simulation : indices dans all_dates avec assez d'historique
    simulation_dates = [
        (i, d) for i, d in enumerate(all_dates)
        if i >= MIN_WINDOW and i <= len(all_dates) - HORIZON - 1
    ]
    simulation_dates = simulation_dates[::STEP]  # Pas

    print(f"  [2/4] {len(simulation_dates)} fenetres de simulation...")

    trades_A = []  # Mode A : ranking predictif
    trades_B = []  # Mode B : TP/Stop

    for date_global_idx, date_str in simulation_dates:
        # Calculer facteurs MF pour tous les symboles à cette date
        all_factors = []

        for sym, rows in data.items():
            if date_str not in sym_date_idx[sym]:
                continue
            sym_idx = sym_date_idx[sym][date_str]
            if sym_idx < MIN_WINDOW:
                continue
            if sym_idx + HORIZON >= len(rows):
                continue

            # Fenêtre historique
            lookback = min(sym_idx + 1, MIN_WINDOW + 10)
            closes, highs, volumes = get_window(rows, sym_idx, lookback)
            closes  = [c for c in closes  if c and c > 0]
            highs   = [h for h in highs]
            volumes = [v if v else 0 for v in volumes]

            if len(closes) < MIN_WINDOW:
                continue

            fac = calculer_facteurs(closes, highs, volumes)
            if fac is None:
                continue

            # Forward return pour MODE A
            fut = get_future_closes(rows, sym_idx, HORIZON)
            if len(fut) < 3:
                continue
            fwd_return = (fut[-1] - closes[-1]) / closes[-1] * 100 if closes[-1] > 0 else None

            fac["symbol"]     = sym
            fac["date"]       = date_str
            fac["fwd_return"] = fwd_return
            fac["fut_closes"] = fut
            all_factors.append(fac)

        if len(all_factors) < 5:
            continue

        # Normalisation cross-sectionnelle
        all_factors = normaliser_cross(all_factors)
        for f in all_factors:
            f["score_mf"] = score_total(f)
            f["mf_label"] = get_label(f["score_mf"])

        sorted_f = sorted(all_factors, key=lambda x: x["score_mf"], reverse=True)

        # ── MODE A : ranking predictif ──────────────────────────────────────
        if 'A' in MODE_CLI:
            for f in all_factors:
                if f.get("fwd_return") is not None:
                    trades_A.append({
                        "symbol":    f["symbol"],
                        "date":      f["date"],
                        "score_mf":  f["score_mf"],
                        "mf_label":  f["mf_label"],
                        "fwd_ret":   round(f["fwd_return"], 2),
                        "rank":      sorted_f.index(f) + 1,
                    })

        # ── MODE B : simulation TP/Stop pour TOP N ──────────────────────────
        if 'B' in MODE_CLI:
            # Pre-filtres production
            filtered = [
                f for f in sorted_f
                if f["score_mf"] >= 55
                and f.get("breakout_score", 50) >= 45
                and f.get("volume_ratio_score", 50) >= 60
            ]
            if not filtered:
                filtered = [f for f in sorted_f if f["score_mf"] >= 50]
            if not filtered:
                filtered = sorted_f
            top = filtered[:TOP_N]

            for pos in top:
                prix_e = pos["close"]
                fut    = pos["fut_closes"]
                if not fut or not prix_e or prix_e <= 0:
                    continue
                stop_pct = pos.get("stop_pct", STOP_DEFAULT)
                rend, motif, details = simuler_tp_stop(fut, prix_e, stop_pct)
                trades_B.append({
                    "symbol":        pos["symbol"],
                    "date":          pos["date"],
                    "prix_entree":   round(prix_e, 1),
                    "score_mf":      pos["score_mf"],
                    "mf_label":      pos["mf_label"],
                    "stop_pct":      round(stop_pct, 2),
                    "rendement":     rend,
                    "gagnant":       rend > 0,
                    "motif":         motif,
                    "tp1_hit":       details.get("tp1_hit", False),
                    "tp2_hit":       details.get("tp2_hit", False),
                    "runner_hit":    details.get("runner_hit", False),
                })

    print(f"  [3/4] Analyse des resultats...\n")

    # ── RÉSULTATS MODE A ─────────────────────────────────────────────────────
    if 'A' in MODE_CLI and trades_A:
        print("=" * 70)
        print(f" MODE A — RANKING PREDICTIF ({len(trades_A)} obs | Horizon J+{HORIZON})")
        print("=" * 70)
        print(f"  Question : les labels MF predisent-ils les retours futurs ?")
        print()

        # Par label : moyenne des retours futurs
        label_returns = {}
        for label in ["EXPLOSION", "SWING_FORT", "SWING_MOYEN", "IGNORER"]:
            t_l = [t["fwd_ret"] for t in trades_A if t["mf_label"] == label]
            if t_l:
                label_returns[label] = {
                    "n":     len(t_l),
                    "mean":  round(statistics.mean(t_l), 2),
                    "med":   round(statistics.median(t_l), 2),
                    "wr":    round(sum(1 for x in t_l if x > 0) / len(t_l) * 100, 1),
                    "max":   round(max(t_l), 2),
                    "min":   round(min(t_l), 2),
                }

        print(f"  {'Label':<14} {'N':>5}  {'Ret moy':>8}  {'Ret med':>8}  {'WR':>6}  {'Max':>8}  {'Min':>8}")
        print(f"  {'─'*66}")
        for label in ["EXPLOSION", "SWING_FORT", "SWING_MOYEN", "IGNORER"]:
            if label in label_returns:
                s = label_returns[label]
                print(f"  {label:<14} {s['n']:>5}  {s['mean']:>+7.2f}%  {s['med']:>+7.2f}%  {s['wr']:>5.1f}%  {s['max']:>+7.2f}%  {s['min']:>+7.2f}%")

        # TOP5 (rank<=5) vs reste
        top5_ret  = [t["fwd_ret"] for t in trades_A if t["rank"] <= 5]
        rest_ret  = [t["fwd_ret"] for t in trades_A if t["rank"] > 5]
        if top5_ret and rest_ret:
            print(f"\n  TOP{TOP_N} selectes vs non selectes :")
            print(f"  TOP{TOP_N}   : retour moy {round(statistics.mean(top5_ret),2):+.2f}%  WR {round(sum(1 for x in top5_ret if x>0)/len(top5_ret)*100,1):.1f}%  ({len(top5_ret)} obs)")
            print(f"  Autres  : retour moy {round(statistics.mean(rest_ret),2):+.2f}%  WR {round(sum(1 for x in rest_ret if x>0)/len(rest_ret)*100,1):.1f}%  ({len(rest_ret)} obs)")

        # Correlation score MF / retour futur
        scores = [t["score_mf"] for t in trades_A]
        retour = [t["fwd_ret"]  for t in trades_A]
        if len(scores) >= 5:
            n_s = len(scores)
            mean_s = statistics.mean(scores)
            mean_r = statistics.mean(retour)
            cov = sum((scores[i]-mean_s)*(retour[i]-mean_r) for i in range(n_s)) / n_s
            std_s = statistics.stdev(scores) if n_s > 1 else 1
            std_r = statistics.stdev(retour) if n_s > 1 else 1
            corr  = cov / (std_s * std_r) if std_s * std_r > 0 else 0
            print(f"\n  Correlation score MF / retour J+{HORIZON} : {corr:+.3f}")
            print(f"  (>+0.10 = signal predictif | proche 0 = pas de lien)")

        # Validation hierarchie
        exp_m  = label_returns.get("EXPLOSION",  {}).get("mean")
        swf_m  = label_returns.get("SWING_FORT", {}).get("mean")
        swo_m  = label_returns.get("SWING_MOYEN",{}).get("mean")
        ign_m  = label_returns.get("IGNORER",    {}).get("mean")

        hierarchy = []
        if exp_m is not None and swf_m is not None:
            hierarchy.append(f"EXPLOSION({exp_m:+.1f}%) {'>' if exp_m>swf_m else '<'} SWING_FORT({swf_m:+.1f}%)")
        if swf_m is not None and swo_m is not None:
            hierarchy.append(f"SWING_FORT({swf_m:+.1f}%) {'>' if swf_m>swo_m else '<'} SWING_MOYEN({swo_m:+.1f}%)")

        print(f"\n  Hierarchie des labels :")
        for h in hierarchy:
            print(f"    {h}")

    # ── RÉSULTATS MODE B ─────────────────────────────────────────────────────
    if 'B' in MODE_CLI and trades_B:
        n         = len(trades_B)
        gagnants  = [t for t in trades_B if t["gagnant"]]
        perdants  = [t for t in trades_B if not t["gagnant"]]
        win_rate  = len(gagnants) / n * 100
        rendements= [t["rendement"] for t in trades_B]
        gain_moy  = round(statistics.mean(rendements), 2)
        gain_med  = round(statistics.median(rendements), 2)
        pertes_tot = abs(sum(t["rendement"] for t in perdants)) if perdants else 0
        gains_tot  = sum(t["rendement"] for t in gagnants)  if gagnants else 0
        pf         = round(gains_tot / pertes_tot, 2) if pertes_tot > 0 else float("inf")

        capital = 100.0
        pic = capital
        max_dd = 0.0
        for t in trades_B:
            capital *= (1 + t["rendement"] / 100)
            if capital > pic: pic = capital
            dd = (pic - capital) / pic * 100
            if dd > max_dd: max_dd = dd

        motifs = {}
        for t in trades_B:
            motifs[t["motif"]] = motifs.get(t["motif"], 0) + 1

        tp1_rate    = sum(1 for t in trades_B if t["tp1_hit"])    / n * 100
        tp2_rate    = sum(1 for t in trades_B if t["tp2_hit"])    / n * 100
        runner_rate = sum(1 for t in trades_B if t["runner_hit"]) / n * 100

        print(f"\n{'='*70}")
        print(f" MODE B — SIMULATION TP/STOP ({n} trades | TOP{TOP_N} | J+{HORIZON})")
        print(f"  Stop : max {STOP_MAX_PCT}% (cap) | Defaut {STOP_DEFAULT}%")
        print(f"{'='*70}")
        print(f"  Win Rate          : {win_rate:.1f}%  ({len(gagnants)} / {len(perdants)})")
        print(f"  Gain moyen/trade  : {gain_moy:+.2f}%")
        print(f"  Gain median/trade : {gain_med:+.2f}%")
        if gagnants:
            print(f"  Gain moy Winners  : {round(statistics.mean(t['rendement'] for t in gagnants), 2):+.2f}%")
        if perdants:
            print(f"  Perte moy Losers  : {round(statistics.mean(t['rendement'] for t in perdants), 2):+.2f}%")
        print(f"  Profit Factor     : {pf:.2f}  (>1.5 = profitable)")
        print(f"  Max Drawdown      : {round(max_dd, 1)}%")
        print(f"  Capital final     : {round(capital, 1)} (base 100)")
        print(f"\n  Motifs : " + " | ".join(f"{k}: {v}" for k, v in sorted(motifs.items())))
        print(f"  Hit rates TP : TP1={tp1_rate:.0f}%  TP2={tp2_rate:.0f}%  Runner={runner_rate:.0f}%")

        # Par label
        print(f"\n  {'Label':<14} {'N':>4}  {'WR':>6}  {'Rend moy':>9}  {'PF':>5}")
        print(f"  {'─'*44}")
        for label in ["EXPLOSION", "SWING_FORT", "SWING_MOYEN", "IGNORER"]:
            t_l = [t for t in trades_B if t["mf_label"] == label]
            if t_l:
                wr_l = sum(1 for t in t_l if t["gagnant"]) / len(t_l) * 100
                gm_l = round(statistics.mean(t["rendement"] for t in t_l), 2)
                g_l  = [t for t in t_l if t["gagnant"]]
                p_l  = [t for t in t_l if not t["gagnant"]]
                pf_l = round(sum(t["rendement"] for t in g_l) / abs(sum(t["rendement"] for t in p_l)), 2) if p_l else float("inf")
                print(f"  {label:<14} {len(t_l):>4}  {wr_l:>5.1f}%  {gm_l:>+8.2f}%  {pf_l:>5.2f}")

        # Top symboles
        sym_stats = {}
        for t in trades_B:
            sym_stats.setdefault(t["symbol"], []).append(t["rendement"])
        top_sym = sorted([(s, round(statistics.mean(v), 2), len(v))
                          for s, v in sym_stats.items()], key=lambda x: x[1], reverse=True)
        print(f"\n  Top 5 symboles : {' | '.join(f'{s} {g:+.1f}%' for s,g,_ in top_sym[:5])}")
        print(f"  Flop 5 symboles: {' | '.join(f'{s} {g:+.1f}%' for s,g,_ in top_sym[-5:])}")

    # ── VERDICT ──────────────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f" VERDICT")
    print(f"{'─'*70}")
    if not fiable:
        print(f"  [!] Seulement {vol_mean:.0f} jours de donnees reelles/symbole en moyenne.")
        print(f"  Ces resultats sont a titre INDICATIF uniquement.")
        print(f"  Relancer ce backtest dans 2-3 mois quand vous aurez 60+ jours reels.")
        print()

    # Verdict Mode A
    if 'A' in MODE_CLI and trades_A and label_returns:
        exp_m  = label_returns.get("EXPLOSION",  {}).get("mean", 0)
        swf_m  = label_returns.get("SWING_FORT", {}).get("mean", 0)
        ign_m  = label_returns.get("IGNORER",    {}).get("mean", 0)
        if exp_m > swf_m and swf_m > ign_m:
            print(f"  Mode A : hirarchie CONFIRMEE — EXPLOSION > SWING_FORT > IGNORER")
        elif exp_m > ign_m:
            print(f"  Mode A : signal PARTIEL — EXPLOSION > IGNORER mais hierarchie imparfaite")
        else:
            print(f"  Mode A : signal FAIBLE — labels ne predisent pas clairement les retours")

    # Verdict Mode B
    if 'B' in MODE_CLI and trades_B:
        if win_rate >= 55 and pf >= 1.5:
            print(f"  Mode B : SYSTEME PROFITABLE — WR={win_rate:.1f}% PF={pf:.2f}")
        elif win_rate >= 50 and pf >= 1.2:
            print(f"  Mode B : SYSTEME CORRECT — WR={win_rate:.1f}% PF={pf:.2f}")
        elif win_rate >= 45:
            print(f"  Mode B : BORDERLINE — WR={win_rate:.1f}%, revisiter les filtres")
        else:
            print(f"  Mode B : ALERTE — WR={win_rate:.1f}% insuffisant")

    print(f"\n{'='*70}\n")

    # ── EXPORT CSV ───────────────────────────────────────────────────────────
    print(f"  [4/4] Export CSV...")
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    for mode_label, trades in [("A_ranking", trades_A), ("B_tpstop", trades_B)]:
        if trades and mode_label[0] in MODE_CLI:
            fname = f"backtest_mf_{mode_label}_{ts}.csv"
            with open(fname, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=trades[0].keys())
                w.writeheader()
                w.writerows(trades)
            print(f"  [OK] {fname} ({len(trades)} lignes)")
    print()


if __name__ == "__main__":
    run_backtest()
