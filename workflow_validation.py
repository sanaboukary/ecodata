#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow Complet: Validation des Recommandations
Utilise les dernières données disponibles (23 ou 24/12)
"""

import os
import sys
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
import json

def main():
    print("\n" + "="*80)
    print("WORKFLOW: VALIDATION RECOMMANDATIONS FIABLES")
    print("="*80 + "\n")
    
    # 1. Vérifier données disponibles
    print("Etape 1: Verification donnees BRVM...")
    client, db = get_mongo_db()
    
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    count_today = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': today
    })
    count_yesterday = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': yesterday
    })
    
    print(f"   Aujourd'hui ({today}): {count_today}/47")
    print(f"   Hier ({yesterday}): {count_yesterday}/47")
    
    if count_today == 0 and count_yesterday == 0:
        print("\n❌ ERREUR: Aucune donnee BRVM disponible")
        print("   Action: Executer d'abord collecter_brvm_complet.py\n")
        client.close()
        return 1
    
    date_reference = today if count_today > 0 else yesterday
    count_reference = count_today if count_today > 0 else count_yesterday
    
    print(f"\n✅ Utilisation donnees du {date_reference} ({count_reference} actions)")
    
    # 2. Vérifier recommandations IA
    print("\nEtape 2: Verification recommandations IA...")
    reco_files = sorted([f for f in os.listdir('.') 
                         if f.startswith('top5_nlp_') and f.endswith('.json')])
    
    if not reco_files:
        print("\n❌ ERREUR: Aucune recommandation IA")
        print("   Action: Executer generer_top5_nlp.py\n")
        client.close()
        return 1
    
    latest_reco = reco_files[-1]
    print(f"✅ Fichier: {latest_reco}")
    
    with open(latest_reco, 'r', encoding='utf-8') as f:
        reco_data = json.load(f)
    
    top5 = reco_data.get('top_5', [])
    print(f"   {len(top5)} recommandations a valider")
    
    # 3. Lancer validation
    print("\nEtape 3: Validation avec 10 criteres stricts...")
    print("   (Accepte donnees J ou J-1 si marche ferme)")
    print()
    
    client.close()
    
    # Lancer le validateur
    os.system('.venv/Scripts/python.exe valider_recommandations_fiables.py')
    
    # 4. Afficher résultats
    print("\nEtape 4: Affichage resultats...")
    os.system('.venv/Scripts/python.exe afficher_validations.py')
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
