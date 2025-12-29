#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚠️  ATTENTION : DONNÉES NON VÉRIFIÉES DÉTECTÉES
================================================

Ce script supprime toutes les données potentiellement incorrectes
et vous guide pour saisir les VRAIS cours depuis le site BRVM.

POLITIQUE ZÉRO TOLÉRANCE:
- Seules les données VÉRIFIÉES manuellement sont acceptées
- AUCUNE estimation ou simulation autorisée
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

def purger_donnees_non_verifiees():
    """Supprime toutes les données BRVM non vérifiées"""
    
    print("\n" + "="*70)
    print("⚠️  PURGE DES DONNÉES NON VÉRIFIÉES")
    print("="*70)
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    # Supprimer TOUTES les données BRVM (car non vérifiées)
    result = collection.delete_many({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE'
    })
    
    print(f"\n🗑️  {result.deleted_count} observations BRVM supprimées")
    print("✅ Base de données BRVM maintenant VIDE")
    print("\n" + "="*70)
    
    return result.deleted_count

def guide_saisie_manuelle():
    """Guide pour saisir les vrais cours"""
    
    print("\n📝 GUIDE DE SAISIE DES VRAIS COURS BRVM")
    print("="*70)
    print("""
🌐 ÉTAPE 1: Aller sur le site officiel BRVM
   → https://www.brvm.org/fr/investir/cours-et-cotations
   → Ou: https://www.brvm.org/fr/cours/actions

📋 ÉTAPE 2: Copier les cours du jour dans Excel/Google Sheets
   Format requis:
   
   DATE       | SYMBOL | CLOSE  | VOLUME | VARIATION
   2025-12-09 | SNTS   | 15500  | 8500   | 2.3
   2025-12-09 | SGBC   | 2150   | 12000  | -0.5
   ... (pour les ~50 actions cotées)

💾 ÉTAPE 3: Sauvegarder en CSV
   → Nom: csv/cours_brvm_20251209_VERIFIE.csv
   → Encodage: UTF-8

📥 ÉTAPE 4: Importer dans la base
   → python collecter_csv_automatique.py --dossier csv

✅ ÉTAPE 5: Vérifier l'import
   → python verifier_cours_brvm.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  IMPORTANT:
- Ne JAMAIS inventer ou estimer des prix
- Toujours copier depuis le site officiel BRVM
- Marquer le fichier CSV comme "VERIFIE" dans le nom
- Supprimer tout fichier contenant des données anciennes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 ALTERNATIVE: Saisie directe dans Python

   Si vous préférez saisir directement dans un script:
   
   1. Créer le fichier: saisir_cours_brvm_manuel.py
   2. Copier-coller les cours depuis BRVM
   3. Lancer: python saisir_cours_brvm_manuel.py
   
   (Plus rapide que CSV pour quelques actions)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

def main():
    print("\n" + "🔴"*35)
    print("ALERTE: DONNÉES NON VÉRIFIÉES DANS LA BASE")
    print("🔴"*35)
    
    print("""
Les données actuellement dans votre base MongoDB proviennent de:
- Imports CSV anciens (dates 2025-12-05 à 2025-12-08)
- Script "corriger_prix_brvm_vrais.py" (prix NON vérifiés)

Ces données violent votre politique ZÉRO TOLÉRANCE.

⚠️  ACTION REQUISE: Purger et resaisir avec vrais cours BRVM
""")
    
    reponse = input("\n❓ Voulez-vous PURGER toutes les données BRVM non vérifiées ? (oui/non): ").strip().lower()
    
    if reponse in ['oui', 'o', 'yes', 'y']:
        count = purger_donnees_non_verifiees()
        guide_saisie_manuelle()
        
        print("\n" + "="*70)
        print("✅ PURGE TERMINÉE")
        print("="*70)
        print(f"\n📊 {count} observations supprimées")
        print("🗃️  Base BRVM maintenant VIDE et propre")
        print("\n👉 Suivez le guide ci-dessus pour saisir les VRAIS cours")
        print("="*70)
    else:
        print("\n⚠️  Purge annulée - Base de données inchangée")
        print("⚠️  Attention: Votre base contient des données NON VÉRIFIÉES")

if __name__ == '__main__':
    main()
