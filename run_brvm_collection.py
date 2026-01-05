#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script d'exécution manuelle de la collecte BRVM
Équivalent à ce que le DAG Airflow devrait faire
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from datetime import datetime
from scripts.pipeline import run_ingestion

def main():
    print("=" * 80)
    print("🚀 LANCEMENT COLLECTE BRVM - Mode Manuel")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        print("📊 Lancement ingestion BRVM...")
        result = run_ingestion(source='brvm')
        
        print("\n" + "=" * 80)
        if result.get('status') == 'success':
            print(f"✅ COLLECTE RÉUSSIE")
            print(f"   Observations collectées: {result.get('obs_count', 0)}")
            print(f"   Durée: {result.get('duration', 'N/A')}")
        else:
            print(f"❌ COLLECTE ÉCHOUÉE")
            print(f"   Erreur: {result.get('error_msg', 'Erreur inconnue')}")
        print("=" * 80)
        
        return 0 if result.get('status') == 'success' else 1
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
