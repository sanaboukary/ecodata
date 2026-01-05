#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de collecte BRVM simplifié - Sans Airflow
Peut être exécuté manuellement ou via Windows Task Scheduler

Usage:
  python collecte_brvm_simple.py                    # Collecte normale
  python collecte_brvm_simple.py --force            # Force la collecte même si données existent
  python collecte_brvm_simple.py --check            # Vérifie uniquement sans collecter
"""

import os
import sys
import argparse
from datetime import datetime
from pymongo import MongoClient

def setup_environment():
    """Configuration minimale de l'environnement."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    
def get_mongo_connection():
    """Connexion directe à MongoDB sans Django."""
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    client = MongoClient(mongo_uri)
    db = client['centralisation_db']
    return client, db

def log(message, level='INFO'):
    """Log simple avec timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    symbols = {'INFO': '📊', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
    print(f"[{timestamp}] {symbols.get(level, 'ℹ️')} {message}")

def check_existing_data(db, date_str):
    """Vérifie si des données existent déjà pour la date."""
    count = db.curated_observations.count_documents({
        'source': 'BRVM',
        'ts': date_str,
        'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
    })
    return count

def collect_brvm_data():
    """Collecte les données BRVM via le pipeline."""
    try:
        # Setup Django minimal
        import django
        setup_environment()
        django.setup()
        
        from scripts.pipeline import run_ingestion
        
        log("Lancement de l'ingestion BRVM...")
        result = run_ingestion(source='brvm')
        
        return result
        
    except Exception as e:
        log(f"Erreur lors de l'ingestion : {e}", 'ERROR')
        return {'status': 'error', 'error_msg': str(e)}

def main():
    parser = argparse.ArgumentParser(description='Collecte BRVM simplifiée')
    parser.add_argument('--force', action='store_true', help='Force la collecte même si données existent')
    parser.add_argument('--check', action='store_true', help='Vérifie uniquement sans collecter')
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 COLLECTE BRVM SIMPLIFIÉE")
    print("=" * 80)
    
    today = datetime.now().strftime('%Y-%m-%d')
    log(f"Date de collecte : {today}")
    
    try:
        # Connexion MongoDB
        log("Connexion à MongoDB...")
        client, db = get_mongo_connection()
        
        # Vérification données existantes
        existing_count = check_existing_data(db, today)
        
        if existing_count > 0:
            log(f"Données existantes trouvées : {existing_count} observations", 'SUCCESS')
            
            if not args.force:
                log("Collecte annulée (données déjà présentes). Utilisez --force pour forcer.", 'WARNING')
                client.close()
                return 0
            else:
                log("Mode --force activé, collecte en cours...", 'WARNING')
        else:
            log("Aucune donnée pour aujourd'hui, collecte nécessaire")
        
        if args.check:
            log("Mode --check uniquement, pas de collecte", 'INFO')
            client.close()
            return 0
        
        # Collecte des données
        log("Démarrage de la collecte...")
        result = collect_brvm_data()
        
        # Résultat
        print("\n" + "=" * 80)
        if result.get('status') == 'success':
            obs_count = result.get('obs_count', 0)
            duration = result.get('duration', 'N/A')
            log(f"COLLECTE RÉUSSIE - {obs_count} observations en {duration}", 'SUCCESS')
            
            # Vérification finale
            final_count = check_existing_data(db, today)
            log(f"Total observations BRVM pour {today} : {final_count}", 'INFO')
            
            client.close()
            return 0
        else:
            error_msg = result.get('error_msg', 'Erreur inconnue')
            log(f"COLLECTE ÉCHOUÉE : {error_msg}", 'ERROR')
            client.close()
            return 1
            
    except Exception as e:
        log(f"ERREUR CRITIQUE : {e}", 'ERROR')
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("=" * 80)

if __name__ == "__main__":
    sys.exit(main())
