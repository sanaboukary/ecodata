#!/usr/bin/env python3
"""
🎓 AUTO-LEARNING TOP5 ENGINE - BRVM
====================================

Objectif : Apprendre des Top 5 hausses réelles chaque semaine
pour améliorer la prédiction des futures hausses

Principe :
- Comparer prédictions vs réalité
- Mesurer quelle feature (WOS, NEWS, VOL...) explique les vraies hausses
- Réajuster les pondérations automatiquement avec lissage
- Gardes-fous pour éviter emballement

Résultat après 6-10 semaines : moteur aligné marché réel BRVM
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db


# Poids par défaut (initiaux)
DEFAULT_WEIGHTS = {
    "wos": 0.30,
    "news_score": 0.25,
    "volume_accel": 0.20,
    "sector_score": 0.15,
    "price_position": 0.10
}

# Gardes-fous
MIN_WEIGHT = 0.05
MAX_WEIGHT = 0.40
SMOOTHING_FACTOR = 0.3  # 30% nouveau, 70% ancien


def get_week_number():
    """Retourne le numéro de semaine ISO (ex: 2026-W05)"""
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def collect_ground_truth_top5(db, week, top5_data):
    """
    Sauvegarde les Top 5 hausses réelles de la semaine
    
    Args:
        week: numéro de semaine (ex: "2026-W05")
        top5_data: liste de dict avec {symbol, gain, rank, source}
        
    Exemple:
        top5_data = [
            {"symbol": "AIRL", "gain": 12.4, "rank": 1, "source": "RICHBOURSE"},
            {"symbol": "BICC", "gain": 9.8, "rank": 2, "source": "RICHBOURSE"},
            ...
        ]
    """
    coll = db["top5_weekly_ground_truth"]
    
    # Supprimer anciennes données de cette semaine (si re-collecte)
    coll.delete_many({"week": week})
    
    for data in top5_data:
        coll.insert_one({
            "week": week,
            "symbol": data["symbol"],
            "weekly_gain": data["gain"],
            "rank": data["rank"],
            "source": data.get("source", "MANUAL"),
            "collected_at": datetime.utcnow()
        })
    
    print(f"✅ {len(top5_data)} Top 5 réels sauvegardés pour {week}")


def save_feature_snapshot(db, week):
    """
    Sauvegarde l'état des features AVANT la semaine
    
    Important: doit être exécuté AVANT la semaine (vendredi soir ou samedi matin)
    pour capturer ce que le moteur voyait
    """
    coll = db["top5_feature_snapshot"]
    
    # Supprimer ancien snapshot de cette semaine
    coll.delete_many({"week": week})
    
    # Récupérer toutes les actions avec BUY
    decisions = list(db.decisions_finales_brvm.find({
        "horizon": "SEMAINE",
        "decision": "BUY"
    }))
    
    snapshots = []
    
    for d in decisions:
        symbol = d["symbol"]
        
        # Feature snapshot
        snapshot = {
            "week": week,
            "symbol": symbol,
            "wos": d.get("weekly_opportunity_score", 0),
            "news_score": d.get("news_score", 0),
            "volume_accel": d.get("volume_acceleration", 0),
            "sector_score": d.get("sector_momentum_score", 0),
            "price_position": d.get("price_position_score", 0),
            "top5_score": d.get("top5_score", 0),
            "confiance": d.get("confiance", 0),
            "gain_attendu": d.get("gain_attendu", 0),
            "snapshotted_at": datetime.utcnow()
        }
        
        snapshots.append(snapshot)
        coll.insert_one(snapshot)
    
    print(f"✅ {len(snapshots)} feature snapshots sauvegardés pour {week}")
    return snapshots


def compute_feature_importance(db, week):
    """
    Calcule l'importance réelle des features basée sur les Top 5 réels
    
    Logique:
    - Moyenne des features pour Top 5 réels
    - Moyenne des features pour non-Top5
    - Différence = importance
    - Normalisation pour obtenir nouveaux poids
    
    Returns:
        dict avec nouveaux poids suggérés
    """
    # Top 5 réels
    ground_truth = list(db.top5_weekly_ground_truth.find({"week": week}))
    if not ground_truth:
        print(f"⚠️  Aucun ground truth pour {week}, impossible de calculer importance")
        return None
    
    top5_symbols = {g["symbol"] for g in ground_truth}
    
    # Feature snapshots
    snapshots = list(db.top5_feature_snapshot.find({"week": week}))
    if not snapshots:
        print(f"⚠️  Aucun snapshot pour {week}, impossible de calculer importance")
        return None
    
    # Séparation Top5 réels vs autres
    top5_features = [s for s in snapshots if s["symbol"] in top5_symbols]
    non_top5_features = [s for s in snapshots if s["symbol"] not in top5_symbols]
    
    if not top5_features or not non_top5_features:
        print("⚠️  Pas assez de données pour apprentissage")
        return None
    
    # Calcul moyennes
    features = ["wos", "news_score", "volume_accel", "sector_score", "price_position"]
    importance = {}
    
    print(f"\n📊 Analyse {week} : {len(top5_features)} Top5 réels vs {len(non_top5_features)} autres\n")
    print(f"{'Feature':<20} {'Top5 moyen':<15} {'Non-Top5 moyen':<15} {'Différence'}")
    print("─" * 70)
    
    for feat in features:
        top5_mean = sum(f.get(feat, 0) for f in top5_features) / len(top5_features)
        non_top5_mean = sum(f.get(feat, 0) for f in non_top5_features) / len(non_top5_features)
        
        diff = max(top5_mean - non_top5_mean, 0)  # Pas de poids négatif
        importance[feat] = diff
        
        print(f"{feat:<20} {top5_mean:<15.2f} {non_top5_mean:<15.2f} {diff:.2f}")
    
    # Normalisation (total = 1.0)
    total = sum(importance.values())
    if total == 0:
        print("⚠️  Aucune différence détectée, pas de mise à jour")
        return None
    
    normalized = {k: round(v / total, 3) for k, v in importance.items()}
    
    print(f"\n✅ Nouveaux poids suggérés (bruts) :")
    for k, v in normalized.items():
        print(f"   {k:<20} : {v:.3f}")
    
    return normalized


def update_model_weights(db, new_weights, apply_smoothing=True, apply_guards=True):
    """
    Met à jour les poids du modèle avec lissage et gardes-fous
    
    Args:
        new_weights: dict avec nouveaux poids calculés
        apply_smoothing: appliquer lissage (70% ancien + 30% nouveau)
        apply_guards: appliquer min/max constraints
    
    Returns:
        dict avec poids finaux appliqués
    """
    if not new_weights:
        return None
    
    coll = db["model_weights_brvm"]
    
    # Récupérer poids actuels
    current = coll.find_one({"model": "TOP5"})
    old_weights = current.get("weights", DEFAULT_WEIGHTS) if current else DEFAULT_WEIGHTS
    
    final_weights = {}
    
    print(f"\n📐 Mise à jour des poids :\n")
    print(f"{'Feature':<20} {'Ancien':<10} {'Nouveau':<10} {'Lissé':<10} {'Final'}")
    print("─" * 70)
    
    for feat in new_weights.keys():
        old = old_weights.get(feat, DEFAULT_WEIGHTS.get(feat, 0.1))
        new = new_weights[feat]
        
        # Lissage 70/30
        if apply_smoothing:
            smoothed = 0.7 * old + 0.3 * new
        else:
            smoothed = new
        
        # Gardes-fous
        if apply_guards:
            final = max(MIN_WEIGHT, min(MAX_WEIGHT, smoothed))
        else:
            final = smoothed
        
        final_weights[feat] = round(final, 3)
        
        print(f"{feat:<20} {old:<10.3f} {new:<10.3f} {smoothed:<10.3f} {final:.3f}")
    
    # Sauvegarde
    coll.update_one(
        {"model": "TOP5"},
        {"$set": {
            "weights": final_weights,
            "updated_at": datetime.utcnow(),
            "version": (current.get("version", 0) + 1) if current else 1
        }},
        upsert=True
    )
    
    print(f"\n✅ Poids mis à jour (version {(current.get('version', 0) + 1) if current else 1})")
    
    return final_weights


def get_current_weights(db):
    """Récupère les poids actuels du modèle (ou défaut si premier run)"""
    coll = db["model_weights_brvm"]
    doc = coll.find_one({"model": "TOP5"})
    
    if doc:
        return doc.get("weights", DEFAULT_WEIGHTS)
    else:
        return DEFAULT_WEIGHTS


def weekly_learning_cycle(db, week, top5_real_data):
    """
    Cycle d'apprentissage hebdomadaire complet
    
    À exécuter chaque samedi matin :
    1. Sauvegarder Top 5 réels de la semaine passée
    2. Charger feature snapshots
    3. Calculer importance des features
    4. Mettre à jour poids du modèle
    
    Args:
        week: semaine à analyser (ex: "2026-W05")
        top5_real_data: liste des Top 5 réels collectés
    """
    print("\n" + "="*70)
    print(f"🎓 CYCLE D'APPRENTISSAGE HEBDOMADAIRE - {week}")
    print("="*70 + "\n")
    
    # 1. Sauvegarder ground truth
    collect_ground_truth_top5(db, week, top5_real_data)
    
    # 2. Calculer importance features
    new_weights = compute_feature_importance(db, week)
    
    if not new_weights:
        print("\n⚠️  Apprentissage impossible cette semaine (données manquantes)")
        return None
    
    # 3. Mettre à jour poids
    final_weights = update_model_weights(db, new_weights)
    
    print("\n" + "="*70)
    print("✅ Apprentissage terminé - Le moteur est maintenant plus aligné marché réel")
    print("="*70 + "\n")
    
    return final_weights


if __name__ == "__main__":
    _, db = get_mongo_db()
    
    print("\n" + "="*70)
    print("🎓 AUTO-LEARNING TOP5 ENGINE - BRVM")
    print("="*70)
    
    week = get_week_number()
    print(f"\nSemaine actuelle : {week}")
    
    # Afficher poids actuels
    current_weights = get_current_weights(db)
    print(f"\n📊 Poids actuels du modèle :")
    for k, v in current_weights.items():
        print(f"   {k:<20} : {v:.3f}")
    
    # Exemple d'utilisation
    print(f"\n💡 Pour lancer un cycle d'apprentissage :")
    print(f"   1. Collecter Top 5 réels depuis RichBourse (vendredi soir)")
    print(f"   2. Exécuter : weekly_learning_cycle(db, '{week}', top5_data)")
    print(f"   3. Le moteur s'adapte automatiquement\n")
    
    print("="*70 + "\n")
