#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 INSTALLATION & ACTIVATION AUTOMATIQUE
Script d'installation complet qui résout le problème des scores à 0
"""

import subprocess
import sys
import time
from pymongo import MongoClient

def executer(cmd, description):
    """Exécute une commande avec affichage"""
    print(f"\n{'='*80}")
    print(f">>> {description}")
    print(f"{'='*80}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.stdout:
        print(result.stdout[:2000])  # Limiter l'affichage
    
    if result.returncode != 0 and result.stderr:
        print(f"⚠️  Erreur: {result.stderr[:500]}")
    
    return result.returncode == 0

def verifier_mongodb():
    """Vérifie la connexion MongoDB"""
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()
        return True
    except Exception as e:
        print(f"[ERREUR] MongoDB non accessible: {e}")
        return False

def compter_resultats():
    """Compte les résultats"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['centralisation_db']
        
        rich = db.curated_observations.count_documents({'source': 'RICHBOURSE'})
        avec_contenu = db.curated_observations.count_documents({
            'source': 'RICHBOURSE',
            'attrs.contenu': {'$exists': True, '$ne': ''}
        })
        agg = db.agregation_semantique_action.count_documents({})
        
        return rich, avec_contenu, agg
    except:
        return 0, 0, 0

def main():
    print("="*80)
    print("INSTALLATION AUTOMATIQUE - SOLUTION SCORES SEMANTIQUES")
    print("="*80)
    
    # Étape 0: Vérifier MongoDB
    print("\n[0] Vérification MongoDB...")
    if not verifier_mongodb():
        print("[ERREUR] MongoDB doit etre demarre!")
        print("   Demarrez MongoDB puis relancez ce script")
        return
    print("[OK] MongoDB accessible")
    
    # Étape 1: Enrichir les articles
    print("\n[1] ENRICHISSEMENT DES ARTICLES")
    print("   Ajout de contenu sémantique aux 116 articles RICHBOURSE...")
    
    success = executer(
        "python enrichir_quick.py",
        "Enrichissement articles RICHBOURSE"
    )
    
    if success:
        print("[OK] Enrichissement termine!")
    else:
        print("[WARN] Probleme enrichissement, mais on continue...")
    
    time.sleep(2)
    
    # Étape 2: Analyse sémantique
    print("\n[2] ANALYSE SÉMANTIQUE")
    print("   Analyse du contenu des articles avec mots-clés BRVM...")
    
    success = executer(
        "python analyse_semantique_brvm_v3.py",
        "Analyse sémantique V3"
    )
    
    if success:
        print("[OK] Analyse terminee!")
    else:
        print("[WARN] Verifiez les logs ci-dessus")
    
    time.sleep(2)
    
    # Étape 3: Agrégation
    print("\n[3] AGRÉGATION PAR ACTION")
    print("   Calcul des scores CT/MT/LT par action...")
    
    success = executer(
        "python agregateur_semantique_actions.py",
        "Agrégation sémantique par action"
    )
    
    if success:
        print("[OK] Agregation terminee!")
    else:
        print("[WARN] Verifiez les logs")
    
    time.sleep(2)
    
    # Étape 4: Pipeline complet
    print("\n[4] GÉNÉRATION RECOMMANDATIONS")
    print("   Pipeline complet avec scores sémantiques...")
    
    success = executer(
        "python pipeline_brvm.py",
        "Pipeline BRVM complet"
    )
    
    # Resultats finaux
    print("\n" + "="*80)
    print("RESULTATS FINAUX")
    print("="*80)
    
    rich, avec_contenu, agg = compter_resultats()
    
    print(f"\nRICHBOURSE:")
    print(f"   Articles total: {rich}")
    print(f"   Avec contenu: {avec_contenu}")
    print(f"   Taux: {avec_contenu/rich*100:.0f}%" if rich > 0 else "0%")
    
    print(f"\nAGREGATION:")
    print(f"   Actions avec scores: {agg}")
    
    if avec_contenu > 50 and agg > 0:
        print("\n" + "="*80)
        print("SUCCES COMPLET!")
        print("="*80)
        print("\n[OK] Votre systeme est maintenant OPERATIONNEL avec:")
        print(f"   - {avec_contenu} articles enrichis")
        print(f"   - {agg} actions avec scores semantiques")
        print("   - Recommandations dynamiques activees")
        print("\n[INFO] Les scores ne seront plus jamais a 0!")
        print("   Relancez pipeline_brvm.py quotidiennement pour mise a jour")
        print("\n[CMD] Commande rapide:")
        print("   python pipeline_brvm.py")
    else:
        print("\n[WARN] Installation partielle")
        print(f"   Contenu: {avec_contenu}/{rich}")
        print(f"   Agregations: {agg}")
        print("\n[FIX] Solutions:")
        print("   1. Relancer: python installation_auto.py")
        print("   2. Verifier MongoDB actif")
        print("   3. Verifier .venv/Scripts/python.exe")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
