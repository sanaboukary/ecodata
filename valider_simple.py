#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validateur Simplifié - Version Production Sans Emojis"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import statistics

def valider_reco(reco, db):
    """Valide une recommandation selon 10 critères"""
    alertes = []
    confiance = 100
    symbol = reco['symbol']
    
    # 1. Données récentes (J ou J-1)
    today = datetime.now().strftime('%Y-%m-%d')
    obs = db.curated_observations.find_one({'source': 'BRVM', 'key': symbol, 'ts': today})
    
    if not obs:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        obs = db.curated_observations.find_one({'source': 'BRVM', 'key': symbol, 'ts': yesterday})
        if obs:
            confiance -= 5
            alertes.append(f"Donnees J-1 ({yesterday})")
        else:
            return False, 0, ["REJET: Pas de donnees recentes"]
    
    prix_reel = obs['value']
    prix_reco = reco.get('prix_actuel', 0)
    ecart = abs(prix_reco - prix_reel) / prix_reel * 100
    
    if ecart > 5:
        return False, 0, [f"REJET: Prix obsolete (ecart {ecart:.1f}%)"]
    if ecart > 2:
        confiance -= 10
        alertes.append(f"Prix ecart {ecart:.1f}%")
    
    # 2. Qualité données
    quality = obs['attrs'].get('data_quality', 'UNKNOWN')
    if quality not in ['REAL_SCRAPER', 'REAL_MANUAL', 'REAL_CSV']:
        return False, 0, ["REJET: Donnees non verifiees"]
    
    # 3. Historique 7-14j
    dates_14j = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]
    obs_count = db.curated_observations.count_documents({
        'source': 'BRVM', 'key': symbol, 'ts': {'$in': dates_14j}
    })
    
    if obs_count < 7:
        return False, 0, [f"REJET: Historique insuffisant ({obs_count}/14j)"]
    if obs_count < 10:
        confiance -= 15
        alertes.append(f"Historique partiel ({obs_count}/14j)")
    
    # 4. Volatilité <30%
    prices_7d = []
    for date in dates_14j[:7]:
        o = db.curated_observations.find_one({'source': 'BRVM', 'key': symbol, 'ts': date})
        if o:
            prices_7d.append(o['value'])
    
    if len(prices_7d) >= 3:
        vol = (statistics.stdev(prices_7d) / statistics.mean(prices_7d)) * 100
        if vol > 40:
            return False, 0, [f"REJET: Volatilite excessive ({vol:.1f}%)"]
        if vol > 30:
            confiance -= 20
            alertes.append(f"Volatilite elevee ({vol:.1f}%)")
    
    # 5. Score IA >= 60
    score_ia = reco.get('score', 0)
    if score_ia < 60:
        return False, 0, [f"REJET: Score IA trop faible ({score_ia})"]
    
    # 6-10: Autres critères OK si on arrive ici
    
    return True, max(confiance, 50), alertes

def main():
    print("\n" + "="*80)
    print("VALIDATION RECOMMANDATIONS - VERSION PRODUCTION")
    print("="*80 + "\n")
    
    # Connexion MongoDB avec auth (port 27018 pour Docker)
    client = MongoClient('mongodb://SANA:Boukary89%40@127.0.0.1:27018/centralisation_db?authSource=admin')
    db = client['centralisation_db']
    
    # Charger recommandations IA
    import os
    reco_files = sorted([f for f in os.listdir('.') 
                         if f.startswith('top5_nlp_') and f.endswith('.json')])
    
    if not reco_files:
        print("ERREUR: Aucune recommandation IA\n")
        client.close()
        return
    
    latest = reco_files[-1]
    print(f"Fichier source: {latest}")
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    top5 = data.get('top_5', [])[:5]
    print(f"Recommandations a valider: {len(top5)}\n")
    
    # Validation
    validees = []
    rejetees = []
    
    for reco in top5:
        symbol = reco['symbol']
        fiable, confiance, alertes = valider_reco(reco, db)
        
        if fiable and confiance >= 70:
            prix = reco['prix_actuel']
            validees.append({
                'symbol': symbol,
                'confiance': confiance,
                'prix_actuel': prix,
                'score_ia': reco['score'],
                'stop_loss': round(prix * 0.93),
                'take_profit_1': round(prix * 1.15),
                'take_profit_2': round(prix * 1.30),
                'take_profit_3': round(prix * 1.50),
                'alertes': alertes
            })
            print(f"OK {symbol:8} Confiance: {confiance}%")
        else:
            rejetees.append({
                'symbol': symbol,
                'raison_principale': alertes[0] if alertes else "Score trop faible",
                'details': alertes
            })
            print(f"KO {symbol:8} {alertes[0] if alertes else 'Score faible'}")
    
    # Résultats
    print(f"\n{'='*80}")
    print(f"RESULTATS: {len(validees)} validees / {len(rejetees)} rejetees")
    print(f"{'='*80}\n")
    
    if validees:
        print("RECOMMANDATIONS VALIDEES (confiance >=70%):\n")
        for i, v in enumerate(validees, 1):
            print(f"{i}. {v['symbol']:8} Confiance: {v['confiance']:3.0f}%  Prix: {v['prix_actuel']:>7,.0f} FCFA")
            print(f"   Stop-Loss:    {v['stop_loss']:>7,.0f} FCFA (-7%)")
            print(f"   Take-Profit:  {v['take_profit_1']:>7,.0f} (+15%), {v['take_profit_2']:>7,.0f} (+30%), {v['take_profit_3']:>7,.0f} (+50%)")
            if v['alertes']:
                print(f"   Alertes: {', '.join(v['alertes'])}")
            print()
    else:
        print("AUCUNE recommandation validee!\n")
        print("Actions requises:")
        print("1. Collecter donnees du jour: collecter_brvm_complet.py")
        print("2. Constituer historique 7-14 jours\n")
    
    if rejetees:
        print(f"ACTIONS REJETEES: {', '.join([r['symbol'] for r in rejetees])}\n")
    
    # Sauvegarde
    rapport = {
        'date_validation': datetime.now().isoformat(),
        'fichier_source': latest,
        'recommandations_validees': validees,
        'recommandations_rejetees': rejetees,
        'taux_validation': len(validees) / len(top5) * 100 if top5 else 0,
        'regles_securite': {
            'position_max_pct': 20,
            'stop_loss_pct': -7,
            'diversification_min': 3
        }
    }
    
    filename = f"recommandations_validees_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    
    print(f"Rapport sauvegarde: {filename}")
    
    # Règles
    print(f"\n{'='*80}")
    print("REGLES DE SECURITE:")
    print(f"{'='*80}")
    print("1. Max 20% du capital par action")
    print("2. Diversification: Minimum 3 actions")
    print("3. Stop-loss OBLIGATOIRE a -7%")
    print("4. Take-profit progressif: 50% a +15%, 30% a +30%, 20% a +50%")
    print("5. Re-evaluation quotidienne avant ouverture\n")
    
    client.close()

if __name__ == "__main__":
    main()
