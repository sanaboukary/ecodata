#!/usr/bin/env python3
"""
TRACK RECORD BRVM - Suivi Performance Publique
===============================================

Suivi hebdomadaire des recommandations vs résultats réels
Calcul KPIs publics : taux réussite, gain moyen, drawdown
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict

def figer_recommandations_semaine():
    """Fige les recommandations TOP5 en début de semaine"""
    
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]  # Base Django
    
    week_id = datetime.now().strftime('%Y-W%U')
    
    # Récupération TOP5 actuel
    top5 = list(db.top5_weekly_brvm.find())
    
    if not top5:
        print(f"\n❌ Aucun TOP5 a figer pour {week_id}\n")
        return
    
    # Figer chaque recommandation
    for t in top5:
        track_entry = {
            "week": week_id,
            "symbol": t.get('symbol'),
            "classe": t.get('classe'),
            "rank": t.get('rank'),
            
            # Prix prévus
            "entry": t.get('prix_entree'),
            "target": t.get('prix_cible'),
            "stop": t.get('stop'),
            
            # Métriques prévues
            "predicted_gain": t.get('gain_attendu') or t.get('expected_return'),
            "confidence": t.get('confidence'),
            "rr": t.get('rr'),
            "wos": t.get('wos'),
            
            # Résultat (à remplir en fin de semaine)
            "outcome": None,  # "WIN" / "LOSS" / "NEUTRAL"
            "real_gain": None,
            "real_exit": None,
            "exit_date": None,
            
            "created_at": datetime.utcnow()
        }
        
        db.track_record_weekly.insert_one(track_entry)
    
    print(f"\n✅ {len(top5)} recommandations figees pour {week_id}\n")


def cloturer_semaine(week_id, resultats_reels):
    """
    Clôture une semaine avec les résultats réels
    
    Args:
        week_id: str, ex: "2026-W05"
        resultats_reels: dict, ex: {"BICC": 1520, "SGBC": 1340, ...}
    """
    
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]  # Base Django
    
    tracks = list(db.track_record_weekly.find({"week": week_id}))
    
    if not tracks:
        print(f"\n❌ Aucun track record pour {week_id}\n")
        return
    
    print(f"\n=== CLOTURE SEMAINE {week_id} ===\n")
    
    for track in tracks:
        symbol = track['symbol']
        entry = track['entry']
        target = track['target']
        stop = track['stop']
        
        real_exit = resultats_reels.get(symbol)
        
        if real_exit is None:
            print(f"⚠  {symbol}: Prix reel manquant")
            continue
        
        # Calcul résultat
        real_gain = ((real_exit - entry) / entry * 100) if entry else 0
        
        # Détermination outcome
        if real_exit >= target:
            outcome = "WIN"
        elif real_exit <= stop:
            outcome = "LOSS"
        else:
            outcome = "NEUTRAL"
        
        # Mise à jour
        db.track_record_weekly.update_one(
            {"_id": track['_id']},
            {"$set": {
                "real_exit": real_exit,
                "real_gain": round(real_gain, 2),
                "outcome": outcome,
                "exit_date": datetime.utcnow()
            }}
        )
        
        print(f"{symbol:8s} | Entry: {entry:.0f} | Exit: {real_exit:.0f} | Gain: {real_gain:+.1f}% | [{outcome}]")
    
    print(f"\n✅ Semaine {week_id} clôturée\n")


def afficher_kpis_publics(nb_semaines=12):
    """Affiche les KPIs publics du track record"""
    
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    db = client["centralisation_db"]  # Base Django
    
    # Récupération historique
    tracks = list(db.track_record_weekly.find(
        {"outcome": {"$ne": None}}
    ).sort("created_at", -1).limit(nb_semaines * 5))
    
    if not tracks:
        print("\n📊 Aucun historique disponible\n")
        print("   Les KPIs seront disponibles après clôture des premières semaines\n")
        return
    
    # Calcul KPIs
    total = len(tracks)
    wins = sum(1 for t in tracks if t['outcome'] == 'WIN')
    losses = sum(1 for t in tracks if t['outcome'] == 'LOSS')
    
    gains = [t['real_gain'] for t in tracks if t.get('real_gain') is not None]
    avg_gain = sum(gains) / len(gains) if gains else 0
    
    # Taux réussite
    taux_reussite = (wins / total * 100) if total else 0
    
    # Gain par trade
    wins_gains = [t['real_gain'] for t in tracks if t['outcome'] == 'WIN']
    losses_gains = [t['real_gain'] for t in tracks if t['outcome'] == 'LOSS']
    
    avg_win = sum(wins_gains) / len(wins_gains) if wins_gains else 0
    avg_loss = sum(losses_gains) / len(losses_gains) if losses_gains else 0
    
    # Drawdown
    cumul = 0
    max_cumul = 0
    max_dd = 0
    
    for g in gains:
        cumul += g
        max_cumul = max(max_cumul, cumul)
        dd = max_cumul - cumul
        max_dd = max(max_dd, dd)
    
    # Par semaine
    semaines = defaultdict(list)
    for t in tracks:
        semaines[t['week']].append(t)
    
    semaines_avec_win = sum(1 for week_tracks in semaines.values() 
                            if any(t['outcome'] == 'WIN' for t in week_tracks))
    
    taux_semaines_gagnantes = (semaines_avec_win / len(semaines) * 100) if semaines else 0
    
    # Affichage
    print("\n" + "="*70)
    print(" KPIs PUBLICS - TRACK RECORD BRVM ".center(70))
    print("="*70 + "\n")
    
    print(f"📊 PERFORMANCE GLOBALE ({total} recommandations sur {len(semaines)} semaines)\n")
    print(f"   Taux de réussite        : {taux_reussite:.1f}%")
    print(f"   Gain moyen par trade    : {avg_gain:+.2f}%")
    print(f"   Trades gagnants         : {wins} ({wins/total*100 if total else 0:.0f}%)")
    print(f"   Trades perdants         : {losses} ({losses/total*100 if total else 0:.0f}%)")
    print("\n")
    
    print(f"💰 GAINS/PERTES\n")
    print(f"   Gain moyen (WIN)        : +{avg_win:.2f}%")
    print(f"   Perte moyenne (LOSS)    : {avg_loss:.2f}%")
    print(f"   Ratio gain/perte        : {abs(avg_win/avg_loss) if avg_loss else 0:.2f}")
    print("\n")
    
    print(f"📉 RISQUE\n")
    print(f"   Drawdown maximum        : {max_dd:.2f}%")
    print(f"   Performance cumulée     : {cumul:+.2f}%")
    print("\n")
    
    print(f"🎯 CONSISTENCY\n")
    print(f"   Semaines avec WIN       : {semaines_avec_win}/{len(semaines)} ({taux_semaines_gagnantes:.0f}%)")
    print("\n")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "figer":
            figer_recommandations_semaine()
        
        elif cmd == "cloturer":
            if len(sys.argv) < 3:
                print("\nUsage: python track_record.py cloturer <week_id>\n")
                print("Exemple: python track_record.py cloturer 2026-W05\n")
            else:
                week_id = sys.argv[2]
                # Exemple prix réels (à adapter)
                resultats_reels = {
                    "BICC": 1520,
                    "SGBC": 1340,
                    "SLBC": 990,
                    "SNTS": 4100,
                    "STBC": 1180
                }
                cloturer_semaine(week_id, resultats_reels)
        
        elif cmd == "kpis":
            afficher_kpis_publics()
        
        else:
            print("\nCommandes disponibles:")
            print("  figer     - Figer les recommandations TOP5 en début de semaine")
            print("  cloturer  - Clôturer une semaine avec résultats réels")
            print("  kpis      - Afficher les KPIs publics\n")
    
    else:
        afficher_kpis_publics()
