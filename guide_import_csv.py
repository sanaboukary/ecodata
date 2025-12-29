#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guide d'import CSV pour données historiques BRVM
Avec modèle CSV téléchargeable
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

def creer_modele_csv():
    """Crée un fichier CSV modèle avec instructions"""
    
    modele = """DATE,SYMBOL,CLOSE,VOLUME,VARIATION
# Format des colonnes:
# DATE: YYYY-MM-DD (ex: 2025-12-15)
# SYMBOL: Code action BRVM (ex: SNTS, SGBC, UNLC)
# CLOSE: Cours de clôture en FCFA (ex: 25500)
# VOLUME: Volume échangé (optionnel, ex: 8500)
# VARIATION: Variation en % (optionnel, ex: 2.3)
#
# IMPORTANT: Supprimer ces lignes de commentaires avant l'import
# Exemples de données (à remplacer par vos vraies données):
2025-12-15,SNTS,25500,8500,2.3
2025-12-15,SGBC,29490,1200,-1.2
2025-12-15,UNLC,43290,950,0.5
2025-12-14,SNTS,24900,7800,1.8
2025-12-14,SGBC,29850,1500,-0.8
2025-12-14,UNLC,43080,1100,1.2
"""
    
    filepath = Path("modele_import_brvm.csv")
    filepath.write_text(modele, encoding='utf-8')
    
    return filepath

def afficher_guide():
    """Affiche le guide d'import CSV"""
    
    print("="*80)
    print("GUIDE D'IMPORT CSV - DONNEES HISTORIQUES BRVM")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*80)
    
    print("\n📋 ETAPE 1: OBTENIR LES DONNEES CSV")
    print("-" * 80)
    print("""
Sources possibles:

1️⃣  Courtier BRVM (SGI, EDC, etc.)
   → Demander: "Historique des cours 60 derniers jours"
   → Format: Excel ou CSV
   
2️⃣  Terminal Bloomberg/Reuters (si accès)
   → Export données BRVM
   → Période: 60 jours ouvrables
   
3️⃣  Portail BRVM (si membre)
   → Section "Historiques"
   → Export CSV
   
4️⃣  Saisie manuelle depuis bulletins PDF
   → Télécharger bulletins: www.brvm.org
   → Extraire données vers CSV
""")
    
    print("\n📝 ETAPE 2: FORMATER LE CSV")
    print("-" * 80)
    
    # Créer modèle
    modele_path = creer_modele_csv()
    
    print(f"""
Un fichier modèle a été créé: {modele_path}

FORMAT REQUIS:
   Colonnes obligatoires: DATE, SYMBOL, CLOSE
   Colonnes optionnelles: VOLUME, VARIATION
   
   DATE: Format YYYY-MM-DD (ex: 2025-12-15)
   SYMBOL: Code BRVM 4-6 lettres (ex: SNTS, SGBC, UNLC)
   CLOSE: Prix en FCFA, nombre entier (ex: 25500)
   VOLUME: Nombre de titres échangés (ex: 8500)
   VARIATION: En pourcentage (ex: 2.3 pour +2.3%)

EXEMPLE DE CONTENU:
   DATE,SYMBOL,CLOSE,VOLUME,VARIATION
   2025-12-15,SNTS,25500,8500,2.3
   2025-12-15,SGBC,29490,1200,-1.2
   2025-12-15,UNLC,43290,950,0.5

IMPORTANT:
   • Pas de ligne vide
   • Pas de caractères spéciaux (sauf virgule)
   • Prix sans espaces ni symboles (25500 et non "25 500 FCFA")
   • Une ligne par action par jour
""")
    
    print("\n✅ ETAPE 3: VALIDER LE CSV")
    print("-" * 80)
    print("""
Vérifications à faire:

✓ En-tête présent: DATE,SYMBOL,CLOSE (minimum)
✓ Dates au format YYYY-MM-DD
✓ Symboles valides BRVM (4-6 lettres majuscules)
✓ Prix > 0 et < 200000 FCFA
✓ Pas de données manquantes dans colonnes obligatoires
✓ Encodage UTF-8 (pas de caractères bizarres)

NOMBRE DE LIGNES ATTENDU:
   60 jours × 47 actions ≈ 2820 lignes
   
   Note: Certains jours peuvent avoir moins d'actions
   (jours fériés, suspensions, etc.)
   
   Minimum acceptable: 40 jours × 40 actions ≈ 1600 lignes
""")
    
    print("\n💾 ETAPE 4: IMPORTER DANS MONGODB")
    print("-" * 80)
    print("""
Commande d'import:

   python collecter_csv_automatique.py --fichier votre_fichier.csv

Ou si le fichier est dans csv_brvm/:

   python collecter_csv_automatique.py --dossier csv_brvm

Le script va:
   1. Lire le CSV
   2. Valider les données
   3. Marquer comme REAL_SCRAPER
   4. Insérer dans MongoDB (évite doublons)
   5. Afficher rapport détaillé
""")
    
    print("\n🔍 ETAPE 5: VERIFIER L'IMPORT")
    print("-" * 80)
    print("""
Après import, vérifier:

   python verifier_historique_rapide.py

Résultat attendu:
   • Total observations: ~2820 (ou votre nombre de lignes)
   • Données REELLES: 100%
   • Jours avec données: 60 (ou votre nombre de jours)
   • Objectif: ATTEINT ✓
""")
    
    print("\n🚀 ETAPE 6: LANCER L'ANALYSE")
    print("-" * 80)
    print("""
Une fois 60 jours importés:

   python systeme_trading_hebdo_auto.py

Avec moins de 60 jours (mais ≥21 jours):

   python trading_adaptatif_demo.py

Le système génèrera:
   • Recommandations BUY/HOLD/SELL
   • Scores de confiance
   • Prix cibles
   • Niveaux techniques
""")
    
    print("\n" + "="*80)
    print("EXEMPLES DE NOMMAGE DE FICHIERS CSV")
    print("="*80)
    print("""
Bons noms:
   ✓ historique_brvm_60jours.csv
   ✓ brvm_data_2025.csv
   ✓ cours_brvm_dec2025.csv
   ✓ export_courtier_brvm.csv

A éviter:
   ✗ données.csv (trop générique)
   ✗ brvm données.csv (espace dans le nom)
   ✗ BRVM_2025.CSV (majuscules)
""")
    
    print("\n" + "="*80)
    print("RESSOURCES")
    print("="*80)
    print("""
📞 Contacts pour obtenir données:

BRVM:
   Email: info@brvm.org
   Tél: +225 20 32 66 85
   Site: www.brvm.org

Courtiers principaux:
   • Société Générale de Bourse CI
   • EDC Investment Corporation
   • Hudson & Cie
   • BICI Bourse
   
💡 Astuce: Certains courtiers fournissent des exports CSV
   si vous êtes client. Demandez "historique cours BRVM".
""")
    
    print("\n" + "="*80)
    print("AIDE EN CAS DE PROBLEME")
    print("="*80)
    print("""
Problème: Format CSV incorrect
→ Solution: Ouvrir avec Excel/LibreOffice, vérifier colonnes

Problème: Erreur d'encodage
→ Solution: Enregistrer en UTF-8 (option dans "Enregistrer sous")

Problème: Dates invalides
→ Solution: Format strict YYYY-MM-DD (2025-12-15 et non 15/12/2025)

Problème: Symboles non reconnus
→ Solution: Vérifier liste des 47 actions BRVM valides

Problème: Prix aberrants
→ Solution: Vérifier que prix sont en FCFA (25500 et non 25.5)

Pour debug détaillé:
   python collecter_csv_automatique.py --fichier XXX.csv --dry-run
""")
    
    print("\n" + "="*80)
    print("FICHIERS UTILES")
    print("="*80)
    print(f"""
✓ Modèle CSV créé: {modele_path}
✓ Guide complet: GUIDE_TELECHARGEMENT_BULLETINS.md
✓ Script d'import: collecter_csv_automatique.py
✓ Vérification: verifier_historique_rapide.py
""")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    afficher_guide()
    
    print("\n💡 PROCHAINE ETAPE:")
    print("   1. Préparer votre fichier CSV avec les données historiques")
    print("   2. Le placer dans le dossier du projet")
    print("   3. Lancer: python collecter_csv_automatique.py --fichier VOTRE_FICHIER.csv")
    print()
