"""
Debug simplifié - Compter les actions qui passent chaque filtre
"""
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n=== 🔍 ANALYSE DES FILTRES SUR 47 ACTIONS ===\n")

analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))
print(f"Total actions disponibles: {len(analyses)}\n")

stats = {
    "total": len(analyses),
    "liquidite_ok": 0,
    "tendance_ok": 0,
    "rsi_ok": 0,
    "volume_actuel_ok": 0,
    "volatilite_ok": 0,
    "nlp_ok": 0,
    "wos_ok": 0,
    "rr_ok": 0,
    "er_ok": 0,
    "classe_ab": 0
}

for doc in analyses:
    attrs = doc.get("attrs", {})
    symbol = attrs.get("symbol")
    
    # Liquidité
    volume = attrs.get("volume_moyen", 0)
    spread = attrs.get("spread", 0)
    seances_sans_tx = attrs.get("seances_sans_transaction", 0)
    if volume >= 5000 and spread <= 5 and seances_sans_tx == 0:
        stats["liquidite_ok"] += 1
    else:
        continue
    
    # Tendance
    sma5 = attrs.get("SMA5", 0)
    sma10 = attrs.get("SMA10", 0)
    prix = attrs.get("prix_actuel", attrs.get("close", 0))
    if sma5 > sma10 and prix > sma10:
        stats["tendance_ok"] += 1
    else:
        continue
    
    # RSI
    rsi = attrs.get("rsi", 0)
    if 30 <= rsi <= 45:
        stats["rsi_ok"] += 1
    else:
        continue
    
    # Volume actuel
    volume_actuel = attrs.get("volume", 0)
    if volume_actuel >= 1.3 * volume:
        stats["volume_actuel_ok"] += 1
    else:
        continue
    
    # Volatilité
    prices = attrs.get("close_prices", [])
    if prices and len(prices) >= 15:
        trs = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        atr = sum(trs[-14:]) / 14
        atr_pct = round(100 * atr / prix, 2) if prix else 0
        if 8 <= atr_pct <= 18:
            stats["volatilite_ok"] += 1
        else:
            continue
    else:
        continue
    
    # NLP
    score_sem = attrs.get("score_semantique_ct", 0)
    nlp_flag = attrs.get("nlp_flag", "NEUTRAL")
    if score_sem > -20 and nlp_flag not in ["VERY_NEGATIVE", "ALERTE", "SUSPENSION"]:
        stats["nlp_ok"] += 1
    else:
        continue
    
    # WOS
    score_tendance = 100 if sma5 > sma10 else 0
    score_rsi = 100 - abs(37.5 - rsi) * 4
    score_volume = min(100, 100 * (volume_actuel / (1.3 * volume)))
    wos = 0.45*score_tendance + 0.25*score_rsi + 0.20*score_volume + 0.10*max(score_sem, 0)
    if wos >= 70:
        stats["wos_ok"] += 1
        print(f"✓ {symbol}: WOS={wos:.1f}, RSI={rsi}, Vol ratio={volume_actuel/volume:.2f}")
    else:
        continue
    
    # Stop & Target
    stop_pct = max(1.2 * atr_pct, 5)
    target_pct = 2.2 * atr_pct
    rr = target_pct / stop_pct if stop_pct else 0
    if rr >= 2:
        stats["rr_ok"] += 1
    else:
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
    if expected_return > 0:
        stats["er_ok"] += 1
    else:
        continue
    
    # Classement
    if wos >= 80 and rr >= 2.5 and expected_return > 10:
        classe = "A"
    elif 70 <= wos < 80 and rr >= 2 and expected_return > 5:
        classe = "B"
    else:
        classe = "C"
    
    if classe in ["A", "B"]:
        stats["classe_ab"] += 1
        print(f"  ✅ {symbol}: Classe {classe} | WOS={wos:.1f} | RR={rr:.2f} | ER={expected_return:.2f}%")

print(f"\n{'='*60}")
print(f"STATISTIQUES DES FILTRES:")
print(f"{'='*60}")
print(f"Total actions:                {stats['total']}")
print(f"Liquidité OK:                 {stats['liquidite_ok']}")
print(f"Tendance OK:                  {stats['tendance_ok']}")
print(f"RSI OK (30-45):              {stats['rsi_ok']}")
print(f"Volume actuel OK (≥1.3x):    {stats['volume_actuel_ok']}")
print(f"Volatilité OK (8-18%):       {stats['volatilite_ok']}")
print(f"NLP OK (≥-20):               {stats['nlp_ok']}")
print(f"WOS OK (≥70):                {stats['wos_ok']}")
print(f"RR OK (≥2):                  {stats['rr_ok']}")
print(f"ER OK (>0):                  {stats['er_ok']}")
print(f"Classe A ou B:               {stats['classe_ab']}")
print(f"{'='*60}\n")
