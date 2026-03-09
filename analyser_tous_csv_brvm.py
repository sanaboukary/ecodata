#!/usr/bin/env python3
"""
Analyser TOUS les fichiers CSV BRVM disponibles
Identifier lesquels contiennent des données réelles pour les 47 actions
"""

import pandas as pd
import os
from datetime import datetime
import glob

def analyser_tous_csv():
    """Analyser tous les CSV trouvés"""
    
    print(f"[ANALYSE COMPLÈTE CSV BRVM]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Liste des 47 actions BRVM officielles
    actions_brvm_47 = [
        'ABJC', 'BICC', 'BOAB', 'BOABF', 'BOAC', 'BOAG', 'BOAM', 'BOAN', 'BOAS',
        'CBIBF', 'CFAO', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'NEIC', 'NSBC', 'NTLC',
        'ONTBF', 'ORGT', 'PALC', 'PRSC', 'SAFC', 'SCRC', 'SDCC', 'SDSC', 'SEMC',
        'SGBC', 'SHEC', 'SIBC', 'SICC', 'SIVC', 'SLBC', 'SMBC', 'SNTS', 'SODE',
        'SOGC', 'SPHC', 'STAC', 'STBC', 'SVOC', 'TTLC', 'TTRC', 'UNXC', 'CIAC',
        'SNDC', 'SPHEC'
    ]
    
    # Chercher tous les CSV
    fichiers_csv = []
    for pattern in ['*.csv', 'out_brvm/*.csv', 'csv/*.csv', 'csv_brvm/*.csv']:
        fichiers_csv.extend(glob.glob(pattern))
    
    fichiers_csv = list(set(fichiers_csv))  # Dédupliquer
    
    print(f"[FICHIERS CSV TROUVÉS: {len(fichiers_csv)}]\n")
    
    # Prioritaires
    prioritaires = [
        'historique_brvm.csv',
        'historique_brvm_complement_nov_dec.csv',
        'donnees_reelles_brvm.csv',
        'donnees_brvm_2026-02-02.csv',
        'donnees_brvm_2026-01-09.csv',
        'donnees_brvm_2026-01-05.csv',
        'brvm_cours_complet_TEMPLATE.csv'
    ]
    
    resultats = []
    
    for fichier in prioritaires + [f for f in fichiers_csv if f not in prioritaires]:
        if not os.path.exists(fichier):
            continue
        
        try:
            # Lire CSV
            df = pd.read_csv(fichier, encoding='utf-8', on_bad_lines='skip')
            
            if len(df) == 0:
                continue
            
            # Identifier colonne symbole
            col_symbole = None
            for col in ['symbol', 'Symbol', 'symbole', 'Symbole', 'ticker', 'Ticker', 'SYMBOL']:
                if col in df.columns:
                    col_symbole = col
                    break
            
            if not col_symbole:
                # Essayer première colonne si ressemble à un symbole
                if df.columns[0] in ['Unnamed: 0', '0'] and len(df) > 0:
                    premiere_valeur = str(df.iloc[0, 0])
                    if len(premiere_valeur) <= 10 and premiere_valeur.isupper():
                        df = df.rename(columns={df.columns[0]: 'symbol'})
                        col_symbole = 'symbol'
            
            if col_symbole:
                actions_uniques = df[col_symbole].dropna().unique()
                actions_brvm = [a for a in actions_uniques if a in actions_brvm_47]
                
                # Compter observations avec prix
                col_prix = None
                for col in ['Close', 'close', 'prix', 'Prix', 'cours', 'Cours', 'price', 'Price', 'value']:
                    if col in df.columns:
                        col_prix = col
                        break
                
                obs_avec_prix = 0
                if col_prix:
                    obs_avec_prix = df[col_prix].notna().sum()
                
                resultats.append({
                    'fichier': fichier,
                    'lignes': len(df),
                    'actions_uniques': len(actions_uniques),
                    'actions_brvm': len(actions_brvm),
                    'obs_avec_prix': obs_avec_prix,
                    'colonnes': df.columns.tolist()
                })
                
        except Exception as e:
            pass
    
    # Trier par nombre d'observations avec prix
    resultats.sort(key=lambda x: x['obs_avec_prix'], reverse=True)
    
    print(f"[TOP FICHIERS PAR DONNÉES RÉELLES]\n")
    
    total_obs = 0
    for i, r in enumerate(resultats[:10], 1):
        print(f"{i}. {r['fichier']}")
        print(f"   Lignes: {r['lignes']} | Actions BRVM: {r['actions_brvm']}/47 | Obs avec prix: {r['obs_avec_prix']}")
        print(f"   Colonnes: {r['colonnes'][:5]}{'...' if len(r['colonnes']) > 5 else ''}")
        print()
        total_obs += r['obs_avec_prix']
    
    print(f"[TOTAL ESTIMÉ]")
    print(f"  Observations disponibles (top 10 fichiers): {total_obs}")
    print(f"  Actions BRVM possibles: {actions_brvm_47}")
    
    # Recommandation
    print(f"\n[RECOMMANDATION]")
    if resultats:
        meilleur = resultats[0]
        print(f"  Meilleur fichier: {meilleur['fichier']}")
        print(f"    → {meilleur['obs_avec_prix']} observations réelles")
        print(f"    → {meilleur['actions_brvm']}/47 actions BRVM")
        
        if meilleur['obs_avec_prix'] >= 500:
            print(f"\n  ✓ Excellent ! Suffisant pour restauration")
        else:
            print(f"\n  ⚠ Peut combiner plusieurs fichiers pour plus de données")

if __name__ == "__main__":
    try:
        analyser_tous_csv()
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
