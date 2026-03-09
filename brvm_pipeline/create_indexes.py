#!/usr/bin/env python3
"""
🗂️ CRÉATION INDEX MONGODB - ANTI-CASSURE

À exécuter UNE FOIS avant mise en production.
Crée tous les index nécessaires pour garantir unicité et performance.

RÈGLES EXPERT BRVM :
- RAW = index unique (symbol, datetime) → garantie mathématique
- DAILY = index unique (symbol, date) → recalculable
- WEEKLY = index unique (symbol, week) → 1 calcul/semaine

USAGE :
  python brvm_pipeline/create_indexes.py
"""
import os, sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# INDEX DEFINITIONS
# ============================================================================

INDEXES = {
    'prices_intraday_raw': [
        {
            'keys': [('symbol', 1), ('datetime', 1)],
            'options': {'unique': True, 'name': 'idx_raw_unique_symbol_datetime'}
        },
        {
            'keys': [('date', -1)],
            'options': {'name': 'idx_raw_date'}
        },
        {
            'keys': [('session_id', 1)],
            'options': {'name': 'idx_raw_session', 'sparse': True}
        },
        {
            'keys': [('symbol', 1), ('date', -1)],
            'options': {'name': 'idx_raw_symbol_date'}
        }
    ],
    
    'prices_daily': [
        {
            'keys': [('symbol', 1), ('date', 1)],
            'options': {'unique': True, 'name': 'idx_daily_unique_symbol_date'}
        },
        {
            'keys': [('date', -1)],
            'options': {'name': 'idx_daily_date'}
        },
        {
            'keys': [('symbol', 1), ('date', -1)],
            'options': {'name': 'idx_daily_symbol_date'}
        }
    ],
    
    'prices_weekly': [
        {
            'keys': [('symbol', 1), ('week', 1)],
            'options': {'unique': True, 'name': 'idx_weekly_unique_symbol_week'}
        },
        {
            'keys': [('week', -1)],
            'options': {'name': 'idx_weekly_week'}
        },
        {
            'keys': [('symbol', 1), ('week', -1)],
            'options': {'name': 'idx_weekly_symbol_week'}
        }
    ],
    
    'top5_weekly_brvm': [
        {
            'keys': [('week', -1)],
            'options': {'unique': True, 'name': 'idx_top5_unique_week'}
        },
        {
            'keys': [('generated_at', -1)],
            'options': {'name': 'idx_top5_generated'}
        }
    ],
    
    'opportunities_brvm': [
        {
            'keys': [('symbol', 1), ('date', -1)],
            'options': {'name': 'idx_opp_symbol_date'}
        },
        {
            'keys': [('date', -1), ('score', -1)],
            'options': {'name': 'idx_opp_date_score'}
        },
        {
            'keys': [('level', 1), ('date', -1)],
            'options': {'name': 'idx_opp_level_date'}
        }
    ],
    
    'autolearning_results': [
        {
            'keys': [('week', -1)],
            'options': {'unique': True, 'name': 'idx_learning_unique_week'}
        },
        {
            'keys': [('compared_at', -1)],
            'options': {'name': 'idx_learning_compared'}
        }
    ]
}

# ============================================================================
# CRÉATION INDEX
# ============================================================================

def create_indexes():
    """Créer tous les index"""
    print("\n" + "="*80)
    print("🗂️  CRÉATION INDEX MONGODB - ANTI-CASSURE")
    print("="*80)
    print(f"Date : {datetime.now()}")
    print("="*80 + "\n")
    
    total_created = 0
    total_existing = 0
    
    for collection_name, indexes in INDEXES.items():
        print(f"\n📁 Collection : {collection_name}")
        print("-" * 60)
        
        collection = db[collection_name]
        
        # Lister index existants
        existing_indexes = {idx['name'] for idx in collection.list_indexes()}
        print(f"   Index existants : {len(existing_indexes)}")
        
        for idx_def in indexes:
            idx_name = idx_def['options']['name']
            
            if idx_name in existing_indexes:
                print(f"   ⏭️  {idx_name:40} (existe déjà)")
                total_existing += 1
                continue
            
            try:
                # Créer index
                result = collection.create_index(
                    idx_def['keys'],
                    **idx_def['options']
                )
                
                unique = idx_def['options'].get('unique', False)
                unique_str = " [UNIQUE]" if unique else ""
                
                print(f"   ✅ {idx_name:40} {unique_str}")
                total_created += 1
                
            except Exception as e:
                print(f"   ❌ {idx_name:40} - Erreur : {e}")
    
    # Récapitulatif
    print("\n" + "="*80)
    print("📊 RÉCAPITULATIF")
    print("="*80)
    print(f"✅ Créés    : {total_created}")
    print(f"⏭️  Existants : {total_existing}")
    print(f"📦 Total     : {total_created + total_existing}")
    print("="*80)
    
    if total_created > 0:
        print("\n🎉 Index créés avec succès !")
        print("   → Pipeline sécurisé contre cassures")
    else:
        print("\n✅ Tous les index déjà présents")
    
    return total_created

# ============================================================================
# VÉRIFICATION INDEX
# ============================================================================

def verify_indexes():
    """Vérifier que tous les index critiques existent"""
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION INDEX CRITIQUES")
    print("="*80 + "\n")
    
    critical_checks = [
        ('prices_intraday_raw', 'idx_raw_unique_symbol_datetime', True),
        ('prices_daily', 'idx_daily_unique_symbol_date', True),
        ('prices_weekly', 'idx_weekly_unique_symbol_week', True),
        ('top5_weekly_brvm', 'idx_top5_unique_week', True),
    ]
    
    all_ok = True
    
    for collection_name, idx_name, is_unique in critical_checks:
        collection = db[collection_name]
        indexes = list(collection.list_indexes())
        
        found = False
        for idx in indexes:
            if idx['name'] == idx_name:
                found = True
                is_actually_unique = idx.get('unique', False)
                
                if is_unique and not is_actually_unique:
                    print(f"❌ {collection_name:30} | {idx_name:40} | ⚠️  PAS UNIQUE")
                    all_ok = False
                else:
                    unique_str = "[UNIQUE]" if is_actually_unique else ""
                    print(f"✅ {collection_name:30} | {idx_name:40} {unique_str}")
                break
        
        if not found:
            print(f"❌ {collection_name:30} | {idx_name:40} | MANQUANT")
            all_ok = False
    
    print("\n" + "="*80)
    if all_ok:
        print("✅ TOUS LES INDEX CRITIQUES PRÉSENTS ET CORRECTS")
        print("   → Protection anti-cassure activée")
    else:
        print("❌ CERTAINS INDEX CRITIQUES MANQUANTS")
        print("   ⚠️  Risque de cassure pipeline")
        print("   → Relancer : python brvm_pipeline/create_indexes.py")
    print("="*80)
    
    return all_ok

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestion index MongoDB")
    parser.add_argument('--create', action='store_true', help='Créer les index')
    parser.add_argument('--verify', action='store_true', help='Vérifier les index')
    parser.add_argument('--drop', type=str, help='Supprimer un index (nom)')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_indexes()
    elif args.drop:
        print(f"⚠️  Suppression index : {args.drop}")
        response = input("Confirmer ? (yes/no): ")
        if response.lower() == 'yes':
            # À implémenter si nécessaire
            print("❌ Fonction non implémentée (sécurité)")
    else:
        # Par défaut : créer + vérifier
        create_indexes()
        print("\n")
        verify_indexes()
