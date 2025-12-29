#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MISE À JOUR MANUELLE - COURS RÉELS BRVM DU 22 DÉCEMBRE 2025
POLITIQUE ZÉRO TOLÉRANCE : DONNÉES RÉELLES UNIQUEMENT
Source: https://www.brvm.org/fr/investir/cours-et-cotations
"""

import os
import sys
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

# 🔴 COURS RÉELS DU 22 DÉCEMBRE 2025 (À COMPLÉTER)
# Veuillez aller sur https://www.brvm.org/fr/investir/cours-et-cotations
# et saisir les VRAIS cours de clôture

VRAIS_COURS_BRVM = {
    # EXEMPLE CONFIRMÉ
    'ECOC': {
        'close': 15000,  # PRIX RÉEL confirmé par l'utilisateur
        'volume': 0,     # À compléter
        'variation': 0,  # À compléter
    },
    
    # ⚠️ VEUILLEZ COMPLÉTER AVEC LES VRAIS COURS DU SITE BRVM ⚠️
    # Copier-coller depuis le tableau officiel BRVM
    
    # 'BICC': {'close': ???, 'volume': ???, 'variation': ???},
    # 'BOABF': {'close': ???, 'volume': ???, 'variation': ???},
    # 'BNBC': {'close': ???, 'volume': ???, 'variation': ???},
    # ... (continuer pour les 47 actions)
}

def mettre_a_jour_cours_reels():
    """Mise à jour MongoDB avec les VRAIS cours BRVM"""
    
    client, db = get_mongo_db()
    date_collecte = '2025-12-22'
    
    print("\n" + "="*80)
    print("🔴 MISE À JOUR COURS RÉELS BRVM - 22 DÉCEMBRE 2025")
    print("="*80)
    print(f"\n📅 Date: {date_collecte}")
    print(f"📊 Nombre d'actions à mettre à jour: {len(VRAIS_COURS_BRVM)}")
    
    if len(VRAIS_COURS_BRVM) < 10:
        print("\n⚠️  ATTENTION: Seulement {} actions configurées!".format(len(VRAIS_COURS_BRVM)))
        print("⚠️  Veuillez compléter le dictionnaire VRAIS_COURS_BRVM avec TOUS les cours")
        print("⚠️  Source: https://www.brvm.org/fr/investir/cours-et-cotations")
        reponse = input("\nContinuer quand même? (y/n): ")
        if reponse.lower() != 'y':
            print("❌ Annulé")
            return
    
    observations_ajoutees = 0
    
    for symbol, data in VRAIS_COURS_BRVM.items():
        # Supprimer les anciennes données FAUSSES de ce jour
        db.curated_observations.delete_many({
            'source': 'BRVM',
            'key': symbol,
            'ts': date_collecte
        })
        
        # Ajouter la nouvelle observation RÉELLE
        observation = {
            'source': 'BRVM',
            'dataset': 'STOCK_PRICE',
            'key': symbol,
            'ts': date_collecte,
            'value': data['close'],
            'attrs': {
                'close': data['close'],
                'volume': data.get('volume', 0),
                'variation': data.get('variation', 0),
                'open': data.get('open', data['close']),
                'high': data.get('high', data['close']),
                'low': data.get('low', data['close']),
                'data_quality': 'REAL_MANUAL',  # 🔴 DONNÉES RÉELLES
                'collection_date': datetime.now().isoformat(),
                'verified': True
            }
        }
        
        db.curated_observations.insert_one(observation)
        observations_ajoutees += 1
        print(f"  ✅ {symbol}: {data['close']:,} FCFA")
    
    print(f"\n{'='*80}")
    print(f"✅ {observations_ajoutees} observations RÉELLES ajoutées")
    print(f"✅ Anciennes données FAUSSES supprimées")
    print(f"{'='*80}\n")
    
    # Relancer l'analyse IA avec les VRAIS cours
    print("🤖 Relancement de l'analyse IA avec les VRAIS cours...")
    os.system('python lancer_analyse_ia_rapide.py')

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️  INSTRUCTIONS IMPORTANTES ⚠️                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

1. Allez sur: https://www.brvm.org/fr/investir/cours-et-cotations

2. Copiez les cours de clôture du 22 décembre 2025 pour TOUTES les actions

3. Modifiez le dictionnaire VRAIS_COURS_BRVM dans ce fichier

4. Relancez ce script

EXEMPLE:
    'ECOC': {'close': 15000, 'volume': 8500, 'variation': 2.3},
    'BICC': {'close': 7990, 'volume': 1200, 'variation': -1.5},
    ...

""")
    
    mettre_a_jour_cours_reels()
