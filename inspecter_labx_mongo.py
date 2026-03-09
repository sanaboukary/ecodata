#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspection du conteneur labx_mongo pour retrouver les données WorldBank/IMF/AfDB"""

import sys
import io
import subprocess
import json
import time

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*120)
print("INSPECTION CONTENEUR labx_mongo - Recherche données WorldBank/IMF/AfDB")
print("="*120)

# 1. Vérifier si conteneur démarre
print("\n1. VERIFICATION CONTENEUR:")
print("-" * 120)

try:
    # Démarrer le conteneur
    result = subprocess.run(['docker', 'start', 'labx_mongo'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print(f"   ✓ Conteneur labx_mongo démarré: {result.stdout.strip()}")
    else:
        print(f"   ✗ Erreur démarrage: {result.stderr}")
        sys.exit(1)
    
    # Attendre que MongoDB soit prêt
    print("   Attente démarrage MongoDB (5 secondes)...")
    time.sleep(5)
    
    # Vérifier statut
    result = subprocess.run(['docker', 'ps', '--filter', 'name=labx_mongo', '--format', '{{.Status}}'],
                          capture_output=True, text=True)
    print(f"   Statut: {result.stdout.strip()}")
    
except Exception as e:
    print(f"   ERREUR: {e}")
    sys.exit(1)

# 2. Inspecter avec PyMongo directement
print("\n2. CONNEXION DIRECTE MONGODB (Port 27018 via Docker):")
print("-" * 120)

# Trouver le port
result = subprocess.run(
    ['docker', 'port', 'labx_mongo', '27017'],
    capture_output=True, text=True
)
mongo_port = result.stdout.strip().split(':')[-1] if result.stdout else None

if not mongo_port:
    # Essayer de se connecter via docker exec
    print("   Pas de port exposé - Utilisation docker exec avec Python...")
    
    # Créer script Python pour exécution dans conteneur
    inspect_script = """
import sys
sys.path.insert(0, '/usr/local/lib/python3.9/site-packages')
from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    
    # Lister bases
    dbs = client.list_database_names()
    print("BASES:", dbs)
    
    # Vérifier centralisation_db
    if 'centralisation_db' in dbs:
        db = client['centralisation_db']
        collections = db.list_collection_names()
        print("COLLECTIONS:", collections)
        
        if 'curated_observations' in collections:
            total = db.curated_observations.count_documents({})
            print("TOTAL OBSERVATIONS:", total)
            
            sources = db.curated_observations.distinct('source')
            print("SOURCES:", sources)
            
            for source in sources:
                count = db.curated_observations.count_documents({'source': source})
                print(f"SOURCE {source}: {count} documents")
                
                # Exemple de document
                doc = db.curated_observations.find_one({'source': source})
                if doc:
                    print(f"EXEMPLE {source}:", {
                        'dataset': doc.get('dataset'),
                        'key': doc.get('key'),
                        'ts': doc.get('ts'),
                        'value': doc.get('value')
                    })
    else:
        print("BASE centralisation_db non trouvée")
        print("Autres bases:", dbs)
        
    client.close()
except Exception as e:
    print("ERREUR:", str(e))
"""
    
    # Sauvegarder script temporaire
    with open('/tmp/inspect_mongo.py', 'w') as f:
        f.write(inspect_script)
    
    # Copier dans conteneur et exécuter
    try:
        subprocess.run(['docker', 'cp', '/tmp/inspect_mongo.py', 'labx_mongo:/tmp/'], check=True)
        result = subprocess.run(
            ['docker', 'exec', 'labx_mongo', 'python3', '/tmp/inspect_mongo.py'],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"   Erreur exécution: {result.stderr}")
            
            # Essayer avec mongo shell
            print("\n   Essai avec mongo shell...")
            mongo_cmd = """
db.getSiblingDB('admin').listDatabases().databases.forEach(function(db) { 
    print('DB: ' + db.name + ' (' + db.sizeOnDisk + ' bytes)');
});

if (db.getSiblingDB('centralisation_db').getCollectionNames().length > 0) {
    print('\\nCollections dans centralisation_db:');
    db.getSiblingDB('centralisation_db').getCollectionNames().forEach(function(coll) {
        var count = db.getSiblingDB('centralisation_db')[coll].count();
        print('  - ' + coll + ': ' + count + ' documents');
    });
    
    var curatedColl = db.getSiblingDB('centralisation_db').curated_observations;
    if (curatedColl.count() > 0) {
        print('\\nSources dans curated_observations:');
        curatedColl.distinct('source').forEach(function(source) {
            var count = curatedColl.count({'source': source});
            print('  - ' + source + ': ' + count + ' docs');
        });
    }
}
"""
            result = subprocess.run(
                ['docker', 'exec', 'labx_mongo', 'mongo', '--quiet', '--eval', mongo_cmd],
                capture_output=True, text=True, timeout=30
            )
            print(result.stdout)
            if result.stderr:
                print(f"Stderr: {result.stderr}")
                
    except Exception as e:
        print(f"   ERREUR inspection: {e}")

else:
    # Connexion directe via PyMongo
    print(f"   Port MongoDB: {mongo_port}")
    try:
        from pymongo import MongoClient
        
        client = MongoClient(f'mongodb://localhost:{mongo_port}', serverSelectionTimeoutMS=5000)
        
        dbs = client.list_database_names()
        print(f"   Bases trouvées: {dbs}")
        
        if 'centralisation_db' in dbs:
            db = client['centralisation_db']
            collections = db.list_collection_names()
            print(f"   Collections: {collections}")
            
            if 'curated_observations' in collections:
                total = db.curated_observations.count_documents({})
                print(f"\n   Total observations: {total:,}")
                
                sources = db.curated_observations.distinct('source')
                print(f"   Sources: {sources}")
                
                for source in sorted(sources):
                    count = db.curated_observations.count_documents({'source': source})
                    print(f"\n      {source}: {count:,} documents")
                    
                    # Stats par source
                    keys = db.curated_observations.distinct('key', {'source': source})
                    dates = db.curated_observations.distinct('ts', {'source': source})
                    print(f"         Keys: {len(keys)}, Dates: {len(dates)}")
                    
                    if dates:
                        dates_sorted = sorted(dates)
                        print(f"         Période: {dates_sorted[0]} -> {dates_sorted[-1]}")
        
        client.close()
        
    except Exception as e:
        print(f"   ERREUR PyMongo: {e}")

print("\n" + "="*120)
print("FIN INSPECTION")
print("="*120)
