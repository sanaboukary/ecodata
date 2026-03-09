#!/usr/bin/env python3
"""
Analyser et extraire les données BRVM réelles depuis les sources trouvées
Priorité : fichiers CSV historiques volumineux
"""

import pandas as pd
import pymongo
from datetime import datetime
import os

def analyser_csv_historiques():
    """Analyser les fichiers CSV historiques BRVM"""
    
    print(f"[ANALYSE FICHIERS CSV HISTORIQUES BRVM]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Fichiers à analyser par priorité
    fichiers_prioritaires = [
        'historique_brvm_60jours_TEMPLATE.csv',
        'historique_brvm.csv',
        'historique_brvm_complement_nov_dec.csv',
        'donnees_reelles_brvm.csv',
        'donnees_brvm_2026-02-02.csv',
        'donnees_brvm_2026-01-09.csv',
        'out_brvm/brvm_complet_20260105_110056.csv',
        'out_brvm/brvm_bs4_20260105_110847.csv'
    ]
    
    donnees_total = []
    
    for fichier in fichiers_prioritaires:
        if not os.path.exists(fichier):
            continue
        
        print(f"[ANALYSE] {fichier}")
        print(f"  Taille: {os.path.getsize(fichier)} bytes")
        
        try:
            # Essayer différents encodages et séparateurs
            df = None
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                for sep in [',', ';', '\t']:
                    try:
                        df = pd.read_csv(fichier, encoding=encoding, sep=sep)
                        if len(df) > 0:
                            break
                    except:
                        continue
                if df is not None and len(df) > 0:
                    break
            
            if df is None or len(df) == 0:
                print(f"  ⚠ Impossible de lire")
                continue
            
            print(f"  Lignes: {len(df)}")
            print(f"  Colonnes: {list(df.columns)[:10]}")
            
            # Afficher échantillon
            print(f"  Échantillon:")
            print(df.head(3).to_string())
            
            # Identifier colonnes importantes
            colonnes = [c.lower() for c in df.columns]
            
            # Chercher colonnes symbole/ticker
            col_symbole = None
            for c in df.columns:
                if any(keyword in c.lower() for keyword in ['symbole', 'symbol', 'ticker', 'action', 'code']):
                    col_symbole = c
                    break
            
            # Chercher colonnes prix
            col_prix = None
            for c in df.columns:
                if any(keyword in c.lower() for keyword in ['prix', 'cours', 'close', 'cloture', 'price', 'valeur']):
                    col_prix = c
                    break
            
            # Chercher colonnes date
            col_date = None
            for c in df.columns:
                if any(keyword in c.lower() for keyword in ['date', 'timestamp', 'ts', 'jour']):
                    col_date = c
                    break
            
            if col_symbole and col_prix:
                print(f"  ✓ Colonnes identifiées:")
                print(f"    Symbole: {col_symbole}")
                print(f"    Prix: {col_prix}")
                if col_date:
                    print(f"    Date: {col_date}")
                
                # Compter symboles uniques
                symboles = df[col_symbole].unique()
                print(f"  📊 {len(symboles)} symboles: {list(symboles)[:10]}")
                
                # Compter observations par symbole
                par_symbole = df[col_symbole].value_counts()
                print(f"  Top 5 symboles:")
                for sym, count in par_symbole.head().items():
                    print(f"    {sym}: {count} obs")
                
                # Stocker pour restauration
                donnees_total.append({
                    'fichier': fichier,
                    'df': df,
                    'col_symbole': col_symbole,
                    'col_prix': col_prix,
                    'col_date': col_date,
                    'nb_lignes': len(df),
                    'symboles': list(symboles)
                })
            else:
                print(f"  ⚠ Colonnes symbole/prix non identifiées")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            print()
    
    # Résumé
    print(f"[RÉSUMÉ DONNÉES TROUVÉES]")
    print(f"Fichiers exploitables: {len(donnees_total)}")
    
    total_obs = sum(d['nb_lignes'] for d in donnees_total)
    print(f"Total observations: {total_obs}")
    
    # Tous les symboles
    all_symboles = set()
    for d in donnees_total:
        all_symboles.update(d['symboles'])
    
    print(f"Symboles uniques: {len(all_symboles)}")
    print(f"Liste: {sorted(all_symboles)}")
    
    return donnees_total

if __name__ == "__main__":
    try:
        donnees = analyser_csv_historiques()
        
        if donnees:
            print(f"\n[OK] {len(donnees)} fichiers CSV analysés avec succès")
            print(f"Total: {sum(d['nb_lignes'] for d in donnees)} observations disponibles")
        else:
            print(f"\n[ERREUR] Aucun fichier CSV exploitable trouvé")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
