#!/usr/bin/env python3
"""Génération décisions avec log fichier"""
from pymongo import MongoClient
from datetime import datetime

LOG_FILE = "generation_log.txt"

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)  # Try aussi terminal

log("\n" + "="*70)
log(" GENERATION DECISIONS BRVM ")
log("="*70)

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]  # Base Django
    log("MongoDB connecte")
    
    analyses = list(db.curated_observations.find({"dataset": "AGREGATION_SEMANTIQUE_ACTION"}))
    log(f"{len(analyses)} analyses trouvees")
    
    if not analyses:
        log("ERREUR: Aucune analyse")
    else:
        db.decisions_finales_brvm.delete_many({"horizon": "SEMAINE"})
        log("Collection nettoyee")
        
        count = 0
        for doc in analyses:  # TOUTES les analyses
            attrs = doc.get("attrs", {})
            symbol = attrs.get("symbol")
            if not symbol:
                continue
            
            # Extraction données analyse
            signal = attrs.get("signal", "")
            if signal != "BUY":
                continue
            
            score_tech = attrs.get("score") or 0
            if score_tech < 40:
                continue
            
            # Filtres BRVM - Pas de volume/spread dans attrs sauvegardé
            # On se base uniquement sur le score et le signal
            
            # Extraction métriques
            atr_pct = attrs.get("volatility") or 10.0  # Fallback 10% si None ou 0
            prix = attrs.get("prix_actuel") or 1000  # Fallback 1000 si None
            
            # Stop/Target
            stop_pct = max(0.9 * atr_pct, 4.0)
            target_pct = 2.4 * atr_pct
            
            prix_entree = prix
            stop = prix * (1 - stop_pct/100)
            cible = prix * (1 + target_pct/100)
            
            # RR
            risk = abs(prix - stop)
            reward = abs(cible - prix)
            rr = reward / risk if risk > 0 else 0
            
            if rr < 2.0:
                continue
            
            # Confidence (basée sur score)
            if score_tech >= 80:
                confidence = 85.0
            elif score_tech >= 60:
                confidence = 75.0
            else:
                confidence = 65.0
            
            # WOS de base (sans données volume, on se base sur score et ATR%)
            wos_base = 30.0
            if atr_pct >= 8 and atr_pct <= 15:
                wos_base += 20
            if score_tech >= 70:
                wos_base += 15
            if score_tech >= 85:
                wos_base += 10
            
            # Classe
            if wos_base >= 75 and confidence >= 85:
                classe = "A"
            elif wos_base >= 60 and confidence >= 75:
                classe = "B"
            else:
                classe = "C"
            
            gain_attendu = target_pct
            
            decision = {
                "symbol": symbol,
                "decision": "BUY",
                "horizon": "SEMAINE",
                "classe": classe,
                "confidence": confidence,
                "wos": wos_base,
                "rr": round(rr, 2),
                "gain_attendu": round(gain_attendu, 2),
                "prix_entree": round(prix_entree, 2),
                "prix_cible": round(cible, 2),
                "stop": round(stop, 2),
                "atr_pct": round(atr_pct, 2),
                "score_technique": score_tech,
                "generated_at": datetime.utcnow()
            }
            
            db.decisions_finales_brvm.insert_one(decision)
            log(f"OK: {symbol} | Classe {classe} | Conf {confidence}% | Gain {gain_attendu:.1f}% | RR {rr:.1f}")
            count += 1
        
        verif = db.decisions_finales_brvm.count_documents({"decision": "BUY"})
        log(f"\nRESULTAT: {count} generees, {verif} dans MongoDB")
    
    log("="*70)
    log(f"Log complet dans: {LOG_FILE}\n")

except Exception as e:
    log(f"ERREUR: {e}")
    import traceback
    log(traceback.format_exc())
