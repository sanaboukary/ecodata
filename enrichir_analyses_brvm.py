#!/usr/bin/env python3
"""
ENRICHIR ANALYSES AVEC DONNÉES BRVM RÉELLES
============================================

Récupère les prix et métriques réels depuis STOCK_PRICE
et met à jour les analyses existantes
"""

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timezone

_, db = get_mongo_db()

print("\n" + "="*80)
print(" ENRICHISSEMENT ANALYSES AVEC DONNÉES BRVM RÉELLES ".center(80))
print("="*80 + "\n")

# 1. Récupérer toutes les actions avec STOCK_PRICE
actions_stock = db.curated_observations.distinct("key", {
    "source": "BRVM", 
    "dataset": "STOCK_PRICE"
})

print(f"[1/3] {len(actions_stock)} actions avec données STOCK_PRICE")

# 2. Pour chaque action, récupérer les données réelles
count_enrichi = 0
count_non_trouve = 0

for symbol in actions_stock:
    # Récupérer la dernière donnée STOCK_PRICE
    stock = db.curated_observations.find_one(
        {"source": "BRVM", "dataset": "STOCK_PRICE", "key": symbol},
        sort=[("ts", -1)]
    )
    
    if not stock:
        count_non_trouve += 1
        continue
    
    attrs_stock = stock.get("attrs", {})
    
    # Données réelles BRVM
    prix_reel = attrs_stock.get("cours") or stock.get("value", 0)
    volatilite_reel = attrs_stock.get("volatilite_pct")  # En %
    volume_reel = attrs_stock.get("volume", 0)
    variation_reel = attrs_stock.get("variation_pct", 0)
    
    # Vérifier si analyse existe
    analyse = db.curated_observations.find_one({
        "source": "AI_ANALYSIS",
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if not analyse:
        # Pas encore d'analyse IA pour cette action
        continue
    
    # Enrichir l'analyse avec données réelles
    attrs_analyse = analyse.get("attrs", {})
    
    enrichi = False
    
    # Mise à jour prix actuel
    if prix_reel and prix_reel > 0:
        attrs_analyse["prix_actuel"] = prix_reel
        enrichi = True
    
    # Mise à jour volatilité réelle
    if volatilite_reel is not None:
        attrs_analyse["volatility"] = volatilite_reel
        enrichi = True
    
    # Mise à jour volume
    if volume_reel and volume_reel > 0:
        attrs_analyse["volume"] = volume_reel
        enrichi = True
    
    # Mise à jour variation
    if variation_reel:
        attrs_analyse["variation_pct"] = variation_reel
        enrichi = True
    
    if enrichi:
        # Sauvegarder l'analyse enrichie
        db.curated_observations.update_one(
            {
                "source": "AI_ANALYSIS",
                "dataset": "AGREGATION_SEMANTIQUE_ACTION",
                "key": symbol
            },
            {
                "$set": {
                    "attrs": attrs_analyse,
                    "value": prix_reel if prix_reel else analyse.get("value"),
                    "enrichi_le": datetime.now(timezone.utc)
                }
            }
        )
        
        print(f"[OK] {symbol:6} | Prix: {prix_reel:>8.0f} FCFA | Vol%: {volatilite_reel if volatilite_reel else 'N/A':>5} | Volume: {volume_reel:>8}")
        count_enrichi += 1

print(f"\n[2/3] {count_enrichi} analyses enrichies avec données réelles")
print(f"      {count_non_trouve} actions sans données STOCK_PRICE")

# 3. Récupérer prix historiques pour calcul SMA et RSI
print(f"\n[3/3] Calcul indicateurs techniques (SMA5, SMA10, RSI)...")

def calculer_sma(prix, periode):
    if len(prix) < periode:
        return None
    return sum(prix[-periode:]) / periode

def calculer_rsi(prix, periode=14):
    if len(prix) < periode + 1:
        return None
    
    deltas = [prix[i] - prix[i-1] for i in range(1, len(prix))]
    gains = [d if d > 0 else 0 for d in deltas[-periode:]]
    pertes = [-d if d < 0 else 0 for d in deltas[-periode:]]
    
    avg_gain = sum(gains) / periode
    avg_loss = sum(pertes) / periode
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

count_indicateurs = 0

for symbol in actions_stock:
    # Récupérer l'historique STOCK_PRICE (derniers 30 jours)
    historique = list(db.curated_observations.find(
        {"source": "BRVM", "dataset": "STOCK_PRICE", "key": symbol}
    ).sort("ts", 1).limit(30))
    
    if len(historique) < 10:
        continue
    
    # Extraire les prix
    prix = []
    for h in historique:
        p = h.get("attrs", {}).get("cours") or h.get("value", 0)
        if p and p > 0:
            prix.append(p)
    
    if len(prix) < 10:
        continue
    
    # Calculer indicateurs
    sma5 = calculer_sma(prix, 5)
    sma10 = calculer_sma(prix, 10)
    rsi = calculer_rsi(prix, 14)
    
    # Mettre à jour l'analyse
    analyse = db.curated_observations.find_one({
        "source": "AI_ANALYSIS",
        "dataset": "AGREGATION_SEMANTIQUE_ACTION",
        "key": symbol
    })
    
    if not analyse:
        continue
    
    attrs = analyse.get("attrs", {})
    attrs["SMA5"] = sma5
    attrs["SMA10"] = sma10
    attrs["rsi"] = rsi
    attrs["close_prices"] = prix  # Historique pour ATR
    
    db.curated_observations.update_one(
        {
            "source": "AI_ANALYSIS",
            "dataset": "AGREGATION_SEMANTIQUE_ACTION",
            "key": symbol
        },
        {
            "$set": {
                "attrs": attrs,
                "indicateurs_calcules_le": datetime.now(timezone.utc)
            }
        }
    )
    
    sma5_str = f"{sma5:>8.0f}" if sma5 else "     N/A"
    sma10_str = f"{sma10:>8.0f}" if sma10 else "     N/A"
    rsi_str = f"{rsi:>5.1f}" if rsi else "  N/A"
    
    print(f"[CALC] {symbol:6} | SMA5: {sma5_str} | SMA10: {sma10_str} | RSI: {rsi_str}")
    count_indicateurs += 1

print(f"\n[RESULTAT] {count_indicateurs} actions avec indicateurs calculés")

# 4. Statistiques finales
analyses_finales = list(db.curated_observations.find({
    "source": "AI_ANALYSIS",
    "dataset": "AGREGATION_SEMANTIQUE_ACTION"
}))

print(f"\n" + "="*80)
print(" STATISTIQUES ENRICHISSEMENT ".center(80))
print("="*80)

stats = {
    "avec_prix": 0,
    "avec_volatility": 0,
    "avec_sma": 0,
    "avec_rsi": 0,
    "complet": 0
}

for a in analyses_finales:
    attrs = a.get("attrs", {})
    
    if attrs.get("prix_actuel"):
        stats["avec_prix"] += 1
    if attrs.get("volatility") is not None:
        stats["avec_volatility"] += 1
    if attrs.get("SMA5") is not None:
        stats["avec_sma"] += 1
    if attrs.get("rsi") is not None:
        stats["avec_rsi"] += 1
    
    if all([
        attrs.get("prix_actuel"),
        attrs.get("volatility") is not None,
        attrs.get("SMA5") is not None,
        attrs.get("rsi") is not None
    ]):
        stats["complet"] += 1

print(f"  Total analyses     : {len(analyses_finales)}")
print(f"  Avec prix réel     : {stats['avec_prix']}")
print(f"  Avec volatilité    : {stats['avec_volatility']}")
print(f"  Avec SMA5/SMA10    : {stats['avec_sma']}")
print(f"  Avec RSI           : {stats['avec_rsi']}")
print(f"  Enrichissement 100%: {stats['complet']}")

print("\n" + "="*80)
print(f" {'ENRICHISSEMENT TERMINÉ':^80}")
print("="*80)
print(f" Prochaine étape : .venv/Scripts/python.exe decision_finale_brvm.py")
print("="*80 + "\n")
