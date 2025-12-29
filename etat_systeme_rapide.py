#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""État rapide du système de recommandations"""

import os
import json
from datetime import datetime, timedelta
from pymongo import MongoClient

def main():
    print("=" * 80)
    print("ÉTAT SYSTÈME RECOMMANDATIONS FIABLES - 100%")
    print("=" * 80)
    print()
    
    # Connexion MongoDB directe
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['centralisation_db']
        print("✅ MongoDB connecté\n")
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}\n")
        return
    
    # 1. Recommandations IA
    print("📋 1. RECOMMANDATIONS IA")
    print("-" * 80)
    json_files = [f for f in os.listdir('.') if f.startswith('top5_nlp_') and f.endswith('.json')]
    if json_files:
        latest = sorted(json_files)[-1]
        print(f"✅ Fichier : {latest}")
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
        top5 = data.get('top_5', [])
        print(f"   Actions recommandées : {len(top5)}")
        for i, r in enumerate(top5[:5], 1):
            print(f"   {i}. {r['symbol']:8} - Score: {r['score']}/100 - Prix: {r['prix_actuel']:,.0f} FCFA")
    else:
        print("❌ Aucune recommandation trouvée")
    print()
    
    # 2. Données MongoDB aujourd'hui
    print("💾 2. DONNÉES BRVM AUJOURD'HUI")
    print("-" * 80)
    today = datetime.now().strftime('%Y-%m-%d')
    count_today = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': today
    })
    print(f"   Date : {today}")
    print(f"   Actions : {count_today}/47")
    
    if count_today >= 40:
        print("   ✅ EXCELLENT - Collecte quasi-complète")
    elif count_today >= 30:
        print("   ⚠️  BON - Collecte partielle")
    elif count_today > 0:
        print("   ⚠️  INSUFFISANT - Données limitées")
    else:
        print("   ❌ CRITIQUE - Aucune donnée aujourd'hui")
    print()
    
    # 3. Historique 7 jours
    print("📊 3. HISTORIQUE 7 JOURS")
    print("-" * 80)
    date_7j = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    count_7j = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': {'$gte': date_7j}
    })
    dates = db.curated_observations.distinct('ts', {
        'source': 'BRVM',
        'ts': {'$gte': date_7j}
    })
    print(f"   Période : {date_7j} → {today}")
    print(f"   Observations : {count_7j}")
    print(f"   Jours avec données : {len(dates)}/7")
    
    if len(dates) >= 5:
        print("   ✅ EXCELLENT - Historique suffisant pour validation")
    elif len(dates) >= 3:
        print("   ⚠️  MOYEN - Historique limité")
    else:
        print("   ❌ INSUFFISANT - Pas assez d'historique")
    print()
    
    # 4. Qualité données (REAL vs autres)
    print("🔍 4. QUALITÉ DONNÉES")
    print("-" * 80)
    pipeline = [
        {'$match': {'source': 'BRVM', 'ts': {'$gte': date_7j}}},
        {'$group': {'_id': '$attrs.data_quality', 'count': {'$sum': 1}}}
    ]
    quality = list(db.curated_observations.aggregate(pipeline))
    
    total = sum(q['count'] for q in quality)
    real_count = sum(q['count'] for q in quality if q['_id'] in ['REAL_SCRAPER', 'REAL_MANUAL', 'REAL_CSV'])
    real_pct = (real_count / total * 100) if total > 0 else 0
    
    for q in sorted(quality, key=lambda x: x['count'], reverse=True):
        qtype = q['_id'] or 'UNKNOWN'
        count = q['count']
        pct = (count / total * 100) if total > 0 else 0
        status = "✅" if qtype.startswith('REAL') else "⚠️ "
        print(f"   {status} {qtype:20} : {count:4} ({pct:5.1f}%)")
    
    print(f"\n   Données RÉELLES : {real_pct:.1f}%")
    if real_pct >= 90:
        print("   ✅ EXCELLENT - Qualité garantie")
    elif real_pct >= 70:
        print("   ⚠️  BON - Qualité acceptable")
    else:
        print("   ❌ INSUFFISANT - Trop de données non vérifiées")
    print()
    
    # 5. Validation existante
    print("🛡️ 5. VALIDATIONS")
    print("-" * 80)
    val_files = [f for f in os.listdir('.') if f.startswith('recommandations_validees_') and f.endswith('.json')]
    if val_files:
        latest_val = sorted(val_files)[-1]
        print(f"✅ Validation : {latest_val}")
        with open(latest_val, 'r', encoding='utf-8') as f:
            val_data = json.load(f)
        validees = val_data.get('recommandations_validees', [])
        rejetees = val_data.get('recommandations_rejetees', [])
        print(f"   Validées : {len(validees)}")
        print(f"   Rejetées : {len(rejetees)}")
    else:
        print("⏳ Aucune validation (à exécuter)")
    print()
    
    # DIAGNOSTIC FINAL
    print("=" * 80)
    print("🎯 DIAGNOSTIC & ACTIONS PRIORITAIRES")
    print("=" * 80)
    print()
    
    score_global = 0
    max_score = 100
    
    # Scoring
    if json_files:
        score_global += 20
        print("✅ [20/20] Recommandations IA générées")
    else:
        print("❌ [00/20] Générer recommandations : python generer_top5_nlp.py")
    
    if count_today >= 40:
        score_global += 25
        print("✅ [25/25] Collecte aujourd'hui complète")
    elif count_today >= 30:
        score_global += 15
        print("⚠️  [15/25] Collecte partielle - Exécuter : python collecter_brvm_complet.py")
    else:
        print("❌ [00/25] URGENT - Collecter : python collecter_brvm_complet.py")
    
    if len(dates) >= 5:
        score_global += 25
        print("✅ [25/25] Historique 7j suffisant")
    elif len(dates) >= 3:
        score_global += 15
        print("⚠️  [15/25] Historique limité - Collecter quotidiennement")
    else:
        print("❌ [00/25] Historique insuffisant - Constituer base 60 jours")
    
    if real_pct >= 90:
        score_global += 20
        print("✅ [20/20] Qualité données excellente")
    elif real_pct >= 70:
        score_global += 12
        print("⚠️  [12/20] Qualité acceptable - Améliorer collecte")
    else:
        print("❌ [00/20] Qualité insuffisante - Utiliser REAL_SCRAPER uniquement")
    
    if val_files:
        score_global += 10
        print("✅ [10/10] Validation effectuée")
    else:
        print("❌ [00/10] CRITIQUE - Valider : python valider_recommandations_fiables.py")
    
    print()
    print(f"SCORE GLOBAL : {score_global}/{max_score}")
    print()
    
    if score_global >= 90:
        print("🎯 STATUT : SYSTÈME OPÉRATIONNEL ✅")
        print("   → Trading possible avec recommandations validées")
        print("   → Respecter stop-loss (-7%) et position sizing (20% max)")
    elif score_global >= 70:
        print("⚠️  STATUT : SYSTÈME PARTIELLEMENT OPÉRATIONNEL")
        print("   → Améliorer points faibles avant trading intensif")
    elif score_global >= 50:
        print("⚠️  STATUT : SYSTÈME EN CONSTRUCTION")
        print("   → Compléter éléments manquants avant trading")
    else:
        print("❌ STATUT : SYSTÈME NON OPÉRATIONNEL")
        print("   → Résoudre problèmes critiques AVANT trading")
    
    print()
    print("=" * 80)
    print("📋 WORKFLOW QUOTIDIEN")
    print("=" * 80)
    print("Matin :")
    print("  1. python valider_recommandations_fiables.py")
    print("  2. Trader UNIQUEMENT les validées (confiance ≥70%)")
    print("  3. Placer stop-loss (-7%) et take-profit (+15%, +30%, +50%)")
    print()
    print("Soir (16h30) :")
    print("  1. python collecter_brvm_complet.py")
    print("  2. python verifier_cours_brvm.py")
    print()
    print("Vendredi :")
    print("  1. python suivre_performance_recos.py")
    print("  2. Ajuster thresholds si win rate <75%")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    main()
