#!/usr/bin/env python3
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("\n" + "="*80)
print("TOP 5 HAUSSES PROBABLES - BRVM WEEKLY")
print("="*80 + "\n")

top5 = list(db.top5_weekly_brvm.find().sort("rank", 1))

if top5:
    for t in top5:
        print(f"#{t['rank']} {t['symbol']:8s} | Score: {t.get('top5_score',0):5.1f} | Conf: {t.get('confiance',0):3.0f}% | Gain: {t.get('gain_attendu',0):5.1f}%")
    print(f"\n{len(top5)} recommandations affichees\n")
else:
    print("Aucune recommandation TOP 5\n")
