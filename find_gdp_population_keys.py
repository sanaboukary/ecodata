# -*- coding: utf-8 -*-
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

client, db = get_mongo_db()

print("="*80)
print("CLÉS DISPONIBLES POUR PIB ET POPULATION")
print("="*80)

# PIB - échantillon des clés
print("\nPIB (NY.GDP.MKTP.KD.ZG) - 10 premières clés:")
gdp_keys = db.curated_observations.distinct('key', {'source': 'WorldBank', 'dataset': 'NY.GDP.MKTP.KD.ZG'})
for key in list(gdp_keys)[:10]:
    if key:
        print(f"  - {key}")

# Population - échantillon des clés
print("\nPopulation (SP.POP.TOTL) - 10 premières clés:")
pop_keys = db.curated_observations.distinct('key', {'source': 'WorldBank', 'dataset': 'SP.POP.TOTL'})
for key in list(pop_keys)[:10]:
    if key:
        print(f"  - {key}")

# Chercher des patterns avec codes pays
print("\nRecherche de codes pays CEDEAO (BEN, CIV, SEN):")
for dataset_name, dataset_code in [('PIB', 'NY.GDP.MKTP.KD.ZG'), ('Population', 'SP.POP.TOTL')]:
    print(f"\n{dataset_name} ({dataset_code}):")
    for country_code in ['BEN', 'CIV', 'SEN', 'GHA', 'MLI']:
        count = db.curated_observations.count_documents({
            'source': 'WorldBank',
            'dataset': dataset_code,
            'key': {'$regex': country_code, '$options': 'i'}
        })
        if count > 0:
            sample = db.curated_observations.find_one({
                'source': 'WorldBank',
                'dataset': dataset_code,
                'key': {'$regex': country_code, '$options': 'i'}
            })
            print(f"  {country_code}: {count} obs, clé exemple: {sample.get('key')}")

client.close()
