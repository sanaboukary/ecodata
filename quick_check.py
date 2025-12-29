import django,os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','plateforme_centralisation.settings')
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

c,db=get_mongo_db()
n22=db.curated_observations.count_documents({'source':'BRVM','ts':'2025-12-22'})
n23=db.curated_observations.count_documents({'source':'BRVM','ts':'2025-12-23'})

print(f'\n📊 DONNÉES BRVM EN BASE:')
print(f'   22/12/2025: {n22} observations')
print(f'   23/12/2025: {n23} observations')

if n23 > 0:
    print(f'\n✅ Collecte du 23/12 réussie!')
    actions23 = list(db.curated_observations.find({'source':'BRVM','ts':'2025-12-23'}).limit(5))
    print(f'\nÉchantillon:')
    for a in actions23:
        print(f"  {a['key']}: {a['value']:,.0f} FCFA ({a['attrs'].get('variation',0):+.2f}%)")
else:
    print(f'\n⚠️  Aucune donnée du 23/12')

c.close()
print()
