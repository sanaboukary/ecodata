#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test direct des données WorldBank pour le dashboard
"""
from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# Codes pays CEDEAO
PAYS_CEDEAO = {
    'BEN': 'Bénin',
    'BFA': 'Burkina Faso', 
    'CIV': 'Côte d\'Ivoire',
    'GMB': 'Gambie',
    'GHA': 'Ghana',
    'GIN': 'Guinée',
    'GNB': 'Guinée-Bissau',
    'LBR': 'Libéria',
    'MLI': 'Mali',
    'MRT': 'Mauritanie',
    'NER': 'Niger',
    'NGA': 'Nigeria',
    'SEN': 'Sénégal',
    'SLE': 'Sierra Leone',
    'TGO': 'Togo'
}

# Nouveaux indicateurs disponibles
INDICATEURS = {
    'NY.GDP.PCAP.CD': {'nom': 'PIB par Habitant', 'unite': '$'},
    'SP.POP.TOTL': {'nom': 'Population', 'unite': 'M'},
    'FP.CPI.TOTL.ZG': {'nom': 'Inflation (CPI)', 'unite': '%'},
    'SH.DYN.MORT': {'nom': 'Mortalité Infantile', 'unite': '‰'},
    'SE.PRM.ENRR': {'nom': 'Scolarisation Primaire', 'unite': '%'},
    'SL.UEM.TOTL.ZS': {'nom': 'Taux de Chômage', 'unite': '%'},
    'NE.TRD.GNFS.ZS': {'nom': 'Commerce/PIB', 'unite': '%'},
    'IT.NET.USER.ZS': {'nom': 'Utilisateurs Internet', 'unite': '%'}
}

print("=" * 100)
print("🌍 TEST RÉCUPÉRATION DONNÉES WORLDBANK PAR PAYS")
print("=" * 100)
print()

# Test pour chaque pays
for country_code, country_name in sorted(PAYS_CEDEAO.items()):
    print(f"\n{'='*100}")
    print(f"📍 {country_name} ({country_code})")
    print(f"{'='*100}")
    
    for indicator_code, info in INDICATEURS.items():
        # Rechercher données avec regex (comme dans le dashboard)
        data = db.curated_observations.find_one({
            'source': 'WorldBank',
            'dataset': indicator_code,
            'key': {'$regex': f'^{country_code}\\.'}
        }, sort=[('ts', -1)])
        
        if data and data.get('value') is not None:
            value = data['value']
            unite = info['unite']
            ts = data.get('ts', 'N/A')
            
            # Formater selon l'unité
            if unite == 'M':
                formatted = f"{value/1_000_000:,.2f} M"
            elif unite == '$':
                formatted = f"${value:,.0f}"
            elif unite == '%' or unite == '‰':
                formatted = f"{value:.2f}{unite}"
            else:
                formatted = f"{value:,.2f}"
            
            print(f"  ✅ {info['nom']:25s}: {formatted:>15s} ({ts})")
        else:
            print(f"  ❌ {info['nom']:25s}: Pas de données")

print("\n" + "=" * 100)
print("📊 RÉSUMÉ GLOBAL")
print("=" * 100)

# Compter observations par indicateur
for indicator_code, info in INDICATEURS.items():
    count = db.curated_observations.count_documents({
        'source': 'WorldBank',
        'dataset': indicator_code
    })
    
    # Compter pays couverts
    pays_avec_data = set()
    for doc in db.curated_observations.find({
        'source': 'WorldBank',
        'dataset': indicator_code
    }, {'key': 1}):
        country = doc['key'].split('.')[0]
        pays_avec_data.add(country)
    
    print(f"\n{info['nom']:25s}: {count:>4d} observations | {len(pays_avec_data):>2d} pays")
    
print("\n" + "=" * 100)
print("✅ TEST TERMINÉ")
print("=" * 100)
