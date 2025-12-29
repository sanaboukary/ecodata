#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WORKFLOW QUOTIDIEN COMPLET - Recommandations 100% Fiables
1. Collecte données du jour
2. Génération recommandations
3. Validation stricte
"""

import os
import sys
import json
from datetime import datetime
from pymongo import MongoClient

print("=" * 80)
print("🎯 WORKFLOW QUOTIDIEN - RECOMMANDATIONS 100% FIABLES")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print()

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']
today = datetime.now().strftime('%Y-%m-%d')

# ============================================================================
# ÉTAPE 1 : VÉRIFIER DONNÉES DU JOUR
# ============================================================================
print("📊 ÉTAPE 1/3 : Vérification données du jour")
print("-" * 80)

count_today = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE',
    'ts': today
})

print(f"Date: {today}")
print(f"Actions collectées: {count_today}/47")

if count_today >= 40:
    print("✅ Collecte suffisante pour validation")
    collecte_ok = True
elif count_today >= 30:
    print("⚠️  Collecte partielle - Recommandations possibles mais limitées")
    collecte_ok = True
else:
    print("❌ Collecte insuffisante")
    print("\n🚀 ACTION REQUISE:")
    print("   Exécuter: python collecter_quotidien_intelligent.py")
    print("   OU: python mettre_a_jour_cours_brvm.py (saisie manuelle)")
    collecte_ok = False

if not collecte_ok:
    print("\n⏸️  WORKFLOW INTERROMPU - Collectez d'abord les données")
    print("=" * 80)
    client.close()
    sys.exit(1)

print()

# ============================================================================
# ÉTAPE 2 : GÉNÉRER RECOMMANDATIONS FRAÎCHES
# ============================================================================
print("🎯 ÉTAPE 2/3 : Génération recommandations fraîches")
print("-" * 80)

# Vérifier si recommandations récentes existent
json_files = [f for f in os.listdir('.') if f.startswith('top5_') and f.endswith('.json')]
recent_recos = []
for f in json_files:
    # Vérifier si généré aujourd'hui
    file_date = os.path.getmtime(f)
    file_datetime = datetime.fromtimestamp(file_date)
    if file_datetime.date() == datetime.now().date():
        recent_recos.append(f)

if recent_recos:
    latest_reco = sorted(recent_recos)[-1]
    print(f"✅ Recommandations trouvées: {latest_reco}")
    
    with open(latest_reco, 'r', encoding='utf-8') as f:
        reco_data = json.load(f)
    
    top5 = reco_data.get('top_5', reco_data.get('top5', []))
    print(f"   Nombre d'actions: {len(top5)}")
    
    use_existing = True
else:
    print("⚠️  Aucune recommandation récente trouvée")
    print("\n🚀 Génération en cours...")
    
    # Générer avec données fraîches
    result = os.system('.venv/Scripts/python.exe generer_top5_donnees_fraiches.py')
    
    if result == 0:
        print("✅ Recommandations générées")
        # Recharger le fichier généré
        json_files = [f for f in os.listdir('.') if f.startswith('top5_hebdo_frais_') and f.endswith('.json')]
        if json_files:
            latest_reco = sorted(json_files)[-1]
            with open(latest_reco, 'r', encoding='utf-8') as f:
                reco_data = json.load(f)
            top5 = reco_data.get('top_5', [])
            use_existing = True
        else:
            print("❌ Erreur lors de la génération")
            use_existing = False
    else:
        print("❌ Échec génération")
        use_existing = False

if not use_existing:
    print("\n⏸️  WORKFLOW INTERROMPU - Problème génération recommandations")
    print("=" * 80)
    client.close()
    sys.exit(1)

print()

# ============================================================================
# ÉTAPE 3 : VALIDER RECOMMANDATIONS
# ============================================================================
print("🛡️ ÉTAPE 3/3 : Validation stricte (10 critères)")
print("-" * 80)

print("\n🔍 Validation en cours...")
print("   Fichier source:", latest_reco)

# Exécuter validation
result = os.system(f'.venv/Scripts/python.exe valider_recommandations_fiables.py {latest_reco}')

if result == 0:
    print("\n✅ Validation terminée")
    
    # Chercher fichier validation généré
    val_files = [f for f in os.listdir('.') if f.startswith('recommandations_validees_') and f.endswith('.json')]
    if val_files:
        latest_val = sorted(val_files)[-1]
        
        with open(latest_val, 'r', encoding='utf-8') as f:
            val_data = json.load(f)
        
        validees = val_data.get('recommandations_validees', [])
        rejetees = val_data.get('recommandations_rejetees', [])
        
        print(f"\n📋 RÉSULTATS VALIDATION:")
        print(f"   Fichier: {latest_val}")
        print(f"   ✅ Validées: {len(validees)}")
        print(f"   ❌ Rejetées: {len(rejetees)}")
        
        if validees:
            print(f"\n🎯 RECOMMANDATIONS À TRADER (Confiance ≥70%):")
            print("=" * 80)
            for i, reco in enumerate(validees, 1):
                symbol = reco.get('symbol', 'N/A')
                confiance = reco.get('confiance', 0)
                prix = reco.get('prix_actuel', 0)
                stop_loss = reco.get('stop_loss', 0)
                tp1 = reco.get('take_profit_1', 0)
                
                print(f"\n{i}. {symbol} - CONFIANCE: {confiance:.1f}%")
                print(f"   Prix actuel:   {prix:>10,.0f} FCFA")
                print(f"   Stop-Loss:     {stop_loss:>10,.0f} FCFA (-7%)")
                print(f"   Take-Profit 1: {tp1:>10,.0f} FCFA (+15%)")
                print(f"   Position max:  20% du capital")
            
            print("\n" + "=" * 80)
            print("⚠️  RÈGLES DE TRADING OBLIGATOIRES:")
            print("   • Placer IMMÉDIATEMENT le stop-loss à -7%")
            print("   • Maximum 20% du capital par action")
            print("   • Minimum 3 actions pour diversification")
            print("   • Sortir si confiance passe <70%")
            print("=" * 80)
        else:
            print("\n⚠️  AUCUNE RECOMMANDATION VALIDÉE")
            print("   Raisons possibles:")
            print("   • Données incomplètes (<40 actions)")
            print("   • Volatilité trop élevée (>30%)")
            print("   • Qualité données insuffisante")
            print("   • Momentum négatif (<-10%)")
            print("\n🚀 Actions à prendre:")
            print("   1. Collecter les 47 actions complètes")
            print("   2. Constituer historique 7-14 jours")
            print("   3. Re-générer et re-valider")
        
        if rejetees:
            print(f"\n❌ ACTIONS REJETÉES (NE PAS TRADER):")
            for reco in rejetees[:3]:
                symbol = reco.get('symbol', 'N/A')
                raison = reco.get('raison_principale', 'N/A')
                print(f"   • {symbol:8} - {raison}")
            if len(rejetees) > 3:
                print(f"   ... et {len(rejetees) - 3} autres")
    else:
        print("⚠️  Fichier validation non trouvé")
else:
    print("❌ Erreur lors de la validation")

print()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
print("=" * 80)
print("📋 RÉSUMÉ WORKFLOW QUOTIDIEN")
print("=" * 80)

print(f"\n✅ Complété le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
print(f"\n1. Collecte:       {count_today}/47 actions")
print(f"2. Recommandations: {len(top5)} générées")
print(f"3. Validation:     {len(validees) if 'validees' in locals() else 0} validées")

print("\n📅 PROCHAINES ACTIONS:")
print("   • Aujourd'hui: Trader UNIQUEMENT les validées")
print("   • Ce soir 16h30: Collecter nouvelles données")
print("   • Vendredi: Suivre performance réelle (suivre_performance_recos.py)")

print("\n" + "=" * 80)
print("🎯 BON TRADING ! Respectez les stop-loss et position sizing.")
print("=" * 80)

client.close()
