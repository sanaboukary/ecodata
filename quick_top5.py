import django,os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','plateforme_centralisation.settings')
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

c,db=get_mongo_db()
actions=list(db.curated_observations.find({'source':'BRVM','ts':'2025-12-22','value':{'$gt':0}}))

top = sorted(actions, key=lambda x: x['attrs'].get('variation',0), reverse=True)[:5]

print('\nTOP 5 VARIATIONS - 22/12/2025\n')
for a in top:
    print(f"{a['key']:<12} {a['value']:>10,.0f} FCFA  {a['attrs'].get('variation',0):>+7.2f}%")

c.close()
