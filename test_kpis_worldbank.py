"""Test rapide des KPIs WorldBank"""
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
print("🧪 TEST RÉCUPÉRATION KPIs WORLDBANK")
print("="*80)

# Codes pays CEDEAO
pays_cedeao = ['BEN', 'BFA', 'CIV', 'GHA', 'NER', 'TGO', 'MLI', 'SEN', 'GNB']

# Indicateurs
indicateurs = {
    'SP.POP.TOTL': 'Population',
    'FP.CPI.TOTL.ZG': 'Inflation CPI',
    'IT.NET.USER.ZS': 'Utilisateurs Internet',
    'NY.GDP.PCAP.CD': 'PIB par habitant'
}

for code_indic, nom in indicateurs.items():
    print(f"\n📊 {nom} ({code_indic})")
    print("-"*80)
    
    valeurs = []
    
    for pays in pays_cedeao:
        doc = db.curated_observations.find_one({
            'source': 'WorldBank',
            'dataset': code_indic,
            'key': {'$regex': f'^{pays}\\.'}
        }, sort=[('ts', -1)])
        
        if doc:
            val = doc['value']
            if code_indic == 'SP.POP.TOTL':
                val = round(val / 1_000_000, 2)  # En millions
            else:
                val = round(val, 2)
            
            print(f"  {pays}: {val:>10} ({doc['ts'][:10]})")
            valeurs.append(doc['value'])
        else:
            print(f"  {pays}: Pas de données")
    
    if valeurs:
        if code_indic == 'SP.POP.TOTL':
            moyenne = round(sum(valeurs) / len(valeurs) / 1_000_000, 1)
            print(f"\n  ✅ Moyenne CEDEAO: {moyenne} M habitants")
        else:
            moyenne = round(sum(valeurs) / len(valeurs), 2)
            print(f"\n  ✅ Moyenne CEDEAO: {moyenne}")
    else:
        print(f"\n  ❌ Aucune donnée trouvée")

print("\n" + "="*80)
print("✅ Test terminé - Vérifiez que les valeurs s'affichent correctement")
print("="*80)
