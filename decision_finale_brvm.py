import argparse
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from datetime import datetime, timezone, timedelta
from plateforme_centralisation.mongo import get_mongo_db

# MODE DUAL : --mode daily (court terme) ou défaut weekly (moyen terme)
MODE_DAILY = "--mode" in sys.argv and "daily" in sys.argv
HORIZON_TAG = "JOUR" if MODE_DAILY else "SEMAINE"

# MODE EXPERT: Elite Minimaliste (14 semaines données) vs Full System (52+ semaines)
MODE_ELITE_MINIMALISTE = False  # False = formule restaurée 07/02 (target=2.4×ATR, RR=2.67)
MODE_INSTITUTIONAL = False  # Désactivé : import brvm_institutional_alpha non stable

# Import modules institutionnels si MODE_INSTITUTIONAL activé
if MODE_INSTITUTIONAL:
    from brvm_institutional_regime import compute_market_regime, get_tradable_universe
    from brvm_institutional_alpha import compute_alpha_score_institutional, compute_portfolio_allocation

# Source de vérité univers : tradable_universe.py (47 actions BRVM officielles)
# L'ancien UNIVERSE = {12 symboles hardcodés} a été supprimé — code mort non utilisé.
# Pour filtrer par liquidité dynamique : from tradable_universe import get_tradable_universe
from tradable_universe import UNIVERSE_BRVM_SET

# Mapping confiance → proba empirique
def confidence_to_proba(conf):
    if conf > 85:
        return 0.78
    elif conf > 80:
        return 0.70
    elif conf > 75:
        return 0.62
    elif conf >= 70:
        return 0.55
    else:
        return 0.45

def compute_relative_strength_4sem(symbol, db):
    """
    ELITE MINIMALISTE: Relative Strength 4 semaines vs BRVM Composite
    Expert 30 ans: Continuation momentum > retournement magique
    
    Returns:
        rs_4sem: Performance relative % (positive = surperforme indice)
        perf_action: Performance action 4 semaines %
        perf_brvm: Performance indice 4 semaines %
    """
    try:
        # Récupérer 5 dernières semaines prix action (4 semaines + point départ)
        # volume > 0 : exclure semaines sans échange réel (artefacts restauration)
        prices = list(db.prices_weekly.find(
            {"symbol": symbol, "volume": {"$gt": 0}},
            {"close": 1, "week": 1}
        ).sort("week", -1).limit(5))
        
        if len(prices) < 2:
            return None, None, None
        
        # Inverser pour ordre chronologique
        prices = prices[::-1]
        
        # Performance action: (prix actuel - prix il y a 4 semaines) / prix début
        prix_debut = prices[0]["close"]
        prix_fin = prices[-1]["close"]
        
        if prix_debut <= 0:
            return None, None, None
        
        perf_action = ((prix_fin - prix_debut) / prix_debut) * 100
        
        # Récupérer performance indice BRVM Composite (si disponible)
        # Pour l'instant, utiliser moyenne marché comme proxy
        # TODO: remplacer par vrai indice BRVM Composite quand disponible
        # volume > 0 : exclure semaines sans échange réel pour proxy marché cohérent
        all_actions = list(db.prices_weekly.find(
            {"volume": {"$gt": 0}},
            {"symbol": 1, "close": 1, "week": 1}
        ).sort("week", -1).limit(300))
        
        # Calculer moyenne marché dernières 4 semaines
        weeks_unique = sorted(set([a["week"] for a in all_actions]))[-5:]
        
        if len(weeks_unique) < 2:
            # Fallback: pas d'indice dispo, RS = performance absolue
            return perf_action, perf_action, 0.0
        
        # Moyenne prix marché début vs fin
        debut_prices = [a["close"] for a in all_actions if a["week"] == weeks_unique[0]]
        fin_prices = [a["close"] for a in all_actions if a["week"] == weeks_unique[-1]]
        
        if not debut_prices or not fin_prices:
            return perf_action, perf_action, 0.0
        
        # Approximation indice = moyenne géométrique (plus robuste que arithmétique)
        # Fallback statistics.mean si scipy absent
        try:
            from scipy.stats import gmean as _gmean
            indice_debut = _gmean(debut_prices) if debut_prices else 1
            indice_fin = _gmean(fin_prices) if fin_prices else 1
        except ImportError:
            import statistics as _stat
            indice_debut = _stat.mean(debut_prices) if debut_prices else 1
            indice_fin = _stat.mean(fin_prices) if fin_prices else 1
        
        perf_brvm = ((indice_fin - indice_debut) / indice_debut) * 100 if indice_debut > 0 else 0
        
        # Relative Strength = Performance action - Performance marché
        rs_4sem = perf_action - perf_brvm
        
        return rs_4sem, perf_action, perf_brvm
        
    except Exception as e:
        print(f"[ERREUR RS] {symbol}: {e}")
        return None, None, None

def apply_elite_filters(symbol, prix, volume, volume_moyen_8sem, atr_pct, trend_direction, rs_4sem, rs_percentile=None, volume_percentile=None, acceleration=None, prix_max_3w=None):
    """
    ELITE MINIMALISTE BRVM-ADAPTÉ: Filtres basés sur PERCENTILES (logique 2 passes)
    Expert 30 ans BRVM: Marché concentré, étroit, irrégulier →Percentiles > Seuils absolus
    
    Philosophie:
    Top 5 Hebdo ≠ Battre l'indice (peut venir de retardataire, réveil sectoriel, rattrapage)
    
    Filtres BRVM-calibrés avec PERCENTILES:
    1. **RS PERCENTILE >= 75** (top 25% univers)
    2. **VOLUME PERCENTILE >= 40** (éviter 40% actions mortes, sizing si <60)
    3. **ACCÉLÉRATION >= 2%** (BRVM: <1%=bruit, 2-4%=mouvement, >4%=explosion)
    4. **BREAKOUT INTELLIGENT** (+/-2% tolérance spread BRVM)
    5. Pas tendance DOWN chronique (tolérance court terme)
    6. ATR 8-30% (vs 8-25% strict)
    
    Returns:
        (passed: bool, rejection_reason: str, position_size_factor: float)
        position_size_factor: 1.0 (full), 0.5 (volume faible), 0.0 (rejeté)
    """
    position_size_factor = 1.0  # Par défaut: position complète
    # Filtre 1: Relative Strength PERCENTILE (PRIORITÉ: percentile > seuil absolu)
    if rs_percentile is not None:
        # Logique percentile: top 25% (P>=75)
        if rs_percentile < 75:
            return False, f"RS_PERCENTILE_FAIBLE (P{rs_percentile:.0f}, besoin >=P75 top 25%)", 0.0
    elif rs_4sem is not None:
        # Fallback si percentile non calculé: utiliser P70 empirique (top 30%)
        # Données BRVM réelles 14 semaines: P70 = -43.3% (marché très concentré)
        if rs_4sem < -43.3:
            return False, f"RS_TROP_NEGATIF ({rs_4sem:.1f}% vs marché, besoin >-43% P70)", 0.0
    else:
        return False, "RS_INDISPONIBLE", 0.0
    
    # Filtre 2: Volume PERCENTILE avec SIZING ADAPTATIF (PHASE 5)
    if volume_percentile is not None:
        # Logique: Ne PAS bloquer, mais réduire sizing si faible
        if volume_percentile < 30:
            # Bottom 30% = TROP risqué même avec réduction → BLOQUER
            return False, f"VOLUME_PERCENTILE_TROP_FAIBLE (P{volume_percentile:.0f}, besoin >=P30)", 0.0
        elif volume_percentile < 40:
            # P30-P40 = Action peu liquide → 50% position
            position_size_factor = 0.5
        elif volume_percentile < 60:
            # P40-P60 = Volume correct → 100% position
            position_size_factor = 1.0
        else:
            # P60+ = Top liquidité → 100% position
            position_size_factor = 1.0
    elif volume_moyen_8sem and volume_moyen_8sem > 0:
        # Fallback ratio si percentile indisponible
        volume_ratio = volume / volume_moyen_8sem
        if volume_ratio < 0.4:
            return False, f"VOLUME_FAIBLE ({volume_ratio:.2f}x, besoin >=0.4x)", 0.0
        elif volume_ratio < 0.6:
            position_size_factor = 0.5
    else:
        return False, "VOLUME_HISTORIQUE_INSUFFISANT", 0.0
    
    # Filtre 3: ACCÉLÉRATION >= 2% (PHASE 3 - Moteur principal court terme)
    if acceleration is not None:
        # BRVM weekly: <1%=bruit, 2-4%=début mouvement, >4%=potentiel explosion
        if acceleration < 2.0:
            return False, f"ACCELERATION_FAIBLE ({acceleration:.1f}%, besoin >=2%)", 0.0
    # Sinon: pas d'accélération calculée → tolérer (données manquantes)
    
    # Filtre 4: BREAKOUT INTELLIGENT +/-2% (PHASE 4)
    if prix_max_3w is not None and prix is not None:
        # Tolérance 2% pour spread BRVM (faux breakouts fréquents)
        breakout_threshold = prix_max_3w * 0.98  # -2% tolérance
        if prix < breakout_threshold:
            # Prix en dessous du max 3 semaines (même avec tolérance) → pas breakout
            return False, f"PAS_BREAKOUT (prix {prix} < max_3w {prix_max_3w:.0f} -2%)", 0.0
    
    # Filtre 5: Pas de tendance DOWN chronique (tolérance short term)
    # Expert BRVM: Down court terme acceptable si momentum autre signal
    if trend_direction and "DOWN" in trend_direction:
        # Accepter DOWN court terme en mode Elite
        pass
    
    # Filtre 6: ATR élargi pour BRVM (8-30%)
    if atr_pct is None or atr_pct < 8.0 or atr_pct > 30.0:
        if atr_pct is None:
            return False, "ATR_INDISPONIBLE", 0.0
        elif atr_pct < 8.0:
            return False, f"ATR_TROP_BAS ({atr_pct:.1f}% - action morte)", 0.0
        else:
            return False, f"ATR_EXCESSIF ({atr_pct:.1f}% - micro-cap instable)", 0.0
    
    # OK Tous filtres passes
    return True, "OK", position_size_factor

def compute_atr_pct(prices, period=14):
    """
    ATR% (Average True Range en % du prix)
    Formule simplifiée pour BRVM (close seulement, pas high/low)
    
    Ordres de grandeur BRVM weekly :
    - Normal : 5% - 18%
    - Mort : < 5%
    - Excessif : > 25%
    """
    if not prices or len(prices) < period + 1:
        return None
    
    # True Range simplifié
    true_ranges = [
        abs(prices[i] - prices[i-1]) 
        for i in range(1, len(prices)) if prices[i-1] > 0
    ]
    
    if not true_ranges or len(true_ranges) < period:
        return None
    
    # ATR = moyenne des TR
    atr = sum(true_ranges[-period:]) / period
    current_price = prices[-1]
    
    if current_price <= 0:
        return None
    
    # ATR%
    atr_pct = (atr / current_price) * 100
    
    return round(atr_pct, 2)

def compute_wos(sma5, sma10, rsi, volume, volume_ref, score_sem):
    """WOS (Weekly Opportunity Score) - VERSION ORIGINALE (legacy)"""
    # Valeurs par défaut si None
    sma5 = sma5 if sma5 is not None else 0
    sma10 = sma10 if sma10 is not None else 0
    rsi = rsi if rsi is not None else 50  # Neutre
    volume = volume if volume and volume > 0 else 1000  # Défaut minimal
    volume_ref = volume_ref if volume_ref and volume_ref > 0 else volume
    score_sem = score_sem if score_sem is not None else 0
    
    score_tendance = 100 if sma5 > sma10 else 0
    score_rsi = 100 - abs(37.5 - rsi) * 3  # Assouplissement
    score_rsi = max(0, min(100, score_rsi))  # Limiter à [0, 100]
    score_volume = min(100, 100 * (volume / (1.3 * volume_ref)))
    return 0.45*score_tendance + 0.25*score_rsi + 0.20*score_volume + 0.10*max(score_sem, 0)


# ============================================================================
# PHASE 2 + 3 + 4 + 6 : MOTEUR TOP 5 HEBDOMADAIRE EXPERT
# ============================================================================

def compute_acceleration_2w(symbol, db):
    """
    PHASE 2: Acceleration 2 semaines
    = (variation S-1) - (variation S-2)
    Détecte momentum croissant
    """
    try:
        docs = list(db.prices_weekly.find(
            {"symbol": symbol}
        ).sort("week", -1).limit(3))
        
        if len(docs) < 3:
            return 0.0
        
        var_s1 = docs[0].get("variation_pct", 0)  # Semaine -1
        var_s2 = docs[1].get("variation_pct", 0)  # Semaine -2
        
        acceleration = var_s1 - var_s2
        return round(acceleration, 2)
    except:
        return 0.0


def compute_breakout_3w(symbol, db, prix_actuel):
    """
    PHASE 2: Breakout 3 semaines
    = 1 si prix actuel > max(close 3 dernières semaines)
    = 0 sinon
    Détecte ruptures techniques
    """
    try:
        docs = list(db.prices_weekly.find(
            {"symbol": symbol}
        ).sort("week", -1).limit(3))
        
        if not docs or not prix_actuel:
            return 0.0
        
        max_3w = max([d.get("close", 0) for d in docs])
        
        if prix_actuel > max_3w:
            return 100.0  # Normalisé 0-100
        else:
            return 0.0
    except:
        return 0.0


def compute_rsi_momentum(rsi_actuel, symbol, db):
    """
    PHASE 2: RSI Momentum
    = RSI actuel - RSI il y a 2 semaines
    Détecte accélération force relative
    """
    try:
        if not rsi_actuel:
            return 0.0
        
        # Récupérer RSI il y a 2 semaines
        docs = list(db.prices_weekly.find(
            {"symbol": symbol, "rsi": {"$exists": True}}
        ).sort("week", -1).limit(3))
        
        if len(docs) < 3:
            return 0.0
        
        rsi_2w_ago = docs[2].get("rsi", rsi_actuel)
        delta_rsi = rsi_actuel - rsi_2w_ago
        
        # Normaliser -50 à +50 → 0 à 100
        score = 50 + delta_rsi  # RSI momentum positif = bon
        return max(0, min(100, score))
    except:
        return 50.0  # Neutre


def compute_relative_strength(symbol, db):
    """
    PHASE 6: Relative Strength vs BRVM Composite
    = performance action S-1 - performance indice S-1
    
    Alpha > 0 = action surperforme
    """
    try:
        # Performance action semaine -1
        doc_action = db.prices_weekly.find_one(
            {"symbol": symbol},
            sort=[("week", -1)]
        )
        
        if not doc_action:
            return 0.0
        
        var_action = doc_action.get("variation_pct", 0)
        
        # Performance indice BRVM
        doc_indice = db.prices_weekly.find_one(
            {"symbol": "BRVM-COMPOSITE"},
            sort=[("week", -1)]
        )
        
        var_indice = doc_indice.get("variation_pct", 0) if doc_indice else 0
        
        # Relative Strength
        rs = var_action - var_indice
        
        # Normaliser: RS de -10% à +10% → score 0 à 100
        score = 50 + (rs * 5)  # 1% RS = +5 points
        return max(0, min(100, score))
    except:
        return 50.0  # Neutre


def compute_smart_money(symbol, db):
    """
    PHASE 4: Smart Money - Liquidité institutionnelle
    Rank action parmi 47 par volume semaine précédente
    
    Rang 1 = +50% bonus
    Rang 15 = 0% 
    Rang 47 = -50% pénalité
    """
    try:
        from collecter_publications_brvm import ACTIONS_BRVM
        
        # Volumes de toutes les actions semaine -1
        volumes_dict = {}
        for sym in ACTIONS_BRVM.keys():
            doc = db.prices_weekly.find_one(
                {"symbol": sym},
                sort=[("week", -1)]
            )
            if doc:
                volumes_dict[sym] = doc.get("volume", 0)
        
        if not volumes_dict or symbol not in volumes_dict:
            return 1.0  # Neutre
        
        # Ranking (décroissant)
        sorted_symbols = sorted(volumes_dict.items(), key=lambda x: x[1], reverse=True)
        rank = [s[0] for s in sorted_symbols].index(symbol) + 1  # 1-based
        
        # Score: rang 1 = 1.5, rang 15 = 1.0, rang 47 = 0.5
        liquidity_multiplier = 1 + (15 - rank) / 30
        return max(0.5, min(1.5, liquidity_multiplier))
    except:
        return 1.0  # Neutre si erreur


def normalize_sentiment(score_sem, nb_publications):
    """
    PHASE 2: Sentiment normalisé
    Évite biais forte corrélation nb_pubs = score élevé
    """
    if not score_sem or score_sem <= 0:
        return 0.0
    
    if not nb_publications or nb_publications == 0:
        return 0.0
    
    # Formule expert: score total divisé par racine carrée du nombre
    # Bonus si nb_pubs >= 10 (volume significatif)
    import math
    normalized = (score_sem / math.sqrt(nb_publications)) * min(1.0, nb_publications / 10)
    
    # Normaliser 0-100
    # Sur BRVM, top sentiment ~ 400-500 après normalisation
    score = min(100, (normalized / 5) * 100)  # 500 normalized = 100 score
    return max(0, score)


def compute_wos_top5(symbol, sma5, sma10, rsi, volume, volume_ref, score_sem, 
                     nb_publications, prix_actuel, db):
    """
    PHASE 2: WOS_TOP5 - Moteur prédictif Top 5 hebdomadaire
    
    Formule optimisée momentum court terme BRVM:
    WOS_TOP5 = 
        0.25 × Acceleration_2w (momentum croissant)
      + 0.25 × Volume_Zscore (smart money)
      + 0.20 × Sentiment_normalisé (publications BRVM)
      + 0.15 × Breakout_3w (rupture technique)  
      + 0.15 × RSI_Momentum (force relative croissante)
      
    Multiplicateur Smart Money (liquidité institutionnelle)
    """
    
    # Calcul des 5 composantes
    try:
        acceleration = compute_acceleration_2w(symbol, db)
        breakout = compute_breakout_3w(symbol, db, prix_actuel)
        rsi_mom = compute_rsi_momentum(rsi, symbol, db)
        relative_strength = compute_relative_strength(symbol, db)
        sentiment = normalize_sentiment(score_sem, nb_publications)
        
        # Volume Z-score (déjà calculé dans analyse technique)
        # Utiliser volume ratio comme proxy si Z-score absent
        if volume and volume_ref and volume_ref > 0:
            volume_ratio = volume / volume_ref
            volume_score = min(100, volume_ratio * 50)  # 2x volume = 100 points
        else:
            volume_score = 50  # Neutre
        
        # Pondérations PHASE 2 (sentiment 20% comme demandé)
        wos_base = (
            0.25 * max(0, 50 + acceleration)  # Acceleration normalisée
          + 0.25 * volume_score               # Volume institutionnel
          + 0.20 * sentiment                  # Sentiment BRVM (20%)
          + 0.15 * breakout                   # Breakout technique
          + 0.15 * rsi_mom                    # RSI momentum
        )
        
        # PHASE 4: Multiplicateur Smart Money (liquidité)
        smart_money_mult = compute_smart_money(symbol, db)
        
        # PHASE 6: Bonus Relative Strength
        rs_bonus = (relative_strength - 50) / 100  # -0.5 à +0.5
        
        # Score final
        wos_final = wos_base * smart_money_mult * (1 + rs_bonus)
        
        # PHASE 3: Pénalités RSI extrêmes (pas blocage)
        if rsi:
            if rsi > 85:
                wos_final *= 0.4  # -60% si bulle extrême
            elif rsi > 80:
                wos_final *= 0.7  # -30% si surachat fort
        
        return round(wos_final, 1)
        
    except Exception as e:
        print(f"[ERREUR WOS_TOP5] {symbol}: {e}")
        # Fallback sur WOS legacy
        return compute_wos(sma5, sma10, rsi, volume, volume_ref, score_sem)

def calculer_timing_intraday(db, symbol):
    """
    AMÉLIORATION 4 — Timing intraday lundi matin.
    Compare premier cours du jour vs clôture de la veille (prices_daily).

    Retourne:
      "CONFIRME"  → ouverture > clôture veille (direction validée → ENTRER)
      "ATTENDRE"  → ouverture < clôture veille -0.5% (repli → différer l'entrée)
      "NEUTRE"    → variation entre -0.5% et 0% (ok, entrer avec prudence)
      "N/A"       → pas de données intraday aujourd'hui
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        # Premier cours intraday du jour (ouverture réelle)
        first_intraday = db.prices_intraday_raw.find_one(
            {"symbol": symbol, "date": today},
            sort=[("datetime", 1)]
        )

        if not first_intraday:
            return "N/A"

        # Clôture de la veille depuis prices_daily
        yesterday_doc = db.prices_daily.find_one(
            {"symbol": symbol, "date": {"$lt": today}},
            sort=[("date", -1)]
        )

        if not yesterday_doc or not yesterday_doc.get("close"):
            return "N/A"

        prix_ouverture = first_intraday.get("open") or first_intraday.get("close")
        cloture_veille = yesterday_doc.get("close")

        if not prix_ouverture or not cloture_veille or cloture_veille == 0:
            return "N/A"

        variation = (prix_ouverture - cloture_veille) / cloture_veille * 100

        if variation > 0:
            # Valider que la hausse est portée par du volume réel
            volume_intraday = first_intraday.get("volume") or 0
            vol_veille = yesterday_doc.get("volume") or 0
            # Seuil : au moins 5% du volume de la veille en ouverture
            # (BRVM ouvre lentement, 20% était trop restrictif — aucun CONFIRME généré)
            vol_seuil = vol_veille * 0.05 if vol_veille > 0 else 0
            if volume_intraday > 0 and (vol_seuil == 0 or volume_intraday >= vol_seuil):
                return "CONFIRME"
            return "NEUTRE"  # Hausse sans volume suffisant = signal non validé
        elif variation < -0.5:
            return "ATTENDRE"
        else:
            return "NEUTRE"

    except Exception as e:
        return "N/A"


def run_decision_engine_weekly(mode="plus-value", capital=100000):
    _, db = get_mongo_db()
    
    # Calcul semaine ISO pour tracking performance
    # IMPORTANT: Utiliser semaine PRÉCÉDENTE (données complètes après clôture)
    week_ago = datetime.now() - timedelta(days=7)
    week_str = week_ago.strftime("%Y-W%V")
    
    print("\n=== DECISION FINALE BRVM - HEBDOMADAIRE (LOGIQUE PERCENTILE 2 PASSES) ===\n")
    print(f"[SEMAINE] {week_str}")
    analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))
    print(f"[INFO] {len(analyses)} documents trouves dans AGREGATION_SEMANTIQUE_ACTION")
    
    if not analyses:
        print("[ERREUR] Aucune analyse IA disponible")
        return
    decisions_finales = db["decisions_finales_brvm"]
    # Archiver les décisions précédentes au lieu de les supprimer (conservation historique)
    decisions_finales.update_many(
        {"horizon": HORIZON_TAG, "archived": {"$ne": True}},
        {"$set": {"archived": True, "archived_at": datetime.now(timezone.utc)}}
    )
    
    # ========================================================================
    # MODE INSTITUTIONAL: Détection régime + Univers tradable (Layer 1-2)
    # ========================================================================
    regime_data = None
    tradable_universe = None
    exposure_factor = 1.0
    
    if MODE_INSTITUTIONAL:
        print("\n[INSTITUTIONAL] Détection régime marché...")
        regime_data = compute_market_regime(db)
        regime = regime_data["regime"]
        exposure_factor = regime_data["exposure_factor"]
        
        print(f"\n[RÉGIME DÉTECTÉ] {regime}")
        print(f"   - Performance BRVM 4 sem: {regime_data['brvm_perf_4w']:.1f}%")
        print(f"   - Breadth (% UP): {regime_data['breadth_pct']:.1f}%")
        print(f"   - Facteur exposition: {exposure_factor:.0%}")
        
        print("\n[INSTITUTIONAL] Filtrage univers tradable (Top 20 liquidité)...")
        tradable_universe = set(get_tradable_universe(db, top_n=20))
        print(f"   - Univers tradable: {len(tradable_universe)} actions")
        print(f"   - Actions: {sorted(tradable_universe)}")
    
    # ========================================================================
    # PASSE 1: COLLECTE DONNÉES COMPLÈTES (sans filtrage pour distribution)
    # ========================================================================
    print("\n[PASSE 1] Collecte données pour calcul percentiles...")
    
    actions_data = []  # Liste pour stocker toutes les données
    rejected = {"no_symbol": 0, "no_price": 0, "atr_aberrant": 0, "not_tradable": 0}
    
    for doc in analyses:
        attrs = doc.get("attrs", {})
        symbol = attrs.get("symbol")
        if not symbol:
            rejected["no_symbol"] += 1
            continue
        
        # MODE INSTITUTIONAL: Filtrer univers tradable (top 20 liquidité)
        if MODE_INSTITUTIONAL and tradable_universe is not None:
            if symbol not in tradable_universe:
                rejected["not_tradable"] += 1
                continue
        
        print(f"   [{symbol}] Collecte données...")
        
        # Extraction signal et scores
        signal = attrs.get("signal", "HOLD")
        score_tech = attrs.get("score") or 0
        score_sem = attrs.get("score_semantique_semaine") or 0
        
        # CORRECTION EXPERT: Récupérer prix FRAIS depuis collecte horaire
        dernier_prix_doc = db.prices_daily.find_one(
            {"symbol": symbol},
            sort=[("date", -1)]
        )
        
        if not dernier_prix_doc or not dernier_prix_doc.get("close"):
            prix = attrs.get("prix_actuel") or 0
            if not prix or prix == 0:
                rejected["no_price"] += 1
                print(f"   [{symbol}] [X] Pas de prix disponible")
                continue
            volume = attrs.get("volume") or 5000
        else:
            prix = dernier_prix_doc.get("close")
            volume = dernier_prix_doc.get("volume") or 5000
        
        # Extraction métriques techniques
        sma5 = attrs.get("SMA5") or 0
        sma10 = attrs.get("SMA10") or 0
        rsi = attrs.get("rsi")
        volume_ref = volume
        volume_zscore = attrs.get("volume_zscore")
        acceleration = attrs.get("acceleration")

        # Signaux observables (produits par analyse_ia_simple v2)
        vsr = attrs.get("vsr")
        momentum_5j = attrs.get("momentum_5j")
        score_alpha = attrs.get("score_alpha")
        alpha_label = attrs.get("alpha_label")
        
        # Parser details pour récupérer données manquantes
        details = attrs.get("details", [])
        atr_pct_from_details = None
        volume_zscore_from_details = None
        acceleration_from_details = None
        trend_direction = None
        
        import re
        for detail in details:
            if "RSI" in detail and rsi is None:
                match = re.search(r'RSI.*?\((\d+\.?\d*)\)', detail)
                if match:
                    rsi = float(match.group(1))
            
            if "ATR%" in detail:
                match = re.search(r'ATR%.*?\((\d+\.?\d*)%\)', detail)
                if match:
                    atr_pct_from_details = float(match.group(1))
            
            if "Z=" in detail and "VOLUME" in detail.upper():
                match = re.search(r'Z=([-+]?\d+\.?\d*)', detail)
                if match:
                    volume_zscore_from_details = float(match.group(1))
            
            if "ACCÉLÉRATION" in detail.upper():
                match = re.search(r'([+-]?\d+\.?\d*)%', detail)
                if match:
                    acceleration_from_details = float(match.group(1))
            
            if "Tendance haussière" in detail or "haussière (UP)" in detail:
                trend_direction = "UP"
                if sma5 == 0 and sma10 == 0:
                    sma5 = prix or 1000
                    sma10 = (prix or 1000) * 0.95
            elif "Tendance baissière" in detail or "baissière (DOWN)" in detail:
                trend_direction = "DOWN"
        
        # Priorité extraction
        if volume_zscore is None and volume_zscore_from_details is not None:
            volume_zscore = volume_zscore_from_details
        if acceleration is None and acceleration_from_details is not None:
            acceleration = acceleration_from_details
        
        # Calcul ATR%
        if atr_pct_from_details:
            atr_pct = atr_pct_from_details
        else:
            volatility_abs = attrs.get("volatility")
            if volatility_abs and prix > 0:
                atr_pct = (volatility_abs / prix) * 100
            else:
                atr_pct = 10.0
        
        # PHASE 10: ATR aberrant = exclusion immédiate
        if atr_pct and atr_pct > 60.0:
            rejected["atr_aberrant"] += 1
            print(f"   [{symbol}] [X] ATR% aberrant ({atr_pct:.1f}%)")
            continue
        
        # Plafonner ATR%
        if atr_pct and atr_pct > 30.0:
            print(f"   [{symbol}] [!] ATR% eleve ({atr_pct:.1f}%) PLAFONNE a 30%")
            atr_pct = 30.0
        
        # CALCULS POUR PERCENTILES (mode Elite Minimaliste)
        rs_4sem = None
        perf_action = None
        perf_brvm = None
        volume_moyen_8sem = None
        prix_max_3w = None  # PHASE 4: Breakout intelligent
        
        # RS 4 semaines toujours calculé (proxy via médiane prices_weekly)
        rs_4sem, perf_action, perf_brvm = compute_relative_strength_4sem(symbol, db)

        if MODE_ELITE_MINIMALISTE:
            # Calcul volume moyen 8 semaines (uniquement Elite)
            volumes_8sem = list(db.prices_weekly.find(
                {"symbol": symbol},
                {"volume": 1}
            ).sort("week", -1).limit(8))
            
            if volumes_8sem:
                volumes = [v["volume"] for v in volumes_8sem if v.get("volume")]
                volume_moyen_8sem = sum(volumes) / len(volumes) if volumes else None
            
            # PHASE 4: Calculer prix max 3 dernières semaines (breakout intelligent)
            prices_3w = list(db.prices_weekly.find(
                {"symbol": symbol},
                {"close": 1}
            ).sort("week", -1).limit(3))
            
            if prices_3w and len(prices_3w) > 0:
                close_prices = [p["close"] for p in prices_3w if p.get("close")]
                prix_max_3w = max(close_prices) if close_prices else None
        
        # Stocker toutes les données (même celles qui seraient rejetées plus tard)
        
        # 🔥 EXTRACTION DONNÉES PUBLICATIONS pour sentiment dynamique
        nb_publications = attrs.get("count_publications") or attrs.get("count_semaine") or 0
        
        # Détecter événements majeurs dans les publications récentes (7 derniers jours)
        publication_keywords = []
        date_limite = datetime.now(timezone.utc) - timedelta(days=7)
        
        pubs_recentes = db.publications_brvm.find({
            "symbol": symbol,
            "date_publication": {"$gte": date_limite}
        }).limit(10)
        
        for pub in pubs_recentes:
            titre = pub.get("titre", "").upper()
            # Détecter événements clés
            if any(keyword in titre for keyword in ["RESULTAT", "DIVIDEND", "ACQUISITION", "FUSION", "CONSEIL", "ASSEMBLEE"]):
                publication_keywords.append(titre[:50])  # Premier 50 chars
        
        action_data = {
            "symbol": symbol,
            "attrs": attrs,
            "doc": doc,
            "signal": signal,
            "score_tech": score_tech,
            "score_sem": score_sem,
            "prix": prix,
            "volume": volume,
            "volume_ref": volume_ref,
            "sma5": sma5,
            "sma10": sma10,
            "rsi": rsi,
            "volume_zscore": volume_zscore,
            "acceleration": acceleration,
            "atr_pct": atr_pct,
            "details": details,
            "trend_direction": trend_direction,
            # Métriques Elite Minimaliste
            "rs_4sem": rs_4sem,
            "perf_action": perf_action,
            "perf_brvm": perf_brvm,
            "volume_moyen_8sem": volume_moyen_8sem,
            "prix_max_3w": prix_max_3w,  # PHASE 4: Breakout intelligent
            # 🔥 NOUVEAU: données publications pour sentiment dynamique
            "nb_publications": nb_publications,
            "publication_keywords": publication_keywords,
            "perf_action_4sem": perf_action,  # Alias pour institutional_alpha
            # Signaux observables V2
            "vsr": vsr,
            "momentum_5j": momentum_5j,
            "score_alpha": score_alpha,
            "alpha_label": alpha_label,
        }
        
        actions_data.append(action_data)
    
    print(f"\n[PASSE 1] {len(actions_data)} actions collectées pour analyse")
    print(f"[PASSE 1] Rejetées: {rejected}")
    
    # ========================================================================
    # CALCUL PERCENTILES SUR DISTRIBUTION COMPLÈTE
    # ========================================================================
    print("\n[CALCUL PERCENTILES] Analyse distribution complète...")
    
    import numpy as np
    
    # Collecter toutes les valeurs RS et volumes pour percentiles
    rs_values = [a["rs_4sem"] for a in actions_data if a["rs_4sem"] is not None]
    volume_ratios = []
    for a in actions_data:
        if a["volume_moyen_8sem"] and a["volume_moyen_8sem"] > 0:
            ratio = a["volume"] / a["volume_moyen_8sem"]
            volume_ratios.append(ratio)
    
    print(f"   - {len(rs_values)} valeurs RS disponibles")
    print(f"   - {len(volume_ratios)} ratios volume disponibles")
    
    # Calculer percentiles pour chaque action
    for action_data in actions_data:
        # RS Percentile
        if action_data["rs_4sem"] is not None and rs_values:
            rs_percentile = (sum(1 for v in rs_values if v <= action_data["rs_4sem"]) / len(rs_values)) * 100
            action_data["rs_percentile"] = rs_percentile
        else:
            action_data["rs_percentile"] = None
        
        # Volume Percentile
        if action_data["volume_moyen_8sem"] and action_data["volume_moyen_8sem"] > 0 and volume_ratios:
            vol_ratio = action_data["volume"] / action_data["volume_moyen_8sem"]
            vol_percentile = (sum(1 for v in volume_ratios if v <= vol_ratio) / len(volume_ratios)) * 100
            action_data["volume_percentile"] = vol_percentile
        else:
            action_data["volume_percentile"] = None
    
    # Afficher distribution
    if rs_values:
        print(f"\n[DISTRIBUTION RS]")
        print(f"   - Min: {min(rs_values):.1f}%")
        print(f"   - P25: {np.percentile(rs_values, 25):.1f}%")
        print(f"   - P50: {np.percentile(rs_values, 50):.1f}%")
        print(f"   - P75: {np.percentile(rs_values, 75):.1f}%")
        print(f"   - Max: {max(rs_values):.1f}%")
    
    if volume_ratios:
        print(f"\n[DISTRIBUTION VOLUME]")
        print(f"   - Min: {min(volume_ratios):.2f}x")
        print(f"   - P25: {np.percentile(volume_ratios, 25):.2f}x")
        print(f"   - P50: {np.percentile(volume_ratios, 50):.2f}x")
        print(f"   - P75: {np.percentile(volume_ratios, 75):.2f}x")
        print(f"   - Max: {max(volume_ratios):.2f}x")
    
    # ========================================================================
    # PASSE 2: FILTRAGE PERCENTILE ET GÉNÉRATION DÉCISIONS
    # ========================================================================
    print("\n[PASSE 2] Filtrage percentile et génération décisions...")
    
    count = 0
    rejected_p2 = {"elite_filter": 0, "bloquant": 0}
    
    for action_data in actions_data:
        symbol = action_data["symbol"]
        attrs = action_data["attrs"]
        signal = action_data["signal"]
        prix = action_data["prix"]
        volume = action_data["volume"]
        
        print(f"\n   [{symbol}] === FILTRAGE PASSE 2 ===")
        
        # DISCIPLINE INSTITUTIONNELLE: Bloquer BLOQUANTS (mode normal)
        if not MODE_ELITE_MINIMALISTE:
            if signal == "SELL":
                rejected_p2["bloquant"] += 1
                print(f"   [{symbol}] [X] Signal SELL (motif bloquant)")
                continue

            details_text = str(action_data["details"])
            if "[BLOQUANT]" in details_text:
                rejected_p2["bloquant"] += 1
                print(f"   [{symbol}] [X] [BLOQUANT] dans analyse technique")
                continue

            # HOLD tiède = pas de recommandation (HOLD ≠ BUY sémantiquement)
            if signal == "HOLD" and action_data["score_tech"] < 65:
                rejected_p2["bloquant"] += 1
                print(f"   [{symbol}] [X] HOLD score faible ({action_data['score_tech']:.0f} < 65) — pas de recommandation")
                continue
        else:
            if signal == "SELL":
                print(f"   [{symbol}] [!] Signal SELL - filtres Elite valideront")
        
        # FILTRES ELITE MINIMALISTE avec PERCENTILES
        position_size_factor = 1.0  # Par défaut: position complète
        
        if MODE_ELITE_MINIMALISTE:
            passed, rejection_reason, position_size_factor = apply_elite_filters(
                symbol=symbol,
                prix=prix,
                volume=volume,
                volume_moyen_8sem=action_data["volume_moyen_8sem"],
                atr_pct=action_data["atr_pct"],
                trend_direction=action_data["trend_direction"],
                rs_4sem=action_data["rs_4sem"],
                rs_percentile=action_data["rs_percentile"],
                volume_percentile=action_data["volume_percentile"],
                acceleration=action_data.get("acceleration"),  # PHASE 3
                prix_max_3w=action_data.get("prix_max_3w")  # PHASE 4
            )
            
            if not passed:
                rejected_p2["elite_filter"] += 1
                print(f"   [{symbol}] [X] FILTRE ELITE: {rejection_reason}")
                if action_data["rs_percentile"] is not None:
                    print(f"   [{symbol}] RS: {action_data['rs_4sem']:+.1f}% (P{action_data['rs_percentile']:.0f})")
                if action_data["volume_percentile"] is not None:
                    vol_ratio = volume / action_data["volume_moyen_8sem"] if action_data["volume_moyen_8sem"] else 0
                    print(f"   [{symbol}] Volume: {vol_ratio:.2f}x (P{action_data['volume_percentile']:.0f})")
                continue
            
            # OK Action passee filtres elite
            size_info = f" | Sizing: {int(position_size_factor*100)}%" if position_size_factor < 1.0 else ""
            print(f"   [{symbol}] [OK] FILTRES ELITE PASSES{size_info}")
            if action_data["rs_percentile"] is not None:
                print(f"   [{symbol}] RS: {action_data['rs_4sem']:+.1f}% (P{action_data['rs_percentile']:.0f})")
            if action_data["volume_percentile"] is not  None:
                vol_ratio = volume / action_data["volume_moyen_8sem"] if action_data["volume_moyen_8sem"] else 0
                print(f"   [{symbol}] Volume: {vol_ratio:.2f}x (P{action_data['volume_percentile']:.0f})")
            if action_data.get("acceleration") is not None:
                print(f"   [{symbol}] Accélération: {action_data['acceleration']:+.1f}%")
        
        # ===================================================================
        # MODE INSTITUTIONAL: ALPHA_SCORE composite (Layer 3)
        # Sinon: WOS_TOP5 classique
        # ===================================================================
        if MODE_INSTITUTIONAL and regime_data:
            # Calculer ALPHA_SCORE institutionnel (6 facteurs pondérés)
            alpha_score, alpha_components, alpha_weights = compute_alpha_score_institutional(
                action_data=action_data,
                regime_data=regime_data
            )
            
            # Conversion ALPHA_SCORE (0-100) vers échelle WOS (0-100) 
            # Pour compatibilité avec logique stops/targets existante
            wos = round(alpha_score, 1)
            
            print(f"   [{symbol}] [OK] ALPHA_SCORE: {alpha_score:.1f}/100 (regime {regime_data['regime']})")
            if alpha_components:
                print(f"      Composants:")
                for key, value in alpha_components.items():
                    weight = alpha_weights.get(key, 0) * 100
                    print(f"         - {key}: {value:.1f} (poids {weight:.0f}%)")
        else:
            # Mode classique: WOS_TOP5
            nb_publications = attrs.get("count_publications", attrs.get("count_semaine", 10))
            
            wos = round(compute_wos_top5(
                symbol=symbol,
                sma5=action_data["sma5"],
                sma10=action_data["sma10"],
                rsi=action_data["rsi"],
                volume=volume,
                volume_ref=action_data["volume_ref"],
                score_sem=action_data["score_sem"],
                nb_publications=nb_publications,
                prix_actuel=prix,
                db=db
            ), 1)
            
            alpha_score = wos  # Mode classique: alpha_score = wos

            # NORMALISATION : WOS ne peut dépasser 100 (classes A/B/C stables)
            wos = min(100.0, wos)

            print(f"   [{symbol}] WOS_TOP5: {wos}/100")
        
        # ===================================================================
        atr_pct = action_data["atr_pct"]

        # P4 — Filtre ATR daily trop faible : mouvement trop étroit pour être tradable
        if MODE_DAILY and atr_pct and atr_pct < 0.56:
            print(f"   [{symbol}] [X] ATR_DAILY_FAIBLE ({atr_pct:.2f}% < 0.56% — gain < 1% : non tradable BRVM)")
            continue

        # A3 — Classe préliminaire pour Dynamic RR (wos déjà calculé à ce stade)
        if wos >= 75:
            classe_prelim = "A"
        elif wos >= 60:
            classe_prelim = "B"
        else:
            classe_prelim = "C"

        if atr_pct and atr_pct > 0:
            stop_pct = max(1.5 * atr_pct, 0.5 if MODE_DAILY else 4.0)

            if MODE_ELITE_MINIMALISTE:
                target_pct = max(10.0, 0.5 * atr_pct)
                rr = target_pct / stop_pct if stop_pct > 0 else 0
                if rr < 2.0:
                    stop_pct = target_pct / 2.0
                    rr = 2.0
            else:
                # A3 — Dynamic RR par classe : A=2.0 (stable) | B=2.4 (standard) | C=3.0 (plus risqué)
                # target relatif au stop_pct réel → cohérence RR garantie même si floor actif
                rr_par_classe = {"A": 2.0, "B": 2.4, "C": 3.0}
                rr_cible = rr_par_classe.get(classe_prelim, 2.4)
                target_pct = rr_cible * stop_pct
            
            gain_attendu = round(target_pct, 1)
        else:
            atr_pct = 10.0
            stop_pct = 9.0           # 0.9 × 10.0
            target_pct = 24.0        # 2.4 × 10.0 → RR = 2.67
            gain_attendu = 24.0
        
        # Prix cible/stop
        prix_sortie = round(prix * (1 + target_pct/100), 2) if prix else 0
        stop = round(prix * (1 - stop_pct/100), 2) if prix else 0
        rr = round(target_pct / stop_pct, 2) if stop_pct > 0 else 0
        
        # CONFIANCE DIFFÉRENCIÉE avec WOS — plage [0-100] discriminante
        # WOS=0 → 0%, WOS=100 → 100% (avec bonus accélération/RSI plafonnés)
        confiance = round(min(100, max(0, wos)), 1)

        # Bonus confiance (plafonné à 100)
        if action_data["acceleration"] and action_data["acceleration"] > 10:
            confiance = min(100, confiance + 5)
        if action_data["rsi"] and 50 <= action_data["rsi"] <= 70:
            confiance = min(100, confiance + 3)
        
        # Classification
        if wos >= 75:
            classe = "A"
        elif wos >= 60:
            classe = "B"
        else:
            classe = "C"
        
        # Raisons
        raisons = action_data["details"][:4] if action_data["details"] else ["Signal technique favorable"]
        
        # Construction décision
        decision = {
            "symbol": symbol,
            "decision": signal,  # BUY ou HOLD (HOLD fort score≥65 remonte en surveillance)
            "signal": signal,  # PRODUCTION: Signal principal (SELL/HOLD/etc)
            "signal_technique": signal,
            "horizon": HORIZON_TAG,
            "is_primary": True,
            
            # Champs obligatoires TOP5
            "classe": classe,
            "confidence": round(confiance, 1),
            "wos": wos,
            "alpha_score": alpha_score if MODE_INSTITUTIONAL and regime_data else wos,  # PRODUCTION: ALPHA institutionnel
            "rr": rr,
            "gain_attendu": gain_attendu,
            
            # ELITE MINIMALISTE: Relative Strength + Percentiles
            "rs_4sem": action_data["rs_4sem"] if action_data["rs_4sem"] is not None else 0,
            "rs_percentile": action_data["rs_percentile"],
            "perf_action_4sem": action_data["perf_action"] if action_data["perf_action"] is not None else 0,
            "perf_brvm_4sem": action_data["perf_brvm"] if action_data["perf_brvm"] is not None else 0,
            "volume_percentile": action_data["volume_percentile"],
            "position_size_factor": position_size_factor,  # PHASE 5: Sizing adaptatif (0.5 si volume faible)
            "mode_elite": MODE_ELITE_MINIMALISTE,
            
            # Champs legacy
            "confiance": confiance,
            "score": action_data["score_tech"],
            "score_technique": action_data["score_tech"],
            "score_semantique": action_data["score_sem"],
            "risk_reward": rr,
            "expected_return": gain_attendu,
            
            # Prix et stops
            "prix_entree": prix,
            "prix_actuel": prix,
            "prix_sortie": prix_sortie,
            "prix_cible": prix_sortie,
            "stop": stop,
            "stop_loss": stop,  # PRODUCTION: Alias pour clarté
            "stop_pct": stop_pct,
            "target_pct": target_pct,
            "take_profit": prix_sortie,  # PRODUCTION: Alias pour clarté
            
            # Techniques
            "rsi": action_data["rsi"],
            "volume": volume,
            "spread": 5,  # Valeur par défaut
            "volatilite": atr_pct,
            "atr_pct": atr_pct,
            
            # Métriques experts
            "volume_zscore": action_data["volume_zscore"],
            # Signaux observables V2 (tracabilité complète)
            "vsr": action_data.get("vsr"),
            "momentum_5j": action_data.get("momentum_5j"),
            "score_alpha": action_data.get("score_alpha"),
            "alpha_label": action_data.get("alpha_label"),
            "acceleration": action_data["acceleration"],
            
            # Justifications
            "raisons": raisons,
            "justification": "; ".join(raisons),
            
            # Tracking performance
            "week": week_str,
            "generated_at": datetime.now(timezone.utc),
            "company_name": attrs.get("company_name", symbol),

            # AMÉLIORATION 2 — Sizing obligatoire (% max du portefeuille par classe)
            "allocation_max": 15.0 if classe == "A" else (10.0 if classe == "B" else 5.0),

            # AMÉLIORATION 4 — Timing intraday: confirmation direction lundi matin
            "timing_signal": calculer_timing_intraday(db, symbol)
        }
        
        decisions_finales.update_one(
            {"symbol": symbol, "horizon": HORIZON_TAG, "archived": {"$ne": True}},
            {"$set": {**decision, "archived": False}},
            upsert=True
        )
        
        # Logging
        score_label = "ALPHA" if MODE_INSTITUTIONAL else "WOS"
        log_parts = [f"[OK] {symbol:8s} | {signal:4s} | Classe {classe} | {score_label} {wos:4.1f} | Conf {confiance:2.0f}%"]
        if action_data["rs_percentile"] is not None:
            log_parts.append(f" | RS P{action_data['rs_percentile']:.0f}")
        if action_data["volume_percentile"] is not None:
            log_parts.append(f" | Vol P{action_data['volume_percentile']:.0f}")
        
        print("".join(log_parts))
        count += 1
    
    # ========================================================================
    # MODE INSTITUTIONAL: Allocation dynamique portfolio (Layer 4)
    # ========================================================================
    if MODE_INSTITUTIONAL and regime_data and count > 0:
        print(f"\n[INSTITUTIONAL] Calcul allocation dynamique portfolio...")
        
        # Récupérer toutes les recommandations générées
        recommendations = list(decisions_finales.find({"horizon": HORIZON_TAG}))
        
        if recommendations:
            # Calculer allocation avec contraintes institutionnelles
            portfolio = compute_portfolio_allocation(
                recommendations=recommendations,
                regime_data=regime_data,
                total_capital=capital
            )
            
            print(f"\n[ALLOCATION PORTFOLIO] Régime {regime_data['regime']} - Exposition {exposure_factor:.0%}")
            print(f"   Nombre positions: {len(portfolio)}")
            
            # Mise à jour des décisions avec allocation
            for alloc in portfolio:
                symbol = alloc["symbol"]
                
                # Calculer nombre de titres (capital / prix)
                prix = alloc.get("prix_entree", 0)
                nombre_titres = int(alloc["capital_alloue"] / prix) if prix > 0 else 0
                alloc["nombre_titres"] = nombre_titres  # Ajouter au dict pour logging
                
                decisions_finales.update_one(
                    {"symbol": symbol, "horizon": HORIZON_TAG},
                    {"$set": {
                        "capital_alloue": alloc["capital_alloue"],
                        "pct_portfolio": alloc["pct_portfolio"],
                        "nombre_titres": nombre_titres,
                        "alpha_score": alloc.get("alpha_score"),
                        "regime_marche": regime_data["regime"],
                        "exposure_factor": exposure_factor
                    }}
                )
                
                print(f"      {symbol:8s}: {alloc['capital_alloue']:>10,.0f} FCFA ({alloc['pct_portfolio']:>5.1f}%) - {alloc['nombre_titres']:>4.0f} titres")
            
            print(f"   Capital total investi: {sum(a['capital_alloue'] for a in portfolio):,.0f} FCFA")
    
    print(f"\n[STATS PASSE 2] Rejetées:")
    print(f"  - Filtres Elite: {rejected_p2['elite_filter']}")
    print(f"  - Bloquants: {rejected_p2['bloquant']}")
    print(f"\n[RESULTAT] {count} recommandations hebdomadaires générées (logique PERCENTILE)\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Décision finale BRVM — Weekly Pro")
    parser.add_argument("--mode", default="plus-value")
    parser.add_argument("--capital", type=float, default=100000)
    args = parser.parse_args()
    run_decision_engine_weekly(args.mode, capital=args.capital)

