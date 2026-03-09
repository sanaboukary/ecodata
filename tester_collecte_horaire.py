#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du système de collecte horaire BRVM
- Teste le scraper sans insérer dans MongoDB
- Vérifie la structure des données
- Simule une collecte horaire
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin du projet
PROJECT_PATH = r'E:\DISQUE C\Desktop\Implementation plateforme'
sys.path.insert(0, PROJECT_PATH)

print("="*100)
print(" " * 30 + "TEST COLLECTE HORAIRE BRVM")
print(" " * 35 + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
print("="*100)


def test_scraper_production():
    """Test du scraper production"""
    print("\n🧪 TEST 1: Scraper Production BRVM")
    print("-" * 100)
    
    try:
        sys.path.insert(0, os.path.join(PROJECT_PATH, 'scripts', 'connectors'))
        from brvm_scraper_production import scraper_brvm_complet
        
        print("\n🌐 Tentative scraping site officiel BRVM...")
        resultats = scraper_brvm_complet()
        
        if resultats and len(resultats) > 0:
            print(f"✅ Scraping RÉUSSI - {len(resultats)} actions récupérées\n")
            
            # Afficher quelques exemples
            print("📊 Échantillon de données:")
            for i, (action, data) in enumerate(list(resultats.items())[:5]):
                print(f"\n   {action}:")
                print(f"      Cours: {data.get('close', 'N/A')} FCFA")
                print(f"      Variation: {data.get('variation', 'N/A')}%")
                print(f"      Volume: {data.get('volume', 'N/A')}")
            
            if len(resultats) > 5:
                print(f"\n   ... et {len(resultats) - 5} autres actions")
            
            return True, resultats
        else:
            print("❌ Scraping ÉCHOUÉ - Aucune donnée récupérée")
            print("   Raisons possibles:")
            print("   - Site BRVM inaccessible")
            print("   - Structure HTML changée")
            print("   - Problème de connexion réseau")
            return False, None
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_structure_donnees(resultats):
    """Vérifie la structure des données scrapées"""
    print("\n🧪 TEST 2: Validation Structure Données")
    print("-" * 100)
    
    if not resultats:
        print("⏭️  Skip - Pas de données à valider")
        return False
    
    champs_requis = ['close', 'volume', 'variation']
    champs_optionnels = ['open', 'high', 'low', 'name']
    
    erreurs = []
    avertissements = []
    
    for action, data in resultats.items():
        # Vérifier champs requis
        for champ in champs_requis:
            if champ not in data or data[champ] is None:
                erreurs.append(f"{action}: Champ '{champ}' manquant")
        
        # Vérifier champs optionnels
        for champ in champs_optionnels:
            if champ not in data:
                avertissements.append(f"{action}: Champ '{champ}' absent")
        
        # Vérifier types
        if 'close' in data and data['close'] is not None:
            try:
                float(data['close'])
            except (ValueError, TypeError):
                erreurs.append(f"{action}: 'close' n'est pas un nombre valide")
        
        if 'volume' in data and data['volume'] is not None:
            try:
                int(data['volume'])
            except (ValueError, TypeError):
                erreurs.append(f"{action}: 'volume' n'est pas un entier valide")
    
    print(f"\n✅ Actions validées: {len(resultats)}")
    print(f"❌ Erreurs critiques: {len(erreurs)}")
    print(f"⚠️  Avertissements: {len(avertissements)}")
    
    if erreurs:
        print("\n❌ ERREURS:")
        for err in erreurs[:10]:
            print(f"   - {err}")
        if len(erreurs) > 10:
            print(f"   ... et {len(erreurs) - 10} autres erreurs")
        return False
    
    if avertissements:
        print("\n⚠️  AVERTISSEMENTS (non bloquants):")
        for warn in avertissements[:5]:
            print(f"   - {warn}")
    
    print("\n✅ Structure des données VALIDE")
    return True


def test_insertion_mongodb(resultats, dry_run=True):
    """Test insertion dans MongoDB"""
    print("\n🧪 TEST 3: Insertion MongoDB")
    print("-" * 100)
    
    if not resultats:
        print("⏭️  Skip - Pas de données à insérer")
        return False
    
    if dry_run:
        print("\n🔄 Mode DRY-RUN (simulation sans insertion réelle)\n")
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
        django.setup()
        
        from plateforme_centralisation.mongo import get_mongo_db
        
        client, db = get_mongo_db()
        collection = db.curated_observations
        
        # Préparer observations
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        
        observations = []
        for action, data in resultats.items():
            obs = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': action,
                'ts': date_str,
                'value': float(data.get('close', 0)),
                'attrs': {
                    'close': float(data.get('close', 0)),
                    'volume': int(data.get('volume', 0)),
                    'variation': float(data.get('variation', 0)),
                    'data_quality': 'REAL_SCRAPER',
                    'collected_at': now.isoformat(),
                    'collection_hour': now.hour,
                    'test_mode': dry_run,
                }
            }
            observations.append(obs)
        
        print(f"📦 {len(observations)} observations préparées")
        
        if dry_run:
            print("\n📋 Exemple d'observation (première action):")
            import json
            print(json.dumps(observations[0], indent=2, default=str))
            
            print(f"\n✅ Test simulation RÉUSSI")
            print(f"   {len(observations)} observations seraient insérées")
            return True
        else:
            # Insertion réelle
            from scripts.mongo_utils import upsert_observations
            upsert_observations(observations)
            
            # Vérification
            count = collection.count_documents({
                'source': 'BRVM',
                'ts': date_str,
                'attrs.collection_hour': now.hour
            })
            
            print(f"\n✅ Insertion RÉUSSIE")
            print(f"   {count} observations insérées dans MongoDB")
            return True
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_verification_doublons():
    """Vérifie qu'il n'y a pas de doublons dans la collecte horaire"""
    print("\n🧪 TEST 4: Vérification Doublons")
    print("-" * 100)
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
        django.setup()
        
        from plateforme_centralisation.mongo import get_mongo_db
        
        client, db = get_mongo_db()
        collection = db.curated_observations
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Pipeline pour détecter doublons
        pipeline = [
            {'$match': {'source': 'BRVM', 'ts': date_str}},
            {'$group': {
                '_id': {
                    'action': '$key',
                    'heure': '$attrs.collection_hour'
                },
                'count': {'$sum': 1}
            }},
            {'$match': {'count': {'$gt': 1}}},
            {'$sort': {'count': -1}}
        ]
        
        doublons = list(collection.aggregate(pipeline))
        
        if doublons:
            print(f"\n⚠️  {len(doublons)} doublons détectés:")
            for d in doublons[:10]:
                action = d['_id']['action']
                heure = d['_id']['heure']
                count = d['count']
                print(f"   - {action} à {heure}h: {count} entrées")
            
            return False
        else:
            print("\n✅ Aucun doublon détecté")
            return True
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False


def generer_rapport_test():
    """Génère un rapport final du test"""
    print("\n" + "="*100)
    print("📊 RAPPORT FINAL DU TEST")
    print("="*100)
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
        django.setup()
        
        from plateforme_centralisation.mongo import get_mongo_db
        
        client, db = get_mongo_db()
        collection = db.curated_observations
        
        # Stats BRVM
        total_brvm = collection.count_documents({'source': 'BRVM'})
        
        # Stats aujourd'hui
        date_str = datetime.now().strftime('%Y-%m-%d')
        today_count = collection.count_documents({
            'source': 'BRVM',
            'ts': date_str
        })
        
        # Actions distinctes
        actions = collection.distinct('key', {'source': 'BRVM'})
        
        # Heures de collecte aujourd'hui
        heures = collection.distinct('attrs.collection_hour', {
            'source': 'BRVM',
            'ts': date_str
        })
        
        print(f"\n📈 Statistiques BRVM:")
        print(f"   Total observations: {total_brvm:,}")
        print(f"   Observations aujourd'hui: {today_count}")
        print(f"   Actions distinctes: {len(actions)}")
        print(f"   Heures collectées aujourd'hui: {len([h for h in heures if h is not None])}")
        
        if today_count > 0:
            print(f"\n   Détail heures aujourd'hui:")
            for h in sorted([h for h in heures if h is not None]):
                count_h = collection.count_documents({
                    'source': 'BRVM',
                    'ts': date_str,
                    'attrs.collection_hour': h
                })
                print(f"      {h}h00: {count_h} obs")
        
        print("\n✅ Système de collecte horaire opérationnel")
        
    except Exception as e:
        print(f"\n⚠️  Impossible de générer le rapport: {e}")


def main():
    """Fonction principale de test"""
    print("\n🚀 Démarrage des tests...\n")
    
    tests_resultats = {}
    
    # Test 1: Scraper
    success, resultats = test_scraper_production()
    tests_resultats['scraper'] = success
    
    if success and resultats:
        # Test 2: Structure
        tests_resultats['structure'] = test_structure_donnees(resultats)
        
        # Test 3: Insertion (dry-run)
        tests_resultats['insertion'] = test_insertion_mongodb(resultats, dry_run=True)
        
        # Test 4: Doublons
        tests_resultats['doublons'] = test_verification_doublons()
    
    # Rapport
    generer_rapport_test()
    
    # Résumé
    print("\n" + "="*100)
    print("🏁 RÉSUMÉ DES TESTS")
    print("="*100)
    
    for test, result in tests_resultats.items():
        statut = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test.upper():<20} {statut}")
    
    all_passed = all(tests_resultats.values())
    
    if all_passed:
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("\n📝 Prochaines étapes:")
        print("   1. Activer le DAG 'brvm_collecte_horaire' dans Airflow")
        print("   2. Le système collectera automatiquement toutes les heures (9h-16h)")
        print("   3. Vérifier les logs dans airflow/logs/brvm_collecte_horaire/")
        return 0
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("   Vérifier les erreurs ci-dessus avant activation")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
