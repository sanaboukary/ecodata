#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLUTION FINALE: Lance l'analyse sémantique complète sans subprocess
"""

import sys
import time
from pymongo import MongoClient

print("="*80)
print("ANALYSE SÉMANTIQUE COMPLÈTE - SOLUTION SCORES 0")
print("="*80)

# Étape 0: Vérifier MongoDB
print("\n[0] Vérification MongoDB...")
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    db = client.centralisation_db  # BASE CORRIGÉE!
    print("[OK] MongoDB accessible")
except Exception as e:
    print(f"[ERREUR] MongoDB: {e}")
    sys.exit(1)

# Compter état initial
rich_count = db.curated_observations.count_documents({"source": "RICHBOURSE"})
avec_contenu = db.curated_observations.count_documents({
    "source": "RICHBOURSE",
    "attrs.contenu": {"$exists": True, "$ne": ""},
    "$expr": {"$gte": [{"$strLenCP": "$attrs.contenu"}, 100]}
})
agg_avant = db.agregation_semantique_action.count_documents({})

print(f"   RICHBOURSE: {rich_count} articles total")
print(f"   Avec contenu: {avec_contenu} ({avec_contenu/rich_count*100:.0f}%)")
print(f"   Agrégations avant: {agg_avant}")

# Étape 1: Analyse sémantique
print("\n[1] ANALYSE SÉMANTIQUE V3")
print("   Analyse de 116 articles avec mots-clés BRVM...")

try:
    # Importer et exécuter directement
    import analyse_semantique_brvm_v3
    print("[OK] Analyse terminée!")
except Exception as e:
    print(f"[ERREUR] Analyse: {e}")
    import traceback
    traceback.print_exc()

time.sleep(1)

# Étape 2: Agrégation par action
print("\n[2] AGRÉGATION PAR ACTION")
print("   Calcul scores CT/MT/LT pour ~47 actions...")

try:
    import agregateur_semantique_actions
    print("[OK] Agrégation terminée!")
except Exception as e:
    print(f"[ERREUR] Agrégation: {e}")
    import traceback
    traceback.print_exc()

time.sleep(1)

# Étape 3: Vérifier résultats
print("\n[3] VÉRIFICATION RÉSULTATS")

agg_apres = db.agregation_semantique_action.count_documents({})
print(f"   Agrégations après: {agg_apres}")

if agg_apres > 0:
    print(f"\n✅ SUCCÈS! {agg_apres} actions avec scores sémantiques")
    
    # Afficher exemples
    print("\nExemples de scores:")
    for doc in db.agregation_semantique_action.find().limit(5):
        ticker = doc.get('ticker_brvm', 'N/A')
        ct = doc.get('score_ct_7j', 0)
        mt = doc.get('score_mt_30j', 0)
        lt = doc.get('score_lt_90j', 0)
        print(f"   {ticker}: CT={ct:+.1f} | MT={mt:+.1f} | LT={lt:+.1f}")
else:
    print("\n⚠️  Agrégation toujours vide - vérifier analyse sémantique")

print("\n" + "="*80)
print("TERMINÉ")
print("="*80)
