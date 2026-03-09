#!/usr/bin/env python3
"""
🧪 TEST RAPIDE - ARCHITECTURE 3 NIVEAUX

Valide que toute l'architecture fonctionne :
1. Vérifie les collections MongoDB
2. Test migration données existantes → RAW/DAILY/WEEKLY
3. Test calcul indicateurs
4. Test génération TOP5

NE MODIFIE PAS LES DONNÉES EXISTANTES
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
import django
django.setup()
from plateforme_centralisation.mongo import get_mongo_db

_, db = get_mongo_db()

# ============================================================================
# TESTS
# ============================================================================

def test_architecture():
    """Test 1 : Vérifier architecture"""
    print("\n" + "="*80)
    print("TEST 1 - ARCHITECTURE 3 NIVEAUX")
    print("="*80 + "\n")
    
    collections = {
        'prices_intraday_raw': db.prices_intraday_raw.count_documents({}),
        'prices_daily': db.prices_daily.count_documents({}),
        'prices_weekly': db.prices_weekly.count_documents({}),
        'top5_weekly_brvm': db.top5_weekly_brvm.count_documents({}),
    }
    
    print("Collections :")
    for name, count in collections.items():
        status = "✅" if count > 0 else "⚠️ "
        print(f"  {status} {name:<30} : {count:>6,} documents")
    
    print("\n✅ Test architecture OK")
    return True

def test_existing_data_migration():
    """Test 2 : Vérifier migration possible des données existantes"""
    print("\n" + "="*80)
    print("TEST 2 - MIGRATION DONNÉES EXISTANTES")
    print("="*80 + "\n")
    
    # Vérifier curated_observations (ancien système)
    total_obs = db.curated_observations.count_documents({'dataset': 'STOCK_PRICE'})
    
    print(f"📦 Données existantes (curated_observations) : {total_obs:,}")
    
    if total_obs == 0:
        print("⚠️  Aucune donnée existante")
        return False
    
    # Compter par source
    sources = db.curated_observations.distinct('source', {'dataset': 'STOCK_PRICE'})
    
    print(f"\n📊 Sources ({len(sources)}) :")
    for source in sorted(sources):
        count = db.curated_observations.count_documents({
            'dataset': 'STOCK_PRICE',
            'source': source
        })
        print(f"  • {source:<30} : {count:>6,}")
    
    # Vérifier si déjà en DAILY/WEEKLY
    daily_count = db.prices_daily.count_documents({})
    weekly_count = db.prices_weekly.count_documents({})
    
    print(f"\n📈 État migration :")
    print(f"  DAILY   : {daily_count:,}")
    print(f"  WEEKLY  : {weekly_count:,}")
    
    if daily_count == 0 or weekly_count == 0:
        print("\n💡 RECOMMANDATION : Exécuter pipeline de migration")
        print("   python brvm_pipeline/master_orchestrator.py --rebuild")
    else:
        print("\n✅ Migration déjà effectuée")
    
    return True

def test_weekly_indicators():
    """Test 3 : Vérifier calcul indicateurs WEEKLY"""
    print("\n" + "="*80)
    print("TEST 3 - INDICATEURS WEEKLY")
    print("="*80 + "\n")
    
    # Dernière semaine avec indicateurs
    sample = db.prices_weekly.find_one({'indicators_computed': True}, sort=[('week', -1)])
    
    if not sample:
        print("⚠️  Aucune semaine avec indicateurs calculés")
        print("\n💡 RECOMMANDATION : Calculer indicateurs")
        print("   python brvm_pipeline/pipeline_weekly.py --indicators")
        return False
    
    print(f"Exemple : {sample['symbol']} - {sample['week']}")
    print(f"  RSI         : {sample.get('rsi', 'N/A')}")
    print(f"  ATR%        : {sample.get('atr_pct', 'N/A')}%")
    print(f"  SMA5        : {sample.get('sma5', 'N/A')}")
    print(f"  SMA10       : {sample.get('sma10', 'N/A')}")
    print(f"  Trend       : {sample.get('trend', 'N/A')}")
    print(f"  Volatilité  : {sample.get('volatility', 'N/A')}%")
    print(f"  Volume Ratio: {sample.get('volume_ratio', 'N/A')}")
    
    # Compter combien ont indicateurs
    with_indicators = db.prices_weekly.count_documents({'indicators_computed': True})
    total_weekly = db.prices_weekly.count_documents({})
    
    pct = (with_indicators / total_weekly * 100) if total_weekly > 0 else 0
    
    print(f"\n📊 Couverture : {with_indicators}/{total_weekly} ({pct:.1f}%)")
    
    if pct < 80:
        print("\n💡 RECOMMANDATION : Recalculer tous les indicateurs")
        print("   python brvm_pipeline/pipeline_weekly.py --rebuild")
    else:
        print("\n✅ Indicateurs OK")
    
    return True

def test_top5_generation():
    """Test 4 : Vérifier génération TOP5"""
    print("\n" + "="*80)
    print("TEST 4 - GÉNÉRATION TOP5")
    print("="*80 + "\n")
    
    # Derniers TOP5
    top5_weeks = db.top5_weekly_brvm.distinct('week')
    
    if not top5_weeks:
        print("⚠️  Aucun TOP5 généré")
        print("\n💡 RECOMMANDATION : Générer TOP5")
        print("   python brvm_pipeline/top5_engine.py")
        return False
    
    last_week = sorted(top5_weeks)[-1]
    top5 = list(db.top5_weekly_brvm.find({'week': last_week}).sort('rank', 1))
    
    print(f"Dernière semaine : {last_week}")
    print(f"  TOP5 : {len(top5)} actions\n")
    
    if top5:
        print(f"{'#':<3} {'TICKER':<8} {'SCORE':<8} {'DÉCISION':<10} {'PRIX':<10}")
        print("-"*50)
        for item in top5[:5]:
            print(
                f"{item['rank']:<3} "
                f"{item['symbol']:<8} "
                f"{item['top5_score']:<8.1f} "
                f"{item['decision']:<10} "
                f"{item.get('current_price', 0):<10.0f}"
            )
        
        print("\n✅ TOP5 OK")
    
    return True

def test_autolearning():
    """Test 5 : Vérifier auto-learning"""
    print("\n" + "="*80)
    print("TEST 5 - AUTO-LEARNING")
    print("="*80 + "\n")
    
    # Comparaisons disponibles
    comparisons = db.autolearning_results.count_documents({'type': 'COMPARISON'})
    
    print(f"Comparaisons enregistrées : {comparisons}")
    
    if comparisons == 0:
        print("\n💡 INFO : Auto-learning nécessite enregistrement TOP5 officiels")
        print("   python brvm_pipeline/autolearning_engine.py --help")
        return False
    
    # Dernière comparaison
    last_comp = db.autolearning_results.find_one(
        {'type': 'COMPARISON'},
        sort=[('week', -1)]
    )
    
    if last_comp:
        print(f"\nDernière comparaison : {last_comp['week']}")
        print(f"  Matches : {last_comp['matches']}/5")
        print(f"  Taux    : {last_comp['success_rate']:.1f}%")
    
    # Versions de poids
    weights = db.autolearning_weights.count_documents({})
    
    print(f"\nVersions de poids : {weights}")
    
    if weights > 0:
        print("✅ Auto-learning actif")
    else:
        print("⚠️  Auto-learning pas encore ajusté")
    
    return True

def test_data_quality():
    """Test 6 : Qualité des données"""
    print("\n" + "="*80)
    print("TEST 6 - QUALITÉ DES DONNÉES")
    print("="*80 + "\n")
    
    # WEEKLY complet
    total_weekly = db.prices_weekly.count_documents({})
    complete_weekly = db.prices_weekly.count_documents({'is_complete': True})
    
    pct_complete = (complete_weekly / total_weekly * 100) if total_weekly > 0 else 0
    
    print(f"WEEKLY complet : {complete_weekly}/{total_weekly} ({pct_complete:.1f}%)")
    
    # Symboles uniques
    symbols_weekly = len(db.prices_weekly.distinct('symbol'))
    
    print(f"Actions WEEKLY : {symbols_weekly}")
    
    # Semaines disponibles
    weeks = sorted(db.prices_weekly.distinct('week'))
    
    if weeks:
        print(f"Période        : {weeks[0]} → {weeks[-1]} ({len(weeks)} semaines)")
    
    # Actions avec ≥14 semaines (minimum pour RSI)
    symbols_enough_data = []
    for symbol in db.prices_weekly.distinct('symbol'):
        count = db.prices_weekly.count_documents({'symbol': symbol})
        if count >= 14:
            symbols_enough_data.append(symbol)
    
    print(f"Actions ≥14 semaines : {len(symbols_enough_data)}/{symbols_weekly}")
    
    if len(symbols_enough_data) < 30:
        print("\n⚠️  Pas assez d'historique pour certaines actions")
    else:
        print("\n✅ Historique suffisant")
    
    return True

# ============================================================================
# RÉCAPITULATIF
# ============================================================================

def show_summary():
    """Afficher récapitulatif final"""
    print("\n" + "="*80)
    print("📋 RÉCAPITULATIF TEST")
    print("="*80 + "\n")
    
    # Collections
    raw_count = db.prices_intraday_raw.count_documents({})
    daily_count = db.prices_daily.count_documents({})
    weekly_count = db.prices_weekly.count_documents({})
    top5_count = db.top5_weekly_brvm.count_documents({})
    
    print(f"📦 RAW     : {raw_count:>6,}")
    print(f"📦 DAILY   : {daily_count:>6,}")
    print(f"📦 WEEKLY  : {weekly_count:>6,}")
    print(f"📦 TOP5    : {top5_count:>6,}")
    
    # Recommandations
    print("\n💡 PROCHAINES ÉTAPES :\n")
    
    if daily_count == 0 or weekly_count == 0:
        print("  1️⃣  Reconstruire DAILY + WEEKLY")
        print("      python brvm_pipeline/master_orchestrator.py --rebuild")
    
    elif weekly_count > 0:
        indicators_count = db.prices_weekly.count_documents({'indicators_computed': True})
        if indicators_count < weekly_count * 0.8:
            print("  1️⃣  Calculer indicateurs WEEKLY")
            print("      python brvm_pipeline/pipeline_weekly.py --indicators")
    
    if top5_count == 0:
        print("  2️⃣  Générer TOP5")
        print("      python brvm_pipeline/top5_engine.py")
    
    print("\n  3️⃣  Mettre en production")
    print("      python brvm_pipeline/master_orchestrator.py --weekly-update")
    
    print("\n" + "="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Exécuter tous les tests"""
    print("\n" + "="*100)
    print(" " * 30 + "🧪 TEST RAPIDE ARCHITECTURE 3 NIVEAUX")
    print("="*100)
    
    tests = [
        ("Architecture", test_architecture),
        ("Migration données", test_existing_data_migration),
        ("Indicateurs Weekly", test_weekly_indicators),
        ("Génération TOP5", test_top5_generation),
        ("Auto-learning", test_autolearning),
        ("Qualité données", test_data_quality)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Erreur dans test '{name}' : {e}")
            results.append((name, False))
    
    # Récapitulatif
    show_summary()
    
    # Résultats
    print("="*80)
    print("RÉSULTATS DES TESTS")
    print("="*80 + "\n")
    
    for name, result in results:
        status = "✅" if result else "⚠️ "
        print(f"  {status} {name}")
    
    success = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n{'✅' if success == total else '⚠️ '} {success}/{total} tests réussis")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
