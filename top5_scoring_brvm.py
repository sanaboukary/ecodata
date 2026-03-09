#!/usr/bin/env python3
"""
🎯 TOP 5 PROBABILITY SCORING - BRVM
====================================

Objectif : Prédire quelles actions finiront dans le Top 5 hausses hebdomadaires

Philosophie BRVM (30 ans terrain) :
- Chaque semaine, 3-7 actions font l'essentiel de la hausse
- Top 5 viennent TOUJOURS de : annonce fraîche, volume accélération, rotation sectorielle
- Recommander = viser le Top 5, pas juste "BUY générique"

Formule :
TOP5_SCORE = 0.35×NEWS + 0.25×VOLUME_ACCEL + 0.20×SECTOR_MOM + 0.10×PRICE_POS + 0.10×WOS
"""

import os
import sys
from datetime import datetime, timedelta

# --- Django & MongoDB ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db


# ========================================
# 1. NEWS_IMPACT_SCORE (35% du TOP5_SCORE)
# ========================================

def compute_news_impact_score(symbol, db):
    """
    Score basé sur les annonces BRVM récentes
    
    Type annonce         Score base
    ----------------     ----------
    Résultat positif     +30
    Dividende confirmé   +25
    Nouveau contrat      +35
    Notation financière  +20
    AGO sans surprise    +5
    Aucune annonce       0
    
    Bonus fraîcheur : ×1.5 si < 7 jours
    """
    
    # Chercher publications récentes (30 derniers jours)
    cutoff_date = datetime.now() - timedelta(days=30)
    
    publications = list(db.curated_observations.find({
        "source": "BRVM_PUBLICATION",
        "attrs.emetteur": symbol,
        "ts": {"$gte": cutoff_date.strftime("%Y-%m-%d")}
    }).sort("ts", -1))
    
    if not publications:
        return 0
    
    max_score = 0
    
    for pub in publications:
        attrs = pub.get("attrs", {})
        pub_type = attrs.get("type", "").upper()
        pub_date_str = pub.get("ts")
        
        # Score de base selon type
        base_score = 0
        
        if pub_type == "RESULTATS":
            resultat = attrs.get("resultat", "").upper()
            ca = attrs.get("ca", "").upper()
            if resultat == "HAUSSE" and ca == "HAUSSE":
                base_score = 30
            elif resultat == "HAUSSE":
                base_score = 25
        
        elif pub_type == "DIVIDENDE":
            evolution = attrs.get("evolution", "").upper()
            if evolution == "HAUSSE" or attrs.get("rendement", 0) > 5:
                base_score = 25
            else:
                base_score = 15
        
        elif pub_type == "CONTRAT" or pub_type == "PARTENARIAT":
            base_score = 35
        
        elif pub_type == "NOTATION":
            base_score = 20
        
        elif pub_type == "GOUVERNANCE" or pub_type == "AGO":
            base_score = 5
        
        # Bonus fraîcheur
        try:
            pub_date = datetime.fromisoformat(pub_date_str)
            days_old = (datetime.now() - pub_date).days
            
            if days_old <= 7:
                base_score *= 1.5  # Annonce très fraîche
            elif days_old <= 14:
                base_score *= 1.2  # Annonce récente
        except:
            pass
        
        max_score = max(max_score, base_score)
    
    return round(max_score, 1)


# ========================================
# 2. VOLUME_ACCELERATION (25%)
# ========================================

def compute_volume_acceleration(symbol, db):
    """
    Mesure l'accélération du volume
    
    volume_accel = volume_5j / volume_20j
    
    Ratio         Lecture
    -----         -------
    < 1.0         Mort
    1.0 - 1.3     Normal
    1.3 - 1.7     Pré-breakout
    > 1.7         Flux dominant 🔥
    
    Top 5 hebdo = presque toujours > 1.5
    """
    
    # Récupérer données de volume (simplification : on utilise curated_observations)
    docs = list(db.curated_observations.find({
        "source": "BRVM",
        "key": symbol,
        "attrs.volume": {"$exists": True}
    }).sort("date", -1).limit(25))
    
    if len(docs) < 20:
        return 0
    
    volumes = [d.get("attrs", {}).get("volume", 0) for d in docs if d.get("attrs", {}).get("volume", 0) > 0]
    
    if len(volumes) < 20:
        return 0
    
    volume_5j = sum(volumes[:5]) / 5
    volume_20j = sum(volumes[:20]) / 20
    
    if volume_20j == 0:
        return 0
    
    accel_ratio = volume_5j / volume_20j
    
    # Scoring
    if accel_ratio > 1.7:
        score = 100
    elif accel_ratio > 1.5:
        score = 85
    elif accel_ratio > 1.3:
        score = 60
    elif accel_ratio >= 1.0:
        score = 30
    else:
        score = 0
    
    return round(score, 1)


# ========================================
# 3. SECTOR_MOMENTUM (20%)
# ========================================

def compute_sector_momentum(symbol, sector, db):
    """
    Les Top 5 sont rarement isolés
    
    Si l'action appartient au secteur dominant cette semaine :
    → Score élevé
    
    Sinon :
    → Score bas
    """
    
    if not sector:
        return 0
    
    # Récupérer le score sectoriel (déjà calculé par propagation_sector_to_action.py)
    sector_doc = db.sector_sentiment_brvm.find_one({"sector": sector})
    
    if not sector_doc:
        return 0
    
    sector_score = sector_doc.get("score_semaine", sector_doc.get("score_ct", 0))
    
    # Scoring
    if sector_score > 20:
        score = 100  # Secteur très positif
    elif sector_score > 10:
        score = 70   # Secteur positif
    elif sector_score > 0:
        score = 40   # Secteur légèrement positif
    else:
        score = 0    # Secteur négatif/neutre
    
    return round(score, 1)


# ========================================
# 4. PRICE_POSITION (10%)
# ========================================

def compute_price_position(prices):
    """
    Timing pur BRVM
    
    price_position = (prix - plus_bas_20j) / (plus_haut_20j - plus_bas_20j)
    
    Position      Lecture
    --------      -------
    < 0.3         Trop tôt
    0.3 - 0.6     ZONE IDÉALE ✅
    > 0.7         Trop tard
    
    Top hausses = zone 0.35 - 0.55
    """
    
    if not prices or len(prices) < 20:
        return 0
    
    last_20 = prices[-20:]
    current_price = prices[-1]
    
    high_20 = max(last_20)
    low_20 = min(last_20)
    
    if high_20 == low_20:
        return 0
    
    position = (current_price - low_20) / (high_20 - low_20)
    
    # Scoring
    if 0.35 <= position <= 0.55:
        score = 100  # Zone idéale
    elif 0.30 <= position <= 0.60:
        score = 80   # Zone acceptable
    elif position < 0.30:
        score = 40   # Potentiel mais tôt
    else:
        score = 20   # Trop haut
    
    return round(score, 1)


# ========================================
# 5. TOP5_SCORE FINAL
# ========================================

def compute_top5_score(symbol, wos, db):
    """
    Score de probabilité Top 5 hebdomadaire
    
    TOP5_SCORE = (
        0.35 × NEWS_IMPACT
      + 0.25 × VOLUME_ACCELERATION
      + 0.20 × SECTOR_MOMENTUM
      + 0.10 × PRICE_POSITION
      + 0.10 × WOS
    )
    """
    
    # Récupérer données de base
    doc = db.curated_observations.find_one({
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if not doc:
        return {
            "top5_score": 0,
            "news_score": 0,
            "volume_accel_score": 0,
            "sector_mom_score": 0,
            "price_pos_score": 0,
            "wos_normalized": 0
        }
    
    attrs = doc.get("attrs", {})
    sector = attrs.get("sector")
    prices = attrs.get("close_prices", [])
    
    # Calcul des composantes
    news_score = compute_news_impact_score(symbol, db)
    volume_accel_score = compute_volume_acceleration(symbol, db)
    sector_mom_score = compute_sector_momentum(symbol, sector, db)
    price_pos_score = compute_price_position(prices)
    wos_normalized = min(100, wos)  # WOS déjà sur 100
    
    # Score final
    top5_score = (
        0.35 * news_score +
        0.25 * volume_accel_score +
        0.20 * sector_mom_score +
        0.10 * price_pos_score +
        0.10 * wos_normalized
    )
    
    return {
        "top5_score": round(top5_score, 1),
        "news_score": news_score,
        "volume_accel_score": volume_accel_score,
        "sector_mom_score": sector_mom_score,
        "price_pos_score": price_pos_score,
        "wos_normalized": wos_normalized
    }


# ========================================
# MAIN - Calcul et classement Top 5
# ========================================

if __name__ == "__main__":
    _, db = get_mongo_db()
    
    print("\n=== 🎯 TOP 5 PROBABILITY SCORING - BRVM ===\n")
    
    # Récupérer les décisions BUY hebdomadaires
    decisions = list(db.decisions_finales_brvm.find({
        "horizon": "SEMAINE",
        "decision": "BUY"
    }))
    
    if not decisions:
        print("❌ Aucune décision BUY trouvée")
        print("   → Exécuter 'decision_finale_brvm.py' d'abord\n")
        sys.exit(0)
    
    print(f"📊 {len(decisions)} décisions BUY à scorer\n")
    
    # Calculer TOP5_SCORE pour chaque décision
    scored_decisions = []
    
    for decision in decisions:
        symbol = decision["symbol"]
        wos = decision.get("score", 70)
        
        top5_data = compute_top5_score(symbol, wos, db)
        
        scored_decisions.append({
            "symbol": symbol,
            "top5_score": top5_data["top5_score"],
            "wos": wos,
            "confiance": decision.get("confiance", 70),
            "gain_attendu": decision.get("gain_attendu", 0),
            "news_score": top5_data["news_score"],
            "volume_accel": top5_data["volume_accel_score"],
            "sector_mom": top5_data["sector_mom_score"],
            "price_pos": top5_data["price_pos_score"]
        })
        
        # Mettre à jour dans MongoDB
        db.decisions_finales_brvm.update_one(
            {"symbol": symbol, "horizon": "SEMAINE"},
            {"$set": {
                "top5_score": top5_data["top5_score"],
                "top5_components": {
                    "news": top5_data["news_score"],
                    "volume_accel": top5_data["volume_accel_score"],
                    "sector_momentum": top5_data["sector_mom_score"],
                    "price_position": top5_data["price_pos_score"],
                    "wos": top5_data["wos_normalized"]
                },
                "top5_scored_at": datetime.utcnow()
            }}
        )
    
    # Classement par TOP5_SCORE
    scored_decisions.sort(key=lambda x: x["top5_score"], reverse=True)
    
    # Affichage hiérarchisé
    print("=" * 100)
    print(f"{'RANG':^6} | {'SYMBOLE':^8} | {'TOP5':^6} | {'WOS':^5} | {'NEWS':^5} | {'VOL':^5} | {'SECT':^5} | {'POS':^5} | {'GAIN':^6}")
    print("=" * 100)
    
    for i, dec in enumerate(scored_decisions[:10], 1):  # Top 10 max
        marker = "🔥" if i <= 3 else "✅" if i <= 5 else "⚪"
        
        print(f"{marker} {i:^4} | {dec['symbol']:^8} | {dec['top5_score']:^6.1f} | "
              f"{dec['wos']:^5.0f} | {dec['news_score']:^5.0f} | {dec['volume_accel']:^5.0f} | "
              f"{dec['sector_mom']:^5.0f} | {dec['price_pos']:^5.0f} | {dec['gain_attendu']:^6.1f}%")
    
    print("=" * 100)
    
    # Recommandations finales
    top5_recommendations = scored_decisions[:5]
    
    print(f"\n🎯 RECOMMANDATIONS HEBDOMADAIRES (Top 5 probabilité)")
    print(f"   → {len(top5_recommendations)} actions sélectionnées sur {len(decisions)} candidats BUY\n")
    
    for i, rec in enumerate(top5_recommendations, 1):
        print(f"{i}. {rec['symbol']} | TOP5: {rec['top5_score']:.1f} | Gain attendu: {rec['gain_attendu']:.1f}%")
        print(f"   NEWS: {rec['news_score']:.0f} | VOL: {rec['volume_accel']:.0f} | SECT: {rec['sector_mom']:.0f} | POS: {rec['price_pos']:.0f}")
        print()
    
    print("✅ Scoring Top 5 terminé\n")
