"""
Nettoyage des données BRVM simulées
Supprime toutes les observations sans marqueur data_quality
"""
import sys
import os

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def nettoyer_donnees_simulees():
    print('\n' + '='*60)
    print('🧹 NETTOYAGE DES DONNEES SIMULEES BRVM')
    print('='*60 + '\n')
    
    _, db = get_mongo_db()
    
    # Compter avant suppression
    total_avant = db.curated_observations.count_documents({'source': 'BRVM'})
    simule_avant = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$exists': False}
    })
    reel_avant = total_avant - simule_avant
    
    print(f'📊 Avant nettoyage:')
    print(f'   Total observations BRVM: {total_avant}')
    print(f'   Données simulées: {simule_avant}')
    print(f'   Données réelles: {reel_avant}')
    
    if simule_avant == 0:
        print('\n✅ Aucune donnée simulée à supprimer!')
        print('   La base est déjà propre.')
        return
    
    # Confirmation automatique
    print(f'\n⚠️  Suppression de {simule_avant} observations simulées...')
    print('\n🔄 Suppression en cours...')
    
    # Suppression
    result = db.curated_observations.delete_many({
        'source': 'BRVM',
        'attrs.data_quality': {'$exists': False}
    })
    
    print(f'\n✅ Suppression terminée!')
    print(f'   {result.deleted_count} observations supprimées')
    
    # Vérification après
    total_apres = db.curated_observations.count_documents({'source': 'BRVM'})
    reel_apres = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    
    print(f'\n📊 Après nettoyage:')
    print(f'   Total observations BRVM: {total_apres}')
    print(f'   Données réelles: {reel_apres}')
    
    if total_apres > 0:
        pct_reel = (reel_apres / total_apres) * 100
        print(f'   Pourcentage réel: {pct_reel:.1f}%')
        
        if reel_apres == total_apres:
            print('\n🎉 PARFAIT! 100% de données réelles!')
        else:
            print(f'\n⚠️  Il reste {total_apres - reel_apres} observations sans marqueur qualité')
    
    print('\n' + '='*60)
    print('✅ Base de données nettoyée et prête pour la production')
    print('='*60 + '\n')

if __name__ == '__main__':
    nettoyer_donnees_simulees()
