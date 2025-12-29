#!/usr/bin/env python3
"""
Vérification des actions BRVM dans la base de données
Identification des actions invalides
"""
from plateforme_centralisation.mongo import get_mongo_db

# Liste officielle des 47 actions BRVM
ACTIONS_OFFICIELLES_BRVM = {
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM',
    'CABC', 'CBIBF', 'CFAC', 'CIEC', 'CIAC', 'ECOC', 'ETIT',
    'FTSC', 'NEIC', 'NSBC', 'NTLC', 'ONTBF', 'ORAC', 'ORGT',
    'PALC', 'PHCC', 'PRSC', 'SABC', 'SCRC', 'SDCC', 'SDSC',
    'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICB', 'SICC', 'SIVC',
    'SLBC', 'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC', 'SVOC',
    'TPCI', 'TTLC', 'TTLS', 'UNLC', 'UNXC'
}

def main():
    print("="*80)
    print("VÉRIFICATION DES ACTIONS BRVM")
    print("="*80)
    
    _, db = get_mongo_db()
    
    # Récupérer toutes les actions uniques dans la base
    actions_db = db.curated_observations.distinct('key', {'source': 'BRVM'})
    
    print(f"\n📊 Statistiques:")
    print(f"   • Actions officielles BRVM: {len(ACTIONS_OFFICIELLES_BRVM)}")
    print(f"   • Actions dans MongoDB: {len(actions_db)}")
    
    # Identifier les actions invalides
    actions_invalides = set(actions_db) - ACTIONS_OFFICIELLES_BRVM
    actions_manquantes = ACTIONS_OFFICIELLES_BRVM - set(actions_db)
    
    if actions_invalides:
        print(f"\n❌ ACTIONS INVALIDES ({len(actions_invalides)}):")
        for action in sorted(actions_invalides):
            count = db.curated_observations.count_documents({
                'source': 'BRVM',
                'key': action
            })
            print(f"   • {action}: {count} observations")
    
    if actions_manquantes:
        print(f"\n⚠️  ACTIONS MANQUANTES ({len(actions_manquantes)}):")
        for action in sorted(actions_manquantes):
            print(f"   • {action}")
    
    if not actions_invalides and not actions_manquantes:
        print(f"\n✅ Toutes les actions sont valides!")
    
    # Proposer nettoyage
    if actions_invalides:
        print(f"\n" + "="*80)
        print(f"NETTOYAGE RECOMMANDÉ")
        print("="*80)
        
        total_invalides = sum(
            db.curated_observations.count_documents({'source': 'BRVM', 'key': action})
            for action in actions_invalides
        )
        
        print(f"\n🗑️  {total_invalides} observations invalides à supprimer")
        print(f"\nCommande de nettoyage:")
        print(f'   python -c "from plateforme_centralisation.mongo import get_mongo_db; _, db = get_mongo_db(); '
              f'result = db.curated_observations.delete_many({{\'source\': \'BRVM\', \'key\': {{\'$nin\': {list(ACTIONS_OFFICIELLES_BRVM)}}}}}); '
              f'print(f\'✅ {{result.deleted_count}} observations invalides supprimées\')"')

if __name__ == '__main__':
    main()
