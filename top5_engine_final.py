#!/usr/bin/env python3
"""
TOP5 ENGINE - BRVM (VERSION FINALE PRODUCTION)
===============================================

Une seule mission : classer les 5 meilleures opportunités
à partir de decisions_finales_brvm (source unique de vérité)

Modes :
  python top5_engine_final.py               → moyen terme weekly (4-8 sem)
  python top5_engine_final.py --mode daily  → court terme daily  (2-3 sem)
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from pymongo import MongoClient
from datetime import datetime, timezone
import statistics


def compute_corr_pairs(db, symbols, mode_daily=True, seuil=0.95):
    """
    Calcule les paires de symboles dont la corrélation des rendements dépasse `seuil`.
    Retourne un dict {(sym_a, sym_b): corr} pour les paires ≥ seuil (sym_a < sym_b).
    Utilise prices_daily ou prices_weekly selon mode_daily.
    """
    prix_dict = {}
    for sym in symbols:
        if mode_daily:
            docs = list(db.prices_daily.find({"symbol": sym}, {"close": 1}).sort("date", 1))
        else:
            docs = list(db.prices_weekly.find({"symbol": sym}, {"close": 1}).sort("week", 1))
        prix = [d["close"] for d in docs if d.get("close") and d["close"] > 0]
        if len(prix) >= 20:
            prix_dict[sym] = prix

    if len(prix_dict) < 2:
        return {}

    # Aligner les séries sur la longueur minimale
    min_len = min(len(p) for p in prix_dict.values())
    aligned = {sym: prix[-min_len:] for sym, prix in prix_dict.items()}

    # Rendements
    rendements = {}
    for sym, prix in aligned.items():
        rdt = [(prix[i] - prix[i-1]) / prix[i-1] for i in range(1, len(prix)) if prix[i-1] > 0]
        if len(rdt) >= 10:
            rendements[sym] = rdt

    syms = sorted(rendements.keys())
    corr_fortes = {}
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            a, b = syms[i], syms[j]
            ra, rb = rendements[a], rendements[b]
            n = min(len(ra), len(rb))
            if n < 10:
                continue
            ra_t, rb_t = ra[-n:], rb[-n:]
            try:
                mean_a = statistics.mean(ra_t)
                mean_b = statistics.mean(rb_t)
                cov = sum((ra_t[k] - mean_a) * (rb_t[k] - mean_b) for k in range(n)) / n
                std_a = statistics.stdev(ra_t)
                std_b = statistics.stdev(rb_t)
                if std_a > 0 and std_b > 0:
                    corr = cov / (std_a * std_b)
                    if abs(corr) >= seuil:
                        corr_fortes[(a, b)] = round(corr, 3)
            except Exception:
                pass

    return corr_fortes


def get_liquidity_stats(db, symbols):
    """
    Calcule pour chaque symbole :
    - val_moy20j    : valeur moyenne echangee sur 20j (volume x close) en FCFA
    - jours_trades  : nb jours avec volume > 0 sur les 20 derniers jours
    Si prices_daily ne couvre pas le symbole → stats nulles (exclu par filtre).
    """
    stats = {}
    for sym in symbols:
        docs = list(db.prices_daily.find(
            {"symbol": sym, "close": {"$gt": 0}},
            {"volume": 1, "close": 1}
        ).sort("date", -1).limit(20))
        if not docs:
            stats[sym] = {"val_moy20j": 0, "jours_trades": 0}
            continue
        valeurs = [d.get("volume", 0) * d.get("close", 0) for d in docs]
        jours   = sum(1 for d in docs if (d.get("volume") or 0) > 0)
        stats[sym] = {
            "val_moy20j":  sum(valeurs) / len(valeurs) if valeurs else 0,
            "jours_trades": jours
        }
    return stats


# MODE DUAL
MODE_DAILY  = "--mode" in sys.argv and "daily" in sys.argv
HORIZON_TAG = "JOUR" if MODE_DAILY else "SEMAINE"
COLLECTION  = "top5_daily_brvm" if MODE_DAILY else "top5_weekly_brvm"
LABEL       = "SWING 1-2 semaines" if MODE_DAILY else "SWING 1-2 semaines (weekly)"

# Meta-model desactive : features backtest != features MF prod
# Reactiver quand track_record_weekly >= 60 trades fermes
ENABLE_META_MODEL = False

def generate_top5():
    """Génère le TOP 5 hebdomadaire à partir des décisions BUY"""
    
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]  # Base Django
    
    print("\n" + "="*70)
    print(f" TOP5 ENGINE — {LABEL} ".center(70))
    print("="*70 + "\n")

    # Récupération decisions BUY validées uniquement (non archivées)
    decisions = list(db.decisions_finales_brvm.find(
        {"decision": "BUY", "horizon": HORIZON_TAG, "archived": {"$ne": True}},
        {
            "symbol": 1,
            "classe": 1,
            "confidence": 1,
            "gain_attendu": 1,
            "expected_return": 1,
            "rr": 1,
            "wos": 1,
            "prix_entree": 1,
            "prix_cible": 1,
            "stop": 1,
            "atr_pct": 1,
            "rsi": 1,
            "justification": 1,
            "raisons": 1,
            "position_size_factor": 1,
            "allocation_max": 1,
            "timing_signal": 1,
            "vsr": 1,
            "momentum_5j": 1,
            "score_alpha": 1,
            "alpha_label": 1,
            "score_total_mf": 1,
            "mf_label": 1,
            "setup_type": 1,
            "setup_id": 1,
            "acceleration_score_mf": 1,
            "breakout_score_mf": 1,
            "volume_score_mf": 1,
            "compression_score_mf": 1,
            "rs_percentile": 1,
            "rs_score_mf": 1,
            "momentum_score_mf": 1,
            "vsr_ratio_10j": 1
        }
    ))
    
    if not decisions:
        print("[INFO] Aucune decision BUY hebdomadaire trouvee\n")
        print("   Executer d'abord: decision_finale_brvm.py\n")
        return []

    print(f"[STATS] {len(decisions)} decisions BUY hebdomadaires disponibles\n")

    # ── CHARGEMENT SCORES SEMANTIQUES (agrégateur V2) ─────────────────────────
    # score_semantique_7j = SUM top-3 docs après decay exponentiel (half_life=5j)
    # signal_explosion    = score>=12 + catalyseur fondamental dans les 72h
    sem_scores = {}
    for sem_doc in db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}):
        sym_key = sem_doc.get("key") or sem_doc.get("attrs", {}).get("symbol")
        if sym_key:
            sa = sem_doc.get("attrs", {})
            sem_scores[sym_key] = {
                "score_7j":            sa.get("score_semantique_7j", 0) or 0,
                "signal_explosion":    sa.get("signal_explosion",   False),
                "catalyseur_recent":   sa.get("catalyseur_recent_72h", False),
                "sentiment_global":    sa.get("sentiment_global",   "NEUTRE"),
            }
    n_sem = sum(1 for v in sem_scores.values() if abs(v["score_7j"]) > 0)
    n_exp = sum(1 for v in sem_scores.values() if v["signal_explosion"])
    print(f"  [SEMANTIQUE] {len(sem_scores)} actions chargees, {n_sem} avec score>0, {n_exp} signal EXPLOSION\n")

    # Enrichir chaque décision avec les données sémantiques
    for d in decisions:
        sym = d.get("symbol", "")
        sem = sem_scores.get(sym, {})
        d["score_semantique_7j"]  = sem.get("score_7j", 0)
        d["signal_explosion"]     = sem.get("signal_explosion", False)
        d["catalyseur_recent_72h"]= sem.get("catalyseur_recent", False)
        d["sentiment_global"]     = sem.get("sentiment_global", "NEUTRE")
        # Normaliser score_7j → [0, 100] (0=très négatif, 40=neutre, 100=très positif+)
        # scale : score_7j=0 → 40, score_7j=+15 → 70, score_7j=+30 → 100
        sem_norm = max(0.0, min(100.0, (d["score_semantique_7j"] + 20.0) / 50.0 * 100.0))
        d["sem_score_normalized"] = round(sem_norm, 1)

    # Calcul TOP5_SCORE (probabilité de surperformance)
    for d in decisions:
        gain = d.get("gain_attendu") or d.get("expected_return") or 0
        conf = d.get("confidence") or 0
        rr   = d.get("rr") or 0
        wos  = min(100.0, d.get("wos") or 0)   # cap normalisé
        vsr          = d.get("vsr")
        momentum_5j_val = d.get("momentum_5j")

        # AMÉLIORATION 3 — Pénalité liquidité : position_size_factor=0.5 → score ×0.5
        liq_factor = d.get("position_size_factor") or 1.0

        if vsr is not None and momentum_5j_val is not None:
            # FORMULE V2 — Classement par signaux observables (pas par gain espéré)
            # VSR : 0x→0pts, 1x→33pts, 2x→67pts, ≥3x→100pts
            vsr_norm  = min(100.0, (vsr / 3.0) * 100)
            # Momentum 5j : -5%→0pts, 0%→50pts, +5%→100pts
            mom5_norm = min(100.0, max(0.0, (momentum_5j_val + 5.0) / 10.0 * 100))
            raw_score = (
                0.30 * vsr_norm  +      # Volume Spike Ratio (précurseur clé BRVM)
                0.25 * mom5_norm +      # Momentum 5j brut observable
                0.25 * conf      +      # Confiance technique
                0.15 * (rr * 10) +      # Risk/Reward normalisé
                0.05 * wos              # Setup quality (normalisé 0-100)
            )
        else:
            # FORMULE LEGACY — backward compat si pipeline pas encore mis à jour
            raw_score = (
                0.35 * gain      +      # Gain attendu
                0.30 * conf      +      # Confiance
                0.20 * (rr * 10) +      # Risk/Reward
                0.15 * wos              # Setup quality
            )

        d["top5_score"] = raw_score * liq_factor

        # SCORE_ALPHA — Breakout Acceleration Score (formule desk quant)
        # SCORE_ALPHA = 0.30*Breakout + 0.25*VolumeShock + 0.20*RS + 0.15*VolExp + 0.10*VCP (0-1)
        score_alpha = d.get("score_alpha")
        score_total_mf = d.get("score_total_mf")

        # SCORE FINAL — Ensemble : technique (90%) + sentiment catalyseur (10%)
        # Formule : 0.55×MF + 0.35×Alpha + 0.10×Sentiment_normalisé
        # Bonus +5 si signal_explosion (catalyseur fort dans les 72h)
        sem_norm       = d.get("sem_score_normalized", 40.0)   # 40 = neutre si pas de données
        explosion_bonus = 5.0 if d.get("signal_explosion") else 0.0

        # VCP Pattern : compression + breakout cassure + choc liquidité
        # +4 pts si les 3 conditions simultanées (signal qualité supérieur BRVM)
        _vsr10 = d.get("vsr_ratio_10j") or 0.0
        vcp_pattern = (
            d.get("compression_score_mf", 0) >= 60
            and d.get("breakout_score_mf",  0) >= 60
            and _vsr10 >= 2.5
        )
        vcp_bonus = 4.0 if vcp_pattern else 0.0
        d["vcp_pattern"] = vcp_pattern

        if score_total_mf is not None and score_alpha is not None:
            base = 0.55 * score_total_mf + 0.35 * score_alpha * 100 + 0.10 * sem_norm
            d["top5_score"] = (base + explosion_bonus + vcp_bonus) * liq_factor
        elif score_total_mf is not None:
            base = 0.90 * score_total_mf + 0.10 * sem_norm
            d["top5_score"] = (base + explosion_bonus + vcp_bonus) * liq_factor
        elif score_alpha is not None:
            base = 0.55 * raw_score + 0.35 * score_alpha * 100 + 0.10 * sem_norm
            d["top5_score"] = (base + explosion_bonus + vcp_bonus) * liq_factor

        # AMÉLIORATION 2 — Sizing si pas encore en base
        if not d.get("allocation_max"):
            classe = d.get("classe", "C")
            d["allocation_max"] = 15.0 if classe == "A" else (10.0 if classe == "B" else 5.0)

    # ── FILTRE LIQUIDITE ABSOLUE (R3) ────────────────────────────────────────
    # valeur echangee moy 20j >= 3M FCFA ET jours trades >= 10/20
    # evite les signaux "fantomes" sur actions illiquides BRVM
    LIQ_MIN_FCFA  = 3_000_000   # 3 millions FCFA/jour
    LIQ_MIN_JOURS = 10          # au moins 1 jour sur 2 actif

    print("  [LIQUIDITE] Calcul valeur echangee 20j...")
    liq_stats = get_liquidity_stats(db, [d["symbol"] for d in decisions])
    decisions_liq = []
    for d in decisions:
        sym   = d.get("symbol", "")
        lst   = liq_stats.get(sym, {})
        val   = lst.get("val_moy20j", 0)
        jours = lst.get("jours_trades", 0)
        if val < LIQ_MIN_FCFA or jours < LIQ_MIN_JOURS:
            print(f"  [LIQUIDITE] {sym} exclu — {val/1e6:.1f}M FCFA/j, {jours}/20 jours")
            continue
        d["val_moy20j"]    = round(val)
        d["jours_trades20j"] = jours
        decisions_liq.append(d)
    n_excl_liq = len(decisions) - len(decisions_liq)
    if n_excl_liq:
        print(f"  [LIQUIDITE] {n_excl_liq} exclu(s) illiquide(s), {len(decisions_liq)} restants")
    decisions = decisions_liq

    # A7 — BLACKLIST track record (filtrage dur — symboles systématiquement perdants)
    # WR < 30% sur >= 10 trades = blacklisté (aucun TOP3 possible)
    # WR entre 30-40% = pénalité x0.5 (admis mais décoté)
    # Readmission : si WR > 40% sur les 20 derniers trades
    blacklist = set()
    track_record_stats = {}
    if MODE_DAILY:
        import glob as _glob
        csv_files = sorted(_glob.glob("backtest_daily_v2_*.csv"), reverse=True)
        if csv_files:
            import csv
            from collections import defaultdict
            _stats = defaultdict(lambda: {"total": 0, "wins": 0})
            try:
                with open(csv_files[0], "r", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        sym = row.get("symbol", "")
                        _stats[sym]["total"] += 1
                        if row.get("gagnant") == "True":
                            _stats[sym]["wins"] += 1
                track_record_stats = {
                    sym: s["wins"] / s["total"] * 100
                    for sym, s in _stats.items() if s["total"] >= 10
                }
            except Exception:
                pass
    else:
        from collections import defaultdict
        _stats = defaultdict(lambda: {"total": 0, "wins": 0})
        for tr in db.track_record_weekly.find():
            sym = tr.get("symbol", "")
            _stats[sym]["total"] += 1
            statut = str(tr.get("statut", ""))
            if "CIBLE" in statut.upper():
                _stats[sym]["wins"] += 1
        track_record_stats = {
            sym: s["wins"] / s["total"] * 100
            for sym, s in _stats.items() if s["total"] >= 3
        }

    if track_record_stats:
        print(f"  [TRACK RECORD] {len(track_record_stats)} symboles avec historique suffisant")
        for sym, wr in sorted(track_record_stats.items(), key=lambda x: x[1]):
            if wr < 30:
                blacklist.add(sym)
                print(f"  [BLACKLIST] {sym} EXCLU (WR={wr:.0f}% < 30%)")
            elif wr < 40:
                # Pénalité sévère mais pas blacklist
                for d in decisions:
                    if d.get("symbol") == sym:
                        d["top5_score"] *= 0.5
                        print(f"  [TRACK RECORD] {sym} penalise x0.5 (WR={wr:.0f}%)")

    # Retirer les blacklistés des décisions
    n_avant_bl = len(decisions)
    decisions = [d for d in decisions if d.get("symbol", "") not in blacklist]
    if blacklist:
        print(f"  [BLACKLIST] {n_avant_bl - len(decisions)} symboles retires, {len(decisions)} restants")

    # A8 — RÉGIME DE MARCHÉ ADAPTATIF (Market Regime Filter)
    # Combine largeur du marché (% > SMA20) + momentum médian (perf 20j)
    # Détermine BULL / NEUTRAL / BEAR → ajuste topN et risk_per_trade
    market_regime = "NEUTRAL"  # défaut
    regime_risk_pct = 1.0      # risque par trade (% du capital)
    try:
        n_above_sma20 = 0
        n_total_sma20 = 0
        perf_20j_list = []
        price_col = "prices_daily" if MODE_DAILY else "prices_weekly"
        date_field = "date" if MODE_DAILY else "week"
        all_symbols = db[price_col].distinct("symbol")
        for sym in all_symbols:
            hist = list(db[price_col].find(
                {"symbol": sym, "close": {"$gt": 0}},
                {"close": 1}
            ).sort(date_field, -1).limit(21))
            if len(hist) >= 20:
                last_close = hist[0]["close"]
                sma20 = sum(h["close"] for h in hist[:20]) / 20
                n_total_sma20 += 1
                if last_close > sma20:
                    n_above_sma20 += 1
                # Perf 20j = (close actuel - close il y a 20j) / close il y a 20j
                close_20j = hist[19]["close"] if len(hist) >= 20 else hist[-1]["close"]
                if close_20j and close_20j > 0:
                    perf = (last_close - close_20j) / close_20j * 100
                    perf_20j_list.append(perf)

        if n_total_sma20 > 0:
            pct_above = n_above_sma20 / n_total_sma20 * 100
            market_momentum = statistics.median(perf_20j_list) if perf_20j_list else 0

            print(f"\n  [REGIME] Largeur marche: {n_above_sma20}/{n_total_sma20} au-dessus SMA20 ({pct_above:.0f}%)")
            print(f"  [REGIME] Momentum median 20j: {market_momentum:+.2f}%")

            if pct_above > 60 and market_momentum > 0:
                market_regime = "BULL"
                regime_risk_pct = 1.5
                print(f"  [REGIME] >>> BULL <<< — topN=5, risk=1.5%/trade")
            elif pct_above >= 40:
                market_regime = "NEUTRAL"
                regime_risk_pct = 1.0
                print(f"  [REGIME] >>> NEUTRAL <<< — topN=3, risk=1.0%/trade")
            else:
                market_regime = "BEAR"
                regime_risk_pct = 0.5
                print(f"  [REGIME] >>> BEAR <<< — topN=1, risk=0.5%/trade")

            for d in decisions:
                d["market_regime"] = market_regime
                d["regime_risk_pct"] = regime_risk_pct
        else:
            print("  [REGIME] Pas assez de donnees SMA20")
    except Exception as e:
        print(f"  [REGIME] Erreur calcul: {e}")

    # A11 — META-MODEL DE PROBABILITÉ (désactivé — ENABLE_META_MODEL = False)
    # Raison : features backtest (score, atr_pct, rr) != features MF prod
    # => modele entraine sur realite inexistante en live => precision ~52% (hasard)
    # Reactiver quand track_record_weekly >= 60 trades fermes avec labels MF reels
    if ENABLE_META_MODEL:
        try:
            import glob as _glob2
            csv_files = sorted(_glob2.glob("backtest_daily_v2_*.csv"), reverse=True) if MODE_DAILY else []
            if csv_files:
                import csv as _csv
                import numpy as np
                from sklearn.linear_model import LogisticRegression
                from sklearn.preprocessing import StandardScaler
                train_rows = []
                with open(csv_files[0], "r", encoding="utf-8") as f:
                    for row in _csv.DictReader(f):
                        try:
                            features = {
                                "score": float(row.get("score", 0)),
                                "atr_pct": float(row.get("atr_pct", 0)),
                                "stop_pct": float(row.get("stop_pct", 0)),
                                "rr": float(row.get("rr", 0)),
                                "vsr": float(row.get("vsr", 0)) if row.get("vsr") else 0,
                                "gain_attendu": float(row.get("gain_attendu", 0)),
                            }
                            label = 1 if row.get("gagnant") == "True" else 0
                            train_rows.append((features, label))
                        except (ValueError, TypeError):
                            continue
                if len(train_rows) >= 50:
                    feature_names = ["score", "atr_pct", "stop_pct", "rr", "vsr", "gain_attendu"]
                    X_train = np.array([[r[0][f] for f in feature_names] for r in train_rows])
                    y_train = np.array([r[1] for r in train_rows])
                    scaler = StandardScaler()
                    X_scaled = scaler.fit_transform(X_train)
                    model = LogisticRegression(random_state=42, max_iter=500, C=0.5)
                    model.fit(X_scaled, y_train)
                    train_acc = model.score(X_scaled, y_train)
                    print(f"\n  [META-MODEL] Entraine sur {len(train_rows)} trades (acc={train_acc:.1%})")
                    n_filtered = 0
                    for d in decisions:
                        try:
                            x = np.array([[
                                d.get("confidence", 0) or 0,
                                d.get("atr_pct", 0) or 0,
                                (d.get("atr_pct", 2) or 2) * 1.5,
                                d.get("rr", 0) or 0,
                                d.get("vsr", 0) or 0,
                                d.get("gain_attendu") or d.get("expected_return") or 0,
                            ]])
                            x_scaled = scaler.transform(x)
                            prob_win = model.predict_proba(x_scaled)[0][1]
                            d["prob_win"] = round(prob_win, 3)
                            reject_threshold = max(0.45, train_acc - 0.10)
                            boost_high = min(0.80, train_acc + 0.20)
                            boost_mid  = min(0.70, train_acc + 0.10)
                            sym = d.get("symbol", "?")
                            if prob_win < reject_threshold:
                                d["meta_model_rejected"] = True
                                n_filtered += 1
                                print(f"  [META-MODEL] {sym} REJETE P(win)={prob_win:.1%}")
                            elif prob_win >= boost_high:
                                d["prob_boost"] = 2.0
                            elif prob_win >= boost_mid:
                                d["prob_boost"] = 1.5
                        except Exception:
                            d["prob_win"] = 0.55
                    decisions = [d for d in decisions if not d.get("meta_model_rejected")]
                    if n_filtered:
                        print(f"  [META-MODEL] {n_filtered} rejetes, {len(decisions)} restants")
                else:
                    print(f"  [META-MODEL] Pas assez de donnees ({len(train_rows)} < 50)")
            else:
                print("  [META-MODEL] Aucun fichier backtest CSV trouve")
        except Exception as e:
            print(f"  [META-MODEL] Erreur: {e}")
    else:
        # Meta-model desactive : prob_win neutre 0.55 pour tous
        for d in decisions:
            d["prob_win"] = 0.55
        print("  [META-MODEL] Desactive (< 60 trades fermes) — prob_win=0.55 constant")


    # A5 — Enrichissement secteur depuis prices_daily (filtre corrélation sectorielle)
    BANQUE_SYMBOLS = {"BOAB", "BOABF", "BOAC", "BOAM", "BOAN", "BOAS", "SGBC", "SIBC", "BICC", "CBIBF", "ETIT"}
    for d in decisions:
        daily_doc = db.prices_daily.find_one({"symbol": d["symbol"]}, {"secteur_officiel": 1, "sector": 1})
        d["_sector"] = (daily_doc.get("secteur_officiel") or daily_doc.get("sector") or "AUTRE") if daily_doc else "AUTRE"

    # A6 — Pré-calcul corrélations fortes entre candidats (seuil 0.85)
    candidat_symbols = [d["symbol"] for d in decisions]
    corr_fortes = compute_corr_pairs(db, candidat_symbols, mode_daily=MODE_DAILY, seuil=0.85)
    if corr_fortes:
        print(f"  [CORR] {len(corr_fortes)} paires avec corrélation ≥ 0.85 détectées")
        for (sa, sb), cv in sorted(corr_fortes.items(), key=lambda x: -abs(x[1]))[:5]:
            print(f"         {sa}/{sb}: {cv:.3f}")

    # A5 — Classement avec filtre sectoriel + filtre corrélation (max 2 banques, max 2 même secteur)
    decisions_sorted = sorted(decisions, key=lambda x: x["top5_score"], reverse=True)

    # PRE-FILTRE MF — Swing 1-2 semaines (explosion setup)
    # Conditions :
    #   score_total_mf >= 55           → pas IGNORER
    #   breakout_score_mf >= 50        → breakout au-dessus médiane (renforce vs 45)
    #   volume_score_mf >= 60          → carburant present P60
    #   RSI <= 78                      → pas de "trop tard" (R5)
    #   compression_score_mf >= 45
    #     OU atr_pct <= 3.0            → setup compression (porte fermée, pas encore ouverte)
    _n_avant = len(decisions_sorted)
    mf_available = any(d.get("score_total_mf") is not None for d in decisions_sorted)
    if mf_available:
        decisions_filtered = [
            d for d in decisions_sorted
            if d.get("score_total_mf", 0) >= 55
            and d.get("breakout_score_mf", 50) >= 50
            and d.get("volume_score_mf", 50) >= 60
            and (d.get("rsi") is None or d.get("rsi", 50) <= 78)   # RSI cap
            and (                                                    # compression
                d.get("compression_score_mf", 0) >= 45
                or (d.get("atr_pct") is not None and d.get("atr_pct", 10) <= 3.0)
            )
        ]
        if not decisions_filtered:
            print("  [PRE-FILTRE] 0 candidats (filtres stricts) — assoupli score>=50 RSI<=82")
            decisions_filtered = [
                d for d in decisions_sorted
                if d.get("score_total_mf", 0) >= 50
                and (d.get("rsi") is None or d.get("rsi", 50) <= 82)
            ]
        if not decisions_filtered:
            decisions_filtered = decisions_sorted           # fallback total
        # Fallback Tier 2 : si < 5 candidats, relâcher volume P>=60 → P>=40 (BRVM thin market)
        if len(decisions_filtered) < 5:
            decisions_t2 = [
                d for d in decisions_sorted
                if d.get("score_total_mf", 0) >= 55
                and d.get("breakout_score_mf", 50) >= 45
                and d.get("volume_score_mf", 50) >= 40
                and (d.get("rsi") is None or d.get("rsi", 50) <= 82)
            ]
            if len(decisions_t2) > len(decisions_filtered):
                print(f"  [PRE-FILTRE T2] Volume assoupli P>=40 — {len(decisions_t2)} candidats")
                decisions_filtered = decisions_t2
        # Fallback Tier 3 : si toujours < 5, relâcher aussi breakout P>=35
        if len(decisions_filtered) < 5:
            decisions_t3 = [
                d for d in decisions_sorted
                if d.get("score_total_mf", 0) >= 55
                and d.get("breakout_score_mf", 50) >= 35
            ]
            if len(decisions_t3) > len(decisions_filtered):
                print(f"  [PRE-FILTRE T3] Breakout assoupli P>=35 — {len(decisions_t3)} candidats")
                decisions_filtered = decisions_t3
        n_filtres = _n_avant - len(decisions_filtered)
        if n_filtres > 0:
            print(f"  [PRE-FILTRE SWING] {n_filtres} exclus (RSI/Compression/Breakout/VSR) | {len(decisions_filtered)} candidats restants\n")
        decisions_sorted = decisions_filtered

    # MAX_POSITIONS adaptatif selon le régime de marché
    REGIME_TOPN = {"BULL": 5, "NEUTRAL": 3, "BEAR": 1}
    MAX_POSITIONS = REGIME_TOPN.get(market_regime, 3)
    top5 = []
    sector_counts = {}
    banque_count = 0
    for d in decisions_sorted:
        if len(top5) >= MAX_POSITIONS:
            break
        symbol = d.get("symbol", "")
        sector = d.get("_sector", "AUTRE")
        is_banque = (symbol in BANQUE_SYMBOLS or
                     "banque" in sector.lower() or
                     "bank" in sector.lower() or
                     "finance" in sector.lower())
        if is_banque and banque_count >= 2:
            print(f"  [FILTRE SECTORIEL] {symbol} exclu — max 2 banques atteint")
            continue
        if sector != "AUTRE" and sector_counts.get(sector, 0) >= 2:
            print(f"  [FILTRE SECTORIEL] {symbol} exclu — max 2 actions secteur '{sector}'")
            continue
        # A6 — Filtre corrélation : exclure si corr ≥ 0.85 avec un titre déjà sélectionné
        corr_blocked = False
        for sel in top5:
            pair = (min(symbol, sel["symbol"]), max(symbol, sel["symbol"]))
            corr_val = corr_fortes.get(pair)
            if corr_val is not None and abs(corr_val) >= 0.85:
                print(f"  [FILTRE CORRELATION] {symbol} exclu — corr={corr_val:.3f} avec {sel['symbol']} déjà sélectionné")
                corr_blocked = True
                break
        if corr_blocked:
            continue
        top5.append(d)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        if is_banque:
            banque_count += 1

    # A9 — CIRCUIT BREAKER : si les N dernières positions ont un DD cumulé > 12%, suspendre
    try:
        tr_col = "track_record_daily" if MODE_DAILY else "track_record_weekly"
        # Vérifier si la collection existe et a des données, sinon utiliser track_record_weekly
        recent_trades = list(db[tr_col].find().sort("figee_le", -1).limit(10))
        if not recent_trades:
            recent_trades = list(db.track_record_weekly.find().sort("figee_le", -1).limit(10))
        if recent_trades:
            perfs = [t.get("performance_reelle", 0) or 0 for t in recent_trades]
            # DD cumulé = somme des pertes sur les 10 derniers trades
            cumul_dd = sum(p for p in perfs if p < 0)
            if cumul_dd < -12:
                print(f"\n  [CIRCUIT BREAKER] DD cumule 10 derniers = {cumul_dd:.1f}% (> -12%)")
                print(f"  [CIRCUIT BREAKER] SUSPENSION — pas de nouvelles positions")
                top5 = []  # Vider les positions
            elif cumul_dd < -8:
                print(f"\n  [CIRCUIT BREAKER] DD cumule 10 derniers = {cumul_dd:.1f}% (> -8%)")
                print(f"  [CIRCUIT BREAKER] MODE PRUDENT — max 1 position")
                top5 = top5[:1]
            else:
                print(f"\n  [CIRCUIT BREAKER] DD cumule 10 derniers = {cumul_dd:.1f}% — OK")
    except Exception as e:
        print(f"  [CIRCUIT BREAKER] Erreur: {e}")

    # A10 — VOLATILITY TARGETING : sizing adaptatif au risque du régime
    # risk_per_trade ajusté par le régime (BULL=1.5%, NEUTRAL=1%, BEAR=0.5%)
    # Allocation = risk_per_trade / (stop_distance_pct) × 100, capped à 15%
    ALLOC_MAX_CAP = 15.0  # jamais plus de 15% du portefeuille par position
    for d in top5:
        atr_pct = d.get("atr_pct", 5.0)
        stop_distance = 1.5 * atr_pct if atr_pct and atr_pct > 0 else 5.0  # cohérent avec stop ATR×1.5
        if stop_distance > 0:
            alloc_vol_target = (regime_risk_pct / stop_distance) * 100
            alloc_final = round(min(alloc_vol_target, ALLOC_MAX_CAP), 1)
            d["allocation_max"] = alloc_final
            d["sizing_method"] = f"vol_target (regime={market_regime}, risk={regime_risk_pct}%, stop={stop_distance:.1f}% -> alloc={alloc_final}%)"

        # Trailing stop dynamique : niveaux de trailing
        prix_e = d.get("prix_entree") or 0
        if prix_e > 0 and atr_pct:
            atr_abs = prix_e * atr_pct / 100
            d["trailing_stop_rules"] = {
                "initial_stop": round(prix_e - 1.5 * atr_abs),
                "after_1atr":   round(prix_e),                        # breakeven après +1 ATR
                "after_3atr":   f"close - 1 ATR ({round(atr_abs)})",  # trailing après +3 ATR
            }

    # A4 — Préserver first_selected_at pour Time Stop J+10
    existing_dates = {
        doc["symbol"]: doc["first_selected_at"]
        for doc in db[COLLECTION].find({}, {"symbol": 1, "first_selected_at": 1})
        if doc.get("first_selected_at")
    }

    # Calcul week_id courant (ISO)
    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    current_week_id = f"{iso_year}-W{iso_week:02d}"

    # Sauvegarde atomique : purge semaine courante + insert_many (évite _id conflicts)
    db[COLLECTION].delete_many({})

    docs_to_insert = []
    for rank, decision in enumerate(top5, start=1):
        decision.pop("_id", None)          # retire l'_id de decisions_finales_brvm
        decision["rank"]             = rank
        decision["selected_at"]      = now
        decision["week_id"]          = current_week_id
        decision["first_selected_at"] = existing_dates.get(decision.get("symbol"), now)
        docs_to_insert.append(decision)

    if docs_to_insert:
        db[COLLECTION].insert_many(docs_to_insert)

    # Affichage avec horizon dynamique
    horizon_display = "2-3 semaines" if MODE_DAILY else "4-8 semaines"
    print(f"\n[TOP {MAX_POSITIONS} OPPORTUNITES | Regime: {market_regime} | Horizon cible : {horizon_display}]\n")
    print(f"{'Rang':<6} {'Symbol':<8} {'Cl.':<5} {'Conf':<7} {'Gain':<10} {'RR':<7} {'Alloc':<8} {'Timing':<10} {'Score':<8}")
    print("-" * 78)

    for i, t in enumerate(top5, start=1):
        symbol    = t.get('symbol', 'N/A')
        classe    = t.get('classe', 'N/A')
        conf      = t.get('confidence', 0)
        gain      = t.get('gain_attendu') or t.get('expected_return') or 0
        rr        = t.get('rr', 0)
        score     = t.get('top5_score', 0)
        alloc_max = t.get('allocation_max', 5.0)
        timing    = t.get('timing_signal', 'N/A')
        liq       = t.get('position_size_factor', 1.0) or 1.0
        liq_tag   = "" if liq >= 1.0 else " [LIQ-]"
        alpha_lbl = t.get('alpha_label') or ''
        alpha_val = t.get('score_alpha')
        mf_val    = t.get('score_total_mf')
        mf_lbl    = t.get('mf_label') or ''
        sem_7j    = t.get('score_semantique_7j', 0)
        sem_sent  = t.get('sentiment_global', 'NEUTRE')
        explode   = t.get('signal_explosion', False)
        alpha_str = f" | α={alpha_val:.2f} {alpha_lbl}" if alpha_val is not None else ""
        mf_str    = f" | MF={mf_val:.1f} {mf_lbl}" if mf_val is not None else ""
        sem_str   = f" | SEM={sem_7j:+.1f} {sem_sent}"
        exp_str   = " *** EXPLOSION ***" if explode else ""
        vcp_str   = " [VCP]" if t.get("vcp_pattern") else ""
        # Confidence = score MF (0-100) si disponible, sinon WOS legacy (20-78)
        conf      = mf_val if mf_val is not None else t.get('confidence', 0)

        print(f"#{i:<5} {symbol:<8} {classe:<5} {conf:<6.0f}% {gain:<9.1f}% {rr:<6.2f} {alloc_max:<6.0f}%  {timing:<10}{liq_tag} {score:<7.1f}{alpha_str}{mf_str}{sem_str}{vcp_str}{exp_str}")

        # Setup type + facteurs clés
        setup_t = t.get("setup_type") or mf_lbl or "N/D"
        _vsr10  = t.get("vsr_ratio_10j") or 0.0
        _brk    = t.get("breakout_score_mf") or 0
        _cpr    = t.get("compression_score_mf") or 0
        if mf_val is not None:
            print(f"       Setup   : {setup_t} (MF={mf_val:.1f} | VSR={_vsr10:.1f}x | Brk=P{_brk:.0f} | Cpr=P{_cpr:.0f})")
        else:
            print(f"       Setup   : {setup_t}")

        # Plan de sortie en étages (TP1/TP2/Runner + Stop)
        prix_e = t.get('prix_entree') or 0
        stop_e = t.get('stop') or 0
        if prix_e > 0:
            tp1    = round(prix_e * 1.075)
            tp2    = round(prix_e * 1.150)
            runner = round(prix_e * 1.275)
            print(f"       Exit : TP1 {tp1:,.0f} (+7.5% → vendre 50%) | TP2 {tp2:,.0f} (+15% → vendre 30%) | Runner {runner:,.0f} (+27.5%) | Stop {stop_e:,.0f}")
            if stop_e > 0:
                print(f"       Invalide: signal annule si cloture sous {stop_e:,.0f} FCFA (stop ATR×1.5)")
            # Trailing stop rules
            trailing = t.get("trailing_stop_rules")
            if trailing:
                print(f"       Trailing : Initial {trailing['initial_stop']:,} | +1ATR → breakeven {trailing['after_1atr']:,} | +3ATR → {trailing['after_3atr']}")
            sizing = t.get("sizing_method", "")
            if sizing:
                print(f"       Sizing : {sizing}")

        # Risque liquidité (val_moy20j injecté par le filtre liquidité)
        val_j = t.get("val_moy20j", 0)
        j_trd = t.get("jours_trades20j", 0)
        liq_label = "ELEVEE" if val_j > 10_000_000 else ("MOYENNE" if val_j > 3_000_000 else "FAIBLE")
        val_str = f"{val_j/1_000_000:.1f}M FCFA/j" if val_j > 0 else "N/D"
        print(f"       Risque  : Liquidite {liq_label} ({val_str} | {j_trd}/20 jours actifs)")

    print(f"\n  [REGLE] MAX {MAX_POSITIONS} POSITIONS SIMULTANEES ({market_regime}) | Risque {regime_risk_pct}%/trade")
    print(f"  [HORIZON] {horizon_display} en moyenne sur la BRVM")
    print("\n" + "="*70)
    print(f"[OK] TOP5 genere et sauvegarde dans : {COLLECTION}")
    print("="*70 + "\n")
    
    return top5


if __name__ == "__main__":
    generate_top5()
