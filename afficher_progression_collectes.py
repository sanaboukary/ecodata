#!/usr/bin/env python3
"""
📊 PROGRESSION DES COLLECTES - TOUTES LES SOURCES
Affiche l'état actuel de toutes les collectes de données
"""
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def afficher_progression():
    """Affiche la progression de toutes les collectes"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("📊 PROGRESSION DES COLLECTES - TOUTES LES SOURCES")
    print("="*80)
    print(f"🕐 Mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Objectifs par source
    objectifs = {
        'WorldBank': 35000,    # 66 indicateurs × 8 pays × ~67 ans
        'IMF': 9000,           # 18 indicateurs × 8 pays × ~67 ans
        'AfDB': 4000,          # 8 indicateurs × 8 pays × ~67 ans
        'UN_SDG': 1000,        # 8 séries × 8 pays × ~15 ans
        'BRVM': 2000,          # 47 actions × ~43 jours
    }
    
    # Statistiques par source
    sources = ['WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'BRVM']
    stats = {}
    
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        stats[source] = count
    
    # Total
    total = db.curated_observations.count_documents({})
    total_objectif = sum(objectifs.values())
    
    # Affichage détaillé
    print("📋 DÉTAIL PAR SOURCE :\n")
    
    for source in sources:
        count = stats[source]
        objectif = objectifs[source]
        progression = (count / objectif * 100) if objectif > 0 else 0
        
        # Barre de progression
        barre_longueur = 40
        rempli = int(barre_longueur * progression / 100)
        barre = "█" * rempli + "░" * (barre_longueur - rempli)
        
        # Statut
        if progression >= 100:
            statut = "✅ COMPLET"
            couleur = ""
        elif progression >= 75:
            statut = "🟢 EN COURS"
            couleur = ""
        elif progression >= 50:
            statut = "🟡 MOYEN"
            couleur = ""
        elif progression >= 25:
            statut = "🟠 DÉBUT"
            couleur = ""
        else:
            statut = "🔴 FAIBLE"
            couleur = ""
        
        print(f"{source:15} │ {barre} │ {progression:5.1f}% │ {statut}")
        print(f"{'':15} │ {count:,} / {objectif:,} observations")
        
        # Dernière collecte
        dernier = db.curated_observations.find_one(
            {'source': source},
            sort=[('_id', -1)]
        )
        if dernier:
            ts = dernier.get('ts', 'N/A')
            print(f"{'':15} │ Dernière donnée: {ts}")
        
        print()
    
    # Total global
    print("="*80)
    progression_totale = (total / total_objectif * 100)
    barre_totale_longueur = 40
    rempli_total = int(barre_totale_longueur * progression_totale / 100)
    barre_totale = "█" * rempli_total + "░" * (barre_totale_longueur - rempli_total)
    
    print(f"{'TOTAL GLOBAL':15} │ {barre_totale} │ {progression_totale:5.1f}%")
    print(f"{'':15} │ {total:,} / {total_objectif:,} observations")
    print("="*80 + "\n")
    
    # Répartition par pays (pour sources internationales)
    print("🌍 RÉPARTITION PAR PAYS :\n")
    
    pays_uemoa = {
        'BJ': 'Bénin',
        'BF': 'Burkina Faso',
        'CI': 'Côte d\'Ivoire',
        'GW': 'Guinée-Bissau',
        'ML': 'Mali',
        'NE': 'Niger',
        'SN': 'Sénégal',
        'TG': 'Togo'
    }
    
    for code, nom in pays_uemoa.items():
        # Compter les observations pour ce pays (dans attrs.country ou key)
        count_wb = db.curated_observations.count_documents({
            'source': 'WorldBank',
            'key': {'$regex': f'_{code}$'}
        })
        count_imf = db.curated_observations.count_documents({
            'source': 'IMF',
            'key': {'$regex': f'_{code}$'}
        })
        count_afdb = db.curated_observations.count_documents({
            'source': 'AfDB',
            'key': {'$regex': f'_{code}$'}
        })
        count_un = db.curated_observations.count_documents({
            'source': 'UN_SDG',
            'key': {'$regex': f'_{code}$'}
        })
        
        total_pays = count_wb + count_imf + count_afdb + count_un
        
        print(f"{code} - {nom:20} │ {total_pays:5,} obs │ WB:{count_wb:5,} IMF:{count_imf:4,} AfDB:{count_afdb:4,} UN:{count_un:3,}")
    
    print("\n" + "="*80)
    
    # Historique des ingestions
    print("\n📜 DERNIÈRES INGESTIONS :\n")
    
    dernieres_ingestions = list(db.ingestion_runs.find().sort('start_time', -1).limit(10))
    
    for ing in dernieres_ingestions:
        source = ing.get('source', 'N/A')
        status = ing.get('status', 'N/A')
        start = ing.get('start_time', '')
        obs_count = ing.get('obs_count', 0)
        duration = ing.get('duration_seconds', 0)
        
        if status == 'success':
            icone = "✅"
        elif status == 'error':
            icone = "❌"
        else:
            icone = "⏳"
        
        if isinstance(start, datetime):
            start_str = start.strftime('%d/%m/%Y %H:%M')
        else:
            start_str = str(start)[:16] if start else 'N/A'
        
        print(f"{icone} {source:15} │ {start_str} │ {obs_count:5,} obs │ {duration:5.0f}s │ {status}")
    
    print("\n" + "="*80)
    
    # Estimation temps restant
    print("\n⏱️  ESTIMATION TEMPS RESTANT :\n")
    
    restant = {
        'WorldBank': max(0, objectifs['WorldBank'] - stats['WorldBank']),
        'IMF': max(0, objectifs['IMF'] - stats['IMF']),
        'AfDB': max(0, objectifs['AfDB'] - stats['AfDB']),
        'UN_SDG': max(0, objectifs['UN_SDG'] - stats['UN_SDG']),
    }
    
    # Vitesse moyenne par source (obs/minute estimée)
    vitesses = {
        'WorldBank': 50,   # ~50 obs/min
        'IMF': 30,         # ~30 obs/min
        'AfDB': 20,        # ~20 obs/min
        'UN_SDG': 10,      # ~10 obs/min
    }
    
    temps_restant_total = 0
    for source, nb_restant in restant.items():
        if nb_restant > 0 and source in vitesses:
            minutes = nb_restant / vitesses[source]
            heures = minutes / 60
            temps_restant_total += minutes
            
            if heures >= 1:
                print(f"{source:15} │ {nb_restant:5,} obs restantes │ ~{heures:.1f}h")
            else:
                print(f"{source:15} │ {nb_restant:5,} obs restantes │ ~{minutes:.0f}min")
    
    if temps_restant_total > 0:
        heures_totales = temps_restant_total / 60
        print(f"\n{'TEMPS TOTAL':15} │ ~{heures_totales:.1f}h ({temps_restant_total:.0f} minutes)")
    else:
        print("\n✅ Toutes les collectes sont complètes !")
    
    print("\n" + "="*80)
    print("💡 Commandes utiles :")
    print("  - Vérifier les logs : tail -f collecte_*.log")
    print("  - Moniteur en temps réel : python moniteur_collecte.py")
    print("  - Relancer une source : python collecter_<source>.py")
    print("="*80 + "\n")

if __name__ == '__main__':
    afficher_progression()
