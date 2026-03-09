#!/usr/bin/env python3
"""
ABLATION STUDY — BRVM Multi-Factor Engine
==========================================
Teste chaque composante du modèle en isolation pour identifier
d'où vient réellement la performance.

Principe : charger les données UNE FOIS, calculer les scores bruts UNE FOIS,
puis tester 10+ configurations de poids différentes. Aucun fichier modifié.

Configurations testées :
  C00  RS seul                        (RS=1.0)
  C01  Breakout seul                  (BRK=1.0)
  C02  Volume seul                    (VOL=1.0)
  C03  Momentum seul                  (MOM=1.0)
  C04  RS + Breakout                  (RS=0.55, BRK=0.45)
  C05  RS + Volume                    (RS=0.55, VOL=0.45)
  C06  RS + Breakout + Volume         (RS=0.40, BRK=0.35, VOL=0.25)
  C07  MF 5-facteurs (production)     (RS=0.30, BRK=0.25, VOL=0.20, MOM=0.15, CPR=0.10)
  C08  MF production SANS bonus acc.  (même poids, bonus acc désactivé)
  C09  MF production + filtre VCP     (C07 mais uniquement signaux VCP)
  C10  Poids égaux                    (tous à 0.20)

Métriques par configuration :
  N, WR%, Gain_moy/trade, Gain_win, Perte_loss, PF, MaxDD, Capital_final, EV_net

Usage :
  python ablation_study.py
  python ablation_study.py --horizon 15
  python ablation_study.py --min-trades 20
"""

import sys
import statistics
from collections import defaultdict
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pymongo import MongoClient

# ─── Paramètres ────────────────────────────────────────────────────────────
HORIZON_SORTIE  = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--horizon'), 10))
MIN_TRADES_DISP = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--min-trades'), 10))
MIN_HIST        = 22
ATR_MIN         = 0.56
STOP_FACTOR     = 1.5
RR_MIN          = 2.0
TOTAL_COST      = 0.70   # 0.5% frais + 0.2% slippage

# ─── Indices à exclure ─────────────────────────────────────────────────────
INDICES = {'BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10'}

# ─── Configurations d'ablation ──────────────────────────────────────────────
CONFIGURATIONS = {
    "C00_RS_seul":       {"rs": 1.00, "brk": 0.00, "vol": 0.00, "mom": 0.00, "cpr": 0.00, "acc_bonus": True,  "vcp_only": False},
    "C01_Breakout_seul": {"rs": 0.00, "brk": 1.00, "vol": 0.00, "mom": 0.00, "cpr": 0.00, "acc_bonus": True,  "vcp_only": False},
    "C02_Volume_seul":   {"rs": 0.00, "brk": 0.00, "vol": 1.00, "mom": 0.00, "cpr": 0.00, "acc_bonus": True,  "vcp_only": False},
    "C03_Momentum_seul": {"rs": 0.00, "brk": 0.00, "vol": 0.00, "mom": 1.00, "cpr": 0.00, "acc_bonus": True,  "vcp_only": False},
    "C04_RS+Breakout":   {"rs": 0.55, "brk": 0.45, "vol": 0.00, "mom": 0.00, "cpr": 0.00, "acc_bonus": True,  "vcp_only": False},
    "C05_RS+Volume":     {"rs": 0.55, "brk": 0.00, "vol": 0.45, "mom": 0.00, "cpr": 0.00, "acc_bonus": True,  "vcp_only": False},
    "C06_RS+BRK+VOL":    {"rs": 0.40, "brk": 0.35, "vol": 0.25, "mom": 0.00, "cpr": 0.00, "acc_bonus": True,  "vcp_only": False},
    "C07_MF_PROD":       {"rs": 0.30, "brk": 0.25, "vol": 0.20, "mom": 0.15, "cpr": 0.10, "acc_bonus": True,  "vcp_only": False},
    "C08_MF_sans_acc":   {"rs": 0.30, "brk": 0.25, "vol": 0.20, "mom": 0.15, "cpr": 0.10, "acc_bonus": False, "vcp_only": False},
    "C09_MF_VCP_only":   {"rs": 0.30, "brk": 0.25, "vol": 0.20, "mom": 0.15, "cpr": 0.10, "acc_bonus": True,  "vcp_only": True},
    "C10_Poids_egaux":   {"rs": 0.20, "brk": 0.20, "vol": 0.20, "mom": 0.20, "cpr": 0.20, "acc_bonus": True,  "vcp_only": False},
}


# ─── Fonctions utilitaires ──────────────────────────────────────────────────

def _score_linear(val, lo, hi):
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (val - lo) / (hi - lo) * 100))


def calculer_rsi(closes, n=14):
    if len(closes) < n + 1:
        return None
    gains, pertes = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        pertes.append(abs(min(diff, 0)))
    avg_gain = statistics.mean(gains[-n:])
    avg_loss = statistics.mean(pertes[-n:])
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))


def calculer_atr_pct(closes, n=8):
    if len(closes) < n + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        if closes[i-1] > 0 and closes[i] > 0:
            trs.append(abs(closes[i] - closes[i-1]) / closes[i] * 100)
    if len(trs) < 3:
        return None
    return statistics.median(trs[-n:])


def extraire_scores_bruts(closes, vols):
    """
    Calcule les 5 scores bruts (0-100) + metadata pour une fenêtre donnée.
    Appelé UNE FOIS par point temporel. Les configs appliquent ensuite leurs poids.
    Retourne None si données insuffisantes.
    """
    if len(closes) < MIN_HIST:
        return None

    trs = [abs(closes[i] - closes[i-1]) for i in range(1, len(closes))]

    # ── RS proxy = perf_20j
    rs_raw = None
    if len(closes) >= 21 and closes[-21] > 0:
        rs_raw = (closes[-1] - closes[-21]) / closes[-21] * 100

    # ── Breakout = (close - max_20j) / ATR_20
    brk_raw = None
    if len(closes) >= 20 and len(trs) >= 20:
        max_20j = max(closes[-20:])
        atr_20  = statistics.mean(trs[-20:])
        if atr_20 > 0:
            brk_raw = (closes[-1] - max_20j) / atr_20

    # ── Volume ratio = mean_5j / mean_20j
    vol_raw = None
    if vols and len(vols) >= 20:
        v5  = [v for v in vols[-5:]  if v and v > 0]
        v20 = [v for v in vols[-20:] if v and v > 0]
        if v5 and v20:
            moy5  = statistics.mean(v5)
            moy20 = statistics.mean(v20)
            if moy20 > 0:
                vol_raw = moy5 / moy20

    # ── Momentum = perf_10j
    mom_raw = None
    if len(closes) >= 11 and closes[-11] > 0:
        mom_raw = (closes[-1] - closes[-11]) / closes[-11] * 100

    # ── Compression = 1 - (ATR_5_delayed / ATR_20), fenêtre [-11:-6]
    cpr_raw = None
    if len(trs) >= 20:
        delayed = trs[-11:-6]
        if len(delayed) == 5:
            atr_5d = statistics.mean(delayed)
            atr_20v = statistics.mean(trs[-20:])
            if atr_20v > 0:
                cpr_raw = 1.0 - (atr_5d / atr_20v)

    # ── Accélération = perf_5j - perf_20j
    acc_raw = None
    if len(closes) >= 21 and closes[-6] > 0 and closes[-21] > 0:
        p5  = (closes[-1] - closes[-6])  / closes[-6]  * 100
        p20 = (closes[-1] - closes[-21]) / closes[-21] * 100
        acc_raw = p5 - p20

    # ── VSR 3j / 10j
    vsr_ratio = None
    if vols and len(vols) >= 10:
        v3j  = [v for v in vols[-3:]  if v and v > 0]
        v10j = [v for v in vols[-10:] if v and v > 0]
        if v3j and v10j:
            m3  = statistics.mean(v3j)
            m10 = statistics.mean(v10j)
            if m10 > 0:
                vsr_ratio = round(m3 / m10, 2)

    # ── Normalisation 0-100
    rs_s   = _score_linear(rs_raw,  -10.0, 10.0) if rs_raw  is not None else 50.0
    brk_s  = _score_linear(brk_raw,  -3.0,  3.0) if brk_raw is not None else 50.0
    vol_s  = _score_linear(vol_raw,   0.3,  3.0)  if vol_raw is not None else 50.0
    mom_s  = _score_linear(mom_raw,  -5.0,  5.0)  if mom_raw is not None else 50.0
    cpr_s  = _score_linear(cpr_raw,   0.0,  1.0)  if cpr_raw is not None else 50.0
    acc_s  = _score_linear(acc_raw,  -5.0,  5.0)  if acc_raw is not None else 50.0

    # ── ATR % et RSI (filtres qualité, indépendants des poids)
    atr_pct = calculer_atr_pct(closes)
    rsi     = calculer_rsi(closes)

    # ── VCP pattern (indépendant des poids)
    vcp = (cpr_s >= 60 and brk_s >= 60 and vsr_ratio is not None and vsr_ratio >= 2.5)

    return {
        "rs_s": rs_s, "brk_s": brk_s, "vol_s": vol_s,
        "mom_s": mom_s, "cpr_s": cpr_s, "acc_s": acc_s,
        "atr_pct": atr_pct, "rsi": rsi, "vcp": vcp,
        "vsr_ratio": vsr_ratio,
    }


def appliquer_config(scores, cfg):
    """
    Applique une configuration de poids sur des scores bruts précalculés.
    Retourne un signal dict ou None si les filtres qualité échouent.
    """
    if scores is None:
        return None

    atr_pct = scores["atr_pct"]
    rsi     = scores["rsi"]

    # Filtres qualité (fixes, indépendants des poids)
    if not atr_pct or atr_pct < ATR_MIN:
        return None
    if rsi and rsi > 78:
        return None

    # Filtre VCP-only
    if cfg["vcp_only"] and not scores["vcp"]:
        return None

    # Score composite
    score_mf = (
        cfg["rs"]  * scores["rs_s"]
        + cfg["brk"] * scores["brk_s"]
        + cfg["vol"] * scores["vol_s"]
        + cfg["mom"] * scores["mom_s"]
        + cfg["cpr"] * scores["cpr_s"]
    )
    if cfg["acc_bonus"] and scores["acc_s"] >= 80:
        score_mf = min(100.0, score_mf + 5.0)
    score_mf = round(score_mf, 1)

    # Gate score
    if score_mf < 55:
        return None

    # Classe et stops
    if score_mf >= 85:
        classe   = "A"
        rr_cible = 2.0
    elif score_mf >= 70:
        classe   = "B"
        rr_cible = 2.4
    else:
        classe   = "C"
        rr_cible = 3.0

    stop_pct  = max(STOP_FACTOR * atr_pct, 0.5)
    gain_att  = round(rr_cible * stop_pct, 1)
    rr        = round(gain_att / stop_pct, 2)

    if rr < RR_MIN:
        return None

    return {
        "classe":       classe,
        "score_mf":     score_mf,
        "atr_pct":      atr_pct,
        "stop_pct":     stop_pct,
        "gain_attendu": gain_att,
        "rr":           rr,
        "vcp":          scores["vcp"],
    }


def calculer_metriques(trades):
    """Calcule WR, PF, MaxDD, capital_final, EV net depuis une liste de trades."""
    if not trades:
        return None

    n = len(trades)
    gagnants = [t for t in trades if t["gain_net"] > 0]
    perdants  = [t for t in trades if t["gain_net"] <= 0]

    wr = len(gagnants) / n * 100

    gains_tot  = sum(t["gain_net"] for t in gagnants)
    pertes_tot = abs(sum(t["gain_net"] for t in perdants))
    pf = round(gains_tot / pertes_tot, 2) if pertes_tot > 0 else float("inf")

    ev = round(statistics.mean(t["gain_net"] for t in trades), 2)

    gain_win  = round(statistics.mean(t["gain_net"] for t in gagnants), 2) if gagnants else 0
    perte_los = round(statistics.mean(t["gain_net"] for t in perdants), 2) if perdants else 0

    # Max Drawdown séquentiel
    capital = 100.0
    pic     = capital
    max_dd  = 0.0
    for t in trades:
        capital *= (1 + t["gain_net"] / 100)
        if capital > pic:
            pic = capital
        dd = (pic - capital) / pic * 100
        if dd > max_dd:
            max_dd = dd

    return {
        "n":            n,
        "wr":           round(wr, 1),
        "ev":           ev,
        "gain_win":     gain_win,
        "perte_los":    perte_los,
        "pf":           pf,
        "max_dd":       round(max_dd, 1),
        "capital_fin":  round(capital, 1),
    }


def run_ablation():
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    db = client["centralisation_db"]

    print("\n" + "=" * 80)
    print(" ABLATION STUDY — BRVM Multi-Factor Engine ".center(80))
    print(f" Horizon J+{HORIZON_SORTIE} | ATR_MIN={ATR_MIN}% | Stop={STOP_FACTOR}xATR | Couts={TOTAL_COST}% ".center(80))
    print("=" * 80 + "\n")

    debut = datetime.now()

    # ─── 1. Charger tous les symboles ────────────────────────────────────────
    symboles = db.prices_daily.distinct("symbol")
    symboles = [s for s in symboles if s and s not in INDICES]
    print(f"  Symboles charges : {len(symboles)}")

    # ─── 2. Précalculer TOUS les scores bruts (une seule fois) ───────────────
    print("  Precalcul des scores bruts sur tout l'historique...")

    # Structure : events[symbol] = [(close_actuel, close_sortie, scores_bruts)]
    events = defaultdict(list)
    total_windows = 0

    for symbol in symboles:
        docs = list(db.prices_daily.find({"symbol": symbol}).sort("date", 1))
        if len(docs) < MIN_HIST + HORIZON_SORTIE + 5:
            continue

        prix_list = [d.get("close") for d in docs]
        vol_list  = [d.get("volume", 0) for d in docs]

        for i in range(MIN_HIST, len(prix_list) - HORIZON_SORTIE):
            close_act  = prix_list[i]
            close_sort = prix_list[i + HORIZON_SORTIE]

            if not close_act or close_act <= 0:
                continue
            if not close_sort or close_sort <= 0:
                continue

            # Scores bruts sur la fenêtre [0..i]
            window_closes = [p for p in prix_list[:i+1] if p and p > 0]
            window_vols   = vol_list[:i+1]

            scores = extraire_scores_bruts(window_closes, window_vols)
            if scores is None:
                continue

            # Pré-simuler la sortie effective (stops / cible) pour chaque scenario
            # On stocke les prix futurs pour simulation per-config
            prix_futurs = prix_list[i+1 : i + HORIZON_SORTIE + 1]

            events[symbol].append({
                "close_act":   close_act,
                "close_sort":  close_sort,
                "prix_futurs": prix_futurs,
                "scores":      scores,
            })
            total_windows += 1

    print(f"  {total_windows} fenetres valides sur {len(events)} symboles\n")

    # ─── 3. Appliquer chaque configuration ───────────────────────────────────
    resultats = {}

    for config_name, cfg in CONFIGURATIONS.items():
        trades_cfg = []

        for symbol, ev_list in events.items():
            for ev in ev_list:
                scores    = ev["scores"]
                close_act = ev["close_act"]

                # Signal pour cette configuration
                sig = appliquer_config(scores, cfg)
                if sig is None:
                    continue

                # Simuler la sortie effective
                prix_cible = close_act * (1 + sig["gain_attendu"] / 100)
                prix_stop  = close_act * (1 - sig["stop_pct"]     / 100)

                sortie_eff  = (ev["close_sort"] - close_act) / close_act * 100
                motif       = "HORIZON"

                for p in ev["prix_futurs"]:
                    if not p:
                        continue
                    if p >= prix_cible:
                        sortie_eff = sig["gain_attendu"]
                        motif      = "CIBLE"
                        break
                    if p <= prix_stop:
                        sortie_eff = -sig["stop_pct"]
                        motif      = "STOP"
                        break

                gain_net = round(sortie_eff - TOTAL_COST, 2)
                trades_cfg.append({
                    "symbol":   symbol,
                    "classe":   sig["classe"],
                    "score_mf": sig["score_mf"],
                    "vcp":      sig["vcp"],
                    "gain_net": gain_net,
                    "motif":    motif,
                })

        resultats[config_name] = calculer_metriques(trades_cfg)

    # ─── 4. Affichage comparatif ─────────────────────────────────────────────
    duree = (datetime.now() - debut).total_seconds()
    print(f"  Calcul termine en {duree:.1f}s\n")
    print("=" * 80)
    print(" TABLEAU COMPARATIF — 11 CONFIGURATIONS ".center(80))
    print("=" * 80)

    # En-tête
    header = f"{'Config':<22} {'N':>5} {'WR%':>6} {'EV':>7} {'Win':>7} {'Los':>7} {'PF':>5} {'DD%':>6} {'Cap':>7}"
    print(header)
    print("─" * 80)

    # Trier par PF décroissant
    sorted_cfgs = sorted(
        [(name, m) for name, m in resultats.items() if m and m["n"] >= MIN_TRADES_DISP],
        key=lambda x: x[1]["pf"] if x[1]["pf"] != float("inf") else 999,
        reverse=True
    )

    # Référence = C07_MF_PROD
    ref_pf = resultats.get("C07_MF_PROD", {})
    ref_pf_val = ref_pf.get("pf", 1.0) if ref_pf else 1.0

    for name, m in sorted_cfgs:
        delta_pf = m["pf"] - ref_pf_val if ref_pf_val else 0
        pf_tag   = f"  << REF" if name == "C07_MF_PROD" else (f"  +{delta_pf:.2f}" if delta_pf > 0 else f"  {delta_pf:.2f}")
        pf_str   = f"{m['pf']:.2f}" if m["pf"] != float("inf") else "  inf"
        row = (f"{name:<22} {m['n']:>5} {m['wr']:>5.1f}% "
               f"{m['ev']:>+6.2f}% {m['gain_win']:>+6.2f}% {m['perte_los']:>+6.2f}% "
               f"{pf_str:>5} {m['max_dd']:>5.1f}% {m['capital_fin']:>7.1f}{pf_tag}")
        print(row)

    print("─" * 80)

    # ─── 5. Analyse qualitative ─────────────────────────────────────────────
    print("\n ANALYSE ".center(80, "─"))

    # Trouver le meilleur PF
    best = max(sorted_cfgs, key=lambda x: x[1]["pf"] if x[1]["pf"] != float("inf") else 0)
    prod = resultats.get("C07_MF_PROD")

    if prod:
        print(f"\n  Production (C07_MF_PROD) : WR={prod['wr']:.1f}% | PF={prod['pf']:.2f} | EV={prod['ev']:+.2f}%/trade | DD={prod['max_dd']:.1f}%")

    if best[0] != "C07_MF_PROD":
        print(f"  Meilleur PF  : {best[0]} (PF={best[1]['pf']:.2f} vs {ref_pf_val:.2f} prod)")

    # Identifier les facteurs solo qui battent / perdent vs prod
    solos = ["C00_RS_seul", "C01_Breakout_seul", "C02_Volume_seul", "C03_Momentum_seul"]
    print(f"\n  Facteurs seuls vs production :")
    for s in solos:
        if s in resultats and resultats[s]:
            m = resultats[s]
            diff_pf = m["pf"] - ref_pf_val
            diff_wr = m["wr"] - (prod["wr"] if prod else 0)
            tag = "MIEUX" if diff_pf > 0.05 else ("EQUIVALENT" if abs(diff_pf) <= 0.05 else "MOINS_BON")
            print(f"    {s:<22} PF={m['pf']:.2f} ({diff_pf:+.2f} vs prod) WR={m['wr']:.1f}% ({diff_wr:+.1f}pp)  [{tag}]")

    # VCP isolation
    vcp_res = resultats.get("C09_MF_VCP_only")
    if vcp_res and vcp_res["n"] >= 5:
        print(f"\n  VCP seul (C09) : N={vcp_res['n']} | WR={vcp_res['wr']:.1f}% | PF={vcp_res['pf']:.2f} | EV={vcp_res['ev']:+.2f}%")
        if prod:
            vcp_wr_delta = vcp_res["wr"] - prod["wr"]
            print(f"    -> WR delta vs prod : {vcp_wr_delta:+.1f}pp ({'VCP surperforme' if vcp_wr_delta > 2 else 'VCP equivalent' if abs(vcp_wr_delta) <= 2 else 'VCP sous-performe'})")
    else:
        print(f"\n  VCP : moins de {MIN_TRADES_DISP} trades (marche BRVM thin, signal rare — normal)")

    # Bonus accélération
    mf_sans_acc = resultats.get("C08_MF_sans_acc")
    if mf_sans_acc and prod:
        diff = prod["pf"] - mf_sans_acc["pf"]
        print(f"\n  Bonus acceleration : +{diff:+.3f} PF (prod={prod['pf']:.2f} vs sans_acc={mf_sans_acc['pf']:.2f})")
        print(f"    -> {'Bonus utile' if diff > 0.03 else 'Bonus negligeable' if abs(diff) <= 0.03 else 'Bonus nuit'}")

    # RS+BRK+VOL vs MF complet
    c06 = resultats.get("C06_RS+BRK+VOL")
    if c06 and prod:
        diff = c06["pf"] - prod["pf"]
        print(f"\n  RS+BRK+VOL (3 facteurs) vs MF_5 : {diff:+.3f} PF")
        print(f"    -> {'Simplifier est preferable' if diff > 0.05 else 'Garder 5 facteurs' if diff < -0.05 else 'Equivalent (simplification possible)'}")

    # Conclusion
    print(f"\n{'─'*80}")
    print("  CONCLUSION")
    print(f"{'─'*80}")

    # Trouver d'où vient réellement l'edge
    best_solo = max(
        [(s, resultats[s]) for s in solos if s in resultats and resultats[s] and resultats[s]["n"] >= MIN_TRADES_DISP],
        key=lambda x: x[1]["pf"],
        default=(None, None)
    )

    if best_solo[0] and prod:
        bs_name = best_solo[0].replace("C0", "").replace("_seul", "")
        bs_pf   = best_solo[1]["pf"]
        if bs_pf > prod["pf"] + 0.10:
            print(f"  ! ALERTE : {best_solo[0]} (facteur seul) bat le modele complet.")
            print(f"    Le modele 5-facteurs dilue l'edge. Envisager simplification.")
        elif bs_pf > prod["pf"] - 0.10:
            print(f"  ~ ATTENTION : {best_solo[0]} est quasi-equivalent au modele complet.")
            print(f"    80%+ de l'edge vient peut-etre d'un seul facteur.")
        else:
            print(f"  OK : La combinaison 5-facteurs est superieure au meilleur facteur seul ({bs_name}).")
            print(f"    L'approche multi-facteurs est justifiee.")

    print(f"\n  [RAPPEL] Ces resultats sont sur donnees historiques BRVM.")
    print(f"  La validation live (paper trading 8-12 semaines) reste indispensable.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_ablation()
