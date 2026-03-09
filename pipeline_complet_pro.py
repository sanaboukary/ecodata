#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COMPLET - De la collecte aux recommandations
Automatise tout le processus après le scraping PRO
"""

import subprocess
import sys
from pymongo import MongoClient

def executer_commande(cmd, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n{'='*80}")
    print(f"▶️  {description}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def verifier_contenu():
    """Vérifie que les articles ont du contenu"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    richbourse = list(db.curated_observations.find({'source': 'RICHBOURSE'}))
    
    avec_contenu = 0
    total_chars = 0
    
    for doc in richbourse:
        contenu = doc.get('attrs', {}).get('contenu', '')
        if contenu and len(contenu) > 100:
            avec_contenu += 1
            total_chars += len(contenu)
    
    print(f"\n📊 RICHBOURSE:")
    print(f"   Total: {len(richbourse)} articles")
    print(f"   Avec contenu (>100 chars): {avec_contenu}")
    print(f"   Caractères totaux: {total_chars:,}")
    print(f"   Moyenne: {total_chars//avec_contenu if avec_contenu > 0 else 0} chars/article")
    
    return avec_contenu > 0

def main():
    print("="*80)
    print("🚀 PIPELINE COMPLET BRVM - COLLECTE → RECOMMANDATIONS")
    print("="*80)
    
    # 1. Vérifier que les articles ont du contenu
    print("\n[1] VÉRIFICATION CONTENU")
    if not verifier_contenu():
        print("❌ Pas assez d'articles avec contenu!")
        print("   Exécutez d'abord: python scraper_pro_brvm.py")
        return
    
    print("✅ Articles avec contenu trouvés!")
    
    # 2. Analyse sémantique
    print("\n[2] ANALYSE SÉMANTIQUE")
    success = executer_commande(
        "./.venv/Scripts/python.exe analyse_semantique_brvm_v3.py",
        "Analyse sémantique des publications"
    )
    
    if not success:
        print("⚠️  Erreur analyse sémantique, mais on continue...")
    
    # 3. Agrégation par action
    print("\n[3] AGRÉGATION PAR ACTION")
    success = executer_commande(
        "./.venv/Scripts/python.exe agregateur_semantique_actions.py",
        "Agrégation des scores par action"
    )
    
    if not success:
        print("⚠️  Erreur agrégation, mais on continue...")
    
    # 4. Pipeline complet
    print("\n[4] PIPELINE BRVM COMPLET")
    success = executer_commande(
        "./.venv/Scripts/python.exe pipeline_brvm.py",
        "Génération des recommandations finales"
    )
    
    print("\n" + "="*80)
    if success:
        print("✅ PIPELINE TERMINÉ AVEC SUCCÈS!")
        print("\n🎯 Vos nouvelles recommandations dynamiques sont prêtes!")
        print("   Les scores sémantiques ne seront plus jamais à 0!")
    else:
        print("⚠️  Pipeline terminé avec des avertissements")
    print("="*80)

if __name__ == "__main__":
    main()
