"""
🔧 Correction des Dashboards - Utiliser VRAIES DONNÉES
========================================================
Fix dashboards WorldBank, IMF, UN_SDG, AfDB pour afficher vraies données MongoDB
au lieu de valeurs simulées/estimées
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def verifier_structure_donnees():
    """Vérifier structure réelle des données dans MongoDB"""
    _, db = get_mongo_db()
    
    print("="*80)
    print("🔍 ANALYSE STRUCTURE DONNÉES MONGODB")
    print("="*80)
    
    sources = ['WorldBank', 'IMF', 'UN_SDG', 'AfDB']
    
    for source in sources:
        print(f"\n📊 {source}")
        print("-"*80)
        
        # Prendre 3 exemples
        samples = list(db.curated_observations.find({'source': source}).limit(3))
        
        if samples:
            for i, sample in enumerate(samples, 1):
                print(f"\nExemple {i}:")
                print(f"  key: {sample.get('key')}")
                print(f"  dataset: {sample.get('dataset')}")
                print(f"  ts: {sample.get('ts')}")
                print(f"  value: {sample.get('value')}")
                
                attrs = sample.get('attrs', {})
                if attrs:
                    print(f"  attrs:")
                    for k, v in list(attrs.items())[:5]:
                        print(f"    {k}: {v}")
        else:
            print("  ⚠️ Aucune donnée")
    
    print("\n" + "="*80)


def tester_recuperation_indicateurs():
    """Tester récupération des principaux indicateurs"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("🧪 TEST RÉCUPÉRATION INDICATEURS WORLDBANK")
    print("="*80)
    
    # Indicateurs clés
    indicateurs = {
        'NY.GDP.MKTP.KD.ZG': 'Croissance PIB',
        'SP.POP.TOTL': 'Population totale',
        'FP.CPI.TOTL.ZG': 'Inflation (CPI)',
        'IT.NET.USER.ZS': 'Utilisateurs Internet (%)',
        'EG.ELC.ACCS.ZS': 'Accès électricité (%)',
        'SE.ADT.LITR.ZS': 'Alphabétisation (%)'
    }
    
    pays_test = ['SN', 'CI', 'BEN', 'BFA', 'GHA']
    
    for code_indicateur, nom in indicateurs.items():
        print(f"\n📌 {nom} ({code_indicateur})")
        print("-"*80)
        
        count = db.curated_observations.count_documents({
            'source': 'WorldBank',
            'dataset': code_indicateur
        })
        
        print(f"Total observations: {count}")
        
        if count > 0:
            # Dernières valeurs par pays
            print("\nDernières valeurs par pays:")
            for pays in pays_test:
                doc = db.curated_observations.find_one({
                    'source': 'WorldBank',
                    'dataset': code_indicateur,
                    'key': pays
                }, sort=[('ts', -1)])
                
                if doc:
                    print(f"  {pays}: {doc['value']} ({doc['ts'][:10]})")
                else:
                    print(f"  {pays}: Pas de données")
    
    print("\n" + "="*80)
    print("✅ Tests terminés")
    print("="*80)


def afficher_indicateurs_disponibles():
    """Afficher tous les indicateurs avec données"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("📋 INDICATEURS DISPONIBLES PAR SOURCE")
    print("="*80)
    
    sources = ['WorldBank', 'IMF', 'UN_SDG', 'AfDB']
    
    for source in sources:
        print(f"\n{source}:")
        print("-"*80)
        
        # Grouper par dataset
        pipeline = [
            {'$match': {'source': source}},
            {'$group': {
                '_id': '$dataset',
                'count': {'$sum': 1},
                'pays': {'$addToSet': '$key'},
                'derniere_date': {'$max': '$ts'},
                'exemple_valeur': {'$first': '$value'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        datasets = list(db.curated_observations.aggregate(pipeline))
        
        for ds in datasets:
            print(f"  {ds['_id']}")
            print(f"    Observations: {ds['count']}")
            print(f"    Pays: {len(ds['pays'])} ({', '.join(list(ds['pays'])[:5])}...)")
            print(f"    Dernière date: {ds['derniere_date'][:10]}")
            print(f"    Exemple valeur: {ds['exemple_valeur']}")
            print()


def generer_mapping_correct():
    """Générer le mapping correct pour les dashboards"""
    _, db = get_mongo_db()
    
    print("\n" + "="*80)
    print("📝 MAPPING CORRECT POUR DASHBOARDS")
    print("="*80)
    
    # WorldBank
    print("\n🌍 WORLDBANK:")
    print("="*80)
    
    indicateurs_wb = {
        'NY.GDP.MKTP.KD.ZG': 'Croissance PIB (%)',
        'SP.POP.TOTL': 'Population Totale',
        'FP.CPI.TOTL.ZG': 'Inflation CPI (%)',
        'IT.NET.USER.ZS': 'Utilisateurs Internet (%)',
        'EG.ELC.ACCS.ZS': 'Accès Électricité (%)',
        'SE.ADT.LITR.ZS': 'Taux Alphabétisation (%)',
        'SE.XPD.TOTL.GD.ZS': 'Dépenses Éducation/PIB (%)',
        'SH.XPD.CHEX.GD.ZS': 'Dépenses Santé/PIB (%)'
    }
    
    print("\nCode Python pour dashboard_worldbank :")
    print("-"*80)
    print("""
# Mapping codes indicateurs -> KPIs
kpi_mapping = {
    'NY.GDP.MKTP.KD.ZG': 'gdp_growth',
    'SP.POP.TOTL': 'population',
    'FP.CPI.TOTL.ZG': 'inflation',
    'IT.NET.USER.ZS': 'internet_users',
    'EG.ELC.ACCS.ZS': 'electricity_access',
    'SE.ADT.LITR.ZS': 'literacy_rate',
    'SE.XPD.TOTL.GD.ZS': 'education_expenditure',
    'SH.XPD.CHEX.GD.ZS': 'health_expenditure'
}

# Calculer KPIs moyens CEDEAO
for code_indicateur, kpi_key in kpi_mapping.items():
    # Récupérer dernières valeurs pour pays CEDEAO
    pays_cedeao = ['SN', 'CI', 'BEN', 'BFA', 'GHA', 'NER', 'TGO', 'MLI']
    
    valeurs = []
    for pays in pays_cedeao:
        doc = db.curated_observations.find_one({
            'source': 'WorldBank',
            'dataset': code_indicateur,
            'key': pays
        }, sort=[('ts', -1)])
        
        if doc and doc.get('value'):
            valeurs.append(doc['value'])
    
    if valeurs:
        # Moyenne
        kpis[kpi_key]['value'] = round(sum(valeurs) / len(valeurs), 2)
        
        # Cas spécial Population (convertir en millions)
        if kpi_key == 'population':
            kpis[kpi_key]['value'] = round(kpis[kpi_key]['value'] / 1_000_000, 1)
""")
    
    print("\n" + "="*80)
    print("✅ Utilisez ce code dans dashboard/views.py")
    print("="*80)


if __name__ == '__main__':
    print("🔧 DIAGNOSTIC DASHBOARDS - VRAIES DONNÉES")
    print("="*80)
    
    # 1. Vérifier structure
    verifier_structure_donnees()
    
    # 2. Tester récupération
    tester_recuperation_indicateurs()
    
    # 3. Afficher indicateurs disponibles
    afficher_indicateurs_disponibles()
    
    # 4. Générer mapping correct
    generer_mapping_correct()
    
    print("\n" + "="*80)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("="*80)
    print("\nProchaines étapes:")
    print("1. Vérifier que le champ 'key' contient bien les codes pays (SN, CI, etc.)")
    print("2. Modifier dashboard/views.py pour utiliser 'key' au lieu de 'attrs.country'")
    print("3. Supprimer les valeurs simulées/estimées")
    print("4. Tester les dashboards dans le navigateur")
    print("="*80)
