#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérification détaillée des prix BRVM vs Réels
Compare les prix dans la base avec les prix réels du marché
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from collections import defaultdict

# Prix réels de référence BRVM (Décembre 2025)
# Source: https://www.brvm.org/fr/investir/cours-et-cotations
PRIX_REELS_BRVM = {
    # Actions les plus liquides (à mettre à jour quotidiennement)
    'SNTS': 15500,  # Sonatel (Senegal Telecom)
    'SGBC': 2150,   # Société Générale Côte d'Ivoire
    'BOAB': 5200,   # BOA Bénin
    'TTLS': 1650,   # Total Sénégal
    'ETIT': 21,     # Ecobank CI
    'BICC': 7800,   # BICICI
    'ORGT': 5800,   # Orange CI
    'CFAC': 5800,   # Compagnie Fruitière
    'SICG': 8100,   # SICOGI
    'SITC': 7400,   # SITAB CI
    'BOAM': 3100,   # BOA Mali
    'NTLC': 1250,   # NSIA Tech
    'BNBC': 6200,   # BOA Burkina
    'SLBC': 16000,  # SLBC
    'SCRC': 9200,   # Sucrivoire
    'SDCC': 3800,   # SODE CI
    'SOGC': 7800,   # SOGECI
    'CBIBF': 6200,  # Coris Bank BF
    'NSBC': 3500,   # NSIA Banque CI
    'SIBC': 4200,   # SIB CI
    'CIEC': 2000,   # CIE CI
    'SDSC': 21000,  # SODE CI
    'SEMC': 2200,   # SOGEM
    'UNLB': 2150,   # Uniwax
    'NEIC': 750,    # NEI-CEDA
    'CABC': 2100,   # Coris Bank CI
    'STAC': 480,    # SETAO CI
    'PALC': 7200,   # Palm CI
    'TTRC': 290,    # TRITURAF
    'UNXC': 2300,   # UNILEVER CI
    'SMBC': 10500,  # SMB CI
    'FTSC': 1150,   # Filtisac
    'SAFH': 350,    # SAFCA
    'SIVC': 7400,   # SIVOM
    'PRSC': 650,    # PRESTIGE CI
    'ONTBF': 4500,  # ONATEL BF
    'TTLC': 2500,   # Total CI
    'ECOC': 700,    # ECOBANK CI
    'ABJC': 680000, # Air Liquide CI
    'SICC': 280,    # SICABLE
    'BOAC': 5000,   # BOA CI
    'BOABF': 4500,  # BOA BF
    'SOAC': 105000, # SOLIBRA
    'SPHC': 6200,   # SPH CI
    'TPCI': 3200,   # Tractafric CI
    'BISC': 45000,  # BICI
    'BOAG': 5900,   # BOA GABON
}

def comparer_prix():
    """Compare les prix DB vs réels"""
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION PRIX BRVM - COMPARAISON DB vs RÉEL")
    print("="*80)
    
    # Récupérer les derniers prix pour chaque action
    pipeline = [
        {'$match': {'source': 'BRVM', 'dataset': 'STOCK_PRICE'}},
        {'$sort': {'ts': -1}},
        {'$group': {
            '_id': '$key',
            'dernier_prix': {'$first': '$value'},
            'derniere_date': {'$first': '$ts'},
            'data_quality': {'$first': '$attrs.data_quality'},
            'variation': {'$first': '$attrs.variation'}
        }}
    ]
    
    resultats = list(collection.aggregate(pipeline))
    
    # Grouper par qualité
    par_qualite = defaultdict(list)
    differences = []
    
    print(f"\n📊 Analyse de {len(resultats)} actions:\n")
    
    for res in resultats:
        symbol = res['_id']
        prix_db = res['dernier_prix']
        date = res['derniere_date']
        quality = res.get('data_quality', 'N/A')
        
        par_qualite[quality].append(symbol)
        
        # Comparer avec prix réel si disponible
        if symbol in PRIX_REELS_BRVM:
            prix_reel = PRIX_REELS_BRVM[symbol]
            diff_pct = ((prix_db - prix_reel) / prix_reel) * 100
            
            differences.append({
                'symbol': symbol,
                'prix_db': prix_db,
                'prix_reel': prix_reel,
                'diff_pct': diff_pct,
                'quality': quality,
                'date': date
            })
    
    # Afficher statistiques par qualité
    print("📋 Répartition par qualité:")
    for quality, symbols in sorted(par_qualite.items()):
        print(f"   {quality:20s}: {len(symbols):3d} actions")
    
    # Afficher les différences
    print("\n" + "="*80)
    print("⚠️  DIFFÉRENCES DÉTECTÉES (DB vs Prix Réels BRVM):")
    print("="*80)
    
    if not differences:
        print("✅ Aucune action de référence trouvée pour comparaison")
        return
    
    # Trier par différence absolue
    differences.sort(key=lambda x: abs(x['diff_pct']), reverse=True)
    
    erreurs_majeures = []
    erreurs_mineures = []
    corrects = []
    
    for diff in differences:
        if abs(diff['diff_pct']) > 10:  # Erreur > 10%
            erreurs_majeures.append(diff)
        elif abs(diff['diff_pct']) > 2:  # Erreur > 2%
            erreurs_mineures.append(diff)
        else:
            corrects.append(diff)
    
    # Afficher erreurs majeures
    if erreurs_majeures:
        print(f"\n🔴 ERREURS MAJEURES (>10% différence): {len(erreurs_majeures)}")
        print("-" * 80)
        for d in erreurs_majeures[:20]:  # Limiter à 20
            print(f"   {d['symbol']:6s} | DB: {d['prix_db']:8.0f} | Réel: {d['prix_reel']:8.0f} | "
                  f"Diff: {d['diff_pct']:+7.1f}% | {d['quality']:15s} | {d['date']}")
    
    # Afficher erreurs mineures
    if erreurs_mineures:
        print(f"\n🟡 ERREURS MINEURES (2-10% différence): {len(erreurs_mineures)}")
        print("-" * 80)
        for d in erreurs_mineures[:10]:  # Limiter à 10
            print(f"   {d['symbol']:6s} | DB: {d['prix_db']:8.0f} | Réel: {d['prix_reel']:8.0f} | "
                  f"Diff: {d['diff_pct']:+7.1f}% | {d['quality']:15s}")
    
    # Afficher corrects
    if corrects:
        print(f"\n✅ PRIX CORRECTS (<2% différence): {len(corrects)}")
        print("-" * 80)
        for d in corrects[:10]:  # Limiter à 10
            print(f"   {d['symbol']:6s} | DB: {d['prix_db']:8.0f} | Réel: {d['prix_reel']:8.0f} | "
                  f"Diff: {d['diff_pct']:+7.1f}%")
    
    # Résumé
    print("\n" + "="*80)
    print("📈 RÉSUMÉ:")
    print("="*80)
    print(f"   Total actions vérifiées: {len(differences)}")
    print(f"   🔴 Erreurs majeures (>10%): {len(erreurs_majeures)}")
    print(f"   🟡 Erreurs mineures (2-10%): {len(erreurs_mineures)}")
    print(f"   ✅ Prix corrects (<2%): {len(corrects)}")
    
    if erreurs_majeures or erreurs_mineures:
        print("\n⚠️  ACTION REQUISE:")
        print("   1. Mettre à jour les prix avec:")
        print("      python mettre_a_jour_cours_brvm.py")
        print("   2. Ou importer CSV récent:")
        print("      python collecter_csv_automatique.py --dossier csv")
    else:
        print("\n✅ Tous les prix sont à jour !")
    
    print("="*80)


if __name__ == '__main__':
    try:
        comparer_prix()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
