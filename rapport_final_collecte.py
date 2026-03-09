#!/usr/bin/env python3
"""
📊 RAPPORT FINAL DE COLLECTE - RÉSUMÉ COMPLET
"""
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def generer_rapport():
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("RAPPORT FINAL DE COLLECTE - PLATEFORME CENTRALISATION DONNÉES UEMOA")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
    
    # Compter les observations
    stats = {
        'WorldBank': db.curated_observations.count_documents({'source': 'WorldBank'}),
        'IMF': db.curated_observations.count_documents({'source': 'IMF'}),
        'AfDB': db.curated_observations.count_documents({'source': 'AfDB'}),
        'UN_SDG': db.curated_observations.count_documents({'source': 'UN_SDG'}),
        'BRVM': db.curated_observations.count_documents({'source': 'BRVM'}),
    }
    
    total = sum(stats.values())
    
    # Objectifs
    objectifs = {
        'WorldBank': 35000,
        'IMF': 9000,
        'AfDB': 4000,
        'UN_SDG': 1000,
        'BRVM': 2000,
    }
    
    objectif_total = sum(objectifs.values())
    
    print("RÉSUMÉ PAR SOURCE :\n")
    print(f"{'Source':<15} | {'Observations':<12} | {'Objectif':<10} | {'%':<6} | {'Statut'}")
    print("-" * 80)
    
    for source in ['WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'BRVM']:
        obs = stats[source]
        obj = objectifs[source]
        pct = (obs / obj * 100) if obj > 0 else 0
        
        if pct >= 90:
            statut = "EXCELLENT"
            icone = "✅"
        elif pct >= 75:
            statut = "BON     "
            icone = "🟢"
        elif pct >= 50:
            statut = "MOYEN   "
            icone = "🟡"
        else:
            statut = "FAIBLE  "
            icone = "🔴"
        
        print(f"{source:<15} | {obs:>11,} | {obj:>9,} | {pct:>5.1f}% | {icone} {statut}")
    
    print("-" * 80)
    pct_total = (total / objectif_total * 100)
    print(f"{'TOTAL':<15} | {total:>11,} | {objectif_total:>9,} | {pct_total:>5.1f}% |")
    print("=" * 80 + "\n")
    
    # Répartition par pays
    print("RÉPARTITION PAR PAYS (sources internationales) :\n")
    
    pays_codes = {
        'BJ': 'Bénin',
        'BF': 'Burkina Faso',
        'CI': 'Côte d\'Ivoire',
        'GW': 'Guinée-Bissau',
        'ML': 'Mali',
        'NE': 'Niger',
        'SN': 'Sénégal',
        'TG': 'Togo'
    }
    
    print(f"{'Pays':<20} | {'WB':<8} | {'IMF':<8} | {'AfDB':<8} | {'UN SDG':<8} | {'Total'}")
    print("-" * 80)
    
    for code, nom in pays_codes.items():
        wb = db.curated_observations.count_documents({
            'source': 'WorldBank',
            'key': {'$regex': f'_{code}$'}
        })
        imf = db.curated_observations.count_documents({
            'source': 'IMF',
            'key': {'$regex': f'_{code}$'}
        })
        afdb = db.curated_observations.count_documents({
            'source': 'AfDB',
            'key': {'$regex': f'_{code}$'}
        })
        un = db.curated_observations.count_documents({
            'source': 'UN_SDG',
            'key': {'$regex': f'_{code}$'}
        })
        
        total_pays = wb + imf + afdb + un
        
        print(f"{nom:<20} | {wb:>7,} | {imf:>7,} | {afdb:>7,} | {un:>7,} | {total_pays:>6,}")
    
    print("=" * 80 + "\n")
    
    # Performance
    print("PERFORMANCE DE COLLECTE :\n")
    
    # Compter les ingestions
    nb_ingestions = db.ingestion_runs.count_documents({})
    nb_succes = db.ingestion_runs.count_documents({'status': 'success'})
    nb_erreurs = db.ingestion_runs.count_documents({'status': 'error'})
    
    taux_succes = (nb_succes / nb_ingestions * 100) if nb_ingestions > 0 else 0
    
    print(f"Total ingestions    : {nb_ingestions:,}")
    print(f"Succès              : {nb_succes:,} ({taux_succes:.1f}%)")
    print(f"Erreurs             : {nb_erreurs:,}")
    print(f"\nObservations totales: {total:,}")
    print(f"Taux completion     : {pct_total:.1f}%")
    
    print("\n" + "=" * 80)
    print("CONCLUSION :\n")
    
    if pct_total >= 85:
        print("✅ COLLECTE RÉUSSIE - Base de données bien remplie !")
        print("   La plateforme dispose de données substantielles pour l'analyse.")
    elif pct_total >= 70:
        print("🟢 COLLECTE SATISFAISANTE - Bonne couverture des données")
        print("   Quelques sources peuvent être complétées davantage.")
    else:
        print("🟡 COLLECTE PARTIELLE - Couverture modérée")
        print("   Poursuivre les collectes pour améliorer la couverture.")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    generer_rapport()
