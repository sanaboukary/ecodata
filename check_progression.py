#!/usr/bin/env python3
from pymongo import MongoClient

db = MongoClient()['centralisation_db']

before = 40
after = db.prices_weekly.count_documents({'indicators_computed': True})
total = db.prices_weekly.count_documents({})

print('='*60)
print('PROGRESSION CALCUL INDICATEURS')
print('='*60)
print(f'AVANT : {before}/{total} ({100*before/total:.1f}%)')
print(f'APRES : {after}/{total} ({100*after/total:.1f}%)')
print(f'GAIN  : +{after-before} documents')
print('='*60)

if after >= total*0.7:
    print('[OK] Plus de 70% mis a jour - EXCELLENT')
elif after > before:
    print('[!!] Calcul interrompu - relancer pour finir')
else:
    print('[!] Aucun progres')

print('='*60)
