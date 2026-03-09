#!/usr/bin/env python3
"""
MODULE SALLE DE MARCHÉ – BRVM
=============================
Backtest massif, reporting automatique, monitoring, optimisation dynamique des seuils, alertes/logs avancés
"""
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import logging
from datetime import datetime, timedelta, timezone
from plateforme_centralisation.mongo import get_mongo_db

# --- Logger avancé ---
LOG_FILE = "salle_marche_brvm.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger()

def log_alert(msg):
    logger.warning(f"ALERTE: {msg}")
    print(f"[ALERTE] {msg}")

def log_info(msg):
    logger.info(msg)
    print(f"[INFO] {msg}")

# --- Backtest massif ---
def backtest_signaux(horizon="SEMAINE", mode="plus-value", window=180):
    _, db = get_mongo_db()
    # NOTE: ce calcul utilise prix_cible vs prix_actuel (gain ESPERE, pas gain REALISE)
    # Pour un vrai backtest, utiliser backtest_daily_v2.py
    decisions = list(db.decisions_finales_brvm.find({
        "horizon": horizon,
        "archived": {"$ne": True}   # FIX: exclure archives → chiffre non gonflé
    }))
    total_gain = 0
    n_trades = 0
    for d in decisions:
        prix_actuel = d.get("prix_actuel")
        prix_cible = d.get("prix_cible")
        if prix_actuel and prix_cible:
            gain = (prix_cible - prix_actuel) / prix_actuel * 100
            total_gain += gain
            n_trades += 1
    avg_gain = total_gain / n_trades if n_trades else 0
    log_info(f"Backtest {horizon} (espere) | {n_trades} trades actifs | Gain moyen cible: {avg_gain:.2f}%")
    return avg_gain

# --- Optimisation dynamique des seuils ---
def optimiser_seuils(horizon="SEMAINE"):
    # Ex: ajuste le seuil BUY selon la volatilité moyenne
    _, db = get_mongo_db()
    vols = [d.get("volatility", 0) for d in db.decisions_finales_brvm.find({"horizon": horizon})]
    avg_vol = sum(vols) / len(vols) if vols else 0
    seuil_buy = 50 if avg_vol < 20 else 55 if avg_vol < 35 else 60
    log_info(f"Seuil BUY optimisé ({horizon}): {seuil_buy} (volatilité moyenne: {avg_vol:.2f})")
    return seuil_buy

# --- Fraîcheur et qualité des données ---
def verifier_fraicheur():
    _, db = get_mongo_db()
    # Chercher uniquement ts string (YYYY-MM-DD ou ISO), pas les datetime MongoDB
    last_pub = db.curated_observations.find_one(
        {"ts": {"$type": "string"}},
        sort=[("ts", -1)]
    )
    if last_pub:
        ts = last_pub.get("ts", "")
        try:
            # Normaliser : enlever la partie timezone si présente pour comparaison cohérente
            ts_clean = ts[:19]  # "YYYY-MM-DDTHH:MM:SS" ou "YYYY-MM-DD"
            dt = datetime.fromisoformat(ts_clean)
            now_naive = datetime.now()  # datetime local naive
            delta = (now_naive - dt).total_seconds() / 3600
            if abs(delta) > 24 * 30:  # plus de 30 jours = données probablement stales
                log_alert(f"Donnees potentiellement stales: derniere ts={ts_clean} (delta={delta:.1f}h)")
            elif delta > 24:
                log_alert(f"Donnees non fraiches: derniere publication il y a {delta:.1f}h")
            else:
                log_info(f"Donnees fraiches: derniere publication il y a {delta:.1f}h")
        except Exception as e:
            log_alert(f"Impossible de parser ts='{ts}': {e}")
    else:
        log_alert("Aucune donnee de publication trouvee!")

# --- Monitoring et alertes avancées ---
def monitoring_pipeline():
    try:
        verifier_fraicheur()
        for horizon in ["SEMAINE", "MOIS", "TRIMESTRE", "ANNUEL"]:
            backtest_signaux(horizon)
            optimiser_seuils(horizon)
        log_info("Monitoring pipeline OK")
    except Exception as e:
        log_alert(f"Erreur pipeline: {e}")

if __name__ == "__main__":
    monitoring_pipeline()
    print("\n📊 Rapport salle de marché généré. Voir salle_marche_brvm.log pour le détail.")
