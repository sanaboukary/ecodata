#!/usr/bin/env python3
"""
Analyse des actions BRVM présentes dans la base de données
"""
from plateforme_centralisation.mongo import get_mongo_db

# Liste officielle des 47 actions BRVM
ACTIONS_OFFICIELLES_BRVM = {
    'ABJC', 'BICC', 'BNBC', 'BOAB', 'BOABF', 'BOAC', 'BOAM',
    'CABC', 'CBIBF', 'CFAC', 'CIE', 'CIAC', 'ECOC', 'ETIT',
    'FTSC', 'NEIC', 'NSBC', 'NTLC', 'ONTBF', 'ORAC', 'ORGT',
    'PALC', 'PHCC', 'PRSC', 'SABC', 'SCRC', 'SDCC', 'SDSC',
    'SEMC', 'SGBC', 'SHEC', 'SIBC', 'SICB', 'SICC', 'SIVC',
    'SLBC', 'SMBC', 'SNTS', 'SOGC', 'STAC', 'STBC', 'SVOC',
    'TPCI', 'TTLC', 'TTLS', 'UNLC', 'UNXC'
}

def analyser_actions_db():
    client, db = get_mongo_db()
    
    print("="*80)
    print("📊 ANALYSE DES ACTIONS BRVM DANS LA BASE DE DONNÉES")
    print("="*80)
    
    # Récupérer toutes les clés uniques
    actions_db = db.curated_observations.distinct('key', {
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE'
    })
    
    print(f"\n✅ Actions officielles BRVM : {len(ACTIONS_OFFICIELLES_BRVM)}")
    print(f"📦 Actions dans la base     : {len(actions_db)}")
    
    # Analyser les différences
    actions_db_set = set(actions_db)
    
    # Actions en trop (non officielles)
    actions_extra = actions_db_set - ACTIONS_OFFICIELLES_BRVM
    
    # Actions manquantes
    actions_manquantes = ACTIONS_OFFICIELLES_BRVM - actions_db_set
    
    if actions_extra:
        print(f"\n🔴 ACTIONS NON OFFICIELLES TROUVÉES : {len(actions_extra)}")
        print("-"*80)
        for action in sorted(actions_extra):
            count = db.curated_observations.count_documents({
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': action
            })
            # Récupérer un exemple
            exemple = db.curated_observations.find_one({
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': action
            })
            qualite = exemple.get('attrs', {}).get('data_quality', 'UNKNOWN') if exemple else 'N/A'
            print(f"  • {action:15s} - {count:4d} obs - Qualité: {qualite}")
    
    if actions_manquantes:
        print(f"\n⚠️  ACTIONS OFFICIELLES MANQUANTES : {len(actions_manquantes)}")
        print("-"*80)
        for action in sorted(actions_manquantes):
            print(f"  • {action}")
    
    # Détails par type de clé
    print("\n📋 ANALYSE PAR FORMAT DE CLÉ")
    print("-"*80)
    
    formats = {}
    for action in actions_db:
        if '.BC' in action:
            fmt = 'AVEC_SUFFIXE_.BC'
        elif action in ACTIONS_OFFICIELLES_BRVM:
            fmt = 'SANS_SUFFIXE (OK)'
        else:
            fmt = 'AUTRE_FORMAT'
        
        if fmt not in formats:
            formats[fmt] = []
        formats[fmt].append(action)
    
    for fmt, actions in formats.items():
        print(f"\n{fmt}: {len(actions)} actions")
        for action in sorted(actions)[:10]:  # Afficher les 10 premières
            print(f"  • {action}")
        if len(actions) > 10:
            print(f"  ... et {len(actions) - 10} autres")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    analyser_actions_db()
