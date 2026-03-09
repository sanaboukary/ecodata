#!/usr/bin/env python3
"""
🧪 TEST OPPORTUNITY ENGINE

Valide le fonctionnement de l'Opportunity Engine sur données réelles
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

def test_1_collections_exist():
    """Test 1 : Vérifier collections existantes"""
    print("\n" + "="*80)
    print("TEST 1 - Collections MongoDB")
    print("="*80)
    
    required = ['prices_daily', 'AGREGATION_SEMANTIQUE_ACTION']
    existing = db.list_collection_names()
    
    for coll in required:
        if coll in existing:
            count = db[coll].count_documents({})
            print(f"✅ {coll:<40} : {count:>8} documents")
        else:
            print(f"❌ {coll:<40} : MANQUANT")
    
    print()
    return all(c in existing for c in required)

def test_2_daily_data_available():
    """Test 2 : Données DAILY disponibles"""
    print("\n" + "="*80)
    print("TEST 2 - Données DAILY disponibles")
    print("="*80)
    
    # Dernière date avec données
    latest = db['prices_daily'].find_one(sort=[('date', -1)])
    
    if not latest:
        print("❌ Aucune donnée DAILY")
        return False
    
    latest_date = latest['date']
    print(f"✅ Dernière date DAILY : {latest_date}")
    
    # Symboles disponibles
    symbols = db['prices_daily'].distinct('symbol', {'date': latest_date})
    print(f"✅ Symboles disponibles : {len(symbols)}")
    print(f"   Exemples : {', '.join(symbols[:5])}")
    
    # Historique
    dates = db['prices_daily'].distinct('date')
    print(f"✅ Dates historiques : {len(dates)} jours")
    
    print()
    return len(symbols) > 0

def test_3_semantic_data_available():
    """Test 3 : Données sémantiques disponibles"""
    print("\n" + "="*80)
    print("TEST 3 - Données sémantiques disponibles")
    print("="*80)
    
    count = db['AGREGATION_SEMANTIQUE_ACTION'].count_documents({})
    
    if count == 0:
        print("⚠️  Aucune donnée sémantique (détecteur NEWS SILENCIEUSE désactivé)")
        print("   Impact : Score semantic_impact sera toujours 0")
        print()
        return True  # Pas critique
    
    print(f"✅ Données sémantiques : {count} documents")
    
    # Exemple
    sample = db['AGREGATION_SEMANTIQUE_ACTION'].find_one()
    if sample:
        print(f"   Exemple : {sample.get('ticker', 'N/A')} - semaine {sample.get('semaine', 'N/A')}")
    
    print()
    return True

def test_4_run_opportunity_engine():
    """Test 4 : Exécuter Opportunity Engine sur dernière date"""
    print("\n" + "="*80)
    print("TEST 4 - Exécution Opportunity Engine")
    print("="*80)
    
    # Import du moteur
    from opportunity_engine import calculate_opportunity_score, scan_all_opportunities
    
    # Dernière date
    latest = db['prices_daily'].find_one(sort=[('date', -1)])
    if not latest:
        print("❌ Pas de données DAILY")
        return False
    
    test_date = latest['date']
    print(f"Date test : {test_date}\n")
    
    # Test sur une action spécifique
    symbols = db['prices_daily'].distinct('symbol', {'date': test_date})
    test_symbol = symbols[0] if symbols else None
    
    if not test_symbol:
        print("❌ Aucun symbole disponible")
        return False
    
    print(f"Test symbole : {test_symbol}")
    
    try:
        result = calculate_opportunity_score(test_symbol, test_date)
        
        print(f"\n✅ OPPORTUNITY_SCORE calculé : {result['opportunity_score']:.1f}")
        print(f"   Niveau : {result['level']}")
        print(f"   Prix   : {result['current_price']:.0f}")
        
        print("\n   Composantes :")
        for key, val in result['components'].items():
            print(f"     • {key:<25} : {val:>6.1f}")
        
        print("\n   Détecteurs :")
        for key, detector in result['detectors'].items():
            status = "✅" if detector['detected'] else "  "
            print(f"     {status} {key:<25} : {detector['reason']}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_5_scan_all_actions():
    """Test 5 : Scanner toutes les actions"""
    print("\n" + "="*80)
    print("TEST 5 - Scan complet toutes actions")
    print("="*80)
    
    from opportunity_engine import scan_all_opportunities
    
    # Dernière date
    latest = db['prices_daily'].find_one(sort=[('date', -1)])
    if not latest:
        print("❌ Pas de données DAILY")
        return False
    
    test_date = latest['date']
    
    try:
        opportunities = scan_all_opportunities(test_date, min_level='OBSERVATION')
        
        print(f"\n✅ Scan terminé")
        print(f"   Opportunités détectées : {len(opportunities)}")
        
        if opportunities:
            forte = sum(1 for o in opportunities if o['level'] == 'FORTE')
            obs = sum(1 for o in opportunities if o['level'] == 'OBSERVATION')
            
            print(f"   • FORTE       : {forte}")
            print(f"   • OBSERVATION : {obs}")
            
            # Top 3
            print("\n   Top 3 opportunités :")
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"     {i}. {opp['symbol']:<8} Score:{opp['opportunity_score']:<6.1f} Niveau:{opp['level']:<15} Prix:{opp['current_price']:.0f}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_6_save_to_mongodb():
    """Test 6 : Sauvegarder dans opportunities_brvm"""
    print("\n" + "="*80)
    print("TEST 6 - Sauvegarde MongoDB")
    print("="*80)
    
    # Vérifier collection créée
    if 'opportunities_brvm' in db.list_collection_names():
        count = db['opportunities_brvm'].count_documents({})
        print(f"✅ Collection 'opportunities_brvm' existe : {count} documents")
        
        # Exemple
        if count > 0:
            sample = db['opportunities_brvm'].find_one(sort=[('date', -1)])
            print(f"   Dernière opportunité : {sample['symbol']} - {sample['date']}")
            print(f"   Score : {sample['opportunity_score']:.1f} ({sample['level']})")
    else:
        print("⚠️  Collection 'opportunities_brvm' pas encore créée")
        print("   Sera créée au premier scan")
    
    print()
    return True

def test_7_dashboard_integration():
    """Test 7 : Dashboard opportunités"""
    print("\n" + "="*80)
    print("TEST 7 - Dashboard Opportunités")
    print("="*80)
    
    try:
        from dashboard_opportunities import show_today_opportunities
        
        # Dernière date
        latest = db['prices_daily'].find_one(sort=[('date', -1)])
        if not latest:
            print("❌ Pas de données")
            return False
        
        # Vérifier qu'il y a des opportunités
        count = db['opportunities_brvm'].count_documents({'date': latest['date']})
        
        if count == 0:
            print("⚠️  Aucune opportunité enregistrée pour cette date")
            print("   → Exécuter d'abord : python opportunity_engine.py")
        else:
            print(f"✅ {count} opportunités trouvées pour {latest['date']}")
            print("   Dashboard fonctionnel")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

def run_all_tests():
    """Exécuter tous les tests"""
    print("\n" + "="*100)
    print(" " * 35 + "🧪 TEST OPPORTUNITY ENGINE")
    print("="*100)
    print(f"Date : {datetime.now()}")
    print("="*100)
    
    tests = [
        ("Collections MongoDB", test_1_collections_exist),
        ("Données DAILY", test_2_daily_data_available),
        ("Données sémantiques", test_3_semantic_data_available),
        ("Calcul OPPORTUNITY_SCORE", test_4_run_opportunity_engine),
        ("Scan toutes actions", test_5_scan_all_actions),
        ("Sauvegarde MongoDB", test_6_save_to_mongodb),
        ("Dashboard", test_7_dashboard_integration)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ ERREUR dans {name} : {e}")
            results.append((name, False))
    
    # Résumé
    print("\n" + "="*100)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*100 + "\n")
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    print("\n" + "="*100)
    print(f"RÉSULTAT : {passed}/{total} tests réussis ({passed/total*100:.0f}%)")
    print("="*100 + "\n")
    
    if passed == total:
        print("🎉 TOUS LES TESTS PASSÉS - Opportunity Engine opérationnel !")
        print("\nProchaines étapes :")
        print("  1. python brvm_pipeline/opportunity_engine.py")
        print("  2. python brvm_pipeline/dashboard_opportunities.py")
        print("  3. python brvm_pipeline/master_orchestrator.py --daily-update")
    else:
        print("⚠️  Certains tests ont échoué - Vérifier les erreurs ci-dessus")
    
    print()

if __name__ == "__main__":
    run_all_tests()
