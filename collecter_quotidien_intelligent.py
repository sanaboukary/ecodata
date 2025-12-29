#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecteur Quotidien Intelligent BRVM - DONNÉES RÉELLES UNIQUEMENT
Stratégies : Scraping → Saisie manuelle → AUCUNE COLLECTE
AUCUNE estimation ni simulation - Politique zéro tolérance
"""

import os
import sys
import io
import django
from datetime import datetime, timedelta

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

class CollecteurQuotidienBRVM:
    """Collecteur intelligent qui essaie plusieurs stratégies RÉELLES uniquement."""
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
        self.collection = self.db.curated_observations
        self.date_collecte = datetime.now().strftime('%Y-%m-%d')
        self.strategies_tentees = []
        self.observations_collectees = []
    
    def log(self, message, level='INFO'):
        """Log avec timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = {'INFO': 'ℹ️ ', 'SUCCESS': '✅', 'WARNING': '⚠️ ', 'ERROR': '❌'}
        print(f"[{timestamp}] {prefix.get(level, '')} {message}")
    
    def verifier_donnees_existantes(self):
        """Vérifie si des données existent déjà pour aujourd'hui."""
        count = self.collection.count_documents({
            'source': 'BRVM',
            'ts': self.date_collecte,
            'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
        })
        
        if count > 0:
            self.log(f"✅ {count} observations réelles déjà présentes pour {self.date_collecte}", 'SUCCESS')
            return True
        return False
    
    def strategie_1_scraping_production(self):
        """Stratégie 1 : Scraping du site BRVM (données réelles)."""
        self.log("Tentative stratégie 1 : Scraping site BRVM...")
        self.strategies_tentees.append('scraping')
        
        try:
            # Importer le scraper production
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'connectors'))
            
            try:
                from brvm_scraper_production import scraper_brvm_production
                
                self.log("Exécution du scraper production...")
                resultats = scraper_brvm_production()
                
                if resultats and len(resultats) > 0:
                    self.log(f"✅ Scraping réussi : {len(resultats)} observations", 'SUCCESS')
                    self.observations_collectees = resultats
                    return True
                else:
                    self.log("⚠️  Scraping n'a retourné aucune donnée", 'WARNING')
                    return False
                    
            except ImportError as e:
                self.log(f"⚠️  Module scraper non disponible : {e}", 'WARNING')
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur scraping : {e}", 'ERROR')
            return False
    
    def strategie_2_saisie_manuelle(self):
        """Stratégie 2 : Demander saisie manuelle (données réelles)."""
        self.log("Tentative stratégie 2 : Saisie manuelle...")
        self.strategies_tentees.append('saisie_manuelle')
        
        print("\n" + "=" * 80)
        print("📝 SAISIE MANUELLE DES COURS BRVM")
        print("=" * 80)
        print(f"\n🔴 IMPORTANT : Saisir UNIQUEMENT les cours officiels du {self.date_collecte}")
        print("   Source : https://www.brvm.org/fr/investir/cours-et-cotations\n")
        
        response = input("Avez-vous les cours officiels à saisir maintenant ? (y/n) : ").strip().lower()
        
        if response != 'y':
            self.log("❌ Saisie manuelle annulée par l'utilisateur", 'ERROR')
            return False
        
        # Lancer le script de saisie manuelle
        try:
            self.log("Lancement du script de saisie manuelle...")
            os.system('python mettre_a_jour_cours_brvm.py')
            
            # Vérifier si des données ont été ajoutées
            if self.verifier_donnees_existantes():
                self.log("✅ Saisie manuelle réussie", 'SUCCESS')
                return True
            else:
                self.log("⚠️  Aucune donnée saisie", 'WARNING')
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur saisie manuelle : {e}", 'ERROR')
            return False
    
    def sauvegarder_observations(self):
        """Sauvegarde les observations collectées dans MongoDB."""
        if not self.observations_collectees:
            return 0
        
        try:
            from pymongo import UpdateOne
            
            bulk_ops = []
            for obs in self.observations_collectees:
                filter_query = {
                    'source': obs['source'],
                    'dataset': obs['dataset'],
                    'key': obs['key'],
                    'ts': obs['ts']
                }
                
                bulk_ops.append(
                    UpdateOne(
                        filter_query,
                        {'$set': obs},
                        upsert=True
                    )
                )
            
            if bulk_ops:
                result = self.collection.bulk_write(bulk_ops, ordered=False)
                total = result.upserted_count + result.modified_count
                self.log(f"✅ {total} observations sauvegardées dans MongoDB", 'SUCCESS')
                return total
            
            return 0
            
        except Exception as e:
            self.log(f"❌ Erreur sauvegarde : {e}", 'ERROR')
            return 0
    
    def collecter(self):
        """Exécute la collecte avec stratégies successives - DONNÉES RÉELLES UNIQUEMENT."""
        print("\n" + "=" * 80)
        print("🤖 COLLECTEUR QUOTIDIEN INTELLIGENT BRVM")
        print("=" * 80)
        print(f"\n📅 Date de collecte : {self.date_collecte}")
        print("🔴 Politique : DONNÉES RÉELLES UNIQUEMENT - Aucune estimation\n")
        
        # Vérifier si déjà collecté
        if self.verifier_donnees_existantes():
            print("\n" + "=" * 80)
            print("✅ Collecte déjà effectuée pour aujourd'hui")
            print("=" * 80 + "\n")
            return True
        
        self.log("Aucune donnée existante, lancement des stratégies de collecte...")
        
        # STRATÉGIE 1 : Scraping
        if self.strategie_1_scraping_production():
            saved = self.sauvegarder_observations()
            if saved > 0:
                print("\n" + "=" * 80)
                print(f"✅ COLLECTE RÉUSSIE via SCRAPING")
                print(f"   {saved} observations réelles sauvegardées")
                print("=" * 80 + "\n")
                return True
        
        # STRATÉGIE 2 : Saisie manuelle
        self.log("Scraping échoué, passage à la saisie manuelle...", 'WARNING')
        if self.strategie_2_saisie_manuelle():
            print("\n" + "=" * 80)
            print(f"✅ COLLECTE RÉUSSIE via SAISIE MANUELLE")
            print("=" * 80 + "\n")
            return True
        
        # ÉCHEC : Aucune stratégie n'a fonctionné
        print("\n" + "=" * 80)
        print("❌ COLLECTE ÉCHOUÉE - AUCUNE DONNÉE COLLECTÉE")
        print("=" * 80)
        print("\n🔴 AUCUNE DONNÉE N'A ÉTÉ AJOUTÉE (politique données réelles uniquement)")
        print("\n💡 Actions possibles :")
        print("   1. Vérifier l'accès au site BRVM : https://www.brvm.org")
        print("   2. Exécuter manuellement : python mettre_a_jour_cours_brvm.py")
        print("   3. Importer depuis CSV : python collecter_csv_automatique.py")
        print("   4. Ré-essayer plus tard : python collecter_quotidien_intelligent.py")
        print("\n⚠️  Le système n'ajoute JAMAIS de données estimées ou simulées")
        print("=" * 80 + "\n")
        
        return False
    
    def generer_rapport(self):
        """Génère un rapport de collecte."""
        print("\n📊 RAPPORT DE COLLECTE")
        print("-" * 80)
        print(f"Date : {self.date_collecte}")
        print(f"Stratégies tentées : {', '.join(self.strategies_tentees) if self.strategies_tentees else 'Aucune'}")
        
        # Compter observations du jour
        count_jour = self.collection.count_documents({
            'source': 'BRVM',
            'ts': self.date_collecte,
            'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
        })
        
        print(f"Observations réelles aujourd'hui : {count_jour}")
        
        # Compter total observations réelles
        count_total = self.collection.count_documents({
            'source': 'BRVM',
            'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
        })
        
        print(f"Total observations réelles (historique) : {count_total}")
        print("-" * 80 + "\n")

def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Collecteur quotidien intelligent BRVM - Données réelles uniquement'
    )
    parser.add_argument(
        '--rapport',
        action='store_true',
        help='Afficher uniquement le rapport (sans collecter)'
    )
    
    args = parser.parse_args()
    
    collecteur = CollecteurQuotidienBRVM()
    
    if args.rapport:
        collecteur.generer_rapport()
    else:
        try:
            success = collecteur.collecter()
            collecteur.generer_rapport()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\n⚠️  Collecte interrompue par l'utilisateur")
            sys.exit(130)
        except Exception as e:
            print(f"\n❌ Erreur fatale : {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    main()
