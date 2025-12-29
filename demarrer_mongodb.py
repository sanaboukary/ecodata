#!/usr/bin/env python3
"""Démarrer MongoDB et vérifier la connexion"""

import subprocess
import time
import os
from pymongo import MongoClient

print("="*80)
print("🚀 DÉMARRAGE MONGODB")
print("="*80)

# Chemins MongoDB possibles sur Windows
chemins_possibles = [
    r"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
    r"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe",
    r"C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe",
    r"C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe",
    r"C:\MongoDB\bin\mongod.exe",
]

mongod_path = None
for chemin in chemins_possibles:
    if os.path.exists(chemin):
        mongod_path = chemin
        print(f"✅ MongoDB trouvé: {chemin}")
        break

if not mongod_path:
    print("❌ MongoDB non trouvé aux emplacements standards")
    print("\n🔍 Recherche de mongod.exe en cours...")
    try:
        result = subprocess.run(['where', 'mongod'], capture_output=True, text=True)
        if result.returncode == 0:
            mongod_path = result.stdout.strip().split('\n')[0]
            print(f"✅ Trouvé via 'where': {mongod_path}")
    except:
        pass

if not mongod_path:
    print("\n⚠️  SOLUTION:")
    print("1. Installer MongoDB Community Server")
    print("2. Ou démarrer MongoDB manuellement")
    print("3. Ou utiliser MongoDB Atlas (cloud)")
    exit(1)

# Vérifier si déjà démarré
print("\n🔍 Vérification processus MongoDB...")
try:
    result = subprocess.run(['tasklist'], capture_output=True, text=True)
    if 'mongod.exe' in result.stdout:
        print("✅ MongoDB déjà en cours d'exécution")
    else:
        print("📍 MongoDB non actif, démarrage...")
        # Démarrer mongod en arrière-plan
        subprocess.Popen([mongod_path, '--dbpath', 'C:\\data\\db'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print("⏳ Attente démarrage (5 secondes)...")
        time.sleep(5)
except Exception as e:
    print(f"⚠️  Erreur vérification: {e}")

# Tester connexion
print("\n🔌 Test connexion MongoDB...")
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.server_info()
    print("✅ Connexion réussie!")
    
    # Vérifier la base
    db = client['centralisation_db']
    count = db.curated_observations.count_documents({'source': 'BRVM'})
    print(f"📊 Base: centralisation_db")
    print(f"📈 Observations BRVM: {count}")
    
    # Dernière date
    today = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': '2025-12-23'
    })
    print(f"📅 Observations 23/12/2025: {today}")
    
    client.close()
    
    print("\n" + "="*80)
    print("✅ MONGODB OPÉRATIONNEL - Prêt pour collecte")
    print("="*80)
    
except Exception as e:
    print(f"❌ Connexion échouée: {e}")
    print("\n⚠️  SOLUTION:")
    print("1. Vérifier que MongoDB est installé")
    print("2. Créer le dossier: C:\\data\\db")
    print("3. Démarrer manuellement: mongod --dbpath C:\\data\\db")
    exit(1)
