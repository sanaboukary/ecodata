#!/usr/bin/env python3
"""
Recherche et analyse des fichiers CSV BRVM pour restauration
"""
import os
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd

print("\n" + "="*100)
print("                    RECHERCHE FICHIERS CSV BRVM POUR RESTAURATION")
print("="*100 + "\n")

base_dir = Path(r"e:\DISQUE C\Desktop\Implementation plateforme")

# Fichiers CSV potentiels
fichiers_csv = [
    "donnees_reelles_brvm.csv",
    "donnees_brvm_2026-02-02.csv",
    "donnees_brvm_2026-01-09.csv", 
    "donnees_brvm_2026-01-05.csv",
    "historique_brvm_complement_nov_dec.csv",
    "historique_brvm.csv",
    "observation_complement.csv",
    "out_brvm/brvm_complet_20260105_110056.csv",
    "out_brvm/brvm_bs4_20260105_110847.csv"
]

donnees_trouvees = []

print("🔍 ANALYSE DES FICHIERS CSV :")
print("-"*100)

for fichier in fichiers_csv:
    chemin = base_dir / fichier
    
    if not chemin.exists():
        continue
    
    try:
        # Lire les premières lignes pour analyser
        df = pd.read_csv(chemin, nrows=5)
        total_lignes = sum(1 for _ in open(chemin, encoding='utf-8', errors='ignore')) - 1
        
        # Lire tout le fichier pour analyser les dates
        df_full = pd.read_csv(chemin)
        
        # Identifier la colonne de date
        date_col = None
        for col in ['date', 'Date', 'ts', 'timestamp', 'DATE']:
            if col in df_full.columns:
                date_col = col
                break
        
        if date_col:
            dates = df_full[date_col].dropna().unique()
            date_min = min(dates) if len(dates) > 0 else "N/A"
            date_max = max(dates) if len(dates) > 0 else "N/A"
            nb_dates = len(dates)
        else:
            date_min = "N/A"
            date_max = "N/A"
            nb_dates = 0
        
        # Actions
        action_col = None
        for col in ['symbole', 'Symbole', 'ticker', 'action', 'key']:
            if col in df_full.columns:
                action_col = col
                break
        
        if action_col:
            actions = df_full[action_col].dropna().unique()
            nb_actions = len(actions)
        else:
            nb_actions = 0
        
        print(f"\n✅ {fichier}")
        print(f"   Lignes      : {total_lignes:,}")
        print(f"   Colonnes    : {', '.join(df.columns.tolist()[:8])}")
        if len(df.columns) > 8:
            print(f"                 ... +{len(df.columns)-8} colonnes")
        print(f"   Période     : {date_min} → {date_max}")
        print(f"   Jours       : {nb_dates}")
        print(f"   Actions     : {nb_actions}")
        
        donnees_trouvees.append({
            'fichier': fichier,
            'lignes': total_lignes,
            'date_min': date_min,
            'date_max': date_max,
            'nb_dates': nb_dates,
            'nb_actions': nb_actions,
            'colonnes': df.columns.tolist()
        })
        
    except Exception as e:
        print(f"\n❌ {fichier}")
        print(f"   Erreur : {e}")

# Résumé
print("\n" + "="*100)
print("📊 RÉSUMÉ DES DONNÉES DISPONIBLES :")
print("-"*100)

if donnees_trouvees:
    print(f"\n{len(donnees_trouvees)} fichiers CSV analysés :")
    
    # Période manquante
    print(f"\n⚠️  PÉRIODE MANQUANTE EN BASE : 2025-12-13 → 2026-01-06 (25 jours)")
    print(f"⚠️  COLLECTES RÉCENTES        : 2026-01-07 → 2026-02-09 (5 jours seulement)")
    
    print(f"\n💡 FICHIERS POUVANT COMBLER LES TROUS :")
    
    for d in donnees_trouvees:
        # Vérifier si ce fichier peut combler le trou
        date_min_str = str(d['date_min'])
        date_max_str = str(d['date_max'])
        
        # Période manquante : 2025-12-13 → 2026-01-06
        # Collectes récentes : 2026-01-07 → 2026-02-10
        
        peut_combler = False
        raison = ""
        
        if '2025-12' in date_min_str or '2025-12' in date_max_str:
            peut_combler = True
            raison = "Contient décembre 2025"
        elif '2026-01' in date_min_str or '2026-01' in date_max_str:
            peut_combler = True
            raison = "Contient janvier 2026"
        elif '2026-02' in date_min_str or '2026-02' in date_max_str:
            peut_combler = True
            raison = "Contient février 2026"
        
        if peut_combler:
            print(f"\n   ✅ {d['fichier']}")
            print(f"      {raison}")
            print(f"      Période : {d['date_min']} → {d['date_max']} ({d['nb_dates']} jours)")
            print(f"      Lignes  : {d['lignes']:,}")
else:
    print("\n❌ Aucun fichier CSV analysable trouvé")

print("\n" + "="*100)
print("💾 RECOMMANDATION :")
print("-"*100)
print("""
Pour restaurer les données manquantes, vous pouvez :

1. Importer les fichiers CSV de janvier-février 2026 identifiés ci-dessus
2. Vérifier s'il existe d'autres sauvegardes pour décembre 2025
3. Re-collecter les données manquantes si la BRVM fournit un historique

Voulez-vous que je créé un script d'importation pour ces fichiers ?
""")
print("="*100 + "\n")
