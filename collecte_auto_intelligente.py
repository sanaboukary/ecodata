#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte automatique intelligente TOUTES SOURCES
- Gestion timeout et fallback
- Logging détaillé
- Vérification qualité
- Rapport de santé
"""

import sys
import io
from datetime import datetime
from pymongo import MongoClient

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*120)
print(" " * 40 + "COLLECTE AUTOMATIQUE INTELLIGENTE")
print(" " * 45 + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
print("="*120)


def verifier_sante_mongodb():
    """Vérification santé MongoDB avant collecte"""
    print("\n🔍 VÉRIFICATION MONGODB...")
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.server_info()  # Force connexion
        
        db = client['centralisation_db']
        
        # Statistiques actuelles
        sources = {}
        for source in ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'AI_ANALYSIS']:
            count = db.curated_observations.count_documents({'source': source})
            sources[source] = count
        
        total = sum(sources.values())
        
        print(f"   ✅ MongoDB opérationnel - {total:,} observations totales")
        for source, count in sources.items():
            print(f"      {source:<15} {count:>8,} docs")
        
        client.close()
        return True, sources
        
    except Exception as e:
        print(f"   ❌ Erreur MongoDB: {e}")
        return False, {}


def collecter_imf_intelligent():
    """Collecte IMF avec timeout intelligent"""
    from scripts.pipeline import run_ingestion
    
    print("\n" + "="*120)
    print("1. COLLECTE IMF (Fonds Monétaire International)")
    print("="*120)
    
    PAYS = ['BEN', 'BFA', 'CI', 'GH', 'ML', 'NE', 'SN', 'TG']
    SERIES = {
        'PCPI_IX': 'CPI',
        'NGDP_R': 'PIB réel',
        'NGDP_RPCH': 'Croissance PIB',
        'PCPIPCH': 'Inflation',
        'LUR': 'Chômage',
    }
    
    total = 0
    success = 0
    errors = 0
    
    print(f"\n   Séries: {len(SERIES)} × Pays: {len(PAYS)} = {len(SERIES)*len(PAYS)} requêtes")
    print(f"   ⏱️  Timeout par requête: 30s (fallback mock si dépassé)")
    
    for series_code, series_name in SERIES.items():
        for pays in PAYS:
            key = f"A.{pays}.{series_code}"
            
            try:
                print(f"   📊 {pays}-{series_code}...", end=' ', flush=True)
                count = run_ingestion('imf', dataset='IFS', key=key)
                
                if count > 0:
                    total += count
                    success += 1
                    print(f"✅ {count} obs")
                else:
                    print(f"⚠️  Mock")
                    errors += 1
                    
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
                errors += 1
    
    print(f"\n   RÉSUMÉ IMF: {total:,} obs | Succès: {success} | Erreurs: {errors}")
    return total, success, errors


def collecter_afdb_intelligent():
    """Collecte AfDB (mock data)"""
    from scripts.pipeline import run_ingestion
    
    print("\n" + "="*120)
    print("2. COLLECTE AfDB (Banque Africaine de Développement)")
    print("="*120)
    print("   ℹ️  AfDB: Données simulées (pas d'API publique)\n")
    
    PAYS = ['BEN', 'BFA', 'CI', 'GH', 'ML', 'NE', 'SN', 'TG']
    INDICATORS = {
        'DEBT_GDP': 'Dette/PIB',
        'GDP_GROWTH': 'Croissance',
        'FDI_GDP': 'IDE',
        'TRADE_GDP': 'Commerce',
        'GINI': 'Gini',
        'POVERTY': 'Pauvreté',
    }
    
    total = 0
    success = 0
    
    for indicator, desc in INDICATORS.items():
        for pays in PAYS:
            key = f"{pays}.{indicator}"
            
            try:
                print(f"   📊 {pays}-{indicator}...", end=' ', flush=True)
                count = run_ingestion('afdb', dataset='SOCIOECONOMIC', key=key)
                
                if count > 0:
                    total += count
                    success += 1
                    print(f"✅ {count} obs (mock)")
                else:
                    print(f"⚠️  Aucune")
                    
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
    
    print(f"\n   RÉSUMÉ AfDB: {total:,} obs | Succès: {success}")
    return total, success, 0


def collecter_un_sdg_intelligent():
    """Collecte UN SDG avec pagination"""
    from scripts.pipeline import run_ingestion
    
    print("\n" + "="*120)
    print("3. COLLECTE UN SDG (Objectifs Développement Durable)")
    print("="*120)
    
    UN_CODES = {
        'BEN': '204', 'BFA': '854', 'CI': '384', 'GH': '288',
        'ML': '466', 'NE': '562', 'SN': '686', 'TG': '768'
    }
    
    SERIES = {
        'SL_TLF_UEM': 'Chômage',
        'SI_POV_DAY1': 'Pauvreté',
        'SH_STA_MORT': 'Mortalité',
        'SG_GEN_PARL': 'Femmes parlement',
        'SN_ITK_DEFC': 'Malnutrition',
    }
    
    total = 0
    success = 0
    errors = 0
    
    area_codes = ','.join(UN_CODES.values())
    print(f"\n   Séries: {len(SERIES)} | Pays: {area_codes}")
    
    for series_code, series_name in SERIES.items():
        try:
            print(f"   📊 {series_code} ({series_name})...", end=' ', flush=True)
            count = run_ingestion('un', series=series_code, area=area_codes)
            
            if count > 0:
                total += count
                success += 1
                print(f"✅ {count} obs")
            else:
                print(f"⚠️  Aucune")
                errors += 1
                
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
            errors += 1
    
    print(f"\n   RÉSUMÉ UN SDG: {total:,} obs | Succès: {success}")
    return total, success, errors


def generer_rapport_final(sources_avant, sources_apres, stats):
    """Génération rapport final avec comparaison avant/après"""
    print("\n" + "="*120)
    print("📊 RAPPORT FINAL DE COLLECTE")
    print("="*120)
    
    print("\n┌─────────────────────┬──────────────┬──────────────┬──────────────┐")
    print("│ Source              │ Avant        │ Après        │ Nouvelles    │")
    print("├─────────────────────┼──────────────┼──────────────┼──────────────┤")
    
    for source in ['BRVM', 'WorldBank', 'IMF', 'AfDB', 'UN_SDG', 'AI_ANALYSIS']:
        avant = sources_avant.get(source, 0)
        apres = sources_apres.get(source, 0)
        diff = apres - avant
        
        symbole = "📈" if diff > 0 else "  "
        print(f"│ {source:<19} │ {avant:>10,}   │ {apres:>10,}   │ {symbole} {diff:>8,}   │")
    
    print("├─────────────────────┼──────────────┼──────────────┼──────────────┤")
    total_avant = sum(sources_avant.values())
    total_apres = sum(sources_apres.values())
    total_diff = total_apres - total_avant
    print(f"│ {'TOTAL':<19} │ {total_avant:>10,}   │ {total_apres:>10,}   │ 📊 {total_diff:>8,}   │")
    print("└─────────────────────┴──────────────┴──────────────┴──────────────┘")
    
    print(f"\n📈 Statistiques de collecte:")
    print(f"   IMF:    {stats['imf'][0]:>8,} obs | Succès: {stats['imf'][1]:>3} | Erreurs: {stats['imf'][2]:>3}")
    print(f"   AfDB:   {stats['afdb'][0]:>8,} obs | Succès: {stats['afdb'][1]:>3}")
    print(f"   UN SDG: {stats['un'][0]:>8,} obs | Succès: {stats['un'][1]:>3} | Erreurs: {stats['un'][2]:>3}")
    
    print(f"\n🎯 Couverture totale: {total_apres:,} observations")
    print(f"✅ Collecte terminée avec succès")


if __name__ == '__main__':
    # 1. Vérification santé
    sante_ok, sources_avant = verifier_sante_mongodb()
    
    if not sante_ok:
        print("\n❌ ARRÊT: MongoDB non disponible")
        sys.exit(1)
    
    # 2. Collecte intelligente
    stats = {}
    
    try:
        stats['imf'] = collecter_imf_intelligent()
        stats['afdb'] = collecter_afdb_intelligent()
        stats['un'] = collecter_un_sdg_intelligent()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Collecte interrompue par l'utilisateur")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        sys.exit(1)
    
    # 3. Vérification finale
    _, sources_apres = verifier_sante_mongodb()
    
    # 4. Rapport
    generer_rapport_final(sources_avant, sources_apres, stats)
    
    print("\n" + "="*120)
