#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du collecteur BRVM ultra-robuste
Vérifie que toutes les stratégies sont disponibles
"""

import sys
import os

def test_imports():
    """Teste les imports nécessaires."""
    print("=" * 80)
    print("TEST DES DÉPENDANCES")
    print("=" * 80)
    
    modules = {
        'pymongo': 'MongoDB',
        'requests': 'HTTP requests',
        'bs4': 'BeautifulSoup',
        'pandas': 'Pandas',
        'lxml': 'LXML',
        'selenium': 'Selenium (stratégie avancée)',
        'webdriver_manager': 'WebDriver Manager'
    }
    
    available = []
    missing = []
    
    for module, desc in modules.items():
        try:
            __import__(module)
            print(f"✅ {desc:30} - OK")
            available.append(desc)
        except ImportError:
            print(f"❌ {desc:30} - MANQUANT")
            missing.append(module)
    
    print("\n" + "=" * 80)
    print(f"Disponibles: {len(available)}/{len(modules)}")
    
    if missing:
        print(f"\n⚠️  Modules manquants: {', '.join(missing)}")
        print("\nInstallez avec:")
        print("  pip install -r requirements_collecteur.txt")
        print("  ou")
        print("  installer_dependances_collecteur.bat")
        return False
    else:
        print("\n✅ TOUTES LES DÉPENDANCES SONT INSTALLÉES")
        return True

def test_strategies():
    """Teste quelles stratégies sont disponibles."""
    print("\n" + "=" * 80)
    print("STRATÉGIES DISPONIBLES")
    print("=" * 80)
    
    strategies = []
    
    # Test Selenium
    try:
        from selenium import webdriver
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ Stratégie 0: Selenium Avancé - Disponible")
        strategies.append("Selenium Avancé")
    except ImportError:
        print("⚠️  Stratégie 0: Selenium Avancé - Non disponible (modules manquants)")
    
    # Test BeautifulSoup
    try:
        from bs4 import BeautifulSoup
        import requests
        print("✅ Stratégie 1: BeautifulSoup - Disponible")
        strategies.append("BeautifulSoup")
    except ImportError:
        print("❌ Stratégie 1: BeautifulSoup - Non disponible")
    
    # Test CSV (toujours dispo avec Python)
    print("✅ Stratégie 2: Import CSV - Disponible")
    strategies.append("Import CSV")
    
    # Saisie manuelle (toujours dispo)
    print("✅ Stratégie 3: Saisie Manuelle - Disponible")
    strategies.append("Saisie Manuelle")
    
    print(f"\n{len(strategies)}/4 stratégies disponibles")
    
    if len(strategies) >= 2:
        print("\n✅ Collecteur fonctionnel (au moins 2 stratégies)")
        return True
    else:
        print("\n❌ Collecteur limité (moins de 2 stratégies)")
        return False

def test_mongodb():
    """Teste la connexion MongoDB."""
    print("\n" + "=" * 80)
    print("TEST MONGODB")
    print("=" * 80)
    
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
        client.server_info()
        print("✅ MongoDB connecté")
        client.close()
        return True
    except Exception as e:
        print(f"❌ MongoDB non accessible: {e}")
        print("\nDémarrez MongoDB avec:")
        print("  docker start centralisation_db")
        return False

def main():
    print("\n" + "=" * 80)
    print("🧪 TEST COLLECTEUR BRVM ULTRA-ROBUSTE")
    print("=" * 80)
    
    results = []
    
    # Test imports
    results.append(("Dépendances", test_imports()))
    
    # Test stratégies
    results.append(("Stratégies", test_strategies()))
    
    # Test MongoDB
    results.append(("MongoDB", test_mongodb()))
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    for name, success in results:
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"{name:20} {status}")
    
    all_ok = all(r[1] for r in results)
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ COLLECTEUR PRÊT À UTILISER")
        print("\nLancez la collecte avec:")
        print("  python collecteur_brvm_ultra_robuste.py")
        print("  ou")
        print("  COLLECTER_BRVM.bat")
    else:
        print("⚠️  CONFIGURATION INCOMPLÈTE")
        print("\nActions nécessaires:")
        if not results[0][1]:
            print("  1. Installer les dépendances: installer_dependances_collecteur.bat")
        if not results[2][1]:
            print("  2. Démarrer MongoDB: docker start centralisation_db")
    print("=" * 80)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
