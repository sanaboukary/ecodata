"""Collecter des données FMI enrichies pour tous les pays CEDEAO"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from scripts.pipeline import run_ingestion

print("=" * 80)
print("COLLECTE ENRICHIE DES DONNEES FMI")
print("=" * 80)

# Pays CEDEAO avec codes ISO3
cedeao_countries = {
    'BEN': 'Bénin',
    'BFA': 'Burkina Faso',
    'CIV': 'Côte d\'Ivoire',
    'GHA': 'Ghana',
    'GIN': 'Guinée',
    'MLI': 'Mali',
    'NER': 'Niger',
    'NGA': 'Nigeria',
    'SEN': 'Sénégal',
    'TGO': 'Togo',
}

# Indicateurs prioritaires FMI pour investisseurs
# Format: (code_indicateur, nom, description)
key_indicators = [
    ('PCPI_IX', 'Indice Prix Consommation', 'CPI - Inflation'),
    ('NGDP_R', 'PIB Réel', 'GDP Real'),
    ('NGDP', 'PIB Nominal', 'GDP Nominal'),
    ('BCA', 'Balance Compte Courant', 'Current Account Balance'),
    ('GGR', 'Revenus Publics', 'General Government Revenue'),
    ('GGX', 'Dépenses Publiques', 'General Government Expenditure'),
]

print(f"\n🌍 Pays à collecter : {len(cedeao_countries)}")
print(f"📊 Indicateurs par pays : {len(key_indicators)}")
print(f"📈 Total combinaisons : {len(cedeao_countries) * len(key_indicators)}")

print("\n" + "-" * 80)
print("DEBUT DE LA COLLECTE")
print("-" * 80)

total_collected = 0
successful = 0
failed = 0

for country_code, country_name in cedeao_countries.items():
    print(f"\n🇦 {country_name} ({country_code})")
    
    for indicator_code, indicator_name, description in key_indicators:
        # Format clé FMI: M.COUNTRY.INDICATOR (M = Monthly)
        key = f"M.{country_code}.{indicator_code}"
        
        try:
            print(f"  📊 {indicator_name}...", end=" ")
            count = run_ingestion("imf", dataset="IFS", key=key)
            
            if count > 0:
                print(f"✅ {count} obs")
                total_collected += count
                successful += 1
            else:
                print(f"⚠️  Aucune donnée")
                failed += 1
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)[:50]}")
            failed += 1

print("\n" + "=" * 80)
print("RESUME DE LA COLLECTE")
print("=" * 80)
print(f"\n✅ Succès : {successful}")
print(f"❌ Échecs : {failed}")
print(f"📊 Total observations collectées : {total_collected}")
print(f"\n💡 Les données sont maintenant disponibles dans MongoDB")
print(f"   Collection : curated_observations (source: 'IMF')")
