"""
Script pour déclencher la collecte immédiate de TOUTES les populations CEDEAO
Sans passer par Airflow - Exécution directe
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from scripts.pipeline import run_ingestion
from plateforme_centralisation.mongo import get_mongo_db

# Pays CEDEAO
COUNTRIES = "BEN,BFA,CIV,GNB,MLI,NER,SEN,TGO,GHA,GMB,GIN,LBR,MRT,NGA,SLE"

def trigger_population_collection():
    """Déclencher la collecte de population pour tous les pays"""
    
    print("=" * 80)
    print("🚀 COLLECTE AUTOMATIQUE - POPULATION CEDEAO")
    print("=" * 80)
    print(f"\n📍 Pays ciblés: {COUNTRIES.replace(',', ', ')}")
    print("📊 Indicateur: SP.POP.TOTL (Population totale)")
    print("📅 Période: 2010-2024")
    print()
    
    try:
        print("⏳ Lancement de la collecte...")
        count = run_ingestion(
            "worldbank",
            indicator="SP.POP.TOTL",
            date="2010:2024",
            country=COUNTRIES
        )
        
        print(f"\n✅ Collecte terminée: {count} observations collectées")
        
        # Vérifier les données dans MongoDB
        print("\n" + "=" * 80)
        print("📊 VÉRIFICATION DES DONNÉES")
        print("=" * 80)
        
        _, db = get_mongo_db()
        
        country_codes = COUNTRIES.split(',')
        print(f"\n{'Pays':<6} {'Clé':<25} {'Dernière valeur':<20} {'Année'}")
        print("-" * 80)
        
        for code in country_codes:
            key = f"{code}.SP.POP.TOTL"
            doc = db.curated_observations.find_one(
                {'source': 'WorldBank', 'dataset': 'SP.POP.TOTL', 'key': key},
                sort=[('ts', -1)]
            )
            
            if doc:
                value = doc.get('value', 0)
                value_m = value / 1_000_000
                ts = doc.get('ts', 'N/A')
                year = ts[:4] if ts and len(ts) >= 4 else 'N/A'
                print(f"{code:<6} {key:<25} {value_m:>12.1f}M {year:<10}")
            else:
                print(f"{code:<6} {key:<25} {'❌ Pas de données':>20}")
        
        total = db.curated_observations.count_documents({
            'source': 'WorldBank',
            'dataset': 'SP.POP.TOTL'
        })
        
        print(f"\n📊 Total observations SP.POP.TOTL: {total}")
        
        print("\n" + "=" * 80)
        print("✅ COLLECTE AUTOMATIQUE TERMINÉE AVEC SUCCÈS")
        print("=" * 80)
        print("\n💡 Les données sont maintenant disponibles dans le dashboard Banque Mondiale")
        print("🔗 http://127.0.0.1:8000/dashboards/worldbank/")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la collecte: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = trigger_population_collection()
    sys.exit(0 if success else 1)
