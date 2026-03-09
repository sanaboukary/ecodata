"""
Nettoyage intelligent des outliers BRVM pour objectif TRADING
Filtre les erreurs de scraping tout en conservant les vraies opportunites
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import statistics

def nettoyer_outliers_brvm_trading():
    """
    Nettoie les outliers selon l'objectif TRADING:
    - Conserve les variations fortes legitimes (opportunites)
    - Supprime les erreurs de scraping evidentes
    - Applique des limites realistes BRVM
    """
    
    db = MongoClient('mongodb://localhost:27017/')['centralisation_db']
    
    # LIMITES REALISTES BRVM (basees sur historique reel)
    PRIX_MIN_BRVM = 100      # Prix minimum reel: ~100 FCFA
    PRIX_MAX_BRVM = 100000   # Prix maximum reel: ~100,000 FCFA
    VARIATION_MAX_JOUR = 50  # Variation max quotidienne: 50% (rare mais possible)
    VARIATION_MAX_SEMAINE = 150  # Variation max hebdo: 150%
    VOLUME_MIN = 0           # Volume peut etre 0 (illiquidite)
    VOLUME_MAX = 10000000    # Volume max quotidien: 10M actions
    
    print("[NETTOYAGE OUTLIERS BRVM - OBJECTIF TRADING]")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 0. Suppression observations avec symbole manquant
    print("[0/6] Detection observations avec symbole manquant...")
    symbole_manquant = db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        '$or': [
            {'symbole': None},
            {'symbole': {'$exists': False}},
            {'symbole': 'N/A'},
            {'symbole': ''}
        ]
    })
    
    count_symbole_manquant = 0
    for doc in symbole_manquant:
        symbole = doc.get('symbole', 'N/A')
        prix = doc.get('attrs', {}).get('cours', 'N/A')
        print(f"  [OUTLIER SYMBOLE] symbole={symbole}, prix={prix}")
        db.curated_observations.delete_one({'_id': doc['_id']})
        count_symbole_manquant += 1
    
    print(f"  -> {count_symbole_manquant} observations sans symbole supprimees\n")
    
    # 1. Prix aberrants
    print("[1/6] Detection prix aberrants...")
    prix_aberrants = db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        '$or': [
            {'attrs.cours': {'$lt': PRIX_MIN_BRVM}},
            {'attrs.cours': {'$gt': PRIX_MAX_BRVM}},
            {'attrs.cours': {'$exists': False}},
            {'attrs.cours': None}
        ]
    })
    
    count_prix_aberrants = 0
    for doc in prix_aberrants:
        prix = doc.get('attrs', {}).get('cours', 'N/A')
        symbole = doc.get('symbole', 'N/A')
        print(f"  [OUTLIER PRIX] {symbole}: {prix} FCFA (hors limites {PRIX_MIN_BRVM}-{PRIX_MAX_BRVM})")
        
        # Supprimer les prix completement aberrants
        if prix == 'N/A' or prix is None or prix < PRIX_MIN_BRVM or prix > PRIX_MAX_BRVM:
            db.curated_observations.delete_one({'_id': doc['_id']})
            count_prix_aberrants += 1
    
    print(f"  -> {count_prix_aberrants} observations avec prix aberrants supprimees\n")
    
    # 2. Variations extremes (probablement erreurs)
    print("[2/6] Detection variations extremes...")
    variations_extremes = db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        '$or': [
            {'attrs.variation': {'$gt': VARIATION_MAX_JOUR}},
            {'attrs.variation': {'$lt': -VARIATION_MAX_JOUR}}
        ]
    })
    
    count_variations = 0
    for doc in variations_extremes:
        var = doc.get('attrs', {}).get('variation', 0)
        symbole = doc.get('symbole', 'N/A')
        print(f"  [OUTLIER VAR] {symbole}: {var:+.1f}% (limite +/-{VARIATION_MAX_JOUR}%)")
        
        # Flaguer mais NE PAS supprimer (peut etre vraie opportunite)
        # Plafonner a la limite max pour ne pas fausser analyses
        nouvelle_var = max(min(var, VARIATION_MAX_JOUR), -VARIATION_MAX_JOUR)
        db.curated_observations.update_one(
            {'_id': doc['_id']},
            {
                '$set': {
                    'attrs.variation': nouvelle_var,
                    'attrs.variation_originale': var,
                    'attrs.outlier_corrige': True
                }
            }
        )
        count_variations += 1
    
    print(f"  -> {count_variations} variations plafonnees (conservees pour trading)\n")
    
    # 3. Volumes aberrants
    print("[3/6] Detection volumes aberrants...")
    volumes_aberrants = db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        '$or': [
            {'attrs.volume': {'$lt': VOLUME_MIN}},
            {'attrs.volume': {'$gt': VOLUME_MAX}},
            {'attrs.volume': None}
        ]
    })
    
    count_volumes = 0
    for doc in volumes_aberrants:
        vol = doc.get('attrs', {}).get('volume', 0)
        symbole = doc.get('symbole', 'N/A')
        
        if vol is None or vol < VOLUME_MIN:
            # Volume null -> mettre a 0 (action illiquide)
            db.curated_observations.update_one(
                {'_id': doc['_id']},
                {'$set': {'attrs.volume': 0}}
            )
            count_volumes += 1
        elif vol > VOLUME_MAX:
            print(f"  [OUTLIER VOL] {symbole}: {vol:,.0f} actions (limite {VOLUME_MAX:,.0f})")
            # Plafonner au max raisonnable
            db.curated_observations.update_one(
                {'_id': doc['_id']},
                {
                    '$set': {
                        'attrs.volume': VOLUME_MAX,
                        'attrs.volume_original': vol,
                        'attrs.outlier_corrige': True
                    }
                }
            )
            count_volumes += 1
    
    print(f"  -> {count_volumes} volumes corriges\n")
    
    # 4. Doublons temporels (meme action, meme date, prix differents)
    print("[4/6] Detection doublons temporels...")
    pipeline = [
        {'$match': {'dataset': 'STOCK_PRICE'}},
        {'$group': {
            '_id': {
                'symbole': '$symbole',
                'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}}
            },
            'count': {'$sum': 1},
            'ids': {'$push': '$_id'},
            'prix': {'$push': '$attrs.cours'}
        }},
        {'$match': {'count': {'$gt': 1}}}
    ]
    
    doublons = list(db.curated_observations.aggregate(pipeline))
    count_doublons = 0
    
    for doublon in doublons:
        # Gerer le cas ou symbole est None ou manquant
        symbole_id = doublon.get('_id', {})
        if symbole_id is None:
            symbole_id = {}
        
        symbole = symbole_id.get('symbole', 'N/A')
        date = symbole_id.get('date', 'N/A')
        prix_list = doublon.get('prix', [])
        ids = doublon.get('ids', [])
        
        if symbole == 'N/A' or len(ids) <= 1:
            continue
        
        print(f"  [DOUBLON] {symbole} {date}: {len(ids)} entrees, prix: {prix_list}")
        
        # Garder uniquement la derniere entree (plus recente)
        # Supprimer les autres
        for id_to_delete in ids[:-1]:
            db.curated_observations.delete_one({'_id': id_to_delete})
            count_doublons += 1
    
    print(f"  -> {count_doublons} doublons temporels supprimes\n")
    
    # 5. Observations avec timestamp invalide
    print("[5/6] Detection timestamps invalides...")
    timestamps_invalides = db.curated_observations.find({
        'dataset': 'STOCK_PRICE',
        '$or': [
            {'timestamp': None},
            {'timestamp': {'$exists': False}}
        ]
    })
    
    count_timestamps = 0
    for doc in timestamps_invalides:
        db.curated_observations.delete_one({'_id': doc['_id']})
        count_timestamps += 1
    
    print(f"  -> {count_timestamps} observations sans timestamp supprimees\n")
    
    # 6. Statistics finales
    print("[6/6] Statistiques apres nettoyage...")
    total_stock_price = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
    
    # Compter par symbole
    pipeline_symboles = [
        {'$match': {'dataset': 'STOCK_PRICE'}},
        {'$group': {
            '_id': '$symbole',
            'count': {'$sum': 1},
            'prix_min': {'$min': '$attrs.cours'},
            'prix_max': {'$max': '$attrs.cours'},
            'prix_moyen': {'$avg': '$attrs.cours'}
        }},
        {'$sort': {'count': -1}}
    ]
    
    stats_symboles = list(db.curated_observations.aggregate(pipeline_symboles))
    
    print(f"\n[STATS FINALES]")
    print(f"Total observations STOCK_PRICE: {total_stock_price}")
    print(f"Nombre d'actions: {len(stats_symboles)}")
    print(f"\nTop 5 actions (nb observations):")
    for i, stat in enumerate(stats_symboles[:5], 1):
        print(f"  {i}. {stat['_id']}: {stat['count']} obs, prix {stat['prix_min']:.0f}-{stat['prix_max']:.0f} FCFA (moy: {stat['prix_moyen']:.0f})")
    
    print(f"\n[RESUME NETTOYAGE]")
    print(f"  Symboles manquants supprimes: {count_symbole_manquant}")
    print(f"  Prix aberrants supprimes:     {count_prix_aberrants}")
    print(f"  Variations plafonnees:        {count_variations}")
    print(f"  Volumes corriges:             {count_volumes}")
    print(f"  Doublons temporels supprimes: {count_doublons}")
    print(f"  Timestamps invalides:         {count_timestamps}")
    total_nettoyage = count_symbole_manquant + count_prix_aberrants + count_variations + count_volumes + count_doublons + count_timestamps
    print(f"  TOTAL OUTLIERS NETTOYES:      {total_nettoyage}")
    
    print(f"\n[OK] Nettoyage termine - Donnees optimisees pour objectif TRADING")
    
    return {
        'symboles_manquants': count_symbole_manquant,
        'prix_aberrants': count_prix_aberrants,
        'variations_plafonnees': count_variations,
        'volumes_corriges': count_volumes,
        'doublons_supprimes': count_doublons,
        'timestamps_invalides': count_timestamps,
        'total_nettoyage': total_nettoyage,
        'total_observations': total_stock_price,
        'nb_actions': len(stats_symboles)
    }


if __name__ == '__main__':
    stats = nettoyer_outliers_brvm_trading()
    
    # Afficher resultats
    print("\n" + "="*60)
    print("NETTOYAGE TERMINE")
    print("="*60)
    print(f"Donnees BRVM propres et pretes pour generation TOP5 hebdomadaire")
    print(f"Outliers nettoyes: {stats['total_nettoyage']} / Observations finales: {stats['total_observations']}")
