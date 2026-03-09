#!/usr/bin/env python
"""
Script de collecte BRVM immédiate - Version simplifiée
Lance la collecte quotidienne des cours BRVM maintenant
"""
import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from scripts.pipeline import run_ingestion

def main():
    print("=" * 80)
    print("🚀 COLLECTE BRVM IMMÉDIATE")
    print("=" * 80)
    print(f"\n📅 Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Source : BRVM (Bourse Régionale des Valeurs Mobilières)")
    print()
    
    try:
        # Vérifier connexion MongoDB
        print("🔌 Vérification connexion MongoDB...")
        client, db = get_mongo_db()
        
        # Compter observations actuelles
        count_avant = db.curated_observations.count_documents({'source': 'BRVM'})
        print(f"   ✅ Connecté à MongoDB")
        print(f"   📊 Observations BRVM actuelles : {count_avant}")
        print()
        
        # Lancer collecte
        print("🔄 Lancement de la collecte BRVM...")
        print("   Stratégie : Scraping site officiel BRVM")
        print()
        
        result = run_ingestion('brvm')
        
        print()
        print("=" * 80)
        print("✅ COLLECTE TERMINÉE")
        print("=" * 80)
        
        # Compter nouvelles observations
        count_apres = db.curated_observations.count_documents({'source': 'BRVM'})
        nouvelles = count_apres - count_avant
        
        print(f"\n📊 Résultats :")
        print(f"   Avant : {count_avant} observations")
        print(f"   Après : {count_apres} observations")
        print(f"   Nouvelles : {nouvelles} observations")
        
        if nouvelles > 0:
            print(f"\n✅ {nouvelles} nouvelles observations BRVM collectées avec succès!")
            
            # Afficher échantillon
            print("\n📝 Échantillon des données collectées :")
            sample = list(db.curated_observations.find({'source': 'BRVM'}).sort('ts', -1).limit(5))
            for obs in sample:
                print(f"   • {obs.get('key')} - {obs.get('ts')} - {obs.get('value')} FCFA")
        else:
            print("\n⚠️  Aucune nouvelle donnée collectée")
            print("   Raisons possibles :")
            print("   - Données déjà à jour")
            print("   - Site BRVM indisponible")
            print("   - Erreur de connexion")
        
        print()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERREUR LORS DE LA COLLECTE")
        print("=" * 80)
        print(f"\nErreur : {str(e)}")
        print()
        print("💡 Solutions alternatives :")
        print("   1. Vérifier que MongoDB est démarré")
        print("   2. Vérifier la connexion internet")
        print("   3. Utiliser la saisie manuelle : python mettre_a_jour_cours_brvm.py")
        print("   4. Importer depuis CSV : python collecter_csv_automatique.py")
        print()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
