"""
Diagnostic des données pour un pays spécifique
"""
from pymongo import MongoClient
import pandas as pd

# Connexion
client = MongoClient('mongodb://SANA:Boukary89%40@localhost:27018/')
db = client['centralisation_db']
obs = db['curated_observations']

# Pays à tester
test_countries = ['USA', 'FRA', 'BEN', 'CIV', 'CHN']
test_year = 2020

print("\n" + "="*100)
print(f"DIAGNOSTIC DES DONNÉES POUR L'ANNÉE {test_year}")
print("="*100)

for country in test_countries:
    print(f"\n{'='*100}")
    print(f"PAYS: {country}")
    print(f"{'='*100}")
    
    # PIB
    pib = obs.find_one({
        'source': {'$in': ['worldbank', 'WorldBank']},
        'attrs.country': country,
        'attrs.year': test_year,
        'attrs.indicator': 'NY.GDP.MKTP.KD.ZG'
    })
    print(f"PIB: {pib['value'] if pib else 'N/A'}")
    
    # Pauvreté
    pov = obs.find_one({
        'source': {'$in': ['worldbank', 'WorldBank']},
        'attrs.country': country,
        'attrs.year': test_year,
        'attrs.indicator': 'SI.POV.DDAY'
    })
    print(f"Pauvreté: {pov['value'] if pov else 'N/A'}")
    
    # RNB
    rnb = obs.find_one({
        'source': {'$in': ['worldbank', 'WorldBank']},
        'attrs.country': country,
        'attrs.year': test_year,
        'attrs.indicator': 'NY.GNP.PCAP.CD'
    })
    print(f"RNB: {rnb['value'] if rnb else 'N/A'}")
    
    # Santé
    sante = obs.find_one({
        'source': {'$in': ['worldbank', 'WorldBank']},
        'attrs.country': country,
        'attrs.year': test_year,
        'attrs.indicator': 'SH.XPD.GHED.GD.ZS'
    })
    print(f"Santé: {sante['value'] if sante else 'N/A'}")
    
    # Éducation
    edu = obs.find_one({
        'source': {'$in': ['worldbank', 'WorldBank']},
        'attrs.country': country,
        'attrs.year': test_year,
        'attrs.indicator': 'SE.XPD.TOTL.GD.ZS'
    })
    print(f"Éducation: {edu['value'] if edu else 'N/A'}")

print("\n" + "="*100)
print("VÉRIFICATION DES ANNÉES DISPONIBLES PAR INDICATEUR")
print("="*100)

indicators = {
    "NY.GDP.MKTP.KD.ZG": "PIB",
    "SI.POV.DDAY": "Pauvreté",
    "NY.GNP.PCAP.CD": "RNB",
    "SH.XPD.GHED.GD.ZS": "Santé",
    "SE.XPD.TOTL.GD.ZS": "Éducation"
}

for code, name in indicators.items():
    years = obs.distinct('attrs.year', {
        'source': {'$in': ['worldbank', 'WorldBank']},
        'attrs.indicator': code
    })
    years = sorted([y for y in years if y])
    if years:
        print(f"\n{name} ({code}):")
        print(f"  Années: {min(years)} - {max(years)}")
        print(f"  Total: {len(years)} années")
        print(f"  Exemple d'années récentes: {years[-5:] if len(years) >= 5 else years}")

print("\n" + "="*100)
