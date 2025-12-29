#!/usr/bin/env python3
"""
🔗 FUSIONNER TEMPLATE 60J + DONNÉES RÉELLES EXISTANTES
Remplace les placeholders par vraies données quand disponible
"""

import csv
from collections import defaultdict
from datetime import datetime

def fusionner_template_avec_reelles():
    """Fusionne template vide avec données réelles"""
    
    print("\n" + "="*80)
    print("FUSION TEMPLATE 60J + DONNEES REELLES")
    print("="*80 + "\n")
    
    # 1. Charger template
    try:
        with open('historique_brvm_60jours_TEMPLATE.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            template = list(reader)
        print(f"✓ Template chargé: {len(template):,} lignes")
    except FileNotFoundError:
        print("❌ Template manquant. Générer d'abord:")
        print("   python generer_template_historique_60j.py")
        return
    
    # 2. Charger données réelles (chercher fichier le plus récent)
    import glob
    fichiers_reels = glob.glob('donnees_reelles_brvm_*.csv')
    
    donnees_reelles = {}
    
    if fichiers_reels:
        fichier_reel = sorted(fichiers_reels)[-1]  # Plus récent
        
        try:
            with open(fichier_reel, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Clé: DATE_SYMBOL
                    key = f"{row['DATE']}_{row['SYMBOL']}"
                    donnees_reelles[key] = row
            
            print(f"✓ Données réelles chargées: {len(donnees_reelles):,} observations")
            print(f"  Source: {fichier_reel}")
        except FileNotFoundError:
            print("⚠  Aucune donnée réelle trouvée")
    else:
        print("⚠  Aucune donnée réelle - template restera vide")
        print("   Exporter d'abord:")
        print("   python exporter_donnees_reelles_existantes.py")
    
    print()
    
    # 3. Fusionner
    fusionne = []
    remplis = 0
    vides = 0
    
    for row in template:
        key = f"{row['DATE']}_{row['SYMBOL']}"
        
        if key in donnees_reelles:
            # Remplacer par données réelles
            fusionne.append(donnees_reelles[key])
            remplis += 1
        else:
            # Garder placeholder
            fusionne.append(row)
            vides += 1
    
    print("Fusion:")
    print(f"  Données réelles: {remplis:,} ({remplis/len(template)*100:.1f}%)")
    print(f"  Placeholders:    {vides:,} ({vides/len(template)*100:.1f}%)")
    print()
    
    # 4. Sauvegarder
    filename = f'historique_brvm_60j_PARTIEL_{datetime.now().strftime("%Y%m%d")}.csv'
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['DATE', 'SYMBOL', 'CLOSE', 'VOLUME', 'VARIATION'])
        writer.writeheader()
        writer.writerows(fusionne)
    
    print(f"✓ Fichier fusionné: {filename}")
    print()
    
    # 5. Statistiques par action
    print("Couverture par action (jours avec données):")
    
    couverture = defaultdict(int)
    for row in fusionne:
        if float(row['CLOSE']) > 0:  # Données réelles
            couverture[row['SYMBOL']] += 1
    
    if couverture:
        for symbol in sorted(couverture.keys()):
            count = couverture[symbol]
            print(f"  {symbol:<12} {count:>2}/60 jours ({count/60*100:>5.1f}%)")
    else:
        print("  Aucune donnée réelle")
    
    print()
    print("="*80)
    print("PROCHAINES ÉTAPES")
    print("="*80)
    print()
    
    if vides > 0:
        print(f"⚠  {vides:,} observations manquantes")
        print()
        print("OPTIONS POUR COMPLÉTER:")
        print()
        print("1. Télécharger bulletins BRVM PDF:")
        print("   - https://www.brvm.org/fr/publications/bulletins-quotidiens")
        print("   - Sauvegarder dans: bulletins_brvm/")
        print("   - Parser: python parser_bulletins_brvm_pdf.py")
        print()
        print("2. Compléter manuellement dans Excel:")
        print(f"   - Ouvrir: {filename}")
        print("   - Remplacer '0' par vraies valeurs")
        print()
        print("3. Importer données partielles maintenant:")
        print("   - python collecter_csv_automatique.py --dossier .")
        print("   - Compléter progressivement plus tard")
    else:
        print("✓ Historique 60 jours COMPLET!")
        print()
        print("IMPORT:")
        print("  python collecter_csv_automatique.py --dossier .")
    
    print()

if __name__ == '__main__':
    fusionner_template_avec_reelles()
