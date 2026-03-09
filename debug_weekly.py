"""
Debug du moteur weekly - Analyse détaillée des filtres
"""
from plateforme_centralisation.mongo import get_mongo_db

UNIVERSE = {"SONATEL", "CFAO", "SGB CI", "BOA CI", "PALM CI", "SIFCA", "TOTAL CI"}

_, db = get_mongo_db()

print("\n=== 🔍 DEBUG WEEKLY ENGINE ===\n")

analyses = list(db.curated_observations.find({
    "dataset": "AGREGATION_SEMANTIQUE_ACTION"
}))

print(f"📊 {len(analyses)} analyses IA disponibles\n")

for doc in analyses:
    attrs = doc.get("attrs", {})
    symbol = attrs.get("symbol")
    
    print(f"\n{'='*60}")
    print(f"🔹 {symbol}")
    print(f"{'='*60}")
    
    # Vérification univers
    in_universe = symbol in UNIVERSE
    print(f"✓ Univers autorisé: {in_universe}")
    if not in_universe:
        print(f"  ❌ BLOQUÉ: {symbol} n'est pas dans l'univers autorisé")
        continue
    
    # Liquidité
    volume = attrs.get("volume_moyen", 0)
    volume_ref = attrs.get("volume_ref", 1)
    spread = attrs.get("spread", 0)
    seances_sans_tx = attrs.get("seances_sans_transaction", 0)
    
    print(f"✓ Volume moyen: {volume} (seuil: 5000)")
    print(f"✓ Spread: {spread}% (seuil: 5%)")
    print(f"✓ Séances sans tx: {seances_sans_tx} (seuil: 0)")
    
    if volume < 5000:
        print(f"  ❌ BLOQUÉ: Volume insuffisant ({volume} < 5000)")
        continue
    if spread > 5:
        print(f"  ❌ BLOQUÉ: Spread trop élevé ({spread}% > 5%)")
        continue
    if seances_sans_tx > 0:
        print(f"  ❌ BLOQUÉ: Séances sans transaction ({seances_sans_tx} > 0)")
        continue
    
    # Tendance
    sma5 = attrs.get("SMA5", 0)
    sma10 = attrs.get("SMA10", 0)
    prix = attrs.get("prix_actuel", attrs.get("close", 0))
    
    print(f"✓ SMA5: {sma5}, SMA10: {sma10}")
    print(f"✓ Prix actuel: {prix}")
    print(f"✓ Tendance: SMA5 > SMA10: {sma5 > sma10}, Prix > SMA10: {prix > sma10}")
    
    if sma5 <= sma10:
        print(f"  ❌ BLOQUÉ: SMA5 <= SMA10 ({sma5} <= {sma10})")
        continue
    if prix <= sma10:
        print(f"  ❌ BLOQUÉ: Prix <= SMA10 ({prix} <= {sma10})")
        continue
    
    # RSI
    rsi = attrs.get("rsi", 0)
    print(f"✓ RSI: {rsi} (zone: 30-45)")
    
    if not (30 <= rsi <= 45):
        print(f"  ❌ BLOQUÉ: RSI hors zone ({rsi} pas dans [30, 45])")
        continue
    
    # Volume actuel
    volume_actuel = attrs.get("volume", 0)
    volume_ratio = volume_actuel / volume if volume else 0
    print(f"✓ Volume actuel: {volume_actuel} (ratio: {volume_ratio:.2f}, seuil: 1.3)")
    
    if volume_actuel < 1.3 * volume:
        print(f"  ❌ BLOQUÉ: Volume actuel insuffisant ({volume_ratio:.2f} < 1.3)")
        continue
    
    # Volatilité
    prices = attrs.get("close_prices", [])
    print(f"✓ Historique de prix disponible: {len(prices)} séances")
    
    if not prices or len(prices) < 15:
        print(f"  ❌ BLOQUÉ: Historique insuffisant pour ATR ({len(prices)} < 15)")
        continue
    
    trs = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
    atr = sum(trs[-14:]) / 14
    atr_pct = round(100 * atr / prix, 2) if prix else 0
    
    print(f"✓ ATR%: {atr_pct}% (zone: 8-18%)")
    
    if not (8 <= atr_pct <= 18):
        print(f"  ❌ BLOQUÉ: Volatilité hors zone ({atr_pct}% pas dans [8, 18])")
        continue
    
    # NLP / News
    score_sem = attrs.get("score_semantique_ct", 0)
    nlp_flag = attrs.get("nlp_flag", "NEUTRAL")
    
    print(f"✓ Score sémantique: {score_sem} (seuil: -20)")
    print(f"✓ NLP flag: {nlp_flag}")
    
    if score_sem <= -20:
        print(f"  ❌ BLOQUÉ: Score sémantique trop négatif ({score_sem} <= -20)")
        continue
    if nlp_flag in ["VERY_NEGATIVE", "ALERTE", "SUSPENSION"]:
        print(f"  ❌ BLOQUÉ: NLP flag négatif ({nlp_flag})")
        continue
    
    # WOS
    score_tendance = 100 if sma5 > sma10 else 0
    score_rsi = 100 - abs(37.5 - rsi) * 4
    score_volume = min(100, 100 * (volume_actuel / (1.3 * volume)))
    wos = 0.45*score_tendance + 0.25*score_rsi + 0.20*score_volume + 0.10*max(score_sem, 0)
    
    print(f"✓ WOS: {wos:.1f} (seuil: 70)")
    print(f"  - Tendance: {score_tendance}")
    print(f"  - RSI: {score_rsi:.1f}")
    print(f"  - Volume: {score_volume:.1f}")
    print(f"  - Sémantique: {max(score_sem, 0)}")
    
    if wos < 70:
        print(f"  ❌ BLOQUÉ: WOS insuffisant ({wos:.1f} < 70)")
        continue
    
    # Stop & Target
    stop_pct = max(1.2 * atr_pct, 5)
    target_pct = 2.2 * atr_pct
    rr = target_pct / stop_pct if stop_pct else 0
    
    print(f"✓ Stop: {stop_pct:.1f}%, Target: {target_pct:.1f}%")
    print(f"✓ RR: {rr:.2f} (seuil: 2)")
    
    if rr < 2:
        print(f"  ❌ BLOQUÉ: RR insuffisant ({rr:.2f} < 2)")
        continue
    
    # Expected Return
    confiance = min(95, round(wos, 1))
    if confiance > 85:
        proba = 0.78
    elif confiance > 80:
        proba = 0.70
    elif confiance > 75:
        proba = 0.62
    elif confiance >= 70:
        proba = 0.55
    else:
        proba = 0.45
    
    expected_return = (target_pct * proba) - (stop_pct * (1 - proba))
    
    print(f"✓ Expected Return: {expected_return:.2f}% (proba: {proba})")
    
    if expected_return <= 0:
        print(f"  ❌ BLOQUÉ: Expected Return négatif ou nul ({expected_return:.2f}%)")
        continue
    
    # Classement
    if wos >= 80 and rr >= 2.5 and expected_return > 10:
        classe = "A"
    elif 70 <= wos < 80 and rr >= 2 and expected_return > 5:
        classe = "B"
    else:
        classe = "C"
    
    print(f"✓ Classement: {classe}")
    
    if classe == "C":
        print(f"  ❌ BLOQUÉ: Trade de classe C non autorisé")
        continue
    
    print(f"\n  ✅ TRADE VALIDE - Classe {classe}")
    print(f"     Entry: {prix}, Target: {round(prix * (1 + target_pct/100), 2)}, Stop: {round(prix * (1 - stop_pct/100), 2)}")

print("\n" + "="*60)
print("Fin du diagnostic")
print("="*60 + "\n")
