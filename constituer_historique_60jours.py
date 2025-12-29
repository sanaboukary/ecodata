"""
SOLUTION HISTORIQUE 60 JOURS
============================

3 options pour constituer l'historique :

OPTION 1 : Importer CSV historique (si vous avez le fichier)
OPTION 2 : Marquer données UNKNOWN comme REAL_MANUAL (si vérifiées)
OPTION 3 : Parser bulletins PDF BRVM (60 derniers jours)

Ce script aide à choisir et exécuter la bonne option.
"""

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

def main():
    print("\n" + "="*70)
    print("CONSTITUTION HISTORIQUE 60 JOURS BRVM")
    print("="*70)
    
    client, db = get_mongo_db()
    
    # État actuel
    total = db.curated_observations.count_documents({'source': 'BRVM'})
    unknown = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$exists': False}
    })
    
    print(f"\nÉtat actuel :")
    print(f"  Total observations BRVM : {total}")
    print(f"  Dont UNKNOWN (non marquées) : {unknown}")
    
    # Dates disponibles
    dates = db.curated_observations.distinct('ts', {'source': 'BRVM'})
    dates_clean = sorted([d[:10] if 'T' in d else d for d in dates])
    
    print(f"\n  Dates distinctes : {len(dates_clean)}")
    if dates_clean:
        print(f"  Première date : {dates_clean[0]}")
        print(f"  Dernière date : {dates_clean[-1]}")
    
    print("\n" + "="*70)
    print("OPTIONS DISPONIBLES")
    print("="*70)
    
    print("\n📁 OPTION 1 : Importer CSV historique")
    print("   Si vous avez un fichier CSV avec format :")
    print("   DATE,SYMBOL,CLOSE,VOLUME,VARIATION")
    print("   2025-10-10,SNTS,25000,1200,1.5")
    print("   ...")
    print("   Commande : python collecter_csv_automatique.py")
    
    print("\n✏️  OPTION 2 : Marquer données UNKNOWN comme vérifiées")
    print(f"   {unknown} observations UNKNOWN peuvent être marquées REAL_MANUAL")
    print("   si vous confirmez qu'elles proviennent d'une source fiable")
    print("   Commande : python marquer_donnees_verifiees.py")
    
    print("\n📄 OPTION 3 : Parser bulletins PDF BRVM")
    print("   Télécharger 60 bulletins quotidiens BRVM (PDF)")
    print("   Les parser automatiquement")
    print("   Commande : python parser_bulletins_brvm_pdf.py")
    
    print("\n" + "="*70)
    print("RECOMMANDATION")
    print("="*70)
    
    if unknown > 500:
        print("\n💡 Vous avez beaucoup de données UNKNOWN ({})")
        print("   Si ces données viennent d'un import CSV hier,")
        print("   vous pouvez les marquer comme REAL_MANUAL :")
        print("\n   python marquer_donnees_verifiees.py")
        
        # Afficher échantillon
        samples = list(db.curated_observations.find(
            {'source': 'BRVM', 'attrs.data_quality': {'$exists': False}},
            {'key': 1, 'ts': 1, 'value': 1}
        ).limit(10))
        
        print("\n   Échantillon données UNKNOWN :")
        for s in samples:
            ts = s['ts'][:10] if 'T' in s['ts'] else s['ts']
            print(f"     {ts} - {s['key']:6s} - {s['value']:8.0f} FCFA")
    else:
        print("\n💡 Historique insuffisant (2 jours)")
        print("   Importez un CSV historique 60 jours :")
        print("\n   python collecter_csv_automatique.py --dossier ./data_historiques")

if __name__ == "__main__":
    main()
