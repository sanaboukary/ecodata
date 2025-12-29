"""
📊 État actuel de la base de données - Rapport complet
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from collections import defaultdict

def main():
    _, db = get_mongo_db()
    
    print("="*100)
    print("📊 ÉTAT COMPLET DE LA BASE DE DONNÉES - centralisation_db")
    print("="*100)
    
    # Statistiques globales
    total = db.curated_observations.count_documents({})
    print(f"\n🎯 Total observations: {total:,}")
    
    # Par source
    print("\n" + "="*100)
    print("📈 DÉTAILS PAR SOURCE")
    print("="*100)
    
    sources = ['WorldBank', 'IMF', 'UN_SDG', 'AfDB', 'BRVM']
    
    print(f"\n{'Source':<15} {'Observations':<15} {'Indicateurs':<15} {'Pays/Clés':<15} {'Dernière màj'}")
    print("-"*100)
    
    for source in sources:
        count = db.curated_observations.count_documents({'source': source})
        datasets = db.curated_observations.distinct('dataset', {'source': source})
        datasets = [d for d in datasets if d is not None]
        keys = db.curated_observations.distinct('key', {'source': source})
        keys = [k for k in keys if k is not None]
        
        # Dernière mise à jour
        latest = db.curated_observations.find_one(
            {'source': source},
            sort=[('ts', -1)]
        )
        last_update = latest.get('ts', 'N/A')[:10] if latest else 'N/A'
        
        print(f"{source:<15} {count:<15,} {len(datasets):<15} {len(keys):<15} {last_update}")
    
    # Détails World Bank
    print("\n" + "="*100)
    print("🌐 WORLD BANK - Détails par indicateur")
    print("="*100)
    
    wb_datasets = db.curated_observations.distinct('dataset', {'source': 'WorldBank'})
    wb_datasets = [d for d in wb_datasets if d is not None]
    
    print(f"\n{'Code Indicateur':<25} {'Observations':<15} {'Pays'}")
    print("-"*70)
    
    for dataset in sorted(wb_datasets)[:15]:  # Top 15
        count = db.curated_observations.count_documents({
            'source': 'WorldBank',
            'dataset': dataset
        })
        countries = db.curated_observations.distinct('key', {
            'source': 'WorldBank',
            'dataset': dataset
        })
        print(f"{dataset:<25} {count:<15,} {len(countries)}")
    
    if len(wb_datasets) > 15:
        print(f"... et {len(wb_datasets) - 15} autres indicateurs")
    
    # Vérification population Côte d'Ivoire
    print("\n" + "="*100)
    print("👥 POPULATION - Tous les pays CEDEAO")
    print("="*100)
    
    cedeao = {
        'BEN': 'Bénin', 'BFA': 'Burkina Faso', 'CIV': "Côte d'Ivoire",
        'GHA': 'Ghana', 'GIN': 'Guinée', 'GNB': 'Guinée-Bissau',
        'MLI': 'Mali', 'NER': 'Niger', 'NGA': 'Nigeria',
        'SEN': 'Sénégal', 'TGO': 'Togo', 'CPV': 'Cap-Vert',
        'GMB': 'Gambie', 'LBR': 'Liberia', 'MRT': 'Mauritanie'
    }
    
    print(f"\n{'Pays':<20} {'Code':<6} {'Population (M)':<20} {'Année':<10} {'Statut'}")
    print("-"*70)
    
    for code, name in sorted(cedeao.items(), key=lambda x: x[1]):
        key = f"{code}.SP.POP.TOTL"
        doc = db.curated_observations.find_one(
            {'source': 'WorldBank', 'dataset': 'SP.POP.TOTL', 'key': key},
            sort=[('ts', -1)]
        )
        
        if doc:
            value = doc.get('value', 0) / 1_000_000
            ts = doc.get('ts', 'N/A')
            year = ts[:4] if ts and len(ts) >= 4 else 'N/A'
            status = "✅"
        else:
            value = 0
            year = 'N/A'
            status = "❌ Manquant"
        
        print(f"{name:<20} {code:<6} {value:>15.1f}M {year:<10} {status}")
    
    # BRVM
    print("\n" + "="*100)
    print("📈 BRVM - Actions cotées")
    print("="*100)
    
    brvm_stocks = db.curated_observations.distinct('key', {'source': 'BRVM'})
    brvm_stocks = [s for s in brvm_stocks if s is not None]
    
    print(f"\n{len(brvm_stocks)} actions avec cotations")
    print(f"Dernières cotations: {', '.join(sorted(brvm_stocks)[:10])}...")
    
    # Dernière collecte
    print("\n" + "="*100)
    print("⏰ DERNIÈRES COLLECTES (5 plus récentes)")
    print("="*100)
    
    recent_runs = list(db.ingestion_runs.find().sort('timestamp', -1).limit(5))
    
    if recent_runs:
        print(f"\n{'Date':<20} {'Source':<15} {'Observations':<15} {'Statut'}")
        print("-"*70)
        
        for run in recent_runs:
            timestamp = run.get('timestamp', 'N/A')
            source = run.get('source', 'N/A')
            count = run.get('observations_count', 0)
            status = '✅ Success' if run.get('status') == 'success' else '❌ Failed'
            
            print(f"{str(timestamp)[:19]:<20} {source:<15} {count:<15,} {status}")
    else:
        print("\nAucune collecte enregistrée")
    
    # Recommandations
    print("\n" + "="*100)
    print("💡 RECOMMANDATIONS")
    print("="*100)
    
    missing_pop = sum(1 for code in cedeao.keys() if not db.curated_observations.find_one({
        'source': 'WorldBank',
        'dataset': 'SP.POP.TOTL',
        'key': f"{code}.SP.POP.TOTL"
    }))
    
    if missing_pop > 0:
        print(f"\n⚠️  {missing_pop} pays sans données de population")
        print("   → Lancer: LANCER_COLLECTE_COMPLETE.bat")
    
    if total < 10000:
        print(f"\n⚠️  Seulement {total:,} observations (objectif: 100,000+)")
        print("   → Lancer la collecte complète pour avoir toutes les données")
    
    if len(wb_datasets) < 20:
        print(f"\n⚠️  Seulement {len(wb_datasets)} indicateurs World Bank (objectif: 35)")
        print("   → Configurer Airflow pour collecte automatique hebdomadaire")
    
    if missing_pop == 0 and total >= 10000:
        print("\n✅ Base de données bien fournie et complète!")
        print("✅ Tous les pays CEDEAO ont leurs données de population")
        print("✅ Système opérationnel pour production")
    
    print("\n" + "="*100)

if __name__ == '__main__':
    main()
