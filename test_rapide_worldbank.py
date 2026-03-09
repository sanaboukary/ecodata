#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test des indicateurs pour le dashboard - format simplifié
"""
from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

# Test rapide pour 3 pays
TEST_PAYS = ['BEN', 'NER', 'MRT']

# Nouveaux indicateurs
INDICATEURS = {
    'NY.GDP.PCAP.CD': 'PIB par Habitant',
    'SP.POP.TOTL': 'Population', 
    'FP.CPI.TOTL.ZG': 'Inflation',
    'SH.DYN.MORT': 'Mortalité Infantile',
    'SE.PRM.ENRR': 'Scolarisation',
    'SL.UEM.TOTL.ZS': 'Chômage',
    'NE.TRD.GNFS.ZS': 'Commerce/PIB',
    'IT.NET.USER.ZS': 'Internet'
}

print("TEST RAPIDE INDICATEURS WORLDBANK")
print("=" * 80)

for country_code in TEST_PAYS:
    print(f"\n🌍 {country_code}")
    print("-" * 80)
    
    for indicator_code, nom in INDICATEURS.items():
        # Requête exacte comme dans le dashboard
        data = db.curated_observations.find_one({
            'source': 'WorldBank',
            'dataset': indicator_code,
            'key': {'$regex': f'^{country_code}\\.'}
        }, sort=[('ts', -1)])
        
        if data and data.get('value') is not None:
            value = data['value']
            ts = data.get('ts', '?')
            
            # Formatage simple
            if nom == 'Population':
                formatted = f"{value/1_000_000:.2f} M"
            elif nom == 'PIB par Habitant':
                formatted = f"${value:,.0f}"
            else:
                formatted = f"{value:.2f}"
            
            status = "✅"
        else:
            formatted = "Pas de données"
            ts = "-"
            status = "❌"
        
        print(f"{status} {nom:20s}: {formatted:>15s}  ({ts})")

print("\n" + "=" * 80)
