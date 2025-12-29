#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecteur Automatique de Fichiers CSV vers MongoDB
Scanne et importe tous les CSV dans centralisation_db avec structure normalisée
"""

import os
import sys
import io

# Fix encodage Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import django
import csv
import glob
from datetime import datetime
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from pymongo.errors import BulkWriteError

class CollecteurCSV:
    """Collecte et importe automatiquement les fichiers CSV dans MongoDB."""
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
        self.collection = self.db.curated_observations
        self.stats = {
            'fichiers_trouves': 0,
            'fichiers_importes': 0,
            'observations_creees': 0,
            'observations_maj': 0,
            'erreurs': 0
        }
    
    def detecter_type_csv(self, filepath):
        """Détecte le type de fichier CSV selon son nom et contenu."""
        filename = os.path.basename(filepath).lower()
        
        # Patterns de détection
        if 'brvm' in filename or 'bulletin' in filename or 'cotation' in filename:
            return 'BRVM_STOCK_PRICE'
        elif 'worldbank' in filename or 'wb_' in filename or 'banque_mondiale' in filename:
            return 'WORLDBANK_INDICATOR'
        elif 'imf' in filename or 'fmi' in filename:
            return 'IMF_SERIES'
        elif 'afdb' in filename or 'bad' in filename:
            return 'AFDB_INDICATOR'
        elif 'un_sdg' in filename or 'odd' in filename or 'sdg' in filename:
            return 'UN_SDG_INDICATOR'
        elif 'publication' in filename or 'rapport' in filename or 'document' in filename:
            return 'BRVM_PUBLICATION'
        
        # Analyse du header pour détection automatique
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = [h.lower().strip() for h in reader.fieldnames]
                
                # BRVM: DATE, SYMBOL, CLOSE, VOLUME
                if all(h in headers for h in ['symbol', 'close']) or 'cours' in headers:
                    return 'BRVM_STOCK_PRICE'
                
                # World Bank: country, indicator, year, value
                if 'indicator' in headers and 'country' in headers:
                    return 'WORLDBANK_INDICATOR'
                
                # Generic time series
                if 'date' in headers or 'year' in headers:
                    return 'GENERIC_TIMESERIES'
        except Exception:
            pass
        
        return 'UNKNOWN'
    
    def parser_brvm_csv(self, filepath):
        """Parse un CSV de données BRVM (cours d'actions)."""
        observations = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Mapping flexible des colonnes
                date = row.get('DATE') or row.get('date') or row.get('Date')
                symbol = row.get('SYMBOL') or row.get('symbol') or row.get('Symbole')
                close = row.get('CLOSE') or row.get('close') or row.get('Cours')
                volume = row.get('VOLUME') or row.get('volume') or row.get('Volume')
                variation = row.get('VARIATION') or row.get('variation') or row.get('Var')
                
                if not date or not symbol or not close:
                    continue
                
                # Normalisation
                try:
                    close_value = float(close)
                    volume_value = int(volume) if volume else 0
                    variation_value = float(variation) if variation else 0.0
                except ValueError:
                    continue
                
                obs = {
                    'source': 'BRVM',
                    'dataset': 'STOCK_PRICE',
                    'key': symbol.strip().upper(),
                    'ts': date.strip(),
                    'value': close_value,
                    'attrs': {
                        'close': close_value,
                        'volume': volume_value,
                        'variation_pct': variation_value,
                        'data_quality': 'REAL_MANUAL',
                        'import_source': 'CSV_AUTO',
                        'import_file': os.path.basename(filepath),
                        'import_timestamp': datetime.now().isoformat()
                    }
                }
                
                observations.append(obs)
        
        return observations
    
    def parser_worldbank_csv(self, filepath):
        """Parse un CSV de données World Bank."""
        observations = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                country = row.get('country') or row.get('Country')
                indicator = row.get('indicator') or row.get('Indicator')
                year = row.get('year') or row.get('Year')
                value = row.get('value') or row.get('Value')
                
                if not all([country, indicator, year, value]):
                    continue
                
                try:
                    value_float = float(value)
                except ValueError:
                    continue
                
                obs = {
                    'source': 'WorldBank',
                    'dataset': 'INDICATOR',
                    'key': f"{country}_{indicator}",
                    'ts': f"{year}-12-31",
                    'value': value_float,
                    'attrs': {
                        'country_code': country.strip().upper(),
                        'indicator_code': indicator.strip(),
                        'year': int(year),
                        'data_quality': 'REAL_MANUAL',
                        'import_source': 'CSV_AUTO',
                        'import_file': os.path.basename(filepath),
                        'import_timestamp': datetime.now().isoformat()
                    }
                }
                
                observations.append(obs)
        
        return observations
    
    def parser_generic_csv(self, filepath):
        """Parse un CSV générique avec détection automatique."""
        observations = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in reader.fieldnames]
            
            # Détecter les colonnes clés
            date_col = next((h for h in headers if h.lower() in ['date', 'year', 'ts', 'timestamp']), None)
            key_col = next((h for h in headers if h.lower() in ['key', 'symbol', 'code', 'id', 'name']), None)
            value_col = next((h for h in headers if h.lower() in ['value', 'close', 'price', 'amount']), None)
            
            if not all([date_col, key_col, value_col]):
                print(f"⚠️  Impossible de détecter les colonnes clés dans {filepath}")
                return observations
            
            for row in reader:
                date_val = row.get(date_col)
                key_val = row.get(key_col)
                value_val = row.get(value_col)
                
                if not all([date_val, key_val, value_val]):
                    continue
                
                try:
                    value_float = float(value_val)
                except ValueError:
                    continue
                
                # Collecter tous les autres attributs
                attrs = {
                    'data_quality': 'REAL_MANUAL',
                    'import_source': 'CSV_AUTO',
                    'import_file': os.path.basename(filepath),
                    'import_timestamp': datetime.now().isoformat()
                }
                
                for header in headers:
                    if header not in [date_col, key_col, value_col]:
                        attrs[header.lower()] = row[header]
                
                obs = {
                    'source': 'CSV_IMPORT',
                    'dataset': 'GENERIC',
                    'key': str(key_val).strip(),
                    'ts': str(date_val).strip(),
                    'value': value_float,
                    'attrs': attrs
                }
                
                observations.append(obs)
        
        return observations
    
    def importer_observations(self, observations):
        """Importe les observations dans MongoDB avec upsert."""
        if not observations:
            return 0, 0
        
        try:
            from pymongo import UpdateOne
            
            # Créer les opérations bulk avec UpdateOne
            bulk_ops = []
            for obs in observations:
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
            
            result = self.collection.bulk_write(bulk_ops, ordered=False)
            
            return result.upserted_count, result.modified_count
        
        except BulkWriteError as e:
            # Certaines opérations ont réussi
            upserted = e.details.get('nUpserted', 0)
            modified = e.details.get('nModified', 0)
            return upserted, modified
        
        except Exception as e:
            print(f"❌ Erreur lors de l'import: {e}")
            return 0, 0
    
    def scanner_et_importer(self, dossier='.', pattern='**/*.csv', dry_run=False):
        """Scanne récursivement et importe tous les CSV."""
        print("=" * 80)
        print("📥 COLLECTEUR AUTOMATIQUE DE FICHIERS CSV → MongoDB")
        print("=" * 80)
        print(f"\n🔍 Dossier de scan : {os.path.abspath(dossier)}")
        print(f"📋 Pattern : {pattern}")
        print(f"🧪 Mode : {'DRY-RUN (simulation)' if dry_run else 'IMPORT RÉEL'}")
        print()
        
        # Trouver tous les CSV
        base_path = Path(dossier)
        csv_files = list(base_path.glob(pattern))
        
        # Exclure les fichiers système/temporaires
        csv_files = [
            f for f in csv_files 
            if not any(part.startswith('.') or part.startswith('~') 
                      for part in f.parts)
        ]
        
        self.stats['fichiers_trouves'] = len(csv_files)
        
        if not csv_files:
            print("❌ Aucun fichier CSV trouvé !")
            return
        
        print(f"✅ {len(csv_files)} fichier(s) CSV trouvé(s)\n")
        print("-" * 80)
        
        # Traiter chaque fichier
        for i, csv_file in enumerate(csv_files, 1):
            filepath = str(csv_file)
            filename = os.path.basename(filepath)
            
            print(f"\n📄 [{i}/{len(csv_files)}] {filename}")
            print(f"   📍 {filepath}")
            
            # Détecter le type
            csv_type = self.detecter_type_csv(filepath)
            print(f"   🔍 Type détecté : {csv_type}")
            
            # Parser selon le type
            try:
                if csv_type == 'BRVM_STOCK_PRICE':
                    observations = self.parser_brvm_csv(filepath)
                elif csv_type == 'WORLDBANK_INDICATOR':
                    observations = self.parser_worldbank_csv(filepath)
                elif csv_type in ['GENERIC_TIMESERIES', 'UNKNOWN']:
                    observations = self.parser_generic_csv(filepath)
                else:
                    print(f"   ⚠️  Type non supporté : {csv_type}")
                    continue
                
                nb_obs = len(observations)
                print(f"   📊 {nb_obs} observation(s) parsée(s)")
                
                if nb_obs == 0:
                    print(f"   ⚠️  Aucune donnée valide trouvée")
                    continue
                
                # Import (ou simulation)
                if not dry_run:
                    created, updated = self.importer_observations(observations)
                    print(f"   ✅ Import : {created} créée(s), {updated} mise(s) à jour")
                    
                    self.stats['fichiers_importes'] += 1
                    self.stats['observations_creees'] += created
                    self.stats['observations_maj'] += updated
                else:
                    print(f"   🧪 DRY-RUN : Import simulé")
                    self.stats['fichiers_importes'] += 1
                
            except Exception as e:
                print(f"   ❌ Erreur : {e}")
                self.stats['erreurs'] += 1
                import traceback
                traceback.print_exc()
        
        # Rapport final
        print("\n" + "=" * 80)
        print("📊 RAPPORT FINAL")
        print("=" * 80)
        print(f"\n✅ Fichiers trouvés : {self.stats['fichiers_trouves']}")
        print(f"✅ Fichiers importés : {self.stats['fichiers_importes']}")
        
        if not dry_run:
            print(f"✅ Observations créées : {self.stats['observations_creees']}")
            print(f"✅ Observations mises à jour : {self.stats['observations_maj']}")
            total_obs = self.stats['observations_creees'] + self.stats['observations_maj']
            print(f"📈 Total observations traitées : {total_obs}")
        
        if self.stats['erreurs'] > 0:
            print(f"⚠️  Erreurs : {self.stats['erreurs']}")
        
        print("\n" + "=" * 80)
        
        if dry_run:
            print("\n💡 Pour importer réellement, relancer sans --dry-run")

def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Collecte automatique de fichiers CSV vers MongoDB'
    )
    parser.add_argument(
        '--dossier', '-d',
        default='.',
        help='Dossier de scan (défaut: répertoire courant)'
    )
    parser.add_argument(
        '--pattern', '-p',
        default='**/*.csv',
        help='Pattern de recherche (défaut: **/*.csv)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mode simulation (ne modifie pas la base)'
    )
    parser.add_argument(
        '--exclude-bulletins',
        action='store_true',
        help='Exclure le dossier bulletins_brvm/'
    )
    
    args = parser.parse_args()
    
    # Ajuster le pattern si exclusion
    if args.exclude_bulletins:
        print("⚠️  Exclusion du dossier bulletins_brvm/")
    
    collecteur = CollecteurCSV()
    collecteur.scanner_et_importer(
        dossier=args.dossier,
        pattern=args.pattern,
        dry_run=args.dry_run
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur fatale : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
