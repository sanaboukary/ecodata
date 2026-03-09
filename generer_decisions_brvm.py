#!/usr/bin/env python3
"""
GÉNÉRATION DÉCISIONS BRVM - Standalone (sans Django, production-ready)
========================================================================

Version autonome pymongo pur qui GARANTIT la sauvegarde MongoDB
"""

from pymongo import MongoClient
from datetime import datetime
import statistics

def compute_atr_pct(prices, period=14):
    """ATR% simplifié pour BRVM"""
    if not prices or len(prices) < period + 1:
        return None
    
    true_ranges = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices)) if prices[i-1] > 0]
    
    if not true_ranges or len(true_ranges) < period:
        return None
    
    atr = sum(true_ranges[-period:]) / period
    current_price = prices[-1]
    
    if current_price <= 0:
        return None
    
    return round((atr / current_price) * 100, 2)


def compute_wos(sma5, sma10, rsi, volume, volume_ref, score_sem):
    """Weekly Opportunity Score"""
    # Valeurs par défaut robustes
    sma5 = sma5 or 0
    sma10 = sma10 or 0
    rsi = 50 if rsi is None else rsi
    volume = max(volume or 1000, 1000)
    volume_ref = volume_ref if volume_ref and volume_ref > 0 else volume
    score_sem = score_sem or 0
    
    score_tendance = 100 if sma5 > sma10 else 0
    score_rsi = max(0, min(100, 100 - abs(37.5 - rsi) * 3))
    score_volume = min(100, 100 * (volume / (1.3 * volume_ref)))
    
    return 0.45*score_tendance + 0.25*score_rsi + 0.20*score_volume + 0.10*max(score_sem, 0)


def generer_decisions():
    """Génère les décisions hebdomadaires BUY depuis analyses MongoDB"""
    
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["brvm_db"]
    
    print("\n" + "="*70)
    print(" GENERATION DECISIONS HEBDOMADAIRES BRVM ".center(70))
    print("="*70 + "\n")
    
    # Récupération analyses
    analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))
    print(f"[INFO] {len(analyses)} analyses techniques trouvees\n")
    
    if not analyses:
        print("[ERREUR] Aucune analyse disponible\n")
        print("   Executer d'abord : analyse_ia_simple.py\n")
        return
    
    # Nettoyage collection
    db.decisions_finales_brvm.delete_many({"horizon": "SEMAINE"})
    
    count = 0
    rejected = {"volume": 0, "spread": 0, "score": 0}
    
    for doc in analyses:
        attrs = doc.get("attrs", {})
        symbol = attrs.get("symbol")
        
        if not symbol:
            continue
        
        # Métriques de base
        volume = attrs.get("volume_moyen") or attrs.get("volume") or 5000
        spread = attrs.get("spread") or 5
        score_tech = attrs.get("score_ct") or attrs.get("score") or 0
        score_sem = attrs.get("score_semantique_ct") or attrs.get("score_semantique_mt") or 0
        
        # Filtres souples
        if volume < 1000:
            rejected["volume"] += 1
            continue
        
        if spread > 10:
            rejected["spread"] += 1
            continue
        
        if score_tech < 40:
            rejected["score"] += 1
            continue
        
        # Métriques techniques
        sma5 = attrs.get("SMA5") or 0
        sma10 = attrs.get("SMA10") or 0
        rsi = attrs.get("rsi") or 50
        prix = (attrs.get("prix_actuel") or attrs.get("close") or 
                attrs.get("prix") or attrs.get("last_price") or 5000)
        
        volume_ref = attrs.get("volume_moyen_20j")
        if not volume_ref or volume_ref <= 0:
            volume_ref = volume
        
        # Scores
        confiance = min(95, max(60, score_tech))
        wos = round(compute_wos(sma5, sma10, rsi, volume, volume_ref, score_sem), 1)
        
        # ATR% et prix cible/stop
        prices = attrs.get("close_prices") or []
        atr_pct = compute_atr_pct(prices, 14) if prices else None
        
        if atr_pct and atr_pct > 0:
            stop_pct = max(0.9 * atr_pct, 4.0)
            target_pct = 2.4 * atr_pct
            
            rr = target_pct / stop_pct if stop_pct > 0 else 0
            if rr < 2.0:
                target_pct = 2.0 * stop_pct
            
            gain_attendu = round(target_pct, 1)
        else:
            # Fallback BRVM
            atr_pct = 10.0
            stop_pct = 9.0
            target_pct = 21.6
            gain_attendu = 21.6
        
        prix_cible = round(prix * (1 + target_pct/100), 2)
        stop = round(prix * (1 - stop_pct/100), 2)
        rr = round(target_pct / stop_pct, 2) if stop_pct > 0 else 0
        
        # Classification
        if wos >= 75 and confiance >= 85:
            classe = "A"
        elif wos >= 60 and confiance >= 75:
            classe = "B"
        else:
            classe = "C"
        
        # Raisons
        raisons = []
        if sma5 > sma10:
            raisons.append("Tendance court terme positive")
        if rsi and 40 <= rsi <= 60:
            raisons.append("RSI en zone neutre/favorable")
        if score_sem > 0:
            raisons.append("Sentiment positif detecte")
        if not raisons:
            raisons = ["Signal technique favorable"]
        
        # Décision finale (FORMAT CANONIQUE)
        decision = {
            "symbol": symbol,
            "decision": "BUY",
            "horizon": "SEMAINE",
            "is_primary": True,
            
            # CHAMPS OBLIGATOIRES TOP5
            "classe": classe,
            "confidence": round(confiance, 1),
            "wos": wos,
            "rr": rr,
            "gain_attendu": gain_attendu,
            
            # Legacy compatibility
            "confiance": confiance,
            "score": score_tech,
            "risk_reward": rr,
            "expected_return": gain_attendu,
            
            # Prix
            "prix_entree": prix,
            "prix_actuel": prix,
            "prix_sortie": prix_cible,
            "prix_cible": prix_cible,
            "stop": stop,
            "stop_pct": stop_pct,
            "target_pct": target_pct,
            
            # Techniques
            "rsi": rsi,
            "volume": volume,
            "spread": spread,
            "volatilite": atr_pct if atr_pct else 0,
            "atr_pct": atr_pct,
            
            # Justifications
            "raisons": raisons,
            "justification": "; ".join(raisons),
            
            "generated_at": datetime.utcnow(),
            "company_name": attrs.get("company_name") or symbol
        }
        
        # SAUVEGARDE GARANTIE
        result = db.decisions_finales_brvm.update_one(
            {"symbol": symbol, "horizon": "SEMAINE"},
            {"$set": decision},
            upsert=True
        )
        
        print(f"[OK] {symbol:8s} | BUY | Classe {classe} | WOS {wos:4.1f} | Conf {confiance:2.0f}% | Gain {gain_attendu:4.1f}% | RR {rr:.2f}")
        count += 1
    
    print(f"\n[STATS] Statistiques :")
    print(f"  • Volume < 1000      : {rejected['volume']}")
    print(f"  • Spread > 10        : {rejected['spread']}")
    print(f"  • Score tech < 40    : {rejected['score']}")
    
    print(f"\n[RESULTAT] {count} recommandations hebdomadaires sauvegardees\n")
    
    # Vérification sauvegarde
    verif = db.decisions_finales_brvm.count_documents({"horizon": "SEMAINE", "decision": "BUY"})
    print(f"[VERIF] MongoDB : {verif} documents BUY trouves\n")
    
    print("="*70 + "\n")
    
    return count


if __name__ == "__main__":
    generer_decisions()
