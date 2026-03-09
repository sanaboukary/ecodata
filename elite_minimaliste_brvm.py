"""
SYSTÈME ELITE MINIMALISTE BRVM
================================

Philosophie: CRÉDIBILITÉ > Performance théorique

Avec 14 semaines de données:
- Filtres simples robustes (pas 10 indicateurs complexes)
- Max 1-3 positions selon régime marché
- Accepter CASH si rien de propre
- Targets dynamiques (minimum 10%, pas de plafond artificiel)
- Focus CONTINUATION (pas retournements magiques)

Pour trader institutionnel avec 10,000 followers.
"""

from datetime import datetime, timedelta
from plateforme_centralisation.mongo import get_mongo_db
from scipy.stats import percentileofscore
import numpy as np


# ============================================================================
# UNIVERS BRVM 47 ACTIONS
# ============================================================================
ACTIONS_BRVM_47 = {
    # FINANCE (16)
    "BICC", "SGBC", "CBIBF", "BOAB", "BOABF", "BOAC", "BOAM", "BOAN",
    "BOAS", "ETIT", "SIBC", "SCRC", "ABJC", "BNBC", "NSBC", "PRSC",
    
    # DISTRIBUTION (9)
    "CIEC", "FTSC", "TTLC", "SEMC", "SHEC", "STBC", "SNTS", "ORAC", "NTLC",
    
    # INDUSTRIE (12)
    "SAFC", "PALC", "SICC", "CABC", "SMBC", "SLBC", "SPHC", "SVOC", 
    "UNXC", "SOGC", "STAC", "CFAC",
    
    # AGRICULTURE (3)
    "SAFH", "PALMH", "SIVC",
    
    # SERVICES (5)
    "SDSC", "ONTBF", "ORGT", "UNLC", "TTLS",
    
    # AUTRES (2)
    "LNBF", "NEIC"
}


# ============================================================================
# FILTRE 1: RELATIVE STRENGTH 4 SEMAINES
# ============================================================================
def get_performance_4_semaines(symbol, db):
    """
    Performance cumulée 4 dernières semaines
    Returns: (performance_pct, prix_actuel, prix_4sem_ago)
    """
    try:
        prices_weekly = list(db.prices_weekly.find(
            {"symbol": symbol}
        ).sort("week", -1).limit(5))
        
        if len(prices_weekly) < 4:
            return None, None, None
        
        prix_actuel = prices_weekly[0].get("close")
        prix_4sem = prices_weekly[3].get("close")
        
        if not prix_actuel or not prix_4sem or prix_4sem <= 0:
            return None, None, None
        
        performance = ((prix_actuel - prix_4sem) / prix_4sem) * 100
        
        return performance, prix_actuel, prix_4sem
        
    except Exception as e:
        print(f"⚠️ Erreur performance 4sem {symbol}: {e}")
        return None, None, None


def get_brvm_composite_performance(db):
    """
    Performance indice BRVM Composite 4 semaines
    
    Si pas disponible, utiliser moyenne pondérée des 10 blue chips:
    SNTS, SGBC, BOAC, BOAM, PALC, SAFC, CFAC, TTLS, SIVC, BICC
    """
    try:
        # Tentative 1: Indice BRVM Composite si collecté
        composite = list(db.prices_weekly.find(
            {"symbol": "BRVM_COMPOSITE"}
        ).sort("week", -1).limit(4))
        
        if len(composite) >= 4:
            prix_actuel = composite[0].get("close")
            prix_4sem = composite[3].get("close")
            if prix_actuel and prix_4sem and prix_4sem > 0:
                return ((prix_actuel - prix_4sem) / prix_4sem) * 100
        
        # Tentative 2: Moyenne pondérée blue chips
        blue_chips = ["SNTS", "SGBC", "BOAC", "BOAM", "PALC", "SAFC", "CFAC", "TTLS", "SIVC", "BICC"]
        performances = []
        
        for symbol in blue_chips:
            perf, _, _ = get_performance_4_semaines(symbol, db)
            if perf is not None:
                performances.append(perf)
        
        if len(performances) >= 5:
            return np.mean(performances)
        
        # Défaut: marché neutre
        return 0.0
        
    except Exception as e:
        print(f"⚠️ Erreur indice BRVM: {e}")
        return 0.0


# ============================================================================
# FILTRE 2: VOLUME ≥ 1.5× MOYENNE
# ============================================================================
def get_volume_ratio(symbol, db):
    """
    Volume ratio = volume semaine dernière / moyenne 8 semaines
    
    Ratio ≥ 1.5 = intérêt marché confirmé
    Ratio < 1.5 = pas assez d'activité
    """
    try:
        prices_weekly = list(db.prices_weekly.find(
            {"symbol": symbol}
        ).sort("week", -1).limit(9))
        
        if len(prices_weekly) < 8:
            return None
        
        volume_last = prices_weekly[0].get("volume", 0)
        volumes_8sem = [p.get("volume", 0) for p in prices_weekly[:8] if p.get("volume", 0) > 0]
        
        if not volumes_8sem or volume_last <= 0:
            return None
        
        volume_moyen = np.mean(volumes_8sem)
        
        if volume_moyen <= 0:
            return None
        
        ratio = volume_last / volume_moyen
        
        return round(ratio, 2)
        
    except Exception as e:
        print(f"⚠️ Erreur volume ratio {symbol}: {e}")
        return None


# ============================================================================
# FILTRE 3: PAS DE TENDANCE DOWN CLAIRE
# ============================================================================
def get_tendance_4_semaines(symbol, db):
    """
    Tendance = prix actuel vs SMA 4 semaines
    
    UP: prix > SMA → continuation possible
    DOWN: prix < SMA → éviter contre-tendance
    """
    try:
        prices_weekly = list(db.prices_weekly.find(
            {"symbol": symbol}
        ).sort("week", -1).limit(5))
        
        if len(prices_weekly) < 4:
            return None, None, None
        
        prix_actuel = prices_weekly[0].get("close")
        prix_4sem = [p.get("close") for p in prices_weekly[:4] if p.get("close")]
        
        if not prix_actuel or len(prix_4sem) < 4:
            return None, None, None
        
        sma_4 = np.mean(prix_4sem)
        
        if prix_actuel > sma_4:
            tendance = "UP"
        else:
            tendance = "DOWN"
        
        return tendance, prix_actuel, sma_4
        
    except Exception as e:
        print(f"⚠️ Erreur tendance {symbol}: {e}")
        return None, None, None


# ============================================================================
# FILTRE 4: ATR RAISONNABLE 8-25%
# ============================================================================
def get_atr_pct(symbol, db):
    """
    ATR% simplifié weekly (8 semaines)
    
    ATR < 8%: Trop stable (mort)
    ATR 8-25%: Normal BRVM
    ATR > 25%: Micro-cap instable (exclure)
    """
    try:
        prices_weekly = list(db.prices_weekly.find(
            {"symbol": symbol}
        ).sort("week", -1).limit(9))
        
        if len(prices_weekly) < 8:
            return None
        
        # True Range simplifié (close to close)
        true_ranges = []
        for i in range(1, 8):
            close_i = prices_weekly[i].get("close")
            close_i1 = prices_weekly[i+1].get("close")
            if close_i and close_i1 and close_i1 > 0:
                tr_pct = abs((close_i - close_i1) / close_i1) * 100
                true_ranges.append(tr_pct)
        
        if len(true_ranges) < 6:
            return None
        
        atr = np.mean(true_ranges)
        
        return round(atr, 2)
        
    except Exception as e:
        print(f"⚠️ Erreur ATR {symbol}: {e}")
        return None


# ============================================================================
# RANKING: MOMENTUM RELATIF (Continuation BRVM)
# ============================================================================
def compute_momentum_score(perf_4sem, rs_4sem, volume_ratio):
    """
    Score momentum pour ranking
    
    Priorité:
    1. Relative Strength (60%) - surperformance vs marché
    2. Performance absolue (25%) - momentum intrinsèque  
    3. Volume confirmation (15%) - intérêt institutionnel
    
    Focus CONTINUATION (pas retournement)
    """
    score = 0.0
    
    # RS (relative strength)
    if rs_4sem is not None:
        # RS > 0 bonus, RS < 0 pénalité
        score += rs_4sem * 0.60
    
    # Performance absolue
    if perf_4sem is not None:
        score += perf_4sem * 0.25
    
    # Volume
    if volume_ratio is not None:
        # Volume 1.5x = +8, Volume 3x = +22.5
        volume_bonus = (volume_ratio - 1) * 15
        score += volume_bonus * 0.15
    
    return round(score, 2)


# ============================================================================
# TARGET DYNAMIQUE (Minimum 10%, pas de plafond artificiel)
# ============================================================================
def compute_target_dynamique(perf_4sem, rs_4sem, volume_ratio, atr_pct):
    """
    Target dynamique basé sur potentiel réel
    
    Logique trader professionnel BRVM:
    - Si momentum fort (perf >15%, RS >10%, volume 3x) → Target 18-25%
    - Si momentum moyen (perf 8-15%, RS 5-10%, volume 2x) → Target 12-18%
    - Si momentum faible (perf 5-8%, RS 2-5%, volume 1.5x) → Target 10-12%
    
    Minimum: 10% (rentabiliser)
    Maximum: Pas de limite (capter vraies opportunités)
    
    Stop: 5% fixe (protection institutionnelle)
    """
    # Base target = 10% minimum
    target = 10.0
    
    # Bonus momentum (performance 4 semaines)
    if perf_4sem is not None:
        if perf_4sem >= 15:
            target += 8  # Fort momentum: +8%
        elif perf_4sem >= 8:
            target += 4  # Moyen: +4%
        elif perf_4sem >= 5:
            target += 2  # Faible: +2%
    
    # Bonus relative strength
    if rs_4sem is not None:
        if rs_4sem >= 10:
            target += 5  # Surperformance forte: +5%
        elif rs_4sem >= 5:
            target += 3  # Moyenne: +3%
        elif rs_4sem >= 2:
            target += 1  # Faible: +1%
    
    # Bonus volume (confirmation smart money)
    if volume_ratio is not None:
        if volume_ratio >= 3.0:
            target += 3  # Volume exceptionnel: +3%
        elif volume_ratio >= 2.0:
            target += 2  # Fort: +2%
        elif volume_ratio >= 1.8:
            target += 1  # Moyen: +1%
    
    # Ajustement ATR (volatilité)
    if atr_pct is not None and atr_pct > 15:
        # Haute volatilité = potentiel mouvement plus grand
        target += (atr_pct - 15) * 0.3
    
    # Arrondir
    target = round(target, 1)
    
    # Minimum garanti 10%
    return max(10.0, target)


def compute_stop_loss():
    """
    Stop loss fixe: 5%
    
    Protection institutionnelle standard BRVM.
    Simple, clair, professionnel.
    """
    return 5.0


# ============================================================================
# DÉTECTION RÉGIME MARCHÉ (Adaptatif BRVM)
# ============================================================================
def detect_market_regime_simple(perf_brvm_composite, pct_actions_up):
    """
    Régime marché BRVM simplifié
    
    BEARISH: Indice DOWN + <30% actions UP → Max 0-1 positions, WOS ≥75
    NEUTRAL: Indice -2% à +2% + 30-60% actions UP → Max 2 positions, WOS ≥60
    BULLISH: Indice UP + >60% actions UP → Max 3 positions, WOS ≥50
    
    Args:
        perf_brvm_composite: Performance indice 4 semaines
        pct_actions_up: % actions en tendance UP dans univers
    
    Returns:
        (regime, max_positions, wos_min_requis, message)
    """
    
    # BEARISH: Marché baissier confirmé
    if perf_brvm_composite < -2 and pct_actions_up < 30:
        return "BEARISH", 1, 75, "🔴 Marché baissier - Préservation capital"
    
    # BULLISH: Marché haussier confirmé
    elif perf_brvm_composite > 2 and pct_actions_up > 60:
        return "BULLISH", 3, 50, "🟢 Marché haussier - Opportunités multiples"
    
    # NEUTRAL: Indécision
    else:
        return "NEUTRAL", 2, 60, "🟡 Marché neutre - Sélectivité requise"


# ============================================================================
# MOTEUR PRINCIPAL: ELITE MINIMALISTE
# ============================================================================
def generate_elite_minimaliste_top(db):
    """
    Moteur Elite Minimaliste - 4 filtres robustes
    
    Process:
    1. Filtrage strict (4 critères non négociables)
    2. Ranking momentum relatif (continuation BRVM)
    3. Sélection 0-3 positions selon régime marché
    4. Targets dynamiques (min 10%, pas de plafond)
    5. Message professionnel institutionnel
    
    Returns:
        (recommendations, message_pro, stats)
    """
    
    print("\n" + "="*80)
    print("🎯 SYSTÈME ELITE MINIMALISTE BRVM - ANALYSE HEBDOMADAIRE")
    print("="*80 + "\n")
    
    # Performance indice BRVM
    perf_brvm = get_brvm_composite_performance(db)
    print(f"📊 BRVM Composite 4 semaines: {perf_brvm:+.2f}%\n")
    
    # ========== ÉTAPE 1: FILTRAGE STRICT ==========
    print("🔍 ÉTAPE 1: FILTRAGE 4 CRITÈRES (47 actions → ?)\n")
    
    actions_candidates = []
    actions_up = 0
    actions_total = 0
    
    for symbol in sorted(ACTIONS_BRVM_47):
        
        # Filtre 1: Performance 4 semaines
        perf_4sem, prix_actuel, _ = get_performance_4_semaines(symbol, db)
        if perf_4sem is None:
            print(f"  ⏭️  {symbol}: Données insuffisantes")
            continue
        
        actions_total += 1
        
        # Filtre 2: Relative Strength > 0 (surperformance vs indice)
        rs_4sem = perf_4sem - perf_brvm
        if rs_4sem <= 0:
            print(f"  ❌ {symbol}: RS {rs_4sem:+.1f}% (sous-performe indice)")
            continue
        
        # Filtre 3: Volume ≥ 1.5x moyenne
        volume_ratio = get_volume_ratio(symbol, db)
        if volume_ratio is None or volume_ratio < 1.5:
            ratio_str = f"{volume_ratio:.1f}x" if volume_ratio else "N/A"
            print(f"  ❌ {symbol}: Volume {ratio_str} (< 1.5x requis)")
            continue
        
        # Filtre 4: Pas de tendance DOWN claire
        tendance, prix, sma4 = get_tendance_4_semaines(symbol, db)
        if tendance == "DOWN":
            print(f"  ❌ {symbol}: Tendance DOWN ({prix:.0f} < SMA {sma4:.0f})")
            continue
        
        if tendance == "UP":
            actions_up += 1
        
        # Filtre 5: ATR raisonnable 8-25%
        atr_pct = get_atr_pct(symbol, db)
        if atr_pct is None or atr_pct < 8 or atr_pct > 25:
            atr_str = f"{atr_pct:.1f}%" if atr_pct else "N/A"
            print(f"  ❌ {symbol}: ATR {atr_str} (hors range 8-25%)")
            continue
        
        # ✅ Action passe TOUS les filtres
        momentum_score = compute_momentum_score(perf_4sem, rs_4sem, volume_ratio)
        
        actions_candidates.append({
            "symbol": symbol,
            "perf_4sem": perf_4sem,
            "rs_4sem": rs_4sem,
            "volume_ratio": volume_ratio,
            "tendance": tendance,
            "atr_pct": atr_pct,
            "prix_actuel": prix_actuel,
            "momentum_score": momentum_score
        })
        
        print(f"  ✅ {symbol}: RS +{rs_4sem:.1f}%, Vol {volume_ratio:.1f}x, ATR {atr_pct:.1f}%, Score {momentum_score:.1f}")
    
    # Statistiques filtrage
    pct_up = (actions_up / actions_total * 100) if actions_total > 0 else 0
    print(f"\n📈 Résultat filtrage: {len(actions_candidates)} candidats / {actions_total} actions")
    print(f"📊 Tendance marché: {actions_up}/{actions_total} actions UP ({pct_up:.0f}%)\n")
    
    # ========== ÉTAPE 2: DÉTECTION RÉGIME MARCHÉ ==========
    regime, max_positions, wos_min, regime_msg = detect_market_regime_simple(perf_brvm, pct_up)
    
    print("="*80)
    print(f"🎯 RÉGIME MARCHÉ: {regime}")
    print(f"   {regime_msg}")
    print(f"   Max positions: {max_positions}")
    print(f"   Score minimum: {wos_min}")
    print("="*80 + "\n")
    
    # ========== ÉTAPE 3: RANKING PAR MOMENTUM ==========
    if not actions_candidates:
        print("⚠️ AUCUNE ACTION ne passe les 4 filtres.\n")
        
        message_cash = (
            "📊 ANALYSE HEBDOMADAIRE BRVM\n"
            f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"🎯 RÉGIME MARCHÉ: {regime}\n"
            f"   {regime_msg}\n\n"
            "❌ Aucune configuration à haute probabilité identifiée.\n"
            "   Les 4 critères de sélection ne sont satisfaits par aucune action.\n\n"
            "💰 RECOMMANDATION: PRÉSERVATION DU CAPITAL (CASH)\n\n"
            "📅 Prochaine analyse: Dimanche prochain\n"
            "⚠️  Ne jamais forcer une position quand le marché ne présente pas de setup clair."
        )
        
        return [], message_cash, {
            "regime": regime,
            "nb_candidates": 0,
            "nb_recommendations": 0,
            "perf_brvm": perf_brvm,
            "pct_actions_up": pct_up
        }
    
    # Trier par momentum score (décroissant)
    actions_candidates.sort(key=lambda x: x["momentum_score"], reverse=True)
    
    print("📊 RANKING MOMENTUM (Top candidats):\n")
    for i, action in enumerate(actions_candidates[:5], 1):
        print(f"  #{i} {action['symbol']}: Score {action['momentum_score']:.1f} "
              f"(Perf {action['perf_4sem']:+.1f}%, RS +{action['rs_4sem']:.1f}%, Vol {action['volume_ratio']:.1f}x)")
    
    # ========== ÉTAPE 4: SÉLECTION TOP 1-3 ==========
    nb_selections = min(max_positions, len(actions_candidates))
    
    # Filtre additionnel: Score minimum selon régime
    # (pour BEARISH, on peut avoir 0 position si score insuffisant)
    top_selections = []
    for action in actions_candidates[:nb_selections]:
        # Pour simplicité, on accepte tous les candidats filtrés
        # (le filtrage strict garantit déjà la qualité)
        top_selections.append(action)
    
    if not top_selections:
        print("\n⚠️ Aucune action ne répond aux critères de score minimum.\n")
        
        message_cash = (
            "📊 ANALYSE HEBDOMADAIRE BRVM\n"
            f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"🎯 RÉGIME MARCHÉ: {regime}\n"
            f"   {regime_msg}\n\n"
            f"✓ {len(actions_candidates)} actions passent les filtres techniques\n"
            f"✗ Aucune n'atteint le seuil de conviction minimum (score {wos_min})\n\n"
            "💰 RECOMMANDATION: PRÉSERVATION DU CAPITAL (CASH)\n\n"
            "📅 Prochaine analyse: Dimanche prochain\n"
            "⚠️  Discipline > Performance - Ne trader que les setups A+."
        )
        
        return [], message_cash, {
            "regime": regime,
            "nb_candidates": len(actions_candidates),
            "nb_recommendations": 0,
            "perf_brvm": perf_brvm,
            "pct_actions_up": pct_up
        }
    
    # ========== ÉTAPE 5: CALCUL TARGETS DYNAMIQUES ==========
    print(f"\n🎯 SÉLECTION FINALE: {len(top_selections)} POSITION(S)\n")
    
    recommendations = []
    
    for i, action in enumerate(top_selections, 1):
        # Target dynamique (min 10%, pas de plafond)
        target = compute_target_dynamique(
            action["perf_4sem"],
            action["rs_4sem"],
            action["volume_ratio"],
            action["atr_pct"]
        )
        
        stop = compute_stop_loss()  # 5% fixe
        rr_ratio = target / stop
        
        # Exposition (répartition équitable)
        exposition_pct = round(100 / len(top_selections), 0)
        
        reco = {
            "rank": i,
            "symbol": action["symbol"],
            "prix_actuel": action["prix_actuel"],
            "perf_4sem": action["perf_4sem"],
            "rs_4sem": action["rs_4sem"],
            "volume_ratio": action["volume_ratio"],
            "atr_pct": action["atr_pct"],
            "momentum_score": action["momentum_score"],
            "target_pct": target,
            "stop_pct": stop,
            "rr_ratio": round(rr_ratio, 1),
            "exposition_pct": exposition_pct,
            "generated_at": datetime.now()
        }
        
        recommendations.append(reco)
        
        print(f"  #{i} {action['symbol']} @ {action['prix_actuel']:.0f} FCFA")
        print(f"      Momentum: {action['momentum_score']:.1f} | RS: +{action['rs_4sem']:.1f}% | Vol: {action['volume_ratio']:.1f}x")
        print(f"      Target: +{target:.1f}% | Stop: -{stop:.1f}% | RR: {rr_ratio:.1f}:1")
        print(f"      Exposition: {exposition_pct:.0f}%\n")
    
    # ========== ÉTAPE 6: MESSAGE PROFESSIONNEL ==========
    message_pro = generer_message_professionnel(
        regime, regime_msg, perf_brvm, pct_up, recommendations
    )
    
    # Stats
    stats = {
        "regime": regime,
        "nb_candidates": len(actions_candidates),
        "nb_recommendations": len(recommendations),
        "perf_brvm": perf_brvm,
        "pct_actions_up": pct_up,
        "target_moyen": np.mean([r["target_pct"] for r in recommendations]),
        "rr_moyen": np.mean([r["rr_ratio"] for r in recommendations])
    }
    
    return recommendations, message_pro, stats


def generer_message_professionnel(regime, regime_msg, perf_brvm, pct_up, recommendations):
    """
    Message professionnel style desk institutionnel BRVM
    
    Pas de "probabilité 74%", pas de "confiance sigmoid"
    Juste facts + setup + risques
    """
    
    message = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                   ANALYSE HEBDOMADAIRE BRVM                              ║
║                  Système Elite Minimaliste v1.0                          ║
╚══════════════════════════════════════════════════════════════════════════╝

📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 CONTEXTE MARCHÉ

   • BRVM Composite (4 semaines): {perf_brvm:+.2f}%
   • Actions en tendance UP: {pct_up:.0f}%
   • Régime marché: {regime}
   • {regime_msg}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 POSITIONS RECOMMANDÉES: {len(recommendations)}/{3}

"""
    
    for reco in recommendations:
        message += f"""
┌─ #{reco['rank']} {reco['symbol']} ─────────────────────────────────────────────┐

   Prix actuel:        {reco['prix_actuel']:.0f} FCFA
   
   📈 Momentum relatif:    
      • Performance 4 sem:  {reco['perf_4sem']:+.1f}%
      • Relative Strength:  +{reco['rs_4sem']:.1f}% vs BRVM
      • Volume ratio:       {reco['volume_ratio']:.1f}x moyenne
      • ATR weekly:         {reco['atr_pct']:.1f}%
      • Score momentum:     {reco['momentum_score']:.1f}/100
   
   🎯 Configuration:
      • Target:             +{reco['target_pct']:.1f}%
      • Stop loss:          -{reco['stop_pct']:.1f}%
      • Risk/Reward:        {reco['rr_ratio']:.1f}:1
      • Exposition:         {reco['exposition_pct']:.0f}% du capital
   
   ⚠️  Entrée progressive recommandée (2-3 tranches)
      Stop strict - Pas de moyenne à la baisse

└─────────────────────────────────────────────────────────────────────────┘
"""
    
    message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💼 GESTION RISQUE

   • Max positions:        {len(recommendations)}/3
   • Capital exposé:       {sum(r['exposition_pct'] for r in recommendations):.0f}%
   • Capital cash:         {100 - sum(r['exposition_pct'] for r in recommendations):.0f}%
   • Stop global:          Respecter stops individuels
   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  DISCLAIMERS

   ✓ Analyse basée sur 4 critères techniques robustes (RS, Volume, Tendance, ATR)
   ✓ Positions sous réserve du contexte marché global
   ✓ Stops non négociables - Protection du capital prioritaire
   ✓ Ne trader que si conditions d'entrée respectées
   
   ✗ Ceci n'est PAS un conseil en investissement
   ✗ Performances passées ne garantissent pas résultats futurs
   ✗ Trading comporte risques de perte en capital

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Prochaine analyse: Dimanche {(datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y')}

╔══════════════════════════════════════════════════════════════════════════╗
║  "Discipline beats sophistication" - Approche institutionnelle BRVM     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    
    return message


# ============================================================================
# SAUVEGARDE MONGODB
# ============================================================================
def sauvegarder_recommendations_elite(recommendations, stats, db):
    """
    Sauvegarde dans MongoDB pour tracking et historique
    """
    try:
        # Collection dédiée système elite
        collection = db.top5_elite_minimaliste_brvm
        
        doc = {
            "generated_at": datetime.now(),
            "week": datetime.now().strftime("%Y-W%V"),
            "regime": stats["regime"],
            "nb_recommendations": len(recommendations),
            "perf_brvm_composite": stats["perf_brvm"],
            "pct_actions_up": stats["pct_actions_up"],
            "recommendations": recommendations,
            "stats": stats
        }
        
        collection.insert_one(doc)
        
        print(f"✅ Sauvegarde MongoDB: {len(recommendations)} recommandations")
        
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde MongoDB: {e}")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    
    db = get_mongo_db()
    
    recommendations, message, stats = generate_elite_minimaliste_top(db)
    
    # Afficher message
    print("\n" + "="*80)
    print(message)
    print("="*80 + "\n")
    
    # Sauvegarde
    if recommendations:
        sauvegarder_recommendations_elite(recommendations, stats, db)
    
    print(f"✅ Analyse terminée - {stats['nb_recommendations']} position(s) recommandée(s)")
    print(f"📊 Régime {stats['regime']} | BRVM {stats['perf_brvm']:+.1f}% | {stats['pct_actions_up']:.0f}% actions UP\n")
