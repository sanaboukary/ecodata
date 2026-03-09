from pymongo import MongoClient
db = MongoClient('mongodb://localhost:27017').centralisation_db

print("\n" + "="*100)
print("                    AUDIT COMPLET DONNÉES STOCK_PRICE")
print("="*100 + "\n")

# Total global
total = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
print(f"📊 TOTAL GLOBAL STOCK_PRICE : {total}\n")

# Par source
print("📁 RÉPARTITION PAR SOURCE :")
print("-"*100)
pipeline = [
    {'$match': {'dataset': 'STOCK_PRICE'}},
    {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]

for item in db.curated_observations.aggregate(pipeline):
    source = item['_id']
    count = item['count']
    print(f"  {source:<35} : {count:>6,} observations")

# Vérifier les données restaurées
print("\n" + "="*100)
print("🔍 VÉRIFICATION DONNÉES RESTAURÉES (BRVM_CSV_HISTORIQUE) :")
print("-"*100)

brvm_csv = db.curated_observations.count_documents({
    'source': 'BRVM_CSV_HISTORIQUE',
    'dataset': 'STOCK_PRICE'
})

if brvm_csv > 0:
    print(f"\n✅ Données CSV historiques présentes : {brvm_csv} observations")
    
    # Période couverte
    pipeline_date = [
        {'$match': {'source': 'BRVM_CSV_HISTORIQUE', 'dataset': 'STOCK_PRICE'}},
        {'$group': {'_id': None, 'min_ts': {'$min': '$ts'}, 'max_ts': {'$max': '$ts'}}}
    ]
    periode = list(db.curated_observations.aggregate(pipeline_date))
    if periode:
        print(f"  Période : {periode[0]['min_ts']} → {periode[0]['max_ts']}")
    
    # Actions
    actions = db.curated_observations.distinct('key', {
        'source': 'BRVM_CSV_HISTORIQUE',
        'dataset': 'STOCK_PRICE'
    })
    print(f"  Actions : {len(actions)}")
    
    # Jours uniques
    jours = db.curated_observations.distinct('ts', {
        'source': 'BRVM_CSV_HISTORIQUE',
        'dataset': 'STOCK_PRICE'
    })
    print(f"  Jours de collecte : {len(jours)}")
else:
    print("\n❌ AUCUNE donnée CSV historique trouvée !")

# Vérifier les collectes BRVM actuelles
print("\n" + "="*100)
print("🔍 VÉRIFICATION COLLECTES BRVM ACTUELLES (source=BRVM) :")
print("-"*100)

brvm_actuel = db.curated_observations.count_documents({
    'source': 'BRVM',
    'dataset': 'STOCK_PRICE'
})

print(f"\n  Collectes BRVM actuelles : {brvm_actuel} observations")

if brvm_actuel > 0:
    # Jours
    jours_brvm = db.curated_observations.distinct('ts', {
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE'
    })
    print(f"  Jours : {len(jours_brvm)}")
    
    pipeline_date_brvm = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
        {'$group': {'_id': None, 'min_ts': {'$min': '$ts'}, 'max_ts': {'$max': '$ts'}}}
    ]
    periode_brvm = list(db.curated_observations.aggregate(pipeline_date_brvm))
    if periode_brvm:
        print(f"  Période : {periode_brvm[0]['min_ts']} → {periode_brvm[0]['max_ts']}")

# Vérifier agrégation hebdomadaire
print("\n" + "="*100)
print("🔍 VÉRIFICATION AGRÉGATION HEBDOMADAIRE :")
print("-"*100)

hebdo = db.curated_observations.count_documents({
    'source': 'AGREGATION_HEBDOMADAIRE',
    'dataset': 'STOCK_PRICE'
})

if hebdo > 0:
    print(f"\n✅ Agrégation hebdomadaire présente : {hebdo} semaines")
    
    # Semaines
    semaines = db.curated_observations.distinct('ts', {
        'source': 'AGREGATION_HEBDOMADAIRE',
        'dataset': 'STOCK_PRICE'
    })
    print(f"  Nombre de semaines : {len(semaines)}")
else:
    print("\n  Pas d'agrégation hebdomadaire")

print("\n" + "="*100)
print("📋 RÉSUMÉ :")
print("-"*100)
print(f"  Total STOCK_PRICE           : {total:,}")
print(f"  ├─ BRVM (collectes)         : {brvm_actuel:,}")
print(f"  ├─ BRVM_CSV_HISTORIQUE      : {brvm_csv:,}")
print(f"  └─ AGREGATION_HEBDOMADAIRE  : {hebdo:,}")
print("\n" + "="*100 + "\n")
