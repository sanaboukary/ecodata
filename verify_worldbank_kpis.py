#!/usr/bin/env python
"""Vérification finale des KPIs WorldBank"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# Codes pays CEDEAO
country_to_code = {
    'Bénin': 'BEN', 'Burkina Faso': 'BFA', 'Côte d\'Ivoire': 'CIV',
    'Ghana': 'GHA', 'Guinée': 'GIN', 'Gambie': 'GMB', 'Guinée-Bissau': 'GNB',
    'Liberia': 'LBR', 'Mali': 'MLI', 'Niger': 'NER', 'Nigeria': 'NGA',
    'Sénégal': 'SEN', 'Sierra Leone': 'SLE', 'Togo': 'TGO', 'Cap-Vert': 'CPV'
}

code_to_country = {v: k for k, v in country_to_code.items()}
cedeao_codes = list(country_to_code.values())

# KPIs
kpis = {
    'NY.GDP.MKTP.KD.ZG': 'Croissance PIB',
    'SP.POP.TOTL': 'Population Totale',
    'SI.POV.DDAY': 'Taux de Pauvreté',
    'SH.XPD.GHED.GD.ZS': 'Dépenses Santé/PIB',
    'SE.XPD.TOTL.GD.ZS': 'Dépenses Éducation/PIB',
    'SE.ADT.LITR.ZS': 'Alphabétisation',
    'EG.ELC.ACCS.ZS': 'Accès Électricité',
    'IT.NET.USER.ZS': 'Utilisateurs Internet',
}

print("\n" + "="*80)
print("VERIFICATION FINALE DES KPIs WORLDBANK (avec fallback)")
print("="*80)

for dataset, name in kpis.items():
    country_values = []
    
    for country_code in cedeao_codes:
        # Essayer d'abord avec attrs.country (nouveau format)
        latest_doc = db.curated_observations.find_one({
            'source': 'WorldBank',
            'dataset': dataset,
            'attrs.country': country_code
        }, sort=[('ts', -1)])
        
        # Si pas de résultat, essayer avec key (ancien format)
        if not latest_doc:
            country_name = code_to_country.get(country_code, '')
            if country_name:
                latest_doc = db.curated_observations.find_one({
                    'source': 'WorldBank',
                    'dataset': dataset,
                    'key': country_name
                }, sort=[('ts', -1)])
        
        if latest_doc and latest_doc.get('value') is not None:
            country_values.append(latest_doc['value'])
    
    if country_values:
        avg_val = sum(country_values) / len(country_values)
        
        if dataset == 'SP.POP.TOTL':
            print(f"[OK] {name:30} {avg_val/1_000_000:>8.1f} M ({len(country_values)}/15 pays)")
        else:
            print(f"[OK] {name:30} {avg_val:>8.2f} % ({len(country_values)}/15 pays)")
    else:
        print(f"[!!] {name:30} AUCUNE DONNEE")

print("="*80)
