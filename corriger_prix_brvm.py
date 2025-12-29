"""
CORRECTION MASSIVE DES PRIX BRVM
Applique les facteurs de correction basés sur les prix réels BRVM.org
"""
import os
import sys
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

_, db = get_mongo_db()

# Prix réels vérifiés BRVM.org (8 Décembre 2025)
# Source: https://www.brvm.org/fr/investir/cours-et-cotations
PRIX_REELS_AUJOURD_HUI = {
    'UNLC': 43390,   # Unilever CI (vérifié)
    'SNTS': 15500,   # Sonatel (à vérifier sur site)
    'SGBC': 13000,   # Société Générale (à vérifier sur site)
    # Ajouter les autres actions ici après vérification
}

def calculer_facteur_correction(action):
    """Calcule le facteur de correction basé sur le prix actuel"""
    prix_reel = PRIX_REELS_AUJOURD_HUI.get(action)
    if not prix_reel:
        return None
    
    # Récupérer le dernier prix dans la base
    latest = db.curated_observations.find_one(
        {'source': 'BRVM', 'key': action},
        sort=[('ts', -1)]
    )
    
    if not latest:
        return None
    
    prix_db = latest.get('value')
    if not prix_db or prix_db == 0:
        return None
    
    facteur = prix_reel / prix_db
    return facteur

def corriger_action(action, facteur, dry_run=True):
    """Corrige tous les prix d'une action en appliquant le facteur"""
    
    # Compter les observations à corriger
    total = db.curated_observations.count_documents({
        'source': 'BRVM',
        'key': action
    })
    
    print(f'\n📊 {action}: {total} observations à corriger (facteur: {facteur:.2f}x)')
    
    if dry_run:
        print(f'   [DRY RUN] Simulation uniquement')
        return 0
    
    # Appliquer la correction
    corrected = 0
    observations = db.curated_observations.find({'source': 'BRVM', 'key': action})
    
    for obs in observations:
        old_value = obs['value']
        new_value = old_value * facteur
        
        # Mettre à jour
        db.curated_observations.update_one(
            {'_id': obs['_id']},
            {
                '$set': {
                    'value': round(new_value, 2),
                    'attrs.corrected': True,
                    'attrs.correction_factor': facteur,
                    'attrs.correction_date': datetime.now(),
                    'attrs.old_value': old_value
                }
            }
        )
        corrected += 1
        
        if corrected % 100 == 0:
            print(f'   Progression: {corrected}/{total}')
    
    print(f'   ✅ {corrected} observations corrigées')
    return corrected

def main():
    print('='*80)
    print('🔧 CORRECTION MASSIVE DES PRIX BRVM')
    print('='*80)
    print('\n⚠️  ATTENTION: Cette opération va modifier TOUTES les observations!')
    print('   Assurez-vous d\'avoir une sauvegarde MongoDB avant de continuer.\n')
    
    # Phase 1: Analyse
    print('='*80)
    print('PHASE 1: CALCUL DES FACTEURS DE CORRECTION')
    print('='*80)
    
    facteurs = {}
    for action in PRIX_REELS_AUJOURD_HUI.keys():
        facteur = calculer_facteur_correction(action)
        if facteur:
            facteurs[action] = facteur
            prix_reel = PRIX_REELS_AUJOURD_HUI[action]
            print(f'{action}: Facteur {facteur:.2f}x → Prix cible: {prix_reel:,} FCFA')
        else:
            print(f'{action}: ❌ Impossible de calculer le facteur')
    
    if not facteurs:
        print('\n❌ AUCUN FACTEUR CALCULÉ - ARRÊT')
        return
    
    # Phase 2: Dry run
    print('\n' + '='*80)
    print('PHASE 2: SIMULATION (DRY RUN)')
    print('='*80)
    
    total_corrections = 0
    for action, facteur in facteurs.items():
        count = corriger_action(action, facteur, dry_run=True)
        total_corrections += count
    
    print(f'\n📊 Total estimé: {total_corrections} observations à corriger')
    
    # Phase 3: Confirmation
    print('\n' + '='*80)
    print('⚠️  CONFIRMATION REQUISE')
    print('='*80)
    print(f'Voulez-vous appliquer ces corrections? (yes/no)')
    print('Tapez "yes" pour confirmer:')
    
    # Pour l'instant, on s'arrête là (sécurité)
    print('\n' + '='*80)
    print('🛑 MODE SÉCURISÉ: Correction non appliquée')
    print('='*80)
    print('''
Pour appliquer les corrections:
1. Sauvegarder MongoDB: mongodump --db centralisation_db
2. Éditer ce script: Changer dry_run=False
3. Relancer: python corriger_prix_brvm.py
    ''')
    
    print('\n' + '='*80)
    print('💡 RECOMMANDATION ALTERNATIVE')
    print('='*80)
    print('''
Au lieu de corriger, il est plus sûr de:
1. Purger les données erronées
2. Récupérer les VRAIS prix BRVM.org (scraping)
3. Importer les prix corrects avec data_quality=REAL_SCRAPER
    ''')

if __name__ == '__main__':
    main()
