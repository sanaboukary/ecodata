#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte complète IMF, AfDB, UN_SDG - Test et configuration des APIs
"""

import sys
import io
from scripts.pipeline import run_ingestion

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*120)
print(" " * 40 + "COLLECTE IMF, AfDB, UN_SDG")
print("="*120)

# Configuration pays BRVM
PAYS_BRVM = ['BEN', 'BFA', 'CI', 'GH', 'ML', 'NE', 'SN', 'TG']

# Mapping codes pays pour UN (codes numériques)
UN_COUNTRY_CODES = {
    'BEN': '204',   # Bénin
    'BFA': '854',   # Burkina Faso
    'CI': '384',    # Côte d'Ivoire
    'GH': '288',    # Ghana
    'ML': '466',    # Mali
    'NE': '562',    # Niger
    'SN': '686',    # Sénégal
    'TG': '768'     # Togo
}

# ============================================================================
# 1. IMF - Fonds Monétaire International
# ============================================================================
print("\n" + "="*120)
print("1. COLLECTE IMF (Fonds Monétaire International)")
print("="*120)
print("\nAPI: https://dataservices.imf.org/REST/SDMX_JSON.svc")
print("Documentation: https://datahelp.imf.org/knowledgebase/articles/667681")

# Séries IMF les plus importantes pour analyse économique
IMF_SERIES = {
    'PCPI_IX': 'Indice des prix à la consommation',
    'NGDP_R': 'PIB réel',
    'NGDP_RPCH': 'Croissance du PIB réel (%)',
    'PCPIPCH': 'Inflation (%)',
    'LUR': 'Taux de chômage (%)',
}

print(f"\nSéries à collecter: {len(IMF_SERIES)}")
for code, desc in IMF_SERIES.items():
    print(f"   - {code:<15} {desc}")

print(f"\nPays: {', '.join(PAYS_BRVM)}")

total_imf = 0
success_imf = 0
errors_imf = []

for series_code, series_name in IMF_SERIES.items():
    for pays in PAYS_BRVM:
        # Format clé IMF: Fréquence.Pays.Indicateur (M=mensuel, Q=trimestriel, A=annuel)
        key = f"A.{pays}.{series_code}"  # A = Annuel
        
        print(f"\n   Collecte {pays} - {series_code} ({series_name})...")
        try:
            # Dataset IMF standard: IFS (International Financial Statistics)
            count = run_ingestion('imf', dataset='IFS', key=key)
            
            if count > 0:
                print(f"      ✓ {count} observations collectées")
                total_imf += count
                success_imf += 1
            else:
                print(f"      ⚠ Aucune donnée disponible")
                errors_imf.append(f"{pays}-{series_code}: Pas de données")
        except Exception as e:
            print(f"      ✗ Erreur: {e}")
            errors_imf.append(f"{pays}-{series_code}: {str(e)[:50]}")

print(f"\n   RÉSUMÉ IMF: {total_imf} observations, {success_imf} séries réussies")
if errors_imf:
    print(f"   Erreurs: {len(errors_imf)}")

# ============================================================================
# 2. AfDB - Banque Africaine de Développement
# ============================================================================
print("\n" + "="*120)
print("2. COLLECTE AfDB (Banque Africaine de Développement)")
print("="*120)
print("\nAPI: AfDB Statistical Data Portal (SDMX)")
print("Note: L'API AfDB nécessite souvent une clé d'accès")

# Indicateurs AfDB clés
AFDB_INDICATORS = {
    'DEBT_GDP': 'Dette publique (% PIB)',
    'GDP_GROWTH': 'Croissance PIB (%)',
    'FDI_GDP': 'Investissements directs étrangers (% PIB)',
    'TRADE_GDP': 'Commerce total (% PIB)',
    'GINI': 'Coefficient de Gini (inégalités)',
    'POVERTY': 'Taux de pauvreté (%)',
}

print(f"\nIndicateurs à collecter: {len(AFDB_INDICATORS)}")
for code, desc in AFDB_INDICATORS.items():
    print(f"   - {code:<20} {desc}")

total_afdb = 0
success_afdb = 0
errors_afdb = []

print("\n⚠ Note: AfDB peut nécessiter une configuration API spécifique")
print("   Utilisation de données mock si API non disponible...")

for indicator, desc in AFDB_INDICATORS.items():
    for pays in PAYS_BRVM:
        key = f"{pays}.{indicator}"
        
        print(f"\n   Collecte {pays} - {indicator} ({desc})...")
        try:
            # AfDB utilise souvent le dataset "SOCIOECONOMIC"
            count = run_ingestion('afdb', dataset='SOCIOECONOMIC', key=key)
            
            if count > 0:
                print(f"      ✓ {count} observations collectées")
                total_afdb += count
                success_afdb += 1
            else:
                print(f"      ⚠ Aucune donnée (utilisation mock data)")
        except Exception as e:
            print(f"      ✗ Erreur: {e}")
            errors_afdb.append(f"{pays}-{indicator}: {str(e)[:50]}")

print(f"\n   RÉSUMÉ AfDB: {total_afdb} observations, {success_afdb} indicateurs réussis")

# ============================================================================
# 3. UN SDG - Objectifs de Développement Durable
# ============================================================================
print("\n" + "="*120)
print("3. COLLECTE UN SDG (Objectifs de Développement Durable)")
print("="*120)
print("\nAPI: https://unstats.un.org/SDGAPI/v1/sdg")
print("Documentation: https://unstats.un.org/sdgs/indicators/database/")

# Séries UN SDG importantes pour l'analyse économique et sociale
UN_SDG_SERIES = {
    'SL_TLF_UEM': 'ODD 8.5.2 - Taux de chômage',
    'SI_POV_DAY1': 'ODD 1.1.1 - Pauvreté extrême (<1.90$/jour)',
    'SH_STA_MORT': 'ODD 3.2.1 - Mortalité infantile',
    'SE_PRM_CMPT': 'ODD 4.1.1 - Éducation primaire complète',
    'SG_GEN_PARL': 'ODD 5.5.1 - Femmes au parlement',
    'EN_ATM_CO2E': 'ODD 13.2.2 - Émissions CO2',
    'SP_DYN_LE00': 'ODD 3.8.1 - Espérance de vie',
    'SN_ITK_DEFC': 'ODD 2.1.1 - Malnutrition',
}

print(f"\nSéries à collecter: {len(UN_SDG_SERIES)}")
for code, desc in UN_SDG_SERIES.items():
    print(f"   - {code:<20} {desc}")

total_un = 0
success_un = 0
errors_un = []

for series_code, series_name in UN_SDG_SERIES.items():
    # Collecter pour tous les pays BRVM ensemble
    area_codes = ','.join([UN_COUNTRY_CODES.get(p, '') for p in PAYS_BRVM if p in UN_COUNTRY_CODES])
    
    print(f"\n   Collecte {series_code} ({series_name})...")
    print(f"      Pays: {area_codes}")
    
    try:
        count = run_ingestion('un', series=series_code, area=area_codes)
        
        if count > 0:
            print(f"      ✓ {count} observations collectées")
            total_un += count
            success_un += 1
        else:
            print(f"      ⚠ Aucune donnée disponible")
            errors_un.append(f"{series_code}: Pas de données")
    except Exception as e:
        print(f"      ✗ Erreur: {e}")
        errors_un.append(f"{series_code}: {str(e)[:50]}")

print(f"\n   RÉSUMÉ UN SDG: {total_un} observations, {success_un} séries réussies")

# ============================================================================
# RÉSUMÉ GLOBAL
# ============================================================================
print("\n" + "="*120)
print("RÉSUMÉ GLOBAL DE LA COLLECTE")
print("="*120)

total_collect = total_imf + total_afdb + total_un

print(f"\nObservations collectées:")
print(f"   IMF:    {total_imf:>8,} observations ({success_imf} séries)")
print(f"   AfDB:   {total_afdb:>8,} observations ({success_afdb} indicateurs)")
print(f"   UN SDG: {total_un:>8,} observations ({success_un} séries)")
print(f"   {'─'*50}")
print(f"   TOTAL:  {total_collect:>8,} nouvelles observations")

if errors_imf or errors_afdb or errors_un:
    print(f"\nErreurs rencontrées: {len(errors_imf) + len(errors_afdb) + len(errors_un)}")
    if errors_imf:
        print(f"\n   IMF ({len(errors_imf)} erreurs):")
        for err in errors_imf[:5]:
            print(f"      - {err}")
        if len(errors_imf) > 5:
            print(f"      ... et {len(errors_imf)-5} autres")
    
    if errors_afdb:
        print(f"\n   AfDB ({len(errors_afdb)} erreurs):")
        for err in errors_afdb[:5]:
            print(f"      - {err}")
        if len(errors_afdb) > 5:
            print(f"      ... et {len(errors_afdb)-5} autres")
    
    if errors_un:
        print(f"\n   UN SDG ({len(errors_un)} erreurs):")
        for err in errors_un[:5]:
            print(f"      - {err}")
        if len(errors_un) > 5:
            print(f"      ... et {len(errors_un)-5} autres")

print("\n" + "="*120)
print("VÉRIFICATION FINALE")
print("="*120)

# Vérifier MongoDB
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017')
    db = client['centralisation_db']
    
    sources = db.curated_observations.distinct('source')
    print("\nSources dans MongoDB:")
    for source in sorted(sources):
        count = db.curated_observations.count_documents({'source': source})
        print(f"   - {source:<20} {count:>8,} documents")
    
    total_db = db.curated_observations.count_documents({})
    print(f"\n   TOTAL BASE:          {total_db:>8,} observations")
    
    client.close()
except Exception as e:
    print(f"\nErreur vérification MongoDB: {e}")

print("\n" + "="*120)
print("✓ COLLECTE TERMINÉE")
print("="*120)
