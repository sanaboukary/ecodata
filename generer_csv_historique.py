#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur Interactif de CSV Historique BRVM
Aide à créer un fichier CSV pour import massif
"""

import os
import sys
import io
from datetime import datetime, timedelta
import csv

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Liste complète des 47 actions BRVM
ACTIONS_BRVM = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS',
    'BOAG', 'CABC', 'CBIBF', 'CFAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'LIBC',
    'NEIC', 'NSBC', 'NSIAS', 'NSIAC', 'NTLC', 'ONTBF', 'ORGT', 'PALC', 'PRSC',
    'PVBC', 'SAFC', 'SCRC', 'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC',
    'SICC', 'SICG', 'SITC', 'SLBC', 'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC',
    'TTLS', 'UNLC'
]

def generer_dates_ouvrables(date_debut, nb_jours=60):
    """Génère les dates ouvrables (lun-ven) sur nb_jours."""
    dates = []
    date_actuelle = date_debut
    jours_ajoutes = 0
    
    while jours_ajoutes < nb_jours:
        # Exclure weekends
        if date_actuelle.weekday() < 5:  # 0-4 = lundi à vendredi
            dates.append(date_actuelle.strftime('%Y-%m-%d'))
            jours_ajoutes += 1
        date_actuelle += timedelta(days=1)
    
    return dates

def afficher_header():
    """Affiche l'en-tête."""
    print("\n" + "=" * 80)
    print("📝 GÉNÉRATEUR CSV HISTORIQUE BRVM")
    print("=" * 80)
    print("\n🎯 Ce script va vous aider à créer un CSV pour import massif")
    print("   → Format : DATE,SYMBOL,CLOSE,VOLUME,VARIATION")
    print("   → 47 actions BRVM disponibles")
    print("   → Dates ouvrables automatiques\n")

def mode_rapide():
    """Génère un template avec valeurs fictives pour structure."""
    print("\n🚀 MODE RAPIDE - Génération Template")
    print("-" * 80)
    
    # Paramètres
    print("\n1️⃣  Période à couvrir :")
    print("   a) 7 derniers jours (1 semaine)")
    print("   b) 30 derniers jours (1 mois)")
    print("   c) 60 derniers jours (2 mois) [RECOMMANDÉ pour trading]")
    print("   d) Personnalisé")
    
    choix = input("\nVotre choix (a/b/c/d) : ").strip().lower()
    
    if choix == 'a':
        nb_jours = 5  # 5 jours ouvrables
        date_fin = datetime.now()
    elif choix == 'b':
        nb_jours = 22  # ~22 jours ouvrables par mois
        date_fin = datetime.now()
    elif choix == 'd':
        try:
            nb_jours = int(input("Nombre de jours ouvrables : "))
            date_fin = datetime.now()
        except ValueError:
            print("❌ Nombre invalide, utilisation de 43 jours (60 jours calendaires)")
            nb_jours = 43
            date_fin = datetime.now()
    else:  # 'c' ou défaut
        nb_jours = 43  # ~43 jours ouvrables sur 60 jours calendaires
        date_fin = datetime.now()
    
    # Calculer date de début
    date_debut = date_fin - timedelta(days=nb_jours * 2)  # Large marge pour weekends
    
    # Générer dates
    dates = generer_dates_ouvrables(date_debut, nb_jours)
    
    print(f"\n2️⃣  Actions à inclure :")
    print("   a) Toutes les 47 actions BRVM [RECOMMANDÉ]")
    print("   b) Top 10 uniquement (plus liquides)")
    print("   c) Personnalisé (choisir)")
    
    choix_actions = input("\nVotre choix (a/b/c) : ").strip().lower()
    
    if choix_actions == 'b':
        actions = ['SNTS', 'BICC', 'SGBC', 'SIBC', 'BOAM', 'ECOC', 'ETIT', 'NTLC', 'SAFC', 'PALC']
    elif choix_actions == 'c':
        print("\n📋 Actions disponibles :")
        for i, action in enumerate(ACTIONS_BRVM, 1):
            print(f"   {i:2d}. {action}", end="   ")
            if i % 5 == 0:
                print()
        print("\n\n💡 Entrez les symboles séparés par des virgules (ex: SNTS,BICC,SGBC)")
        actions_input = input("Symboles : ").strip().upper()
        actions = [a.strip() for a in actions_input.split(',') if a.strip() in ACTIONS_BRVM]
        if not actions:
            print("⚠️  Aucune action valide, utilisation de toutes les actions")
            actions = ACTIONS_BRVM
    else:
        actions = ACTIONS_BRVM
    
    # Nom du fichier
    print(f"\n3️⃣  Nom du fichier :")
    filename = input(f"   (défaut: historique_brvm_{nb_jours}jours.csv) : ").strip()
    if not filename:
        filename = f"historique_brvm_{nb_jours}jours.csv"
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    # Type de génération
    print(f"\n4️⃣  Type de données :")
    print("   a) Template vide (vous remplissez les cours)")
    print("   b) Valeurs exemple (pour tester la structure)")
    
    choix_data = input("\nVotre choix (a/b) : ").strip().lower()
    with_examples = choix_data == 'b'
    
    # Génération
    print(f"\n🔄 Génération du fichier...")
    print(f"   • {len(dates)} jours ouvrables")
    print(f"   • {len(actions)} actions")
    print(f"   • {len(dates) * len(actions)} lignes au total")
    
    total_lignes = len(dates) * len(actions)
    
    # Créer le CSV
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['DATE', 'SYMBOL', 'CLOSE', 'VOLUME', 'VARIATION'])
        
        for i, date in enumerate(dates):
            for action in actions:
                if with_examples:
                    # Valeurs exemple (fictives mais réalistes)
                    import random
                    base_price = random.randint(2000, 20000)
                    close = base_price
                    volume = random.randint(500, 10000)
                    variation = round(random.uniform(-3.0, 3.0), 2)
                else:
                    # Template vide
                    close = ''
                    volume = ''
                    variation = ''
                
                writer.writerow([date, action, close, volume, variation])
            
            # Progress
            if (i + 1) % 10 == 0 or i == len(dates) - 1:
                progress = ((i + 1) / len(dates)) * 100
                print(f"   Progression : {progress:.0f}%", end='\r')
    
    print(f"\n\n✅ Fichier créé : {filename}")
    print(f"   📊 {total_lignes} lignes générées")
    
    if not with_examples:
        print(f"\n💡 PROCHAINES ÉTAPES :")
        print(f"   1. Ouvrir le fichier : {filename}")
        print(f"   2. Remplir les colonnes CLOSE, VOLUME, VARIATION")
        print(f"      (Vous pouvez laisser des lignes vides si données manquantes)")
        print(f"   3. Sauvegarder en UTF-8")
        print(f"   4. Importer : python collecter_csv_automatique.py")
    else:
        print(f"\n💡 PROCHAINES ÉTAPES :")
        print(f"   1. Tester l'import : python collecter_csv_automatique.py --dry-run")
        print(f"   2. Si OK, remplacer par vos vraies données")
        print(f"   3. Import réel : python collecter_csv_automatique.py")
    
    return filename

def mode_interactif():
    """Mode interactif pour remplir jour par jour."""
    print("\n📝 MODE INTERACTIF - Saisie Guidée")
    print("-" * 80)
    print("\n⚠️  Ce mode est adapté pour quelques jours seulement")
    print("   Pour 60 jours, utilisez plutôt le mode rapide + tableur\n")
    
    nb_jours = int(input("Combien de jours voulez-vous saisir ? (max 10 recommandé) : "))
    if nb_jours > 10:
        print("⚠️  Plus de 10 jours : passage recommandé au mode rapide")
        return None
    
    date_debut_str = input("Date de début (YYYY-MM-DD) : ").strip()
    try:
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d')
    except ValueError:
        print("❌ Format de date invalide")
        return None
    
    dates = generer_dates_ouvrables(date_debut, nb_jours)
    
    print(f"\n📅 Dates à saisir : {', '.join(dates)}")
    print("\nActions à saisir (ou vide pour toutes) :")
    actions_input = input("Symboles (ex: SNTS,BICC) : ").strip().upper()
    if actions_input:
        actions = [a.strip() for a in actions_input.split(',') if a.strip() in ACTIONS_BRVM]
    else:
        actions = ACTIONS_BRVM
    
    filename = f"historique_brvm_{nb_jours}jours_interactif.csv"
    
    # Saisie
    data = []
    print(f"\n📝 Saisie des données (Entrée vide = skip)")
    print("-" * 80)
    
    for date in dates:
        print(f"\n📆 {date}")
        for action in actions:
            print(f"   {action:10s} → ", end="")
            close = input("Close: ").strip()
            if not close:
                continue
            
            volume = input(f"   {' '*10}    Volume: ").strip() or '0'
            variation = input(f"   {' '*10}    Variation%: ").strip() or '0'
            
            data.append([date, action, close, volume, variation])
    
    # Sauvegarder
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['DATE', 'SYMBOL', 'CLOSE', 'VOLUME', 'VARIATION'])
        writer.writerows(data)
    
    print(f"\n✅ Fichier créé : {filename}")
    print(f"   📊 {len(data)} lignes saisies")
    
    return filename

def mode_aide():
    """Affiche l'aide et les conseils."""
    print("\n📚 AIDE - Comment Remplir votre CSV")
    print("=" * 80)
    
    print("\n🎯 OBJECTIF : Créer un CSV avec vos données historiques BRVM\n")
    
    print("📋 FORMAT REQUIS :")
    print("-" * 80)
    print("DATE,SYMBOL,CLOSE,VOLUME,VARIATION")
    print("2025-12-07,SNTS,15500,8500,2.3")
    print("2025-12-07,BICC,7200,1250,1.2")
    print("...")
    
    print("\n📊 COLONNES :")
    print("-" * 80)
    print("• DATE       : Format YYYY-MM-DD (ex: 2025-12-07)")
    print("• SYMBOL     : Code action BRVM (ex: SNTS, BICC)")
    print("• CLOSE      : Cours de clôture en FCFA (ex: 15500)")
    print("• VOLUME     : Volume échangé (ex: 8500)")
    print("• VARIATION  : Variation % (ex: 2.3 pour +2.3%)")
    
    print("\n✅ CONSEILS :")
    print("-" * 80)
    print("1. Utiliser le mode rapide pour générer la structure")
    print("2. Ouvrir le CSV avec Excel/LibreOffice")
    print("3. Remplir les cours (copier-coller depuis vos sources)")
    print("4. Sauvegarder en UTF-8")
    print("5. Importer : python collecter_csv_automatique.py")
    
    print("\n🏢 47 ACTIONS BRVM :")
    print("-" * 80)
    for i, action in enumerate(ACTIONS_BRVM, 1):
        print(f"{action:10s}", end="")
        if i % 6 == 0:
            print()
    print()
    
    print("\n⏱️  ESTIMATION TEMPS :")
    print("-" * 80)
    print("• Mode rapide (template)    : 2 minutes")
    print("• Remplir tableur (60j)     : 2-4 heures")
    print("• Import automatique        : 30 secondes")
    print("• TOTAL                     : 2-4 heures")
    
    print("\n💡 ALTERNATIVE RECOMMANDÉE :")
    print("-" * 80)
    print("Si vous n'avez pas les données facilement :")
    print("→ Télécharger les bulletins PDF BRVM (plus rapide)")
    print("→ Parser automatique avec parser_bulletins_brvm_pdf.py")
    print("→ Import automatique")
    
    print("\n" + "=" * 80 + "\n")

def main():
    """Fonction principale."""
    afficher_header()
    
    print("🔧 MODES DISPONIBLES :")
    print("-" * 80)
    print("1. Mode Rapide     : Générer un template CSV à remplir")
    print("2. Mode Interactif : Saisie guidée jour par jour (≤10 jours)")
    print("3. Aide           : Voir les instructions détaillées")
    print("4. Quitter\n")
    
    choix = input("Votre choix (1/2/3/4) : ").strip()
    
    if choix == '1':
        filename = mode_rapide()
        if filename:
            print(f"\n🎯 Fichier prêt à remplir : {filename}")
            print("\nVoulez-vous le tester maintenant ?")
            test = input("Test import (y/n) : ").strip().lower()
            if test == 'y':
                print("\n🧪 Test import...")
                os.system(f'python collecter_csv_automatique.py --dry-run')
    
    elif choix == '2':
        filename = mode_interactif()
        if filename:
            print(f"\n🎯 Données saisies : {filename}")
            print("\nVoulez-vous importer maintenant ?")
            import_now = input("Import (y/n) : ").strip().lower()
            if import_now == 'y':
                os.system(f'python collecter_csv_automatique.py')
    
    elif choix == '3':
        mode_aide()
    
    else:
        print("\n👋 Au revoir !\n")
        return
    
    print("\n" + "=" * 80)
    print("✅ Terminé !")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
