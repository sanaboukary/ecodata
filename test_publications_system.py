#!/usr/bin/env python3
"""Test rapide du système de publications"""

import sys
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')

import django
django.setup()

print("=" * 80)
print("🧪 TEST SYSTÈME PUBLICATIONS BRVM")
print("=" * 80)
print()

# 1. Tester connexion MongoDB
print("1️⃣ Test connexion MongoDB...")
try:
    from plateforme_centralisation.mongo import get_mongo_db
    _, db = get_mongo_db()
    print("   ✅ MongoDB connecté")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)

# 2. Compter publications existantes
print("\n2️⃣ Vérification base de données...")
count = db.curated_observations.count_documents({'source': 'BRVM_PUBLICATION'})
print(f"   📊 Publications actuelles: {count}")

if count == 0:
    print("   ⚠️  Aucune publication - Lancement collecte de test...")
    
    # 3. Test scraping minimal
    print("\n3️⃣ Test scraping (Bulletins Officiels)...")
    try:
        from collecter_publications_brvm_intelligent import BRVMPublicationCollector, CATEGORIES
        
        collector = BRVMPublicationCollector()
        config = CATEGORIES['BULLETIN_OFFICIEL']
        
        pubs = collector.scrape_category('BULLETIN_OFFICIEL', config)
        print(f"   ✅ {len(pubs)} publication(s) trouvée(s)")
        
        if pubs:
            print("\n   📄 Exemple publication:")
            pub = pubs[0]
            print(f"      Titre : {pub.get('title', '')[:80]}")
            print(f"      URL   : {pub.get('url', '')[:80]}")
            print(f"      Date  : {pub.get('date', '')}")
            
            # 4. Test insertion
            print("\n4️⃣ Test insertion MongoDB...")
            inserted, duplicates = collector.insert_to_mongodb(pubs[:3])
            print(f"   ✅ {inserted} insérée(s), {duplicates} duplicata(s)")
        else:
            print("   ⚠️  Aucune publication récupérée (site peut-être inaccessible)")
    
    except Exception as e:
        print(f"   ❌ Erreur scraping: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✅ {count} publications déjà en base")
    
    # Afficher échantillon
    print("\n   📄 Dernières publications:")
    recent = list(db.curated_observations.find(
        {'source': 'BRVM_PUBLICATION'}
    ).sort('ts', -1).limit(5))
    
    for i, pub in enumerate(recent, 1):
        title = pub.get('key', 'Sans titre')[:60]
        date = pub.get('ts', '')[:10]
        category = pub.get('dataset', 'N/A')
        print(f"      {i}. [{date}] {category:20s} - {title}")
    
    # 5. Test analyse sentiment
    print("\n5️⃣ Test analyse de sentiment...")
    try:
        from analyser_sentiment_publications import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        
        # Analyser une publication
        test_pub = recent[0]
        text = test_pub.get('key', '') + ' ' + test_pub.get('attrs', {}).get('description', '')
        
        analysis = analyzer.analyze_text(text)
        
        print(f"   Texte     : {text[:80]}...")
        print(f"   Sentiment : {analysis['sentiment']} (score: {analysis['score']})")
        print(f"   Impact    : {analysis['impact']}")
        if analysis['events']:
            print(f"   Événements: {', '.join(analysis['events'])}")
        
        print(f"\n   ✅ Analyse de sentiment fonctionnelle")
    
    except Exception as e:
        print(f"   ⚠️  Erreur analyse sentiment: {e}")

print("\n" + "=" * 80)
print("✅ TESTS TERMINÉS")
print("=" * 80)
print()
print("📋 Prochaines étapes:")
print("   1. Collecter toutes publications : COLLECTER_PUBLICATIONS_BRVM.cmd")
print("   2. Analyser sentiment          : ANALYSER_SENTIMENT.cmd")
print("   3. Voir dashboard               : http://127.0.0.1:8000/brvm/publications/")
print()
