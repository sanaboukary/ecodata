#!/usr/bin/env python3
"""
Vérifier toutes les collections MongoDB contenant des données BRVM
pour restaurer les observations supprimées
"""

import pymongo
from datetime import datetime

def verifier_collections_brvm():
    """Chercher données BRVM dans toutes les collections"""
    
    print(f"[RECHERCHE DONNÉES BRVM]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Connexion MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    # Lister toutes les collections
    collections = db.list_collection_names()
    print(f"Collections disponibles: {len(collections)}")
    
    # Collections potentiellement contenant données BRVM
    collections_brvm = []
    
    for coll_name in collections:
        coll = db[coll_name]
        count = coll.count_documents({})
        
        if count > 0:
            # Chercher documents avec champs BRVM typiques
            sample = coll.find_one()
            
            # Vérifier si c'est lié à BRVM
            brvm_related = False
            if sample:
                sample_str = str(sample).lower()
                if any(keyword in sample_str for keyword in ['brvm', 'stock', 'cours', 'bourse', 'action', 'ticker']):
                    brvm_related = True
                
                # Ou si a des champs typiques BRVM
                if any(field in sample for field in ['symbole', 'ticker', 'prix_cloture', 'cours', 'variation']):
                    brvm_related = True
            
            if brvm_related:
                collections_brvm.append({
                    'nom': coll_name,
                    'count': count,
                    'sample': sample
                })
    
    print(f"\n[COLLECTIONS BRVM TROUVÉES: {len(collections_brvm)}]\n")
    
    # Afficher détails
    for coll_info in collections_brvm:
        print(f"Collection: {coll_info['nom']}")
        print(f"  Documents: {coll_info['count']}")
        
        sample = coll_info['sample']
        if sample:
            # Afficher champs clés
            keys = list(sample.keys())[:10]
            print(f"  Champs: {', '.join(keys)}")
            
            # Si a un champ symbole, montrer exemples
            if 'symbole' in sample:
                coll = db[coll_info['nom']]
                symboles = coll.distinct('symbole')
                print(f"  Symboles ({len(symboles)}): {symboles[:10]}")
            
            if 'ticker' in sample:
                coll = db[coll_info['nom']]
                tickers = coll.distinct('ticker')
                print(f"  Tickers ({len(tickers)}): {tickers[:10]}")
        
        print()
    
    # Chercher spécifiquement données avec prix BRVM typiques
    print("\n[RECHERCHE PAR PRIX BRVM TYPIQUES]")
    
    for coll_name in collections:
        coll = db[coll_name]
        
        # Chercher documents avec prix dans la range BRVM (1000-60000 FCFA)
        query_prix = {}
        if coll_name != 'curated_observations':  # Éviter celle qu'on a vidée
            # Essayer différents noms de champs prix
            for price_field in ['prix', 'cours', 'prix_cloture', 'close', 'price', 'valeur']:
                try:
                    count_prix = coll.count_documents({
                        price_field: {'$gte': 1000, '$lte': 60000}
                    })
                    if count_prix > 0:
                        print(f"  {coll_name}.{price_field}: {count_prix} documents prix BRVM")
                        
                        # Échantillon
                        sample = coll.find_one({price_field: {'$gte': 1000, '$lte': 60000}})
                        if sample:
                            print(f"    Exemple: {sample}\n")
                except:
                    pass
    
    # Vérifier collection raw_brvm ou brvm_raw
    print("\n[COLLECTIONS RAW/BACKUP]")
    for pattern in ['raw', 'backup', 'archive', 'original', 'brvm']:
        matching = [c for c in collections if pattern in c.lower()]
        if matching:
            for coll_name in matching:
                count = db[coll_name].count_documents({})
                print(f"  {coll_name}: {count} documents")
                if count > 0:
                    sample = db[coll_name].find_one()
                    print(f"    Exemple: {list(sample.keys())[:10]}")
    
    client.close()

if __name__ == "__main__":
    try:
        verifier_collections_brvm()
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
