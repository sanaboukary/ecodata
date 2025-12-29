"""
Compléteur automatique des prix BRVM manquants
Utilise les prix moyens historiques pour estimer les prix actuels des 38 actions restantes
"""
import os
import sys
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

_, db = get_mongo_db()

# Actions déjà mises à jour (avec vrais prix)
ACTIONS_DEJA_MISES_A_JOUR = {'UNLC', 'SNTS', 'SGBC', 'SIVC', 'ONTBF', 'BICC', 'BOAM', 'BOAB', 'BOAG'}

# Toutes les actions BRVM (47)
TOUTES_ACTIONS_BRVM = [
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAG', 'BOAM', 'BOAN', 'BOAS',
    'CABC', 'CBIBF', 'CFAC', 'CIEC', 'ECOC', 'ETIT', 'FTSC', 'LIBC', 'NEIC', 'NSBC',
    'NSIAS', 'NSIAC', 'NTLC', 'ONTBF', 'ORGT', 'PALC', 'PRSC', 'PVBC', 'SAFC', 'SCRC',
    'SDCC', 'SDSC', 'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICC', 'SICG', 'SITC', 'SIVC',
    'SLBC', 'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC', 'TTLS', 'UNLC'
]

def calculer_prix_moyen_recent(action, jours=30):
    """Calcule le prix moyen récent d'une action"""
    threshold = (datetime.now() - timedelta(days=jours)).strftime('%Y-%m-%d')
    
    observations = list(db.curated_observations.find({
        'source': 'BRVM',
        'key': action,
        'ts': {'$gte': threshold}
    }).sort('ts', -1))
    
    if not observations:
        # Fallback: prendre toutes les observations
        observations = list(db.curated_observations.find({
            'source': 'BRVM',
            'key': action
        }).sort('ts', -1).limit(20))
    
    if observations:
        prix_recent = observations[0].get('value')
        prix_moyen = sum(obs.get('value', 0) for obs in observations) / len(observations)
        prix_max = max(obs.get('value', 0) for obs in observations)
        prix_min = min(obs.get('value', 0) for obs in observations)
        
        return {
            'recent': prix_recent,
            'moyen': prix_moyen,
            'max': prix_max,
            'min': prix_min,
            'nb_obs': len(observations)
        }
    
    return None

def generer_prix_manquants():
    """Génère les prix manquants basés sur l'historique"""
    print('='*80)
    print('GENERATION PRIX MANQUANTS - BASEE SUR HISTORIQUE')
    print('='*80)
    
    prix_generes = {}
    actions_manquantes = []
    
    for action in TOUTES_ACTIONS_BRVM:
        if action in ACTIONS_DEJA_MISES_A_JOUR:
            continue
        
        stats = calculer_prix_moyen_recent(action)
        
        if stats:
            # Utiliser le prix récent comme estimation
            prix_generes[action] = {
                'close': round(stats['recent'], 0),
                'open': round(stats['recent'] * 0.995, 0),
                'high': round(stats['recent'] * 1.005, 0),
                'low': round(stats['recent'] * 0.995, 0),
                'volume': 1500,
                'variation': 0.5,
                'source': 'HISTORIQUE',
                'confiance': 'MOYENNE'
            }
            
            print(f'{action:6s}: {stats["recent"]:>8,.0f} FCFA (basé sur {stats["nb_obs"]} obs, moy: {stats["moyen"]:.0f})')
        else:
            actions_manquantes.append(action)
            print(f'{action:6s}: ❌ Aucune donnée historique')
    
    if actions_manquantes:
        print(f'\n⚠️  {len(actions_manquantes)} actions sans données: {", ".join(actions_manquantes)}')
    
    return prix_generes

def appliquer_prix_generes(prix_generes, dry_run=True):
    """Applique les prix générés"""
    print('\n' + '='*80)
    if dry_run:
        print('SIMULATION - PRIX À APPLIQUER')
    else:
        print('APPLICATION DES PRIX')
    print('='*80)
    
    today = datetime.now().strftime('%Y-%m-%d')
    updated = 0
    
    for action, data in prix_generes.items():
        print(f'\n{action}: {data["close"]:,.0f} FCFA (source: {data["source"]}, confiance: {data["confiance"]})')
        
        if not dry_run:
            observation = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': action,
                'ts': today,
                'value': data['close'],
                'attrs': {
                    'open': data['open'],
                    'high': data['high'],
                    'low': data['low'],
                    'volume': data['volume'],
                    'day_change_pct': data['variation'],
                    'data_quality': 'ESTIMATED_FROM_HISTORY',
                    'update_source': 'AUTO_COMPLETION_8DEC',
                    'estimation_method': 'recent_price',
                    'update_date': datetime.now()
                }
            }
            
            result = db.curated_observations.insert_one(observation)
            print(f'   ✅ Inséré (ID: {result.inserted_id})')
            updated += 1
    
    print('\n' + '='*80)
    if dry_run:
        print(f'📊 {len(prix_generes)} actions prêtes à être complétées')
    else:
        print(f'✅ {updated} actions complétées')
    print('='*80)
    
    return updated

def main():
    print('\n⚠️  ATTENTION: Ce script complète les prix manquants en utilisant')
    print('   les prix historiques récents (non les vrais prix BRVM.org)')
    print('   Pour avoir des prix 100% réels, mettre à jour manuellement.\n')
    
    # Générer les prix
    prix_generes = generer_prix_manquants()
    
    print(f'\n📊 Résumé:')
    print(f'   Actions avec vrais prix: {len(ACTIONS_DEJA_MISES_A_JOUR)}')
    print(f'   Actions à compléter: {len(prix_generes)}')
    print(f'   Total: {len(ACTIONS_DEJA_MISES_A_JOUR) + len(prix_generes)}/47')
    
    # Dry run
    appliquer_prix_generes(prix_generes, dry_run=True)
    
    print('\n💡 Pour appliquer: python completer_prix_manquants.py --apply')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Appliquer les mises à jour')
    args = parser.parse_args()
    
    if args.apply:
        print('\n' + '='*80)
        print('APPLICATION DES PRIX')
        print('='*80)
        
        prix_generes = generer_prix_manquants()
        updated = appliquer_prix_generes(prix_generes, dry_run=False)
        
        print(f'\n✅ {updated} actions complétées')
        print('\n🔄 Prochaines étapes:')
        print('   1. Vérifier: python verifier_correction_prix.py')
        print('   2. Relancer analyse: python lancer_analyse_ia_complete.py')
        print('   3. Activer Airflow 17h30: python activer_recommandations_17h30.py')
    else:
        main()
