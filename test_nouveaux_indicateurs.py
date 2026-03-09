"""Test rapide nouveaux indicateurs WorldBank"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

print("="*80)
print("🧪 TEST NOUVEAUX INDICATEURS WORLDBANK")
print("="*80)

# Pays test
pays = ['BEN', 'NER', 'MRT', 'CIV', 'SEN']

# Nouveaux indicateurs
indicateurs = {
    'NY.GDP.PCAP.CD': 'PIB par habitant',
    'SP.POP.TOTL': 'Population',
    'FP.CPI.TOTL.ZG': 'Inflation CPI',
    'SH.DYN.MORT': 'Mortalité infantile',
    'SE.PRM.ENRR': 'Scolarisation primaire',
    'SL.UEM.TOTL.ZS': 'Chômage',
    'NE.TRD.GNFS.ZS': 'Commerce/PIB',
    'IT.NET.USER.ZS': 'Internet'
}

for pays_code in pays:
    print(f"\n{'='*80}")
    print(f"🌍 {pays_code}")
    print(f"{'='*80}")
    
    for code_indic, nom in indicateurs.items():
        doc = db.curated_observations.find_one({
            'source': 'WorldBank',
            'dataset': code_indic,
            'key': {'$regex': f'^{pays_code}\\.'}
        }, sort=[('ts', -1)])
        
        if doc:
            val = doc['value']
            
            # Formatage selon indicateur
            if code_indic == 'SP.POP.TOTL':
                formatted = f"{round(val / 1_000_000, 2)} M"
            elif code_indic in ['FP.CPI.TOTL.ZG', 'SE.PRM.ENRR', 'SL.UEM.TOTL.ZS', 'NE.TRD.GNFS.ZS', 'IT.NET.USER.ZS']:
                formatted = f"{round(val, 2)}%"
            elif code_indic == 'SH.DYN.MORT':
                formatted = f"{round(val, 1)}‰"
            elif code_indic == 'NY.GDP.PCAP.CD':
                formatted = f"${round(val, 0):,.0f}"
            else:
                formatted = str(val)
            
            print(f"  ✅ {nom:25s}: {formatted:>15s} ({doc['ts'][:10]})")
        else:
            print(f"  ❌ {nom:25s}: Pas de données")

print("\n" + "="*80)
print("✅ Les nouvelles données devraient s'afficher maintenant!")
print("📌 Rechargez la page: http://127.0.0.1:8000/worldbank/")
print("="*80)
