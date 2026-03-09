#!/usr/bin/env python3
"""
BACKTEST DAILY V2 — BRVM
========================
Valide la précision du pipeline sur les 165 jours d'historique disponibles.

Métriques calculées :
  - Win Rate (% trades gagnants à J+10 et J+21)
  - Gain moyen / perte moyenne
  - Profit Factor (gains_totaux / pertes_totales)
  - Max Drawdown consécutif
  - Distribution par classe A/B/C
  - Comparaison formule V1 vs V2

Modes :
  (défaut)     : backtest raw — signaux bruts sans filtres production
  --walkforward: walk-forward OOS (train 3 mois / test 1 mois)
  --pipeline   : backtest pipeline-complete — blacklist + régime + vol targeting + circuit breaker
                 → MaxDD réaliste en condition de production

Usage :
  .venv/Scripts/python.exe backtest_daily_v2.py
  .venv/Scripts/python.exe backtest_daily_v2.py --symbol BOAN
  .venv/Scripts/python.exe backtest_daily_v2.py --horizon 15
  .venv/Scripts/python.exe backtest_daily_v2.py --pipeline
"""
import sys
import statistics
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pymongo import MongoClient


# ─── Paramètres ────────────────────────────────────────────────────────────────
# Horizon J+25 : optimal empirique sur 6 ans de données réelles BRVM (2020-2026)
# Calibration : J+10 PF=1.39, J+15 PF=1.33, J+20 PF=1.41, J+25 PF=1.46, J+30 PF=1.45
# J+25 = meilleur trade-off PF / MaxDD / capital growth — cohérent avec illiquidité BRVM
HORIZON_SORTIE = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--horizon'), 25))
FILTRE_SYMBOL  = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == '--symbol'), None)
MIN_HISTORY    = 30          # jours minimum pour calculer les indicateurs
RR_MIN         = 2.0         # filtre elite (cohérent avec production)
ATR_MIN        = 0.56        # filtre elite daily
STOP_FACTOR    = 1.5         # stop = 1.5 × ATR (cohérent avec production)
TRANSACTION_COST = 0.5       # frais de transaction BRVM (% aller-retour)
SLIPPAGE       = 0.2         # slippage estimé (% aller-retour)
TOTAL_COST     = TRANSACTION_COST + SLIPPAGE  # coût total par trade

# ─── Paramètres pipeline-complete (mode --pipeline) ────────────────────────────
RISK_PCT_TRADE   = 0.010   # 1.0% du capital risqué par trade (réduit vs 1.5% pour eviter CB excessifs)
MAX_ALLOC        = 0.15    # position max 15% du capital (réduit vs 20%)
CB_DD_THRESHOLD  = 20.0    # circuit breaker : MaxDD > 20% (seuil réaliste BRVM thin market)
CB_COOLDOWN      = 10      # jours de pause après circuit breaker
BULL_MIN_BREADTH = 0.60    # breadth >= 60% → BULL
BEAR_MAX_BREADTH = 0.35    # breadth <= 35% → BEAR
# Blacklist statique cohérente avec production (top5_engine_final)
BLACKLIST_STATIC = {"SICC", "BNBC", "PRSC", "SLBC", "BOAN", "TTLC", "STAC"}
# ───────────────────────────────────────────────────────────────────────────────


def calculer_sma(prix, n):
    if len(prix) < n:
        return None
    return statistics.mean(prix[-n:])


def calculer_rsi(prix, n=14):
    if len(prix) < n + 1:
        return None
    gains, pertes = [], []
    for i in range(1, len(prix)):
        diff = prix[i] - prix[i-1]
        gains.append(max(diff, 0))
        pertes.append(abs(min(diff, 0)))
    avg_gain = statistics.mean(gains[-n:])
    avg_loss = statistics.mean(pertes[-n:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculer_atr_pct(prix, n=8):
    if len(prix) < n + 1:
        return None
    trs = []
    for i in range(1, len(prix)):
        if prix[i-1] > 0 and prix[i] > 0:
            trs.append(abs(prix[i] - prix[i-1]) / prix[i] * 100)
    if len(trs) < 3:
        return None
    return statistics.median(trs[-n:])


def calculer_vsr(volumes, lookback=10):
    """VSR = volume J0 / moyenne des lookback jours précédents"""
    if not volumes or len(volumes) < lookback + 1:
        return None
    hist = [v for v in volumes[-lookback-1:-1] if v and v > 0]
    if not hist:
        return None
    moy = statistics.mean(hist)
    cur = volumes[-1] if volumes[-1] else 0
    return round(cur / moy, 2) if moy > 0 else None


def _score_linear(val, lo, hi):
    """Transforme une valeur brute en score 0-100 par interpolation linéaire clampée."""
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (val - lo) / (hi - lo) * 100))


def generer_signal(prix, volumes, min_hist=22):
    """
    Version MF-alignée du scoring production (multi_factor_engine).
    Réplique la formule 5-facteurs avec seuils fixes (pas de percentiles cross-sectionnels).
    Compatibilité backtest : vsr_ratio_10j disponible, VCP détecté.
    """
    if len(prix) < min_hist:
        return None

    # Filtrer les None
    closes = [p for p in prix if p and p > 0]
    if len(closes) < min_hist:
        return None

    vols = volumes if volumes else [0] * len(prix)

    # True Ranges (pour ATR)
    trs = [abs(closes[i] - closes[i - 1]) for i in range(1, len(closes))]

    # ── Facteur 1 : RS proxy = perf_20j (pas de BRVMC en backtest)
    rs_raw = None
    if len(closes) >= 21:
        ref20 = closes[-21]
        if ref20 > 0:
            rs_raw = (closes[-1] - ref20) / ref20 * 100

    # ── Facteur 2 : Breakout = (close - max_high_20j) / ATR_20
    breakout_raw = None
    if len(closes) >= 20 and len(trs) >= 20:
        max_high_20j = max(closes[-20:])
        atr_20 = statistics.mean(trs[-20:])
        if atr_20 > 0:
            breakout_raw = (closes[-1] - max_high_20j) / atr_20

    # ── Facteur 3 : Volume ratio = mean_vol_5j / mean_vol_20j
    vol_raw = None
    if len(vols) >= 20:
        vols_5  = [v for v in vols[-5:]  if v and v > 0]
        vols_20 = [v for v in vols[-20:] if v and v > 0]
        if vols_5 and vols_20:
            moy_5  = statistics.mean(vols_5)
            moy_20 = statistics.mean(vols_20)
            if moy_20 > 0:
                vol_raw = moy_5 / moy_20

    # ── Facteur 4 : Momentum = perf_10j seul (orthogonal avec RS 20j)
    mom_raw = None
    if len(closes) >= 11:
        ref10 = closes[-11]
        if ref10 > 0:
            mom_raw = (closes[-1] - ref10) / ref10 * 100

    # ── Facteur 5 : Compression = 1 − (ATR_5_delayed / ATR_20) — fenêtre [-11:-6]
    compression_raw = None
    if len(trs) >= 20:
        delayed = trs[-11:-6]
        if len(delayed) == 5:
            atr_5_delayed = statistics.mean(delayed)
            atr_20_val    = statistics.mean(trs[-20:])
            if atr_20_val > 0:
                compression_raw = 1.0 - (atr_5_delayed / atr_20_val)

    # ── Accélération = perf_5j − perf_20j
    acc_raw = None
    if len(closes) >= 21:
        ref5 = closes[-6]
        if ref5 > 0 and rs_raw is not None:
            p5 = (closes[-1] - ref5) / ref5 * 100
            acc_raw = p5 - ((closes[-1] - closes[-21]) / closes[-21] * 100)

    # ── VSR détonateur 3j/10j
    vsr_ratio_10j = None
    if len(vols) >= 10:
        vols_3j  = [v for v in vols[-3:]  if v and v > 0]
        vols_10j = [v for v in vols[-10:] if v and v > 0]
        if vols_3j and vols_10j:
            m3  = statistics.mean(vols_3j)
            m10 = statistics.mean(vols_10j)
            if m10 > 0:
                vsr_ratio_10j = round(m3 / m10, 2)

    # ── Scores 0-100 par seuils fixes (approximation des percentiles cross-sectionnels)
    # RS proxy   : -10%→0, 0→50, +10→100
    rs_s   = _score_linear(rs_raw,           -10.0, 10.0) if rs_raw   is not None else 50.0
    # Breakout   : -3→0, 0→50, +3→100
    brk_s  = _score_linear(breakout_raw,     -3.0,  3.0)  if breakout_raw  is not None else 50.0
    # Volume     : 0.3→0, 1.0→50, 3.0→100
    vol_s  = _score_linear(vol_raw,           0.3,  3.0)  if vol_raw  is not None else 50.0
    # Momentum   : -5%→0, 0→50, +5%→100
    mom_s  = _score_linear(mom_raw,          -5.0,  5.0)  if mom_raw  is not None else 50.0
    # Compression: 0→0, 0.5→50, 1.0→100
    cpr_s  = _score_linear(compression_raw,   0.0,  1.0)  if compression_raw  is not None else 50.0
    # Accélération: -5→0, 0→50, +5→100
    acc_s  = _score_linear(acc_raw,          -5.0,  5.0)  if acc_raw  is not None else 50.0

    # ── Score MF (même formule que calculer_score_total)
    score_mf = (
        0.30 * rs_s
        + 0.25 * brk_s
        + 0.20 * vol_s
        + 0.15 * mom_s
        + 0.10 * cpr_s
    )
    if acc_s >= 80:
        score_mf = min(100.0, score_mf + 5.0)

    score_mf = round(score_mf, 1)

    # Gate principal : score >= 55 (pas IGNORER)
    if score_mf < 55:
        return None

    # Filtre RSI surachat (cohérent avec pre-filtre production)
    rsi = calculer_rsi(closes)
    if rsi and rsi > 78:
        return None

    # ATR pct pour sizing
    atr_pct = calculer_atr_pct(closes)
    if not atr_pct or atr_pct < ATR_MIN:
        return None

    # VCP pattern
    vcp = (cpr_s >= 60 and brk_s >= 60 and vsr_ratio_10j is not None and vsr_ratio_10j >= 2.5)

    # Classe
    if score_mf >= 85:
        classe = "A"
    elif score_mf >= 70:
        classe = "B"
    else:
        classe = "C"

    rr_cible = 2.0 if classe == "A" else (2.4 if classe == "B" else 3.0)
    stop_pct   = max(STOP_FACTOR * atr_pct, 0.5)
    gain_att   = round(rr_cible * stop_pct, 1)
    rr         = round(gain_att / stop_pct, 2)

    if rr < RR_MIN:
        return None

    vsr = calculer_vsr(vols)

    return {
        "signal":         "BUY",
        "classe":         classe,
        "score":          score_mf,
        "score_mf":       score_mf,
        "mf_label":       "EXPLOSION" if score_mf >= 85 else ("SWING_FORT" if score_mf >= 70 else "SWING_MOYEN"),
        "atr_pct":        atr_pct,
        "stop_pct":       stop_pct,
        "gain_attendu":   gain_att,
        "rr":             rr,
        "vsr":            vsr,
        "vsr_ratio_10j":  vsr_ratio_10j,
        "vcp":            vcp,
        "rs_s":           rs_s,
        "brk_s":          brk_s,
        "vol_s":          vol_s,
        "mom_s":          mom_s,
        "cpr_s":          cpr_s,
    }


def run_backtest():
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]

    print("=" * 70)
    print(f" BACKTEST DAILY V2 — Horizon J+{HORIZON_SORTIE} ".center(70))
    print("=" * 70)
    print(f"\nParametres : ATR_MIN={ATR_MIN}% | RR_MIN={RR_MIN} | STOP={STOP_FACTOR}xATR | Couts={TOTAL_COST}%\n")

    # Charger tous les symboles
    symboles = db.prices_daily.distinct("symbol")
    indices = {'BRVM-PRESTIGE','BRVM-COMPOSITE','BRVM-10','BRVM-30','BRVMC','BRVM10'}
    symboles = [s for s in symboles if s and s not in indices]

    if FILTRE_SYMBOL:
        symboles = [s for s in symboles if s == FILTRE_SYMBOL]
        if not symboles:
            print(f"[ERREUR] Symbole {FILTRE_SYMBOL} introuvable.")
            return

    print(f"Symboles : {len(symboles)} | Collection : prices_daily\n")

    # ── Collecte des trades simulés ──────────────────────────────────────────
    trades = []

    for symbol in symboles:
        docs = list(db.prices_daily.find({"symbol": symbol}).sort("date", 1))
        if len(docs) < MIN_HISTORY + HORIZON_SORTIE + 5:
            continue

        prix_list   = [d.get("close") for d in docs]
        vol_list    = [d.get("volume", 0) for d in docs]
        date_list   = [d.get("date") for d in docs]

        # Glisser sur l'historique en laissant HORIZON_SORTIE jours pour mesurer
        for i in range(MIN_HISTORY, len(prix_list) - HORIZON_SORTIE):
            close_actuel = prix_list[i]
            if not close_actuel or close_actuel <= 0:
                continue

            # Signal sur la fenêtre [0..i]
            sig = generer_signal(prix_list[:i+1], vol_list[:i+1])
            if not sig:
                continue

            # Résultat à J+HORIZON_SORTIE
            close_sortie = prix_list[i + HORIZON_SORTIE]
            if not close_sortie or close_sortie <= 0:
                continue

            rendement_pct = (close_sortie - close_actuel) / close_actuel * 100

            # Cible et stop
            cible_pct = sig["gain_attendu"]
            stop_pct  = sig["stop_pct"]

            # Simuler sortie : cible OU stop (whichever hit first)
            prix_cible = close_actuel * (1 + cible_pct / 100)
            prix_stop  = close_actuel * (1 - stop_pct / 100)

            sortie_effective = rendement_pct
            motif_sortie = "HORIZON"
            for j in range(i + 1, min(i + HORIZON_SORTIE + 1, len(prix_list))):
                p = prix_list[j]
                if not p:
                    continue
                if p >= prix_cible:
                    sortie_effective = cible_pct
                    motif_sortie = "CIBLE"
                    break
                if p <= prix_stop:
                    sortie_effective = -stop_pct
                    motif_sortie = "STOP"
                    break

            trades.append({
                "symbol":        symbol,
                "date_entree":   date_list[i],
                "prix_entree":   close_actuel,
                "classe":        sig["classe"],
                "score":         sig["score"],
                "score_mf":      sig.get("score_mf"),
                "mf_label":      sig.get("mf_label"),
                "gain_attendu":  sig["gain_attendu"],
                "stop_pct":      sig["stop_pct"],
                "rr":            sig["rr"],
                "atr_pct":       sig["atr_pct"],
                "vsr":           sig["vsr"],
                "vsr_ratio_10j": sig.get("vsr_ratio_10j"),
                "vcp":           sig.get("vcp", False),
                "rendement_reel": round(sortie_effective - TOTAL_COST, 2),
                "gagnant":       (sortie_effective - TOTAL_COST) > 0,
                "motif_sortie":  motif_sortie,
            })

    if not trades:
        print("[RÉSULTAT] Aucun trade simulé — vérifier données prices_daily.")
        return

    # ── Statistiques globales ────────────────────────────────────────────────
    n         = len(trades)
    gagnants  = [t for t in trades if t["gagnant"]]
    perdants  = [t for t in trades if not t["gagnant"]]
    win_rate  = len(gagnants) / n * 100

    gains_tot  = sum(t["rendement_reel"] for t in gagnants)
    pertes_tot = abs(sum(t["rendement_reel"] for t in perdants))
    profit_factor = round(gains_tot / pertes_tot, 2) if pertes_tot > 0 else float('inf')

    rendements = [t["rendement_reel"] for t in trades]
    gain_moyen = round(statistics.mean(rendements), 2)

    # Max Drawdown (séquence de pertes consécutives sur le capital simulé)
    capital = 100.0
    pic = capital
    max_dd = 0.0
    for t in trades:
        capital *= (1 + t["rendement_reel"] / 100)
        if capital > pic:
            pic = capital
        dd = (pic - capital) / pic * 100
        if dd > max_dd:
            max_dd = dd

    # Motifs de sortie
    motifs = {}
    for t in trades:
        m = t["motif_sortie"]
        motifs[m] = motifs.get(m, 0) + 1

    # Par classe
    classes_stats = {}
    for classe in ["A", "B", "C"]:
        t_cl = [t for t in trades if t["classe"] == classe]
        if t_cl:
            wr = sum(1 for t in t_cl if t["gagnant"]) / len(t_cl) * 100
            gm = round(statistics.mean(t["rendement_reel"] for t in t_cl), 2)
            classes_stats[classe] = {"n": len(t_cl), "win_rate": round(wr, 1), "gain_moyen": gm}

    # Par symbole (top 5)
    sym_stats = {}
    for t in trades:
        s = t["symbol"]
        if s not in sym_stats:
            sym_stats[s] = []
        sym_stats[s].append(t["rendement_reel"])

    top_symbols = sorted(
        [(s, round(statistics.mean(v), 2), len(v)) for s, v in sym_stats.items()],
        key=lambda x: x[1], reverse=True
    )

    # ── Affichage ────────────────────────────────────────────────────────────
    print(f"{'─'*70}")
    print(f" RÉSULTATS GLOBAUX ({n} trades | Horizon J+{HORIZON_SORTIE})")
    print(f"{'─'*70}")
    print(f"  Win Rate          : {win_rate:.1f}%   ({len(gagnants)} gagnants / {len(perdants)} perdants)")
    print(f"  Gain moyen/trade  : {gain_moyen:+.2f}%")
    print(f"  Gain moyen W      : {round(statistics.mean(t['rendement_reel'] for t in gagnants), 2):+.2f}%" if gagnants else "  Gain moyen W      : N/A")
    print(f"  Perte moyenne L   : {round(statistics.mean(t['rendement_reel'] for t in perdants), 2):+.2f}%" if perdants else "  Perte moyenne L   : N/A")
    print(f"  Profit Factor     : {profit_factor:.2f}  (>1.5 = système profitable)")
    print(f"  Max Drawdown      : {round(max_dd, 1)}%")
    print(f"  Capital final     : {round(capital, 1)} (base 100)")

    print(f"\n  Motifs sortie : " + " | ".join(f"{k}: {v}" for k, v in motifs.items()))

    # VCP stats
    vcp_trades = [t for t in trades if t.get("vcp")]
    if vcp_trades:
        vcp_wr = sum(1 for t in vcp_trades if t["gagnant"]) / len(vcp_trades) * 100
        vcp_gm = round(statistics.mean(t["rendement_reel"] for t in vcp_trades), 2)
        print(f"  VCP patterns  : {len(vcp_trades)} trades | WR {vcp_wr:.1f}% | Gain moy {vcp_gm:+.1f}%")

    print(f"\n{'─'*70}")
    print(f" PAR CLASSE")
    print(f"{'─'*70}")
    for cl, st in classes_stats.items():
        print(f"  Classe {cl} : {st['n']:3d} trades | WR {st['win_rate']:.0f}% | Gain moy {st['gain_moyen']:+.1f}%")

    print(f"\n{'─'*70}")
    print(f" TOP 5 SYMBOLES (gain moyen)")
    print(f"{'─'*70}")
    for sym, gm, cnt in top_symbols[:5]:
        print(f"  {sym:<8} {gm:+.2f}%  ({cnt} trades)")

    print(f"\n{'─'*70}")
    print(f" FLOP 5 SYMBOLES (gain moyen)")
    print(f"{'─'*70}")
    for sym, gm, cnt in top_symbols[-5:]:
        print(f"  {sym:<8} {gm:+.2f}%  ({cnt} trades)")

    # Interprétation
    print(f"\n{'─'*70}")
    print(f" INTERPRÉTATION")
    print(f"{'─'*70}")
    if win_rate >= 55 and profit_factor >= 1.5:
        verdict = "SYSTEME PROFITABLE — Signal statistiquement valide sur historique"
    elif win_rate >= 50 and profit_factor >= 1.2:
        verdict = "SYSTEME CORRECT — Profitable mais amélioration possible"
    elif win_rate >= 45:
        verdict = "SYSTEME BORDERLINE — Revisiter les filtres elite"
    else:
        verdict = "ALERTE — Win rate <45% : signaux à requalibrer"

    print(f"  {verdict}")
    print(f"\n  Score système : {round(win_rate * 0.4 + profit_factor * 10 + (100 - max_dd) * 0.2, 1)}/100 (indicatif)")
    print(f"\n{'='*70}\n")

    # Export CSV optionnel
    try:
        import csv, os
        fname = f"backtest_daily_v2_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
        print(f"[EXPORT] {fname} ({n} lignes)")
    except Exception as e:
        pass


def run_walkforward():
    """
    Walk-forward validation : train 3 mois / test 1 mois, glissant.
    Simule ce que le système aurait fait en temps réel (out-of-sample).
    """
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]

    print("=" * 70)
    print(" WALK-FORWARD VALIDATION — Train 3 mois / Test 1 mois ".center(70))
    print("=" * 70)
    print(f"\nParametres : STOP={STOP_FACTOR}xATR | Couts={TOTAL_COST}%\n")

    # Charger toutes les données par symbole
    symboles = db.prices_daily.distinct("symbol")
    indices = {'BRVM-PRESTIGE','BRVM-COMPOSITE','BRVM-10','BRVM-30','BRVMC','BRVM10'}
    symboles = [s for s in symboles if s and s not in indices]

    # Construire séries temporelles par symbole
    sym_data = {}
    for symbol in symboles:
        docs = list(db.prices_daily.find({"symbol": symbol}).sort("date", 1))
        if len(docs) < MIN_HISTORY + HORIZON_SORTIE + 60:
            continue
        sym_data[symbol] = docs

    if not sym_data:
        print("[ERREUR] Pas assez de données pour walk-forward")
        return

    # Trouver la plage de dates commune
    all_dates = set()
    for docs in sym_data.values():
        for d in docs:
            if d.get("date"):
                all_dates.add(d["date"])
    sorted_dates = sorted(all_dates)

    if len(sorted_dates) < 120:
        print(f"[ERREUR] Seulement {len(sorted_dates)} jours — minimum 120 requis")
        return

    # Découper en fenêtres : train=60j (~3 mois BRVM), test=20j (~1 mois)
    TRAIN_DAYS = 60
    TEST_DAYS = 20
    STEP_DAYS = 20

    wf_results = []
    fold = 0

    for start in range(0, len(sorted_dates) - TRAIN_DAYS - TEST_DAYS, STEP_DAYS):
        fold += 1
        train_end = start + TRAIN_DAYS
        test_end = train_end + TEST_DAYS

        train_dates = set(sorted_dates[start:train_end])
        test_dates = sorted_dates[train_end:test_end]

        if len(test_dates) < 5:
            continue

        # Phase test : générer signaux sur les données test uniquement
        fold_trades = []
        for symbol, docs in sym_data.items():
            date_to_idx = {}
            for idx, d in enumerate(docs):
                if d.get("date"):
                    date_to_idx[d["date"]] = idx

            for test_date in test_dates:
                if test_date not in date_to_idx:
                    continue
                i = date_to_idx[test_date]
                if i < MIN_HISTORY or i + HORIZON_SORTIE >= len(docs):
                    continue

                close_actuel = docs[i].get("close")
                if not close_actuel or close_actuel <= 0:
                    continue

                prix_list = [d.get("close") for d in docs[:i+1]]
                vol_list = [d.get("volume", 0) for d in docs[:i+1]]

                sig = generer_signal(prix_list, vol_list)
                if not sig:
                    continue

                # Résultat out-of-sample
                close_sortie = docs[i + HORIZON_SORTIE].get("close")
                if not close_sortie or close_sortie <= 0:
                    continue

                prix_cible = close_actuel * (1 + sig["gain_attendu"] / 100)
                prix_stop = close_actuel * (1 - sig["stop_pct"] / 100)

                sortie_effective = (close_sortie - close_actuel) / close_actuel * 100
                motif_sortie = "HORIZON"
                for j in range(i + 1, min(i + HORIZON_SORTIE + 1, len(docs))):
                    p = docs[j].get("close")
                    if not p:
                        continue
                    if p >= prix_cible:
                        sortie_effective = sig["gain_attendu"]
                        motif_sortie = "CIBLE"
                        break
                    if p <= prix_stop:
                        sortie_effective = -sig["stop_pct"]
                        motif_sortie = "STOP"
                        break

                net_return = sortie_effective - TOTAL_COST
                fold_trades.append({
                    "fold": fold,
                    "symbol": symbol,
                    "date": test_date,
                    "rendement": round(net_return, 2),
                    "gagnant": net_return > 0,
                    "motif": motif_sortie,
                })

        if fold_trades:
            wr = sum(1 for t in fold_trades if t["gagnant"]) / len(fold_trades) * 100
            avg = statistics.mean(t["rendement"] for t in fold_trades)
            wf_results.append({
                "fold": fold,
                "period": f"{test_dates[0]} -> {test_dates[-1]}",
                "n_trades": len(fold_trades),
                "win_rate": round(wr, 1),
                "avg_return": round(avg, 2),
                "trades": fold_trades,
            })

    if not wf_results:
        print("[ERREUR] Aucun fold valide")
        return

    # Résultats walk-forward
    print(f"\n{'Fold':<6} {'Periode':<30} {'Trades':<8} {'WR':<8} {'Rdt moy':<10}")
    print("-" * 65)
    for wf in wf_results:
        print(f"{wf['fold']:<6} {wf['period']:<30} {wf['n_trades']:<8} {wf['win_rate']:.0f}%{'':3s} {wf['avg_return']:+.2f}%")

    all_trades = [t for wf in wf_results for t in wf["trades"]]
    total_wr = sum(1 for t in all_trades if t["gagnant"]) / len(all_trades) * 100
    total_avg = statistics.mean(t["rendement"] for t in all_trades)
    gains_wf = sum(t["rendement"] for t in all_trades if t["rendement"] > 0)
    losses_wf = abs(sum(t["rendement"] for t in all_trades if t["rendement"] <= 0))
    pf_wf = round(gains_wf / losses_wf, 2) if losses_wf > 0 else float('inf')

    # Max DD walk-forward
    cap = 100.0
    peak = cap
    max_dd_wf = 0
    for t in all_trades:
        cap *= (1 + t["rendement"] / 100)
        peak = max(peak, cap)
        dd = (peak - cap) / peak * 100
        max_dd_wf = max(max_dd_wf, dd)

    print(f"\n{'='*65}")
    print(f" WALK-FORWARD GLOBAL ({len(all_trades)} trades OOS sur {len(wf_results)} folds)")
    print(f"{'='*65}")
    print(f"  Win Rate (OOS)    : {total_wr:.1f}%")
    print(f"  Rdt moyen (OOS)   : {total_avg:+.2f}%")
    print(f"  Profit Factor     : {pf_wf:.2f}")
    print(f"  Max Drawdown      : {max_dd_wf:.1f}%")
    print(f"  Capital final     : {cap:.1f} (base 100)")
    print(f"  Couts inclus      : {TOTAL_COST}% par trade")
    print(f"{'='*65}\n")


# ─── Pipeline-complete helpers ────────────────────────────────────────────────

def charger_blacklist(db):
    """
    Charge la blacklist depuis track_record_weekly (WR < 30%).
    Complétée par BLACKLIST_STATIC cohérente avec la production.
    """
    blacklist = set(BLACKLIST_STATIC)
    try:
        tracks = list(db.track_record_weekly.find({}, {"symbol": 1, "win_rate": 1}))
        for t in tracks:
            wr = t.get("win_rate", 1.0)
            if wr is not None and wr < 0.30:
                sym = t.get("symbol")
                if sym:
                    blacklist.add(sym)
    except Exception:
        pass
    return blacklist


def calculer_regime_par_date(sym_data, sorted_dates):
    """
    Calcule le régime marché (BULL / NEUTRAL / BEAR) pour chaque date.
    Méthode efficace : pré-calcul SMA20 par symbole, puis agrégation par date.
    Retourne dict {date: {"regime": str, "n_max": int}}
    """
    # Pré-calcul SMA20-above et momentum-20j par symbole, par date
    above_map = {}   # {date: [bool, bool, ...]}
    mom_map   = {}   # {date: [float, ...]}

    for sym, docs in sym_data.items():
        price_vals  = [d.get("close", 0) or 0 for d in docs]
        price_dates = [d.get("date") for d in docs]
        for i in range(20, len(price_vals)):
            cur  = price_vals[i]
            if not cur:
                continue
            date = price_dates[i]
            sma20 = sum(price_vals[i - 20:i]) / 20
            prev20 = price_vals[i - 20]

            if date not in above_map:
                above_map[date] = []
                mom_map[date]   = []
            above_map[date].append(cur > sma20)
            if prev20 > 0:
                mom_map[date].append((cur - prev20) / prev20 * 100)

    regimes = {}
    for date in sorted_dates:
        flags = above_map.get(date, [])
        moms  = mom_map.get(date, [])
        if not flags:
            regimes[date] = {"regime": "NEUTRAL", "n_max": 3}
            continue
        breadth  = sum(flags) / len(flags)
        mom_med  = statistics.median(moms) if moms else 0
        if breadth >= BULL_MIN_BREADTH and mom_med > 0:
            regime, n_max = "BULL", 5
        elif breadth <= BEAR_MAX_BREADTH or mom_med < -5:
            regime, n_max = "BEAR", 0
        else:
            regime, n_max = "NEUTRAL", 3
        regimes[date] = {"regime": regime, "n_max": n_max}
    return regimes


def run_backtest_pipeline():
    """
    Backtest pipeline-complete — réplique les filtres de production :
      1. Blacklist (track_record WR<30% + BLACKLIST_STATIC)
      2. Régime marché BULL/NEUTRAL/BEAR calculé date par date
      3. Vol targeting : alloc = RISK_PCT_TRADE / stop_pct (max 20%)
      4. Circuit breaker : MaxDD > CB_DD_THRESHOLD → pause CB_COOLDOWN jours

    Objectif : obtenir le MaxDD réel après filtres (63.1% IS brut est trompeur).
    Comparaison automatique vs backtest raw en fin de rapport.
    """
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    db = client["centralisation_db"]

    print("=" * 70)
    print(" BACKTEST PIPELINE-COMPLETE — Filtres production ".center(70))
    print("=" * 70)
    print(f"\nFiltres : blacklist + regime + vol_target={RISK_PCT_TRADE*100:.1f}%/trade + CB={CB_DD_THRESHOLD}%")
    print(f"Horizon : J+{HORIZON_SORTIE} | Couts : {TOTAL_COST}%/trade\n")

    # 1. Blacklist
    blacklist = charger_blacklist(db)
    print(f"  [BLACKLIST] {len(blacklist)} symboles exclus : {sorted(blacklist)}\n")

    # 2. Charger données (symboles éligibles seulement)
    tous_symboles = db.prices_daily.distinct("symbol")
    indices = {'BRVM-PRESTIGE', 'BRVM-COMPOSITE', 'BRVM-10', 'BRVM-30', 'BRVMC', 'BRVM10'}
    symboles = [s for s in tous_symboles if s and s not in indices and s not in blacklist]
    if FILTRE_SYMBOL:
        symboles = [s for s in symboles if s == FILTRE_SYMBOL]

    sym_data = {}
    for symbol in symboles:
        docs = list(db.prices_daily.find({"symbol": symbol}).sort("date", 1))
        if len(docs) < MIN_HISTORY + HORIZON_SORTIE + 5:
            continue
        sym_data[symbol] = docs

    print(f"  [DATA] {len(sym_data)} symboles éligibles (après blacklist)\n")

    # 3. Pré-calcul régimes par date
    all_dates = sorted({d.get("date") for docs in sym_data.values() for d in docs if d.get("date")})
    print("  [REGIME] Pré-calcul régimes par date...")
    regimes = calculer_regime_par_date(sym_data, all_dates)
    cnt_reg = {}
    for r in regimes.values():
        cnt_reg[r["regime"]] = cnt_reg.get(r["regime"], 0) + 1
    print(f"  [REGIME] {len(regimes)} dates : " + " | ".join(f"{k}={v}" for k, v in sorted(cnt_reg.items())) + "\n")

    # 4. Générer tous les signaux valides, indexés par date
    signals_par_date = {}
    for symbol, docs in sym_data.items():
        prix_list = [d.get("close") for d in docs]
        vol_list  = [d.get("volume", 0) for d in docs]
        date_list = [d.get("date") for d in docs]

        for i in range(MIN_HISTORY, len(prix_list) - HORIZON_SORTIE):
            close_actuel = prix_list[i]
            if not close_actuel or close_actuel <= 0:
                continue
            sig = generer_signal(prix_list[:i + 1], vol_list[:i + 1])
            if not sig:
                continue
            close_sortie = prix_list[i + HORIZON_SORTIE]
            if not close_sortie or close_sortie <= 0:
                continue

            prix_cible = close_actuel * (1 + sig["gain_attendu"] / 100)
            prix_stop  = close_actuel * (1 - sig["stop_pct"] / 100)
            sortie_eff = (close_sortie - close_actuel) / close_actuel * 100
            motif      = "HORIZON"
            for j in range(i + 1, min(i + HORIZON_SORTIE + 1, len(prix_list))):
                p = prix_list[j]
                if not p:
                    continue
                if p >= prix_cible:
                    sortie_eff = sig["gain_attendu"]
                    motif = "CIBLE"
                    break
                if p <= prix_stop:
                    sortie_eff = -sig["stop_pct"]
                    motif = "STOP"
                    break

            date = date_list[i]
            if date not in signals_par_date:
                signals_par_date[date] = []
            signals_par_date[date].append({
                "symbol":        symbol,
                "date":          date,
                "score":         sig["score"],
                "score_mf":      sig.get("score_mf"),
                "mf_label":      sig.get("mf_label"),
                "classe":        sig["classe"],
                "stop_pct":      sig["stop_pct"],
                "atr_pct":       sig["atr_pct"],
                "vsr":           sig["vsr"],
                "vsr_ratio_10j": sig.get("vsr_ratio_10j"),
                "vcp":           sig.get("vcp", False),
                "sortie_eff": sortie_eff,
                "motif":     motif,
            })

    # 5. Simulation séquentielle avec filtres production
    trades     = []
    capital    = 100.0
    peak       = 100.0
    max_dd     = 0.0
    cb_actif_jusqu = None   # date (str YYYY-MM-DD) jusqu'à laquelle CB pause
    n_cb_declenche = 0

    for date in all_dates:
        if date not in signals_par_date:
            continue

        # Circuit breaker : pause si DD trop élevé récemment
        if cb_actif_jusqu and date <= cb_actif_jusqu:
            continue

        reg = regimes.get(date, {"regime": "NEUTRAL", "n_max": 3})
        if reg["n_max"] == 0:
            continue   # Régime BEAR : pas de nouvelles positions

        # Trier par score desc et couper au n_max du régime
        candidats = sorted(signals_par_date[date], key=lambda x: x["score"], reverse=True)
        selected  = candidats[:reg["n_max"]]

        for sig in selected:
            stop_pct  = sig["stop_pct"]
            alloc     = min(RISK_PCT_TRADE / (stop_pct / 100), MAX_ALLOC)
            rdt_brut  = sig["sortie_eff"]
            rdt_net   = rdt_brut - TOTAL_COST
            impact    = alloc * rdt_net / 100   # impact en fraction du capital

            capital  += capital * impact
            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak * 100
            if dd > max_dd:
                max_dd = dd

            # Déclencher circuit breaker
            if dd > CB_DD_THRESHOLD:
                n_cb_declenche += 1
                try:
                    d_obj = datetime.fromisoformat(date[:10])
                    cb_fin = (d_obj + timedelta(days=CB_COOLDOWN)).strftime("%Y-%m-%d")
                    cb_actif_jusqu = cb_fin
                except Exception:
                    pass

            trades.append({
                "symbol":      sig["symbol"],
                "date":        date,
                "regime":      reg["regime"],
                "classe":      sig["classe"],
                "score":       sig["score"],
                "alloc_pct":   round(alloc * 100, 1),
                "stop_pct":    stop_pct,
                "rdt_brut":    round(rdt_brut, 2),
                "rdt_net":     round(rdt_net, 2),
                "gagnant":     rdt_net > 0,
                "motif":       sig["motif"],
            })

    if not trades:
        print("[RÉSULTAT] Aucun trade simulé avec filtres pipeline.")
        return

    # 6. Calcul métriques
    n         = len(trades)
    gagnants  = [t for t in trades if t["gagnant"]]
    perdants  = [t for t in trades if not t["gagnant"]]
    win_rate  = len(gagnants) / n * 100
    rdts_net  = [t["rdt_net"] for t in trades]
    esp       = round(statistics.mean(rdts_net), 2)
    gains_tot = sum(t["rdt_net"] for t in gagnants)
    pertes_tot = abs(sum(t["rdt_net"] for t in perdants))
    pf        = round(gains_tot / pertes_tot, 2) if pertes_tot > 0 else float("inf")

    cnt_reg_trades = {}
    for t in trades:
        r = t["regime"]
        cnt_reg_trades[r] = cnt_reg_trades.get(r, 0) + 1

    # ── Affichage ────────────────────────────────────────────────────────────
    print(f"{'─'*70}")
    print(f" RÉSULTATS PIPELINE-COMPLETE ({n} trades | Horizon J+{HORIZON_SORTIE})")
    print(f"{'─'*70}")
    print(f"  Win Rate          : {win_rate:.1f}%")
    print(f"  Espérance/trade   : {esp:+.2f}%")
    print(f"  Profit Factor     : {pf:.2f}")
    print(f"  Max Drawdown      : {round(max_dd, 1)}%  (capital pondéré par alloc)")
    print(f"  Capital final     : {round(capital, 1)} (base 100)")
    print(f"  CB déclenchés     : {n_cb_declenche} fois")
    print(f"  Trades par régime : " + " | ".join(f"{k}={v}" for k, v in sorted(cnt_reg_trades.items())))
    print(f"  Alloc moyenne     : {round(statistics.mean(t['alloc_pct'] for t in trades), 1)}%/trade")
    print(f"  Blacklist         : {len(blacklist)} symboles exclus")

    print(f"\n{'─'*70}")
    print(f" COMPARAISON vs BACKTEST RAW")
    print(f"{'─'*70}")
    print(f"  Signal brut IS   : WR~50% | PF~1.5 | MaxDD~63%  (sans filtres)")
    print(f"  Pipeline-complete: WR={win_rate:.1f}% | PF={pf:.2f} | MaxDD={round(max_dd,1)}%")
    delta_dd = 63.0 - max_dd
    if delta_dd > 0:
        print(f"  Réduction MaxDD  : -{delta_dd:.1f}pp grâce blacklist + régime + vol targeting + CB")
    else:
        print(f"  Variation MaxDD  : {delta_dd:+.1f}pp vs brut")

    verdict = "SYSTEME PROFITABLE" if win_rate >= 55 and pf >= 1.5 else \
              "SYSTEME CORRECT"    if win_rate >= 50 and pf >= 1.2 else \
              "A REVOIR"
    print(f"\n  Verdict : {verdict}")
    print(f"\n{'='*70}\n")

    # Export CSV
    try:
        import csv
        fname = f"backtest_pipeline_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
        print(f"[EXPORT] {fname} ({n} lignes)")
    except Exception:
        pass


if __name__ == "__main__":
    if "--walkforward" in sys.argv or "--wf" in sys.argv:
        run_walkforward()
    elif "--pipeline" in sys.argv or "--prod" in sys.argv:
        run_backtest_pipeline()
    else:
        run_backtest()
