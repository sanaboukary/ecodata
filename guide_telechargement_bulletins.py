#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assistant Interactif - Téléchargement des 60 Bulletins PDF BRVM
Guide pas à pas pour constituer l'historique 60 jours
"""

import os
import sys
from datetime import datetime, timedelta

def afficher_header():
    """Affiche l'en-tête du guide."""
    print("\n" + "=" * 80)
    print("📥 ASSISTANT TÉLÉCHARGEMENT - 60 BULLETINS PDF BRVM")
    print("=" * 80)
    print("\n🎯 OBJECTIF : Télécharger 60 bulletins de cotation BRVM")
    print("   → Période : 09 octobre 2025 au 08 décembre 2025")
    print("   → Résultat : ~2820 observations pour trading hebdomadaire\n")

def creer_dossier_bulletins():
    """Crée le dossier bulletins_brvm s'il n'existe pas."""
    dossier = "bulletins_brvm"
    
    if not os.path.exists(dossier):
        os.makedirs(dossier)
        print(f"✅ Dossier '{dossier}/' créé")
    else:
        # Compter les PDF existants
        pdf_files = [f for f in os.listdir(dossier) if f.endswith('.pdf')]
        print(f"📁 Dossier '{dossier}/' existe déjà")
        print(f"   → {len(pdf_files)} fichier(s) PDF déjà présent(s)")
    
    return dossier

def generer_dates_cibles():
    """Génère la liste des dates cibles pour les 60 derniers jours."""
    date_fin = datetime(2025, 12, 8)
    date_debut = date_fin - timedelta(days=59)
    
    dates = []
    date_actuelle = date_debut
    
    while date_actuelle <= date_fin:
        # Exclure les weekends
        if date_actuelle.weekday() < 5:  # 0-4 = lundi à vendredi
            dates.append(date_actuelle)
        date_actuelle += timedelta(days=1)
    
    return dates

def afficher_instructions_detaillees():
    """Affiche les instructions détaillées de téléchargement."""
    
    print("\n" + "=" * 80)
    print("📋 INSTRUCTIONS DÉTAILLÉES")
    print("=" * 80)
    
    print("\n🌐 ÉTAPE 1 : Accéder au site BRVM")
    print("-" * 80)
    print("1. Ouvrir votre navigateur web")
    print("2. Aller sur : https://www.brvm.org/fr/actualites-publications")
    print("3. Chercher la section \"Bulletins de cotation\" ou \"Publications quotidiennes\"")
    
    print("\n📥 ÉTAPE 2 : Télécharger les bulletins")
    print("-" * 80)
    print("Pour CHAQUE jour ouvrable (lundi-vendredi) de la période :")
    print("   • 09 octobre 2025 → 08 décembre 2025")
    print("   • Soit environ 43-45 bulletins")
    print()
    print("Action pour chaque bulletin :")
    print("   1. Cliquer sur le PDF du bulletin quotidien")
    print("   2. Télécharger le fichier")
    print("   3. Sauvegarder dans : bulletins_brvm/")
    print("   4. Nommer de préférence : bulletin_YYYY-MM-DD.pdf")
    print("      Exemple : bulletin_2025-12-08.pdf")
    
    print("\n💡 ASTUCES POUR GAGNER DU TEMPS :")
    print("-" * 80)
    print("✓ Téléchargement par mois :")
    print("   • Octobre 2025 : du 09/10 au 31/10 → ~17 bulletins")
    print("   • Novembre 2025 : du 01/11 au 30/11 → ~20 bulletins")
    print("   • Décembre 2025 : du 01/12 au 08/12 → ~6 bulletins")
    print()
    print("✓ Vérification rapide :")
    print("   • Chaque PDF doit contenir un tableau des cotations")
    print("   • Colonnes typiques : Symbole, Cours, Variation, Volume, etc.")
    print("   • Taille typique : 100-500 KB par PDF")

def afficher_checklist_dates():
    """Affiche une checklist des dates à télécharger."""
    
    dates = generer_dates_cibles()
    
    print("\n" + "=" * 80)
    print("📅 CHECKLIST DES DATES À TÉLÉCHARGER")
    print("=" * 80)
    print(f"\nTotal : {len(dates)} jours ouvrables")
    
    # Grouper par mois
    dates_par_mois = {}
    for date in dates:
        mois = date.strftime("%Y-%m")
        if mois not in dates_par_mois:
            dates_par_mois[mois] = []
        dates_par_mois[mois].append(date)
    
    for mois, dates_mois in sorted(dates_par_mois.items()):
        mois_nom = datetime.strptime(mois, "%Y-%m").strftime("%B %Y")
        print(f"\n📆 {mois_nom.upper()} ({len(dates_mois)} jours) :")
        print("-" * 80)
        
        for i, date in enumerate(dates_mois, 1):
            jour_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven"][date.weekday()]
            date_str = date.strftime("%Y-%m-%d")
            print(f"   {i:2d}. [ ] {jour_semaine} {date_str}  →  bulletin_{date_str}.pdf")

def afficher_verification_post_telechargement():
    """Affiche les instructions de vérification."""
    
    print("\n" + "=" * 80)
    print("✅ ÉTAPE 3 : VÉRIFICATION APRÈS TÉLÉCHARGEMENT")
    print("=" * 80)
    
    print("\n1️⃣  Vérifier le nombre de fichiers :")
    print("   Dans bulletins_brvm/, vous devez avoir 43-45 fichiers PDF")
    print()
    print("2️⃣  Vérifier la qualité des PDF :")
    print("   • Ouvrir quelques PDF au hasard")
    print("   • Vérifier que le tableau des cotations est lisible")
    print("   • Vérifier que la date est visible")
    
    print("\n3️⃣  Lancer le parser automatique :")
    print("   Commande : python parser_bulletins_brvm_pdf.py")
    print()
    print("4️⃣  Importer les données :")
    print("   Commande : python importer_csv_brvm.py historique_brvm_60jours.csv")
    print()
    print("5️⃣  Vérifier l'import :")
    print("   Commande : python verifier_historique_60jours.py")
    print("   Attendu : ~2820 observations (47 actions × 60 jours)")

def afficher_plan_b():
    """Affiche les alternatives en cas de problème."""
    
    print("\n" + "=" * 80)
    print("🆘 PLAN B - EN CAS DE DIFFICULTÉ")
    print("=" * 80)
    
    print("\n❓ Problème : Site BRVM inaccessible ou bulletins introuvables")
    print("-" * 80)
    print("Solution 1 : Contacter la BRVM directement")
    print("   • Email : info@brvm.org")
    print("   • Demander les bulletins de cotation des 60 derniers jours")
    print()
    print("Solution 2 : Utiliser le scraper automatique")
    print("   • Commande : python scripts/connectors/brvm_scraper_production.py")
    print("   • Note : Nécessite que le site BRVM soit accessible")
    print()
    print("Solution 3 : Import CSV manuel")
    print("   • Utiliser template_import_brvm.csv")
    print("   • Remplir manuellement avec les cours officiels")
    print("   • Plus long mais garantit 100% de précision")
    
    print("\n❓ Problème : PDFs corrompus ou illisibles")
    print("-" * 80)
    print("Solution : Re-télécharger les PDFs défectueux")
    print("   • Le parser affichera les PDFs non parsables")
    print("   • Re-télécharger uniquement ceux-là")

def afficher_estimation_temps():
    """Affiche l'estimation du temps nécessaire."""
    
    print("\n" + "=" * 80)
    print("⏱️  ESTIMATION DU TEMPS")
    print("=" * 80)
    
    print("\n📥 Téléchargement des 60 bulletins :")
    print("   • Optimiste : 30-45 minutes (si organisation efficace)")
    print("   • Réaliste : 1-2 heures (avec pauses)")
    print("   • Pessimiste : 3 heures (si problèmes d'accès)")
    
    print("\n⚙️  Traitement automatique :")
    print("   • Parser PDF : 2-5 minutes")
    print("   • Import MongoDB : 30 secondes")
    print("   • Vérification : 10 secondes")
    
    print("\n📊 TOTAL : 1-3 heures pour historique 60 jours complet")

def compter_pdf_existants(dossier):
    """Compte les PDFs déjà téléchargés."""
    if not os.path.exists(dossier):
        return 0
    
    pdf_files = [f for f in os.listdir(dossier) if f.endswith('.pdf')]
    return len(pdf_files)

def main():
    """Fonction principale."""
    
    afficher_header()
    
    # Créer le dossier
    dossier = creer_dossier_bulletins()
    nb_pdf = compter_pdf_existants(dossier)
    
    if nb_pdf > 0:
        print(f"\n💡 Vous avez déjà {nb_pdf} PDF(s).")
        print(f"   → Besoin de ~{43 - nb_pdf} PDF(s) supplémentaire(s) pour atteindre 43 jours ouvrables")
    
    # Instructions
    afficher_instructions_detaillees()
    
    # Checklist
    afficher_checklist_dates()
    
    # Vérification
    afficher_verification_post_telechargement()
    
    # Plan B
    afficher_plan_b()
    
    # Estimation temps
    afficher_estimation_temps()
    
    # Footer
    print("\n" + "=" * 80)
    print("🚀 PRÊT À COMMENCER ?")
    print("=" * 80)
    print("\n1. Ouvrir votre navigateur")
    print("2. Aller sur : https://www.brvm.org/fr/actualites-publications")
    print("3. Suivre la checklist ci-dessus")
    print("4. Une fois terminé, revenir ici et exécuter :")
    print("   → python parser_bulletins_brvm_pdf.py")
    print("\nBonne chance ! 🍀")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur. À bientôt !")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
