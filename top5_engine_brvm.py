###############################################################################
# DEPRECATED — NE PAS UTILISER EN PRODUCTION
###############################################################################
# Ce fichier est la version V1 LEGACY du TOP5 engine (formule WOS + sigmoid).
# Il a été remplacé par top5_engine_final.py (V2.5+) qui intègre :
#   - Multi-Factor Engine (MF 5 facteurs cross-sectionnels)
#   - Stop ATR réel × 1.5
#   - Vol targeting par régime de marché
#   - Circuit breaker + filtre corrélation + blacklist dynamique
#
# Pipelines de production :
#   lancer_recos_daily.py  → top5_engine_final.py --mode daily
#   lancer_recos_pro.py    → top5_engine_final.py
#   pipeline_brvm.py       → top5_engine_final.py
#
# Ce fichier est conservé UNIQUEMENT pour comparaison historique (comparer_systemes.py).
# Toute nouvelle fonctionnalité doit être ajoutée dans top5_engine_final.py.
###############################################################################
import warnings
warnings.warn(
    "top5_engine_brvm.py (V1 LEGACY) — utiliser top5_engine_final.py en production.",
    DeprecationWarning, stacklevel=2
)

from plateforme_centralisation.mongo import get_mongo_db
import math

# PHASE 5: Mapping secteurs BRVM (47 actions)
SECTEURS_BRVM = {
    # FINANCE
    "BICC": "FINANCE", "SGBC": "FINANCE", "CBIBF": "FINANCE", "BOAB": "FINANCE",
    "BOABF": "FINANCE", "BOAC": "FINANCE", "BOAM": "FINANCE", "BOAN": "FINANCE",
    "BOAS": "FINANCE", "ETIT": "FINANCE", "SIBC": "FINANCE", "SCRC": "FINANCE",
    "ABJC": "FINANCE", "BNBC": "FINANCE", "NSBC": "FINANCE", "PRSC": "FINANCE",
    
    # DISTRIBUTION
    "CIEC": "DISTRIBUTION", "FTSC": "DISTRIBUTION", "TTLC": "DISTRIBUTION",
    "SEMC": "DISTRIBUTION", "SHEC": "DISTRIBUTION", "STBC": "DISTRIBUTION",
    "SNTS": "DISTRIBUTION", "ORAC": "DISTRIBUTION", "NTLC": "DISTRIBUTION",
    
    # INDUSTRIE
    "SAFC": "INDUSTRIE", "PALC": "INDUSTRIE", "SICC": "INDUSTRIE",
    "CABC": "INDUSTRIE", "SMBC": "INDUSTRIE", "SLBC": "INDUSTRIE",
    "SPHC": "INDUSTRIE", "SVOC": "INDUSTRIE", "UNXC": "INDUSTRIE",
    "SOGC": "INDUSTRIE", "STAC": "INDUSTRIE", "CFAC": "INDUSTRIE",
    
    # AGRICULTURE
    "SAFH": "AGRICULTURE", "PALMH": "AGRICULTURE", "SIVC": "AGRICULTURE",
    
    # SERVICES
    "SDSC": "SERVICES", "ONTBF": "SERVICES", "ORGT":"SERVICES",
    "UNLC": "SERVICES", "TTLS": "SERVICES",
    
    # AUTRES
    "LNBF": "AUTRES", "NSBC": "AUTRES"
}


def sigmoid_probability(wos_normalized):
    """
    PHASE 7: Conversion score WOS en probabilité Top 5
    Fonction sigmoid pour calibration probabiliste
    """
    # Sigmoid centré sur 0.5 avec pente ajustable
    prob = 1 / (1 + math.exp(-5 * (wos_normalized - 0.5)))
    return round(prob, 3)


def compute_capture_rate(top5_symbols, db):
    """
    PHASE 9: Mesure d'edge - Capture Rate
    Calcule combien d'actions du vrai Top 5 performance on a capturé
    
    Returns:
        capture_rate: nombre d'actions réelles Top 5 capturées / 5
        real_top5: liste des 5 meilleures performances réelles
    """
    try:
        # Récupérer performances réelles semaine écoulée
        from datetime import datetime, timedelta
        
        # Toutes actions avec variation semaine -1
        week_ago = datetime.now() - timedelta(days=7)
        week_str = week_ago.strftime("%Y-W%V")
        
        performances = list(db.prices_weekly.find(
            {"week": week_str},
            {"symbol": 1, "variation_pct": 1}
        ).sort("variation_pct", -1).limit(10))
        
        if len(performances) < 5:
            print("[INFO] Pas assez de données performance pour capture rate")
            return 0.0, []
        
        # Top 5 réel
        real_top5 = [p["symbol"] for p in performances[:5]]
        
        # Combien capturés ?
        captured = sum(1 for sym in top5_symbols if sym in real_top5)
        capture_rate = captured / 5
        
        return capture_rate, real_top5
        
    except Exception as e:
        print(f"[ERREUR Capture Rate] {e}")
        return 0.0, []


def detect_market_regime(recommendations):
    """
    DISCIPLINE INSTITUTIONNELLE: Détecter régime de marché (BULLISH/NEUTRAL/BEARISH)
    
    Expert 30 ans BRVM: 
    - MODE ELITE MINIMALISTE (14 semaines données):
      * BEARISH → max 1 position (survival mode)
      * NEUTRAL → max 2 positions (sélectif)
      * BULLISH → max 3 positions (opportuniste)
    
    - MODE COMPLET (52+ semaines données):
      * BEARISH → max 2 positions, WOS ≥70
      * NEUTRAL → max 4 positions, WOS ≥50  
      * BULLISH → max 5 positions, WOS ≥30
    
    Être élite = savoir ne pas trader quand le marché est mauvais
    """
    if not recommendations:
        return "NEUTRAL", 2, 50, "⚠️ Aucune donnée", 50, False
    
    # Détecter si mode elite depuis recommandations
    mode_elite = recommendations[0].get("mode_elite", False) if recommendations else False
    
    # Compter tendances UP/DOWN depuis raisons/details
    total = len(recommendations)
    down_count = 0
    up_count = 0
    
    for r in recommendations:
        raisons = r.get("raisons", [])
        details_text = " ".join(str(raisons))
        
        if "Tendance baissière" in details_text or "baissière (DOWN)" in details_text or "DOWN" in details_text:
            down_count += 1
        elif "Tendance haussière" in details_text or "haussière (UP)" in details_text or "UP" in details_text:
            up_count += 1
    
    down_pct = (down_count / total) * 100 if total > 0 else 0
    
    # Détermination régime avec limites adaptées au mode
    if down_pct >= 70:
        regime = "BEARISH"
        if mode_elite:
            max_positions = 1
            wos_min_threshold = 75
            message = f"🔴 MARCHÉ BAISSIER ({down_pct:.0f}% DOWN) + MODE ELITE → Max 1 position, RS ≥+5%"
        else:
            max_positions = 2
            wos_min_threshold = 70
            message = f"🔴 MARCHÉ BAISSIER ({down_pct:.0f}% DOWN) → Défensif: max 2 positions, WOS ≥70"
    elif down_pct >= 50:
        regime = "NEUTRAL"
        if mode_elite:
            max_positions = 2
            wos_min_threshold = 50
            message = f"🟡 MARCHÉ NEUTRE ({down_pct:.0f}% DOWN) + MODE ELITE → Max 2 positions, RS ≥+3%"
        else:
            max_positions = 4
            wos_min_threshold = 50
            message = f"🟡 MARCHÉ NEUTRE ({down_pct:.0f}% DOWN) → Prudent: max 4 positions, WOS ≥50"
    else:
        regime = "BULLISH"
        if mode_elite:
            max_positions = 3
            wos_min_threshold = 30
            message = f"🟢 MARCHÉ HAUSSIER ({down_pct:.0f}% DOWN) + MODE ELITE → Max 3 positions, RS ≥+2%"
        else:
            max_positions = 5
            wos_min_threshold = 30
            message = f"🟢 MARCHÉ HAUSSIER ({down_pct:.0f}% DOWN) → Agressif: max 5 positions, WOS ≥30"
    
    return regime, max_positions, wos_min_threshold, message, down_pct, mode_elite


def run_top5_engine():
    _, db = get_mongo_db()

    print("\n" + "="*80)
    print("[TOP5 ENGINE EXPERT] MOTEUR PRÉDICTIF HEBDOMADAIRE BRVM")
    print("="*80 + "\n")

    # Récupérer TOUTES recommandations (pas seulement BUY)
    # PHASE 2: Trading relatif = Top 5 performers parmi toutes actions
    # FIX: exclure les décisions archivées (sinon doublons critiques)
    recos_raw = list(db.decisions_finales_brvm.find({
        "horizon": "SEMAINE",
        "archived": {"$ne": True}
    }))

    # FIX: déduplication par symbol (garder le WOS/RS le plus élevé par symbole)
    seen_symbols = {}
    for r in recos_raw:
        sym = r.get("symbol", "")
        score_key = r.get("wos") or r.get("rs_4sem") or 0
        if sym not in seen_symbols or score_key > (seen_symbols[sym].get("wos") or seen_symbols[sym].get("rs_4sem") or 0):
            seen_symbols[sym] = r
    recos = list(seen_symbols.values())

    if not recos:
        print("[ERREUR] Aucune recommandation disponible")
        print("Astuce: Lancer d'abord decision_finale_brvm.py\n")
        return
    
    print(f"[INFO] {len(recos)} recommandations trouvées\n")
    
    # DISCIPLINE INSTITUTIONNELLE: Détection régime de marché
    print("="*80)
    print("[DISCIPLINE] DÉTECTION RÉGIME DE MARCHÉ")
    print("="*80 + "\n")
    
    regime, max_positions, wos_min_threshold, regime_message, down_pct, mode_elite = detect_market_regime(recos)
    
    print(regime_message)
    if mode_elite:
        print("\n🎯 MODE ELITE MINIMALISTE ACTIVÉ (14 semaines données)")
        print("   Priorité: CRÉDIBILITÉ > Performance")
        print("   Critère ranking: Relative Strength 4 semaines")
        print("   Positions limitées: 1-3 selon marché\n")
    
    print(f"\nStatistiques marché:")
    print(f"  - Tendance DOWN: {down_pct:.0f}%")
    print(f"  - Tendance UP:   {100-down_pct:.0f}%")
    print(f"  - Max positions autorisées: {max_positions}")
    print(f"  - Seuil minimum: {'RS ≥ +2%' if mode_elite else f'WOS ≥ {wos_min_threshold}'}")
    print(f"\nDISCIPLINE EXPERT 30 ANS: {regime_message.split('→')[1].strip()}\n")
    
    # Filtrer par seuil minimum selon régime et mode
    if mode_elite:
        # Mode Elite: filtrer par RS 4 semaines minimum
        rs_min = 2.0 if regime == "BULLISH" else (3.0 if regime == "NEUTRAL" else 5.0)
        recos_filtered = [r for r in recos if r.get("rs_4sem", 0) >= rs_min]
        print(f"[FILTRE RS] {len(recos)} → {len(recos_filtered)} actions après seuil RS ≥{rs_min:.1f}%\n")
    else:
        # Mode Complet: filtrer par WOS minimum
        recos_filtered = [r for r in recos if r.get("wos", 0) >= wos_min_threshold]
        print(f"[FILTRE WOS] {len(recos)} → {len(recos_filtered)} actions après seuil WOS ≥{wos_min_threshold}\n")
    
    if not recos_filtered:
        print(f"⚠️  AUCUNE ACTION ne respecte le seuil {'RS' if mode_elite else 'WOS'} marché actuel")
        print(f"   → Marché {regime}: impossible de générer Top 5 de qualité")
        print("   → RECOMMANDATION EXPERT: Rester CASH cette semaine\n")
        return

    # PHASE 7: Normaliser pour probabilité
    if mode_elite:
        # Mode Elite: normaliser RS pour probabilité
        rs_values = [r.get("rs_4sem", 0) for r in recos_filtered]
        rs_min_val = min(rs_values) if rs_values else 0
        rs_max_val = max(rs_values) if rs_values else 10
        rs_range = rs_max_val - rs_min_val if rs_max_val > rs_min_val else 1
        
        for r in recos_filtered:
            rs = r.get("rs_4sem", 0)
            rs_norm = (rs - rs_min_val) / rs_range  # 0-1
            r["rs_normalized"] = round(rs_norm, 3)
            r["proba_top5"] = sigmoid_probability(rs_norm)
    else:
        # Mode Complet: normaliser WOS
        wos_values = [r.get("wos", 0) for r in recos_filtered]
        wos_min = min(wos_values) if wos_values else 0
        wos_max = max(wos_values) if wos_values else 100
        wos_range = wos_max - wos_min if wos_max > wos_min else 1
        
        for r in recos_filtered:
            wos = r.get("wos", 0)
            wos_norm = (wos - wos_min) / wos_range  # 0-1
            r["wos_normalized"] = round(wos_norm, 3)
            r["proba_top5"] = sigmoid_probability(wos_norm)
    
    # Tri par critère approprié au mode
    if mode_elite:
        # Mode Elite: trier par RS 4 semaines (continuation momentum)
        recos_sorted = sorted(
            recos_filtered,
            key=lambda x: x.get("rs_4sem", 0),
            reverse=True
        )
        print(f"[TRI ELITE] Ranking par Relative Strength 4 semaines (continuation)\n")
    else:
        # Mode Complet: trier par WOS (système sophistiqué)
        recos_sorted = sorted(
            recos_filtered,
            key=lambda x: x.get("wos", 0),
            reverse=True
        )
        print(f"[TRI COMPLET] Ranking par WOS Top5 (moteur prédictif)\n")
    
    # PHASE 5: Contrainte sectorielle - Max 3 actions/secteur
    MAX_PAR_SECTEUR = 3
    secteur_count = {}
    top_candidates = []
    
    print("[PHASE 5] Application contrainte sectorielle (max 3/secteur):\n")
    
    for r in recos_sorted:
        symbol = r.get("symbol", "")
        secteur = SECTEURS_BRVM.get(symbol, "AUTRES")
        
        # Compter actions déjà prises dans ce secteur
        count_secteur = secteur_count.get(secteur, 0)
        
        if count_secteur < MAX_PAR_SECTEUR:
            top_candidates.append(r)
            secteur_count[secteur] = count_secteur + 1
            status = f"✓ Ajouté ({count_secteur + 1}/{MAX_PAR_SECTEUR} {secteur})"
        else:
            status = f"✗ Exclu (quota {secteur} atteint: {MAX_PAR_SECTEUR}/{MAX_PAR_SECTEUR})"
        
        if mode_elite:
            print(f"  {symbol:6s} | RS {r.get('rs_4sem', 0):+6.1f}% | Secteur {secteur:12s} | {status}")
        else:
            print(f"  {symbol:6s} | WOS {r.get('wos', 0):6.1f} | Secteur {secteur:12s} | {status}")
        
        # Stop dès qu'on a atteint max_positions (adapté au régime de marché)
        if len(top_candidates) >= max_positions:
            break
    
    # Top final (limité par régime de marché)
    top_final = top_candidates[:max_positions]
    
    if len(top_final) < max_positions:
        print(f"\n⚠️  Seulement {len(top_final)} actions qualifiées (contraintes: secteur + régime {regime})")
        if len(top_final) == 0:
            print("   → RECOMMANDATION EXPERT: Rester CASH cette semaine\n")
            return
        else:
            print(f"   → Position réduite acceptable en marché {regime}\n")

    # PHASE 9: Mesure d'edge (capture rate)
    top_symbols = [r["symbol"] for r in top_final]
    capture_rate, real_top5 = compute_capture_rate(top_symbols, db)
    
    print("\n" + "="*80)
    print("[PHASE 9] MESURE D'EDGE - VALIDATION PERFORMANCE")
    print("="*80)
    print(f"\nCapture Rate: {capture_rate * 100:.0f}% ({int(capture_rate * 5)}/5 actions réelles capturées)")
    
    if real_top5:
        print(f"Top 5 réel semaine précédente: {', '.join(real_top5)}")
        print(f"Top {len(top_final)} recommandé: {', '.join(top_symbols)}")
        
        captured_symbols = [s for s in top_symbols if s in real_top5]
        if captured_symbols:
            print(f"✓ Actions capturées: {', '.join(captured_symbols)}")
        else:
            print("✗ Aucune action capturée (edge faible cette semaine)")
    
    # Affichage Top final avec probabilités
    print("\n" + "="*80)
    print(f"[TOP {len(top_final)} HEBDOMADAIRE] RECOMMANDATIONS EXPERT - RÉGIME {regime}")
    print("="*80 + "\n")

    for i, r in enumerate(top_final, start=1):
        secteur = SECTEURS_BRVM.get(r["symbol"], "AUTRES")
        
        if mode_elite:
            # Mode Elite: afficher RS + performances
            print(
                f"{i}. {r['symbol']:6s} | "
                f"Secteur {secteur:12s} | "
                f"RS {r.get('rs_4sem', 0):+6.1f}% | "
                f"Perf {r.get('perf_action_4sem', 0):+5.1f}% | "
                f"Gain {r.get('gain_attendu', 0):5.1f}% | "
                f"Conf {r.get('confidence', 0):4.1f}% | "
                f"RR {r.get('rr', 0):4.2f}"
            )
        else:
            # Mode Complet: afficher WOS + probabilité
            print(
                f"{i}. {r['symbol']:6s} | "
                f"Secteur {secteur:12s} | "
                f"WOS {r.get('wos', 0):6.1f} | "
                f"Proba {r.get('proba_top5', 0)*100:4.1f}% | "
                f"Gain {r.get('gain_attendu', 0):5.1f}% | "
                f"Conf {r.get('confidence', 0):4.1f}% | "
                f"RR {r.get('rr', 0):4.2f}"
            )

    # Sauvegarde dédiée pour le dashboard
    db.top5_weekly_brvm.delete_many({})
    for rank, r in enumerate(top_final, start=1):
        r["rank"] = rank
        r["secteur"] = SECTEURS_BRVM.get(r["symbol"], "AUTRES")
        r["capture_rate_semaine"] = capture_rate  # Historique performance
        r["market_regime"] = regime  # Nouveau: contexte marché
        r["max_positions"] = max_positions  # Nouveau: discipline
        db.top5_weekly_brvm.insert_one(r)

    print("\n[OK] TOP5 généré et sauvegardé pour le dashboard")
    print(f"     Capture Rate historique: {capture_rate * 100:.0f}%")
    print(f"     Diversification: {len(secteur_count)} secteurs représentés\n")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_top5_engine()
