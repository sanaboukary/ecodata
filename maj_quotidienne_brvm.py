#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de mise à jour QUOTIDIENNE des cours BRVM
À lancer tous les jours après la clôture (16h30)

USAGE:
  python maj_quotidienne_brvm.py                    # Scraping automatique
  python maj_quotidienne_brvm.py --manuel            # Saisie manuelle guidée
  python maj_quotidienne_brvm.py --csv fichier.csv  # Import CSV
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Import des modules de collecte
from plateforme_centralisation.mongo import get_mongo_db

# Configuration
BRVM_ACTIONS = [
    'BICC', 'BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS', 'BNBC', 'BICB',
    'CFAC', 'ECOC', 'ETIT', 'FTSC', 'NSIAC', 'NTLC', 'SAFC', 'SICB',
    'SIBC', 'SLBC', 'SMBC', 'SNTS', 'SOGC', 'TTLC', 'TTLS', 'UNXC',
    'ABJC', 'PALC', 'SDCC', 'SHEC', 'SICC', 'STBC', 'SVOC', 'TTRC',
    'CABC', 'NEIC', palc', 'PRSC', 'SDSC', 'SEMC', 'SIVC', 'SMBC', 'SPHC',
    'STAC', 'SUCR', 'TOTC', 'TOBC', 'UNXC', 'ONTBF'
]

def scraper_brvm_automatique():
    """
    Tentative de scraping automatique du site BRVM
    """
    print("\n🌐 TENTATIVE DE SCRAPING AUTOMATIQUE...")
    print("-" * 80)
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # URLs possibles (le site BRVM change souvent)
        urls_to_try = [
            'https://www.brvm.org/fr/cours-et-cotations',
            'https://www.brvm.org/fr/investir/cours-et-cotations',
            'https://www.brvm.org/fr/cotations',
            'https://www.brvm.org/fr/marches/cours-actions'
        ]
        
        for url in urls_to_try:
            try:
                print(f"📡 Essai: {url}")
                response = requests.get(url, timeout=10, verify=False)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Chercher les tableaux de cours
                    tables = soup.find_all('table')
                    
                    prices_collected = {}
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        
                        for row in rows[1:]:  # Skip header
                            cols = row.find_all('td')
                            
                            if len(cols) >= 2:
                                # Extraire symbole et prix
                                symbol_cell = cols[0].get_text(strip=True)
                                price_cell = cols[1].get_text(strip=True)
                                
                                # Nettoyer le symbole
                                symbol = symbol_cell.replace('.', '').strip().upper()
                                
                                # Nettoyer le prix
                                try:
                                    price = price_cell.replace(' ', '').replace(',', '').replace('FCFA', '').strip()
                                    price = float(price)
                                    
                                    if symbol in BRVM_ACTIONS and price > 0:
                                        prices_collected[symbol] = price
                                except:
                                    continue
                    
                    if prices_collected:
                        print(f"✅ Scraping réussi! {len(prices_collected)} cours collectés")
                        return prices_collected
                        
            except Exception as e:
                print(f"   ⚠️ Échec: {e}")
                continue
        
        print("❌ Échec du scraping automatique")
        return None
        
    except ImportError:
        print("❌ Modules requests/beautifulsoup4 non installés")
        print("   pip install requests beautifulsoup4")
        return None

def saisie_manuelle_guidee():
    """
    Saisie manuelle guidée des cours principaux
    """
    print("\n✍️  SAISIE MANUELLE DES COURS")
    print("-" * 80)
    print("💡 Allez sur https://www.brvm.org/fr/investir/cours-et-cotations")
    print("💡 Saisissez les cours du jour pour les principales actions")
    print("💡 Appuyez sur ENTER pour skip une action\n")
    
    # Top 20 actions par capitalisation (prioritaires)
    top_actions = [
        'SNTS', 'SOGC', 'BOAB', 'NTLC', 'ECOC', 'BICC', 'TTLC', 'BOAS',
        'SIBC', 'SLBC', 'CFAC', 'SMBC', 'ABJC', 'PALC', 'SDCC', 'BICB',
        'BOAM', 'BOAC', 'FTSC', 'ETIT'
    ]
    
    prices_collected = {}
    
    for symbol in top_actions:
        while True:
            prix_input = input(f"{symbol:10} Cours (FCFA): ")
            
            if not prix_input.strip():
                print(f"   → Skipped")
                break
            
            try:
                prix = float(prix_input.replace(',', '').replace(' ', ''))
                
                if 100 <= prix <= 100000:  # Validation range
                    prices_collected[symbol] = prix
                    print(f"   ✅ {symbol}: {prix:,.0f} FCFA")
                    break
                else:
                    print(f"   ⚠️ Prix invalide (100-100,000 FCFA)")
            except ValueError:
                print("   ⚠️ Format invalide, réessayez")
    
    print(f"\n✅ {len(prices_collected)} cours saisis")
    return prices_collected if prices_collected else None

def import_csv_file(csv_path):
    """
    Import depuis fichier CSV
    Format: SYMBOLE,PRIX,DATE (optionnel)
    """
    print(f"\n📄 IMPORT DEPUIS CSV: {csv_path}")
    print("-" * 80)
    
    try:
        import csv
        
        prices_collected = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for row in reader:
                # Skip commentaires et lignes vides
                if not row or row[0].startswith('#'):
                    continue
                
                if len(row) >= 2:
                    symbol = row[0].strip().upper()
                    try:
                        prix = float(row[1].strip().replace(',', ''))
                        
                        if symbol in BRVM_ACTIONS and 100 <= prix <= 100000:
                            prices_collected[symbol] = prix
                    except:
                        continue
        
        print(f"✅ {len(prices_collected)} cours importés")
        return prices_collected if prices_collected else None
        
    except Exception as e:
        print(f"❌ Erreur import CSV: {e}")
        return None

def update_mongodb(prices_dict):
    """
    Met à jour MongoDB avec les nouveaux cours
    """
    if not prices_dict:
        print("⚠️ Aucun prix à mettre à jour")
        return False
    
    print(f"\n💾 MISE À JOUR MONGODB...")
    print("-" * 80)
    
    try:
        _, db = get_mongo_db()
        
        today = datetime.now().strftime('%Y-%m-%d')
        updated_count = 0
        
        for symbol, prix in prices_dict.items():
            # Créer l'observation
            observation = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbol,
                'ts': f"{today}T16:00:00Z",  # Clôture à 16h
                'value': prix,
                'attrs': {
                    'data_quality': 'REAL_MANUAL',  # Prix réel saisi manuellement
                    'close': prix,
                    'collection_method': 'daily_update_script',
                    'verified': True
                }
            }
            
            # Upsert (insert ou update)
            result = db.curated_observations.replace_one(
                {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': symbol,
                    'ts': f"{today}T16:00:00Z"
                },
                observation,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count:
                updated_count += 1
                print(f"  ✅ {symbol:10} {prix:>10,.0f} FCFA")
        
        print(f"\n✅ {updated_count}/{len(prices_dict)} cours mis à jour dans MongoDB")
        return True
        
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Mise à jour quotidienne des cours BRVM')
    parser.add_argument('--manuel', action='store_true', help='Saisie manuelle guidée')
    parser.add_argument('--csv', type=str, help='Import depuis fichier CSV')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(" " * 20 + "💰 MISE À JOUR QUOTIDIENNE BRVM 💰")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Objectif: Collecte des cours réels du jour")
    print()
    
    prices = None
    
    # Choix de la méthode
    if args.csv:
        # Import CSV
        prices = import_csv_file(args.csv)
        
    elif args.manuel:
        # Saisie manuelle
        prices = saisie_manuelle_guidee()
        
    else:
        # Auto-scraping
        prices = scraper_brvm_automatique()
        
        # Fallback sur saisie manuelle si échec
        if not prices:
            print("\n⚠️ Scraping échoué, passage en mode manuel...")
            response = input("\n❓ Voulez-vous saisir manuellement les cours? (o/N): ")
            
            if response.lower() == 'o':
                prices = saisie_manuelle_guidee()
            else:
                print("\n⏭️  Mise à jour annulée")
                return
    
    # Mise à jour MongoDB
    if prices:
        success = update_mongodb(prices)
        
        if success:
            print("\n" + "=" * 80)
            print("✅ MISE À JOUR TERMINÉE AVEC SUCCÈS")
            print("=" * 80)
            print(f"📊 {len(prices)} cours BRVM mis à jour avec des PRIX RÉELS")
            print("💡 Vous pouvez maintenant lancer l'analyse IA:")
            print("   python lancer_analyse_ia_complete.py")
            print("=" * 80)
        else:
            print("\n❌ Échec de la mise à jour MongoDB")
    else:
        print("\n⚠️ Aucun prix collecté - mise à jour annulée")

if __name__ == "__main__":
    main()
