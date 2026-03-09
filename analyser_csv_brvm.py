#!/usr/bin/env python3
"""
Analyser les fichiers CSV BRVM AVANT restauration
Vérifier : nombre d'actions, structure, doublons, complétude
"""

import pandas as pd
import os
from datetime import datetime

def analyser_fichiers_csv():
    """Analyser tous les CSV BRVM pour comprendre la structure"""
    
    print(f"[ANALYSE CSV BRVM - AVANT RESTAURATION]")
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
    
    fichiers_csv = [
        'brvm_cours_complet.csv',
        'brvm_cours_complet_TEMPLATE.csv',
        'donnees_brvm_completes.csv'
    ]
    
    total_observations = 0
    
    for fichier in fichiers_csv:
        if not os.path.exists(fichier):
            print(f"[SKIP] {fichier} - fichier introuvable")
            continue
        
        print(f"\n{'='*70}")
        print(f"[FICHIER] {fichier}")
        print(f"{'='*70}")
        
        try:
            # Lire CSV
            df = pd.read_csv(fichier)
            
            print(f"\n[STRUCTURE]")
            print(f"  Lignes: {len(df)}")
            print(f"  Colonnes: {list(df.columns)}")
            
            # Identifier colonne symbole/ticker
            col_symbole = None
            for col in ['symbol', 'Symbol', 'symbole', 'Symbole', 'ticker', 'Ticker', 'SYMBOL']:
                if col in df.columns:
                    col_symbole = col
                    break
            
            if col_symbole:
                # Compter actions uniques
                actions_uniques = df[col_symbole].dropna().unique()
                print(f"\n[ACTIONS]")
                print(f"  Actions uniques: {len(actions_uniques)}")
                print(f"  Actions: {sorted(actions_uniques)[:20]}")
                
                # Vérifier correspondance avec 47 actions BRVM
                actions_manquantes = set(actions_brvm_47) - set(actions_uniques)
                actions_extra = set(actions_uniques) - set(actions_brvm_47)
                
                if actions_manquantes:
                    print(f"\n  ⚠ Actions BRVM manquantes ({len(actions_manquantes)}): {sorted(actions_manquantes)[:10]}")
                
                if actions_extra:
                    print(f"  ℹ Actions non-standard ({len(actions_extra)}): {sorted(actions_extra)[:10]}")
                
                # Compter observations par action
                obs_par_action = df[col_symbole].value_counts()
                print(f"\n[DISTRIBUTION]")
                print(f"  Top 10 actions (nb observations):")
                for action, count in obs_par_action.head(10).items():
                    print(f"    {action}: {count} obs")
                
                print(f"\n  Bottom 5 actions:")
                for action, count in obs_par_action.tail(5).items():
                    print(f"    {action}: {count} obs")
                
            # Identifier colonne date
            col_date = None
            for col in ['Date', 'date', 'timestamp', 'ts', 'DATE']:
                if col in df.columns:
                    col_date = col
                    break
            
            if col_date:
                print(f"\n[PÉRIODE]")
                try:
                    dates = pd.to_datetime(df[col_date], errors='coerce')
                    dates_valides = dates.dropna()
                    if len(dates_valides) > 0:
                        print(f"  Début: {dates_valides.min()}")
                        print(f"  Fin: {dates_valides.max()}")
                        print(f"  Jours couverts: {(dates_valides.max() - dates_valides.min()).days}")
                except:
                    print(f"  Dates non parsables")
            
            # Identifier colonnes prix
            colonnes_prix = []
            for col in ['Close', 'close', 'prix', 'Prix', 'cours', 'Cours', 'price', 'Price']:
                if col in df.columns:
                    colonnes_prix.append(col)
            
            if colonnes_prix:
                print(f"\n[PRIX]")
                for col_prix in colonnes_prix[:3]:  # Limiter à 3 colonnes
                    prix_valides = pd.to_numeric(df[col_prix], errors='coerce').dropna()
                    if len(prix_valides) > 0:
                        print(f"  {col_prix}:")
                        print(f"    Min: {prix_valides.min():.0f} FCFA")
                        print(f"    Max: {prix_valides.max():.0f} FCFA")
                        print(f"    Médiane: {prix_valides.median():.0f} FCFA")
                        print(f"    Valeurs valides: {len(prix_valides)} / {len(df)}")
            
            # Détecter doublons
            if col_symbole and col_date:
                doublons = df.duplicated(subset=[col_symbole, col_date], keep=False)
                nb_doublons = doublons.sum()
                if nb_doublons > 0:
                    print(f"\n[DOUBLONS]")
                    print(f"  ⚠ {nb_doublons} lignes dupliquées (même symbole+date)")
                    print(f"  Exemples:")
                    print(df[doublons][[col_symbole, col_date]].head(5))
            
            total_observations += len(df)
            
        except Exception as e:
            print(f"  [ERREUR] {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"[TOTAL]")
    print(f"{'='*70}")
    print(f"  Total observations dans CSV: {total_observations}")
    print(f"  Actions BRVM officielles: {len(actions_brvm_47)}")
    
    print(f"\n[RECOMMANDATION]")
    if total_observations > 0:
        print(f"  ✓ {total_observations} observations réelles disponibles pour restauration")
        print(f"  ✓ Prêt pour import dans MongoDB")
    else:
        print(f"  ⚠ Aucune donnée trouvée dans les CSV")

if __name__ == "__main__":
    try:
        analyser_fichiers_csv()
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
