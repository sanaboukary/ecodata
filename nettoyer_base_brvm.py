#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nettoyer la base BRVM - Supprimer TOUTES les anciennes observations
et ne garder que les observations du jour avec data_quality REAL_MANUAL
"""

import os
import sys
import django
from datetime import datetime, timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def nettoyer_base():
    """Nettoie la base BRVM"""
    
    client, db = get_mongo_db()
    collection = db.curated_observations
    
    print("\n" + "="*80)
    print("🧹 NETTOYAGE COMPLET BASE BRVM")
    print("="*80)
    
    # Compter observations actuelles
    total_avant = collection.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
    print(f"\n📊 Observations BRVM avant nettoyage: {total_avant}")
    
    # Récupérer date du jour
    date_aujourdhui = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"📅 Date du jour: {date_aujourdhui}")
    
    # Compter observations du jour
    obs_aujourdhui = collection.count_documents({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': date_aujourdhui
    })
    print(f"✅ Observations du jour à conserver: {obs_aujourdhui}")
    
    # Demander confirmation
    print(f"\n⚠️  ATTENTION: Cette opération va supprimer {total_avant - obs_aujourdhui} observations anciennes")
    print(f"   Seules les {obs_aujourdhui} observations du {date_aujourdhui} seront conservées")
    
    reponse = input("\n❓ Confirmer le nettoyage ? (oui/non): ").strip().lower()
    
    if reponse not in ['oui', 'yes', 'y', 'o']:
        print("\n❌ Nettoyage annulé")
        return
    
    # Supprimer toutes les observations SAUF celles du jour
    print(f"\n🗑️  Suppression en cours...")
    
    result = collection.delete_many({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': {'$ne': date_aujourdhui}
    })
    
    print(f"\n✅ {result.deleted_count} observations supprimées")
    
    # Vérifier résultat
    total_apres = collection.count_documents({'source': 'BRVM', 'dataset': 'STOCK_PRICE'})
    print(f"📊 Observations BRVM après nettoyage: {total_apres}")
    
    # Afficher échantillon des observations conservées
    print(f"\n📋 Échantillon des observations conservées (date: {date_aujourdhui}):\n")
    
    observations = list(collection.find({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'ts': date_aujourdhui
    }).sort('key', 1).limit(15))
    
    for obs in observations:
        quality = obs['attrs'].get('data_quality', 'N/A')
        variation = obs['attrs'].get('variation', 0)
        print(f"   {obs['key']:6s} | {obs['value']:8.0f} FCFA | "
              f"Var: {variation:+6.2f}% | Quality: {quality}")
    
    if len(observations) > 15:
        print(f"   ... et {len(observations) - 15} autres")
    
    print("\n" + "="*80)
    print("✅ NETTOYAGE TERMINÉ")
    print("="*80)
    print("\n💡 Prochaines étapes:")
    print("   1. Vérifier: python comparer_prix_brvm_detaille.py")
    print("   2. Si besoin: python corriger_prix_brvm_vrais.py")
    print("   3. Lancer IA: python lancer_analyse_ia_complete.py")
    print("="*80 + "\n")


if __name__ == '__main__':
    try:
        nettoyer_base()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
