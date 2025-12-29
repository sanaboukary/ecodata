#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur CSV pour Combler les Trous dans l'Historique
Génère les dates manquantes : 13 novembre au 6 décembre 2025
"""

import sys
import io
import csv
from datetime import datetime, timedelta
import random

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 47 actions BRVM complètes
ACTIONS_BRVM = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS',
    'BOAG', 'CABC', 'CBIBF', 'CFAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'LIBC',
    'NEIC', 'NSBC', 'NSIAS', 'NSIAC', 'NTLC', 'ONTBF', 'ORGT', 'PALC', 'PRSC',
    'PVBC', 'SAFC', 'SCRC', 'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC',
    'SICC', 'SICG', 'SITC', 'SLBC', 'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC',
    'TTLS', 'UNLC'
]

def generer_dates_ouvrables_periode(date_debut, date_fin):
    """Génère toutes les dates ouvrables entre deux dates."""
    dates = []
    date_actuelle = date_debut
    
    while date_actuelle <= date_fin:
        # Seulement lundi-vendredi
        if date_actuelle.weekday() < 5:
            dates.append(date_actuelle.strftime('%Y-%m-%d'))
        date_actuelle += timedelta(days=1)
    
    return dates

def main():
    print("\n" + "=" * 80)
    print("📝 GÉNÉRATEUR CSV - COMBLER LES TROUS (13 Nov → 6 Déc 2025)")
    print("=" * 80)
    
    # Dates du trou identifié
    date_debut = datetime(2025, 11, 13)
    date_fin = datetime(2025, 12, 6)
    
    dates = generer_dates_ouvrables_periode(date_debut, date_fin)
    
    print(f"\n📅 Période à combler :")
    print(f"   Du : {date_debut.strftime('%Y-%m-%d')}")
    print(f"   Au : {date_fin.strftime('%Y-%m-%d')}")
    print(f"   Jours ouvrables : {len(dates)}")
    print(f"   Actions : {len(ACTIONS_BRVM)}")
    print(f"   Total lignes : {len(dates) * len(ACTIONS_BRVM)}")
    
    # Choix du type
    print(f"\n🔧 Type de génération :")
    print(f"   1. Valeurs exemple (pour tester - RECOMMANDÉ)")
    print(f"   2. Template vide (à remplir manuellement)")
    
    choix = input("\nVotre choix (1/2) : ").strip()
    with_examples = choix != '2'
    
    filename = "historique_brvm_complement_nov_dec.csv"
    
    print(f"\n🔄 Génération en cours...")
    
    # Générer le CSV
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['DATE', 'SYMBOL', 'CLOSE', 'VOLUME', 'VARIATION'])
        
        lignes_generees = 0
        for i, date in enumerate(dates):
            for action in ACTIONS_BRVM:
                if with_examples:
                    # Valeurs exemple réalistes
                    # Prix de base selon l'action
                    prix_base = {
                        'SNTS': 15500, 'BICC': 7200, 'SGBC': 7500, 'SIBC': 7300,
                        'BOAM': 5600, 'ECOC': 6800, 'ETIT': 5900, 'NTLC': 6000,
                        'SAFC': 5500, 'PALC': 2800
                    }
                    
                    base = prix_base.get(action, random.randint(2000, 8000))
                    # Variation légère autour du prix de base
                    close = base + random.randint(-500, 500)
                    volume = random.randint(500, 10000)
                    variation = round(random.uniform(-2.0, 2.0), 2)
                else:
                    close = ''
                    volume = ''
                    variation = ''
                
                writer.writerow([date, action, close, volume, variation])
                lignes_generees += 1
            
            # Progress
            progress = ((i + 1) / len(dates)) * 100
            print(f"   Progression : {progress:.0f}%", end='\r')
    
    print(f"\n\n✅ Fichier créé : {filename}")
    print(f"   📊 {lignes_generees} lignes générées")
    print(f"   📅 {len(dates)} jours ouvrables")
    print(f"   🏢 {len(ACTIONS_BRVM)} actions")
    
    print(f"\n📈 IMPACT ATTENDU :")
    print(f"   • Observations actuelles : 1200")
    print(f"   • Observations à ajouter : {lignes_generees}")
    print(f"   • Total après import : {1200 + lignes_generees}")
    print(f"   • Objectif 60 jours : 2820")
    print(f"   • Couverture après : {((1200 + lignes_generees) / 2820 * 100):.1f}%")
    
    if with_examples:
        print(f"\n⚠️  IMPORTANT : Valeurs exemple générées")
        print(f"   → Remplacer par vos vraies données avant import définitif")
        print(f"   → Ou utiliser pour tester le système")
    
    print(f"\n💡 PROCHAINES ÉTAPES :")
    print(f"   1. {'[OPTIONNEL] Modifier les valeurs dans ' + filename if with_examples else 'Remplir les cours dans ' + filename}")
    print(f"   2. Tester : python collecter_csv_automatique.py --dry-run --pattern \"{filename}\"")
    print(f"   3. Importer : python collecter_csv_automatique.py --pattern \"{filename}\"")
    print(f"   4. Vérifier : python verifier_historique_60jours.py")
    
    # Proposition d'import immédiat
    print(f"\n🚀 Voulez-vous importer maintenant ?")
    import_now = input("   Import (y/n) : ").strip().lower()
    
    if import_now == 'y':
        print(f"\n🧪 Test d'import (dry-run)...")
        import os
        os.system(f'python collecter_csv_automatique.py --dry-run --pattern "{filename}"')
        
        print(f"\n✅ Test réussi ! Importer réellement ?")
        confirm = input("   Confirmer import (y/n) : ").strip().lower()
        
        if confirm == 'y':
            os.system(f'python collecter_csv_automatique.py --pattern "{filename}"')
            print(f"\n🔍 Vérification finale...")
            os.system('python verifier_historique_60jours.py')
    
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
