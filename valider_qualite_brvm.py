"""
Validation qualite donnees BRVM apres nettoyage outliers
"""
from pymongo import MongoClient
import statistics

def valider_qualite_brvm():
    """Valide la qualite des donnees BRVM pour trading"""
    
    db = MongoClient('mongodb://localhost:27017/')['centralisation_db']
    
    print("[VALIDATION QUALITE DONNEES BRVM]\n")
    
    # 1. Coherence prix
    print("[1/4] Coherence des prix...")
    prix_data = list(db.curated_observations.find(
        {'dataset': 'STOCK_PRICE', 'attrs.cours': {'$exists': True}},
        {'symbole': 1, 'attrs.cours': 1}
    ))
    
    if prix_data:
        prix_list = [d['attrs']['cours'] for d in prix_data if d['attrs'].get('cours')]
        if prix_list:
            prix_min = min(prix_list)
            prix_max = max(prix_list)
            prix_moy = statistics.mean(prix_list)
            prix_med = statistics.median(prix_list)
            
            print(f"  Prix min: {prix_min:.0f} FCFA")
            print(f"  Prix max: {prix_max:.0f} FCFA")
            print(f"  Prix moyen: {prix_moy:.0f} FCFA")
            print(f"  Prix median: {prix_med:.0f} FCFA")
            
            # Verifier limites
            if prix_min >= 100 and prix_max <= 100000:
                print("  [OK] Tous les prix dans limites BRVM reelles (100-100,000 FCFA)")
            else:
                print(f"  [ALERTE] Certains prix hors limites")
    else:
        print("  [ERREUR] Aucune donnee de prix trouvee")
    
    # 2. Coherence variations
    print("\n[2/4] Coherence des variations...")
    var_data = list(db.curated_observations.find(
        {'dataset': 'STOCK_PRICE', 'attrs.variation': {'$exists': True}},
        {'symbole': 1, 'attrs.variation': 1}
    ))
    
    if var_data:
        var_list = [d['attrs']['variation'] for d in var_data if d['attrs'].get('variation') is not None]
        if var_list:
            var_min = min(var_list)
            var_max = max(var_list)
            var_moy = statistics.mean(var_list)
            
            print(f"  Variation min: {var_min:+.2f}%")
            print(f"  Variation max: {var_max:+.2f}%")
            print(f"  Variation moyenne: {var_moy:+.2f}%")
            
            # Compter variations extremes
            extremes = [v for v in var_list if abs(v) > 50]
            print(f"  Variations extremes (>50%): {len(extremes)}")
            
            if abs(var_min) <= 50 and var_max <= 50:
                print("  [OK] Toutes variations dans limites quotidiennes normales")
            else:
                print(f"  [INFO] {len(extremes)} variations extremes (conservees pour opportunites)")
    
    # 3. Completude donnees
    print("\n[3/4] Completude des donnees...")
    total = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
    avec_prix = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'attrs.cours': {'$exists': True, '$ne': None}
    })
    avec_volume = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'attrs.volume': {'$exists': True}
    })
    avec_variation = db.curated_observations.count_documents({
        'dataset': 'STOCK_PRICE',
        'attrs.variation': {'$exists': True, '$ne': None}
    })
    
    print(f"  Total observations: {total}")
    print(f"  Avec prix: {avec_prix} ({avec_prix/total*100:.1f}%)")
    print(f"  Avec volume: {avec_volume} ({avec_volume/total*100:.1f}%)")
    print(f"  Avec variation: {avec_variation} ({avec_variation/total*100:.1f}%)")
    
    if avec_prix == total and avec_variation >= total * 0.95:
        print("  [OK] Donnees completes (>95%)")
    else:
        print("  [ALERTE] Donnees incompletes")
    
    # 4. Distribution par action
    print("\n[4/4] Distribution par action...")
    pipeline = [
        {'$match': {'dataset': 'STOCK_PRICE'}},
        {'$group': {
            '_id': '$symbole',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': 1}}
    ]
    
    distrib = list(db.curated_observations.aggregate(pipeline))
    nb_actions = len(distrib)
    
    if distrib:
        obs_min = distrib[0]['count']
        obs_max = distrib[-1]['count']
        obs_moy = sum(d['count'] for d in distrib) / len(distrib)
        
        print(f"  Nombre d'actions: {nb_actions}")
        print(f"  Observations min par action: {obs_min}")
        print(f"  Observations max par action: {obs_max}")
        print(f"  Observations moyennes: {obs_moy:.1f}")
        
        # Actions avec peu de donnees
        peu_donnees = [d for d in distrib if d['count'] < 10]
        if peu_donnees:
            print(f"\n  [INFO] {len(peu_donnees)} actions avec <10 observations:")
            for action in peu_donnees[:5]:
                print(f"    - {action['_id']}: {action['count']} obs")
        
        if obs_min >= 5:
            print(f"\n  [OK] Toutes actions ont donnees suffisantes (min {obs_min})")
        else:
            print(f"\n  [ALERTE] Certaines actions ont peu de donnees (min {obs_min})")
    
    # VERDICT GLOBAL
    print("\n" + "="*60)
    print("VERDICT QUALITE")
    print("="*60)
    
    score_qualite = 0
    if prix_min >= 100 and prix_max <= 100000:
        score_qualite += 25
    if abs(var_min) <= 150 and var_max <= 150:
        score_qualite += 25
    if avec_prix >= total * 0.95:
        score_qualite += 25
    if obs_min >= 5:
        score_qualite += 25
    
    print(f"Score qualite: {score_qualite}/100")
    
    if score_qualite >= 75:
        print("[OK] EXCELLENTE QUALITE - Donnees pretes pour trading TOP5")
    elif score_qualite >= 50:
        print("[INFO] QUALITE ACCEPTABLE - Quelques ameliorations possibles")
    else:
        print("[ALERTE] QUALITE INSUFFISANTE - Nettoyage supplementaire requis")
    
    return {
        'score_qualite': score_qualite,
        'prix_min': prix_min,
        'prix_max': prix_max,
        'total_observations': total,
        'nb_actions': nb_actions
    }


if __name__ == '__main__':
    stats = valider_qualite_brvm()
    print(f"\nScore final: {stats['score_qualite']}/100")
