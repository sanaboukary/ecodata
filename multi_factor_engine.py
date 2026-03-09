#!/usr/bin/env python3
"""
MULTI-FACTOR ENGINE — BRVM (Modèle quantitatif cross-sectionnel)
=================================================================

Structure fonds quant :
  Rank toutes les 47 actions BRVM sur 5+1 facteurs indépendants.
  Chaque facteur est normalisé par percentile cross-sectionnel.

  SCORE_TOTAL =
    0.30 × RSScore            (surperformance vs marché — leaders BRVM)
    0.25 × BreakoutScore      (cassure du range 20j — déclencheur)
    0.20 × VolumeScore        (VSR — carburant)
    0.15 × MomentumScore      (force tendance 10j seulement)
    0.10 × CompressionScore   (accumulation silencieuse J-10 à J-6)
    + bonus Acceleration      (accélération court terme BRVM-specific)

  Résultat : 0–100
    > 85  → EXPLOSION candidate
    70–85 → SWING_FORT
    55–70 → SWING_MOYEN
    < 55  → IGNORER

  Intégration dans top5_engine_final.py :
    FINAL_SCORE = 0.60 × SCORE_TOTAL + 0.35 × SCORE_ALPHA × 100 + 0.05 × sem_norm

Usage :
  python multi_factor_engine.py
  python multi_factor_engine.py --mode daily
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import hashlib
import os
import statistics
from datetime import datetime, timezone
from typing import Dict, List, Optional

from scipy.stats import percentileofscore

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db
from tradable_universe import UNIVERSE_BRVM_SET, SYMBOLS_HISTORIQUE_INSUFFISANT, INDICES_BRVM

# ─── Config mode ────────────────────────────────────────────────────────────
MODE_DAILY      = "--mode" in sys.argv and "daily" in sys.argv
COLLECTION_PRICE = "prices_daily"  if MODE_DAILY else "prices_weekly"
DATE_FIELD       = "date"          if MODE_DAILY else "week"

# ─── Indices à exclure + Univers de recommandation actif ────────────────────
# Source de vérité : tradable_universe.py (UNIVERSE_BRVM_SET exclut déjà
# BICB, BNBC, LNBB — historique insuffisant pour percentiles cross-sectionnels).
# INDICES_BRVM et UNIVERSE_BRVM_SET importés depuis tradable_universe.

# ─── Helpers ────────────────────────────────────────────────────────────────

def _perf(closes: List[float], n: int) -> Optional[float]:
    """Rendement sur n périodes. None si données insuffisantes."""
    if len(closes) < n + 1:
        return None
    ref = closes[-(n + 1)]
    if not ref or ref <= 0:
        return None
    return (closes[-1] - ref) / ref * 100


# ─── Calcul des facteurs bruts ───────────────────────────────────────────────

def calculer_facteurs_bruts(db, symbol: str, prix_brvmc: List[float]) -> Optional[Dict]:
    """
    Calcule les 6 facteurs bruts pour une action à partir de prices_daily.
    Retourne None si données insuffisantes (< 22 jours).
    """
    docs = list(db[COLLECTION_PRICE].find({"symbol": symbol}).sort(DATE_FIELD, 1))
    if len(docs) < 22:
        return None

    closes  = [d.get("close") for d in docs if d.get("close")]
    highs   = [d.get("high")   for d in docs]
    volumes = [d.get("volume", 0) for d in docs]

    if len(closes) < 22:
        return None

    trs = [abs(closes[i] - closes[i - 1]) for i in range(1, len(closes))]

    # ── Facteur 1 : MOMENTUM = perf_10j (standalone — RS capture déjà la dim. 20j) ─
    p10 = _perf(closes, 10)
    p20 = _perf(closes, 20)
    momentum = p10  # perf_10j seul, orthogonal avec RS (20j)

    # ── Facteur 2 : BREAKOUT = (close − max_high_20j) / ATR_20 ──────────────
    breakout = None
    if len(highs) >= 20 and len(trs) >= 20:
        highs_valides = [h for h in highs[-20:] if h]
        if highs_valides:
            max_high_20j = max(highs_valides)
            atr_20 = statistics.mean(trs[-20:])
            if atr_20 > 0:
                breakout = (closes[-1] - max_high_20j) / atr_20

    # ── Facteur 3 : RS = perf_20j_action − perf_20j_BRVMC ───────────────────
    rs = None
    if p20 is not None:
        if prix_brvmc and len(prix_brvmc) >= 21:
            p20_brvmc = _perf(prix_brvmc, 20)
            rs = (p20 - p20_brvmc) if p20_brvmc is not None else p20
        else:
            rs = p20  # BRVMC indisponible : score = propre performance

    # ── Facteur 4 : VOLUME = mean(volume_5j) / mean(volume_20j) ─────────────
    volume_ratio = None
    if len(volumes) >= 20:
        vols_5  = [v for v in volumes[-5:]  if v and v > 0]
        vols_20 = [v for v in volumes[-20:] if v and v > 0]
        if vols_5 and vols_20:
            moy_5  = statistics.mean(vols_5)
            moy_20 = statistics.mean(vols_20)
            if moy_20 > 0:
                volume_ratio = moy_5 / moy_20

    # ── DÉTONATEUR VSR : ratio volume 3j / moyenne 10j (VCP trigger) ─────────
    # Détecte le choc de liquidité précédant une explosion de prix.
    # vsr_ratio_10j >= 2.5 = volume 2.5x supérieur à la moyenne 10j → détonateur
    vsr_ratio_10j = None
    if len(volumes) >= 10:
        vols_3  = [v for v in volumes[-3:]  if v and v > 0]
        vols_10 = [v for v in volumes[-10:] if v and v > 0]
        if vols_3 and vols_10:
            moy_3  = statistics.mean(vols_3)
            moy_10 = statistics.mean(vols_10)
            if moy_10 > 0:
                vsr_ratio_10j = round(moy_3 / moy_10, 2)

    # ── Facteur 5 : COMPRESSION = 1 − (ATR_5_delayed / ATR_20) ─────────────
    # Fenêtre décalée [-11:-6] = J-10 à J-6
    # Orthogonal à VolatilityExpansion ([-5:]) et à VCP (même fenêtre, même logique)
    compression = None
    if len(trs) >= 20:
        delayed = trs[-11:-6]
        if len(delayed) == 5:
            atr_5_delayed = statistics.mean(delayed)
            atr_20_val    = statistics.mean(trs[-20:])
            if atr_20_val > 0:
                compression = 1.0 - (atr_5_delayed / atr_20_val)

    # ── Facteur 6 : ACCELERATION = perf_5j − perf_20j (BRVM-specifique) ─────
    p5 = _perf(closes, 5)
    acceleration = None
    if p5 is not None and p20 is not None:
        acceleration = p5 - p20

    # ATR % pour sizing des stops dans injection synthétique
    atr_pct = None
    if len(trs) >= 20 and closes[-1] > 0:
        atr_val = statistics.mean(trs[-20:])
        atr_pct = round(atr_val / closes[-1] * 100, 2)

    return {
        "symbol":       symbol,
        "momentum":     momentum,
        "breakout":     breakout,
        "rs":           rs,
        "volume_ratio": volume_ratio,
        "compression":  compression,
        "acceleration": acceleration,
        "vsr_ratio_10j": vsr_ratio_10j,
        "close":        closes[-1],
        "atr_pct":      atr_pct,
        "n_docs":       len(closes),
    }


# ─── Normalisation cross-sectionnelle ────────────────────────────────────────

def normaliser_cross_sectionnel(all_factors: List[Dict]) -> List[Dict]:
    """
    Pour chaque facteur, calcule le percentile cross-sectionnel parmi toutes les actions.
    Les valeurs manquantes (None) sont neutralisées à 50.0 (médiane).
    """
    factor_names = ["momentum", "breakout", "rs", "volume_ratio", "compression", "acceleration"]

    for fname in factor_names:
        raw_vals = [d[fname] for d in all_factors if d[fname] is not None]

        if not raw_vals:
            for d in all_factors:
                d[f"{fname}_score"] = 50.0
            continue

        for d in all_factors:
            if d[fname] is not None:
                d[f"{fname}_score"] = round(
                    percentileofscore(raw_vals, d[fname], kind="rank"), 1
                )
            else:
                d[f"{fname}_score"] = 50.0  # neutre

    return all_factors


# ─── Score total + label ─────────────────────────────────────────────────────

def calculer_score_total(d: Dict) -> float:
    """
    SCORE_TOTAL = 0.30*RS + 0.25*Breakout + 0.20*Volume + 0.15*Momentum + 0.10*Compression

    NOTE : bonus Accélération supprimé suite à ablation study (2026-03-06).
    C08_MF_sans_acc (PF=2.00) > C07_MF_PROD (PF=1.97) sur 579 trades.
    Le bonus diluait l'edge au lieu de l'améliorer.
    """
    score = (
        0.30 * d.get("rs_score",               50.0)   # Leaders BRVM
        + 0.25 * d.get("breakout_score",       50.0)   # Déclencheur
        + 0.20 * d.get("volume_ratio_score",   50.0)   # Carburant (VSR)
        + 0.15 * d.get("momentum_score",       50.0)   # Momentum 10j
        + 0.10 * d.get("compression_score",    50.0)   # Accumulation
    )
    return round(score, 1)


def get_mf_label(score: float) -> str:
    if score >= 85:
        return "EXPLOSION"
    elif score >= 70:
        return "SWING_FORT"
    elif score >= 55:
        return "SWING_MOYEN"
    else:
        return "IGNORER"


def classify_setup_type(d: Dict) -> str:
    """
    Classifie le type de setup pour le track record différentiel.
    Permet l'ablation study par setup et l'apprentissage différentiel.

    Hiérarchie (premier match gagne) :
        EXPLOSION_VSR      : score >=85 + VSR spike fort (>=2.5x)
        VCP                : compression>=60 + breakout>=60 + VSR>=2.5 (pattern classique)
        EXPLOSION_PURE     : score >=85 (sans VSR spike confirmé)
        BREAKOUT_VOLUME    : breakout>=70 + VSR>=2.0
        BREAKOUT_COMPRESS  : compression forte (>=65) — accumulation silencieuse
        SWING_FORT         : score >=70 (tous critères réunis mais pas d'explosion)
        SWING_MOYEN        : signal valide mais modéré
    """
    vsr   = d.get("vsr_ratio_10j") or 0
    comp  = d.get("compression_score", 0)
    brk   = d.get("breakout_score",    0)
    mf    = d.get("score_total_mf",    0)

    if mf >= 85 and vsr >= 2.5:
        return "EXPLOSION_VSR"
    if comp >= 60 and brk >= 60 and vsr >= 2.5:
        return "VCP"
    if mf >= 85:
        return "EXPLOSION_PURE"
    if brk >= 70 and vsr >= 2.0:
        return "BREAKOUT_VOLUME"
    if comp >= 65:
        return "BREAKOUT_COMPRESS"
    if mf >= 70:
        return "SWING_FORT"
    return "SWING_MOYEN"


def make_setup_id(symbol: str, period_key: str, setup_type: str) -> str:
    """Identifiant unique déterministe par recommandation (12 chars hex)."""
    raw = f"{symbol}_{period_key}_{setup_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ─── Injection synthétique des décisions MF manquantes ──────────────────────

def injecter_decisions_mf_manquantes(db, all_factors: List[Dict], mode_daily: bool = False):
    """
    Crée des décisions BUY synthétiques dans decisions_finales_brvm pour les
    symboles EXPLOSION/SWING_FORT (score >= 70) qui n'ont pas encore de BUY actif.

    Ces décisions permettent à top5_engine_final.py de les retrouver même si
    decision_finale_brvm.py ne les a pas inclus dans son UNIVERSE.
    Les champs de prix/stops sont calculés à partir du close et de l'ATR.
    """
    horizon = "JOUR" if mode_daily else "SEMAINE"

    # 1. Symboles ayant déjà un BUY actif sur cet horizon
    existing_buys = set(
        d["symbol"] for d in db.decisions_finales_brvm.find(
            {"decision": "BUY", "horizon": horizon, "archived": {"$ne": True}},
            {"symbol": 1}
        )
    )

    # 2. Candidats EXPLOSION/SWING_FORT sans BUY (score >= 70)
    candidates = [
        d for d in all_factors
        if d["score_total_mf"] >= 70
        and d["symbol"] not in existing_buys
    ]

    if not candidates:
        print("  [INJECTION] Aucune décision MF à injecter (EXPLOSION/SWING_FORT déjà couverts)")
        return

    now = datetime.now(timezone.utc)
    injected = 0

    for d in candidates:
        symbol  = d["symbol"]
        close   = d.get("close") or 0
        atr_pct = d.get("atr_pct") or 2.0   # fallback ATR 2%

        if close <= 0:
            continue

        # Stop ATR-based : 1.5 × ATR sous le close
        stop_pct    = round(1.5 * atr_pct, 2)
        stop_price  = round(close * (1 - stop_pct / 100))
        gain_attendu = round(3.0 * stop_pct, 1)   # RR 3:1 par défaut
        tp1         = round(close * (1 + gain_attendu / 100))

        # Classe basée sur le score MF
        classe = "A" if d["score_total_mf"] >= 85 else "B"

        doc = {
            "symbol":               symbol,
            "decision":             "BUY",
            "horizon":              horizon,
            "classe":               classe,
            "confidence":           round(d["score_total_mf"]),
            "gain_attendu":         gain_attendu,
            "expected_return":      gain_attendu,
            "rr":                   3.0,
            "wos":                  4,
            "prix_entree":          close,
            "prix_cible":           tp1,
            "stop":                 stop_price,
            "atr_pct":              atr_pct,
            "score_total_mf":       d["score_total_mf"],
            "mf_label":             d["mf_label"],
            "setup_type":           d.get("setup_type", classify_setup_type(d)),
            "setup_id":             d.get("setup_id"),
            "breakout_score_mf":    d.get("breakout_score"),
            "volume_score_mf":      d.get("volume_ratio_score"),
            "compression_score_mf": d.get("compression_score"),
            "rs_score_mf":          d.get("rs_score"),
            "momentum_score_mf":    d.get("momentum_score"),
            "acceleration_score_mf": d.get("acceleration_score"),
            "vsr_ratio_10j":        d.get("vsr_ratio_10j"),
            "timing_signal":        "ACHAT_IMMEDIAT",
            "position_size_factor": 1.0,
            "allocation_max":       10.0,
            "generated_by":         "multi_factor_engine",
            "generated_at":         now,
            "archived":             False,
        }

        # Upsert : met à jour un doc existant (HOLD/None) ou en crée un nouveau
        db.decisions_finales_brvm.update_one(
            {"symbol": symbol, "horizon": horizon, "archived": {"$ne": True}},
            {"$set": doc},
            upsert=True
        )
        injected += 1
        print(f"  [INJECTION] {symbol:<8} {d['mf_label']:<12} "
              f"score={d['score_total_mf']:.1f} close={close:,.0f} "
              f"stop={stop_price:,.0f} (-{stop_pct:.1f}%) → BUY injecte")

    print(f"  [OK] {injected} decision(s) MF synthetique(s) injectee(s) → decisions_finales_brvm\n")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  MULTI-FACTOR ENGINE — BRVM")
    print(f"  Mode : {'DAILY (prices_daily)' if MODE_DAILY else 'WEEKLY (prices_weekly)'}")
    print("=" * 70 + "\n")

    _, db = get_mongo_db()

    # 1. BRVMC pour RS cross-marché
    brvmc_docs = list(db[COLLECTION_PRICE].find({"symbol": "BRVMC"}).sort(DATE_FIELD, 1))
    prix_brvmc = [d.get("close") for d in brvmc_docs if d.get("close")] if brvmc_docs else []
    if not prix_brvmc:
        print("  [AVERT] BRVMC indisponible — RS = propre performance de chaque action\n")

    # 2. Symboles disponibles
    symbols_db = set(db[COLLECTION_PRICE].distinct("symbol"))
    actions    = sorted(s for s in UNIVERSE_BRVM_SET if s in symbols_db)
    print(f"  {len(actions)} actions BRVM analysées\n")

    # 3. Calcul facteurs bruts
    all_factors = []
    rejetees    = []
    for symbol in actions:
        result = calculer_facteurs_bruts(db, symbol, prix_brvmc)
        if result:
            all_factors.append(result)
        else:
            rejetees.append(symbol)

    print(f"  Facteurs calculés : {len(all_factors)} | Rejetées (données insuff.) : {len(rejetees)}")
    if rejetees:
        print(f"  Rejetées : {', '.join(rejetees)}\n")

    if len(all_factors) < 5:
        print("[ERREUR] Pas assez d'actions pour le modèle cross-sectionnel (min 5)")
        return

    # 4. Normalisation cross-sectionnelle
    all_factors = normaliser_cross_sectionnel(all_factors)

    # 5. Score total + label + setup_type
    period_key = datetime.now(timezone.utc).strftime("%Y-W%V" if not MODE_DAILY else "%Y-%m-%d")
    for d in all_factors:
        d["score_total_mf"] = calculer_score_total(d)
        d["mf_label"]       = get_mf_label(d["score_total_mf"])
        d["setup_type"]     = classify_setup_type(d)
        d["setup_id"]       = make_setup_id(d["symbol"], period_key, d["setup_type"])

    # 6. Tri décroissant par SCORE_TOTAL
    all_factors_sorted = sorted(all_factors, key=lambda x: x["score_total_mf"], reverse=True)

    # 7. Affichage TOP 15
    print(f"\n{'─'*90}")
    print(f"  {'Symbol':<8} {'Score':>6}  {'Label':<12} {'Mom':>5} {'Brk':>5} {'RS':>5} {'Vol':>5} {'Cpr':>5} {'Acc':>5} {'VSR10':>6}")
    print(f"{'─'*90}")
    for d in all_factors_sorted[:15]:
        vsr10 = d.get("vsr_ratio_10j")
        vsr10_str = f"{vsr10:.1f}x" if vsr10 else "  -"
        vcp_tag = " [VCP]" if (
            d.get("compression_score", 0) >= 60
            and d.get("breakout_score",    0) >= 60
            and vsr10 and vsr10 >= 2.5
        ) else ""
        marker = " ◄◄ CANDIDAT" if d["score_total_mf"] >= 70 else ""
        print(
            f"  {d['symbol']:<8} {d['score_total_mf']:>5.1f}  {d['mf_label']:<12} "
            f"{d.get('momentum_score', 0):>4.0f}P "
            f"{d.get('breakout_score', 0):>4.0f}P "
            f"{d.get('rs_score', 0):>4.0f}P "
            f"{d.get('volume_ratio_score', 0):>4.0f}P "
            f"{d.get('compression_score', 0):>4.0f}P "
            f"{d.get('acceleration_score', 0):>4.0f}P "
            f"{vsr10_str:>6}"
            f"{vcp_tag}{marker}"
        )
    print(f"{'─'*90}\n")

    # 8. Sauvegarde MongoDB
    now = datetime.now(timezone.utc)
    mf_collection = "multi_factor_scores_daily" if MODE_DAILY else "multi_factor_scores_weekly"
    horizon        = "JOUR" if MODE_DAILY else "SEMAINE"

    for d in all_factors:
        symbol = d["symbol"]

        # Collection dédiée multi_factor_scores
        db[mf_collection].update_one(
            {"symbol": symbol},
            {"$set": {
                "symbol":               symbol,
                "score_total_mf":       d["score_total_mf"],
                "mf_label":             d["mf_label"],
                "setup_type":           d.get("setup_type"),
                "setup_id":             d.get("setup_id"),
                "momentum_score_mf":    d.get("momentum_score"),
                "breakout_score_mf":    d.get("breakout_score"),
                "rs_score_mf":          d.get("rs_score"),
                "volume_score_mf":      d.get("volume_ratio_score"),
                "compression_score_mf": d.get("compression_score"),
                "acceleration_score_mf": d.get("acceleration_score"),
                "momentum_raw":         d.get("momentum"),
                "breakout_raw_mf":      d.get("breakout"),
                "rs_raw":               d.get("rs"),
                "volume_ratio_raw":     d.get("volume_ratio"),
                "compression_raw":      d.get("compression"),
                "acceleration_raw":     d.get("acceleration"),
                "vsr_ratio_10j":        d.get("vsr_ratio_10j"),
                "generated_at":         now,
            }},
            upsert=True
        )

        # Injection dans decisions_finales_brvm (pour top5_engine_final.py)
        # IMPORTANT : filtrer par horizon pour éviter la contamination croisée daily↔weekly.
        # Sans ce filtre, le run weekly écrase les scores daily dans les docs horizon="JOUR"
        # (et inversement), causant des incohérences silencieuses entre les deux modes.
        #
        # ATR + STOP recalculés à chaque run depuis prices_daily/weekly (données fraîches).
        # stop = close_courant - 1.5 × ATR_20j  (recalculé ici, pas depuis une valeur gelée)
        close_cur = d.get("close")
        atr_pct_cur = d.get("atr_pct")
        stop_cur = None
        prix_cible_cur = None
        if close_cur and close_cur > 0 and atr_pct_cur and atr_pct_cur > 0:
            stop_pct_cur   = round(1.5 * atr_pct_cur, 2)
            stop_cur       = round(close_cur * (1 - stop_pct_cur / 100))
            gain_cur       = round(3.0 * stop_pct_cur, 1)   # R/R 3:1
            prix_cible_cur = round(close_cur * (1 + gain_cur / 100))

        mf_fields = {
            "score_total_mf":        d["score_total_mf"],
            "mf_label":              d["mf_label"],
            "setup_type":            d.get("setup_type"),
            "setup_id":              d.get("setup_id"),
            "acceleration_score_mf": d.get("acceleration_score"),
            "breakout_score_mf":     d.get("breakout_score"),
            "volume_score_mf":       d.get("volume_ratio_score"),
            "compression_score_mf":  d.get("compression_score"),
            "rs_score_mf":           d.get("rs_score"),
            "momentum_score_mf":     d.get("momentum_score"),
            "vsr_ratio_10j":         d.get("vsr_ratio_10j"),
            "mf_synced_at":          now,
            # Prix rafraîchis depuis les données courantes
            "atr_pct":               atr_pct_cur,
            "prix_entree":           close_cur,
        }
        if stop_cur is not None:
            mf_fields["stop"]        = stop_cur
            mf_fields["gain_attendu"]  = round(3.0 * (1.5 * atr_pct_cur), 1)
            mf_fields["expected_return"] = mf_fields["gain_attendu"]
            mf_fields["prix_cible"]  = prix_cible_cur

        db.decisions_finales_brvm.update_many(
            {"symbol": symbol, "horizon": horizon, "archived": {"$ne": True}},
            {"$set": mf_fields}
        )

    print(f"  [OK] {len(all_factors)} scores sauvegardés → {mf_collection}")
    print(f"  [OK] decisions_finales_brvm enrichi avec score_total_mf\n")

    # ── Injection des décisions manquantes (EXPLOSION/SWING_FORT sans BUY actif)
    print("─" * 70)
    print("  INJECTION DECISIONS MF MANQUANTES")
    print("─" * 70)
    injecter_decisions_mf_manquantes(db, all_factors, mode_daily=MODE_DAILY)

    print("=" * 70)
    print("  MULTI-FACTOR ENGINE — TERMINÉ")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
