"""
Nettoyage COMPLET : supprimer toutes les observations BRVM anciennes
Ne garder QUE les 46 observations avec data_quality = REAL_MANUAL ou REAL_SCRAPER
"""
import sys
import os

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print('\n' + '='*70)
print('🧹 NETTOYAGE COMPLET - CONSERVATION DONNEES REELLES UNIQUEMENT')
print('='*70 + '\n')

_, db = get_mongo_db()

# Stats avant
total = db.curated_observations.count_documents({'source': 'BRVM'})
avec_qualite = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})
sans_qualite = total - avec_qualite

print(f'📊 État actuel:')
print(f'   Total observations BRVM: {total}')
print(f'   Avec marqueur REAL: {avec_qualite}')
print(f'   Sans marqueur (à supprimer): {sans_qualite}')

if sans_qualite == 0:
    print('\n✅ Base déjà propre! Rien à supprimer.')
else:
    print(f'\n🔄 Suppression de {sans_qualite} observations...')
    
    # Supprimer tout ce qui n'a pas data_quality REAL_MANUAL ou REAL_SCRAPER
    result = db.curated_observations.delete_many({
        'source': 'BRVM',
        '$or': [
            {'attrs.data_quality': {'$exists': False}},
            {'attrs.data_quality': {'$nin': ['REAL_MANUAL', 'REAL_SCRAPER']}}
        ]
    })
    
    print(f'✅ {result.deleted_count} observations supprimées!')

# Vérification finale
total_final = db.curated_observations.count_documents({'source': 'BRVM'})
reel_final = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

print(f'\n📊 Après nettoyage:')
print(f'   Total observations BRVM: {total_final}')
print(f'   Données réelles: {reel_final}')

if total_final == reel_final and total_final > 0:
    print(f'\n🎉 PARFAIT! 100% de données réelles ({total_final} observations)')
    print('   La base est maintenant prête pour le trading!')
else:
    print(f'\n⚠️  Attention: {total_final - reel_final} observations restantes sans marqueur')

print('\n' + '='*70)
print('✅ Nettoyage terminé - Base prête pour la production')
print('='*70 + '\n')
