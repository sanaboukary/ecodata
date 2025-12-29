#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic Rapide du Système de Recommandations Fiables
Vérifie tous les éléments nécessaires pour garantir fiabilité 100%
"""

import json
from datetime import datetime, timedelta
from plateforme_centralisation.mongo import get_mongo_db

def main():
    print("=" * 80)
    print("🔍 DIAGNOSTIC SYSTÈME RECOMMANDATIONS FIABLES - 100%")
    print("=" * 80)
    print()
    
    client, db = get_mongo_db()
    
    # 1. Vérifier existence fichier recommandations IA
    print("📋 1. RECOMMANDATIONS IA EXISTANTES")
    print("-" * 80)
    import os
    json_files = [f for f in os.listdir('.') if f.startswith('top5_nlp_') and f.endswith('.json')]
    if json_files:
        latest_file = sorted(json_files)[-1]
        print(f"✅ Fichier trouvé : {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            recommendations = json.load(f)
        
        print(f"   Nombre recommandations : {len(recommendations)}")
        for i, reco in enumerate(recommendations, 1):
            symbol = reco.get('symbol', 'N/A')
            score = reco.get('score_total', 0)
            prix = reco.get('prix_actuel', 0)
            print(f"   {i}. {symbol:8} - Score: {score:5.1f}/100 - Prix: {prix:,.0f} FCFA")
    else:
        print("❌ Aucun fichier top5_nlp_*.json trouvé")
    print()
    
    # 2. Vérifier données MongoDB aujourd'hui
    print("💾 2. DONNÉES BRVM AUJOURD'HUI")
    print("-" * 80)
    today = datetime.now().strftime('%Y-%m-%d')
    count_today = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': today
    })
    print(f"   Date : {today}")
    print(f"   Actions collectées : {count_today}/47")
    
    if count_today >= 47:
        print("   ✅ Collecte complète (47 actions)")
    elif count_today >= 30:
        print(f"   ⚠️  Collecte partielle ({count_today} actions)")
    elif count_today > 0:
        print(f"   ⚠️  Collecte insuffisante ({count_today} actions)")
    else:
        print("   ❌ Aucune donnée aujourd'hui")
    
    # Montrer quelles actions sont disponibles
    if count_today > 0:
        actions = db.curated_observations.find({
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'ts': today
        }).distinct('key')
        print(f"\n   Actions disponibles ({len(actions)}) :")
        for symbol in sorted(actions)[:10]:  # Top 10
            print(f"   - {symbol}")
        if len(actions) > 10:
            print(f"   ... et {len(actions) - 10} autres")
    print()
    
    # 3. Vérifier historique 7 jours (minimum pour validation)
    print("📊 3. HISTORIQUE 7 JOURS")
    print("-" * 80)
    date_7j = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    count_7j = db.curated_observations.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': {'$gte': date_7j}
    })
    
    # Nombre de jours avec données
    dates_with_data = db.curated_observations.distinct('ts', {
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': {'$gte': date_7j}
    })
    
    print(f"   Période : {date_7j} → {today}")
    print(f"   Observations : {count_7j}")
    print(f"   Jours avec données : {len(dates_with_data)}/7")
    print(f"   Moyenne : {count_7j / max(len(dates_with_data), 1):.1f} actions/jour")
    
    if len(dates_with_data) >= 5 and count_7j >= 200:
        print("   ✅ Historique suffisant pour validation")
    elif len(dates_with_data) >= 3:
        print("   ⚠️  Historique partiel (validation limitée)")
    else:
        print("   ❌ Historique insuffisant")
    print()
    
    # 4. Vérifier qualité des données
    print("🔍 4. QUALITÉ DES DONNÉES")
    print("-" * 80)
    
    # Compter par data_quality
    pipeline = [
        {
            '$match': {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'ts': {'$gte': date_7j}
            }
        },
        {
            '$group': {
                '_id': '$attrs.data_quality',
                'count': {'$sum': 1}
            }
        }
    ]
    
    quality_stats = list(db.curated_observations.aggregate(pipeline))
    
    total_obs = sum(stat['count'] for stat in quality_stats)
    
    for stat in sorted(quality_stats, key=lambda x: x['count'], reverse=True):
        quality = stat['_id'] or 'UNKNOWN'
        count = stat['count']
        pct = (count / total_obs * 100) if total_obs > 0 else 0
        
        if quality in ['REAL_SCRAPER', 'REAL_MANUAL', 'REAL_CSV']:
            status = "✅"
        elif quality == 'UNKNOWN':
            status = "⚠️ "
        else:
            status = "❓"
        
        print(f"   {status} {quality:20} : {count:5} observations ({pct:5.1f}%)")
    
    # Pourcentage de données réelles
    real_count = sum(stat['count'] for stat in quality_stats 
                     if stat['_id'] in ['REAL_SCRAPER', 'REAL_MANUAL', 'REAL_CSV'])
    real_pct = (real_count / total_obs * 100) if total_obs > 0 else 0
    
    print()
    print(f"   Données RÉELLES : {real_count}/{total_obs} ({real_pct:.1f}%)")
    
    if real_pct >= 90:
        print("   ✅ Qualité excellente (≥90% réelles)")
    elif real_pct >= 70:
        print("   ⚠️  Qualité acceptable (≥70% réelles)")
    else:
        print("   ❌ Qualité insuffisante (<70% réelles)")
    print()
    
    # 5. Vérifier si validation a déjà été exécutée
    print("🛡️ 5. VALIDATIONS EXISTANTES")
    print("-" * 80)
    
    validation_files = [f for f in os.listdir('.') if f.startswith('recommandations_validees_') and f.endswith('.json')]
    
    if validation_files:
        latest_validation = sorted(validation_files)[-1]
        print(f"✅ Validation trouvée : {latest_validation}")
        
        with open(latest_validation, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        validees = validation_data.get('recommandations_validees', [])
        rejetees = validation_data.get('recommandations_rejetees', [])
        
        print(f"   Recommandations validées : {len(validees)}")
        for reco in validees:
            symbol = reco.get('symbol', 'N/A')
            confiance = reco.get('confiance', 0)
            print(f"   ✅ {symbol:8} - Confiance: {confiance:.1f}%")
        
        print(f"\n   Recommandations rejetées : {len(rejetees)}")
        for reco in rejetees[:5]:  # Top 5
            symbol = reco.get('symbol', 'N/A')
            raison = reco.get('raison_principale', 'N/A')
            print(f"   ❌ {symbol:8} - Raison: {raison}")
    else:
        print("⏳ Aucune validation trouvée (en cours...)")
    print()
    
    # 6. Diagnostic final et recommandations
    print("=" * 80)
    print("📋 DIAGNOSTIC FINAL")
    print("=" * 80)
    
    issues = []
    warnings = []
    success = []
    
    # Vérifications
    if json_files:
        success.append("Recommandations IA générées")
    else:
        issues.append("Aucune recommandation IA générée")
    
    if count_today >= 40:
        success.append(f"Collecte aujourd'hui OK ({count_today}/47)")
    elif count_today >= 20:
        warnings.append(f"Collecte partielle aujourd'hui ({count_today}/47)")
    else:
        issues.append(f"Collecte insuffisante aujourd'hui ({count_today}/47)")
    
    if len(dates_with_data) >= 5:
        success.append(f"Historique 7j OK ({len(dates_with_data)} jours)")
    elif len(dates_with_data) >= 3:
        warnings.append(f"Historique limité ({len(dates_with_data)} jours)")
    else:
        issues.append(f"Historique insuffisant ({len(dates_with_data)} jours)")
    
    if real_pct >= 90:
        success.append(f"Qualité excellente ({real_pct:.0f}% réelles)")
    elif real_pct >= 70:
        warnings.append(f"Qualité acceptable ({real_pct:.0f}% réelles)")
    else:
        issues.append(f"Qualité insuffisante ({real_pct:.0f}% réelles)")
    
    # Affichage
    if success:
        print("\n✅ POINTS POSITIFS:")
        for item in success:
            print(f"   • {item}")
    
    if warnings:
        print("\n⚠️  AVERTISSEMENTS:")
        for item in warnings:
            print(f"   • {item}")
    
    if issues:
        print("\n❌ PROBLÈMES CRITIQUES:")
        for item in issues:
            print(f"   • {item}")
    
    # Recommandations d'actions
    print("\n🚀 PROCHAINES ACTIONS:")
    
    if not json_files:
        print("   1. Générer recommandations IA : python generer_top5_nlp.py")
    
    if count_today < 40:
        print("   1. Collecter 47 actions : python collecter_brvm_complet.py")
    
    if len(dates_with_data) < 5:
        print("   2. Constituer historique 60 jours")
    
    if not validation_files:
        print("   3. Exécuter validation : python valider_recommandations_fiables.py")
    else:
        print("   3. ✅ Validation déjà effectuée")
    
    print("\n   4. Workflow quotidien :")
    print("      - Matin : Valider recommandations (confiance ≥70%)")
    print("      - 16h30 : Collecter données jour")
    print("      - Vendredi : Suivre performance réelle")
    
    # Statut global
    print("\n" + "=" * 80)
    if not issues and not warnings:
        print("🎯 STATUT : SYSTÈME 100% OPÉRATIONNEL")
        print("   Vous pouvez trader en confiance les recommandations validées.")
    elif not issues:
        print("⚠️  STATUT : SYSTÈME OPÉRATIONNEL AVEC LIMITATIONS")
        print("   Trading possible mais améliorer les points d'avertissement.")
    else:
        print("❌ STATUT : SYSTÈME NON OPÉRATIONNEL")
        print("   Résoudre les problèmes critiques avant de trader.")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    main()
