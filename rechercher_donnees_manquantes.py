#!/usr/bin/env python3
"""
Rechercher les 364 données BRVM manquantes (552 - 188 = 364)
Sources possibles :
- Backups MongoDB
- Fichiers CSV
- Logs de collecte
- HTML scrapes sauvegardés
- Autres collections MongoDB
"""

import pymongo
from datetime import datetime
import os
import glob
import json
import re

def rechercher_toutes_sources():
    """Chercher exhaustivement toutes les sources de données BRVM"""
    
    print(f"[RECHERCHE DONNÉES BRVM MANQUANTES]")
    print(f"Objectif: Retrouver 364 observations (552 - 188 = 364)")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    sources_trouvees = []
    
    # 1. Vérifier tous les fichiers CSV
    print("[1/6] Recherche fichiers CSV...")
    csv_files = glob.glob("**/*.csv", recursive=True)
    
    for csv_file in csv_files:
        if any(keyword in csv_file.lower() for keyword in ['brvm', 'cours', 'stock', 'bourse', 'action']):
            try:
                size = os.path.getsize(csv_file)
                if size > 0:
                    print(f"  Trouvé: {csv_file} ({size} bytes)")
                    sources_trouvees.append({
                        'type': 'CSV',
                        'path': csv_file,
                        'size': size
                    })
            except:
                pass
    
    # 2. Vérifier fichiers HTML de scrapes
    print(f"\n[2/6] Recherche fichiers HTML de scrapes...")
    html_files = glob.glob("**/*.html", recursive=True)
    
    for html_file in html_files:
        if 'brvm' in html_file.lower():
            try:
                size = os.path.getsize(html_file)
                if size > 10000:  # Au moins 10KB
                    print(f"  Trouvé: {html_file} ({size} bytes)")
                    sources_trouvees.append({
                        'type': 'HTML',
                        'path': html_file,
                        'size': size
                    })
            except:
                pass
    
    # 3. Vérifier fichiers JSON
    print(f"\n[3/6] Recherche fichiers JSON...")
    json_files = glob.glob("**/*.json", recursive=True)
    
    for json_file in json_files:
        if any(keyword in json_file.lower() for keyword in ['brvm', 'stock', 'cours']):
            try:
                size = os.path.getsize(json_file)
                if size > 0:
                    print(f"  Trouvé: {json_file} ({size} bytes)")
                    sources_trouvees.append({
                        'type': 'JSON',
                        'path': json_file,
                        'size': size
                    })
            except:
                pass
    
    # 4. Vérifier fichiers texte avec données
    print(f"\n[4/6] Recherche fichiers TXT avec données...")
    txt_files = glob.glob("**/*.txt", recursive=True)
    
    for txt_file in txt_files:
        if any(keyword in txt_file.lower() for keyword in ['brvm', 'stock', 'cours', 'collecte', 'scrape']):
            try:
                size = os.path.getsize(txt_file)
                if size > 1000:
                    print(f"  Trouvé: {txt_file} ({size} bytes)")
                    sources_trouvees.append({
                        'type': 'TXT',
                        'path': txt_file,
                        'size': size
                    })
            except:
                pass
    
    # 5. Chercher dans TOUTES les collections MongoDB
    print(f"\n[5/6] Recherche dans MongoDB (toutes collections)...")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['centralisation_db']
    
    collections = db.list_collection_names()
    
    for coll_name in collections:
        coll = db[coll_name]
        
        # Chercher documents avec prix BRVM typiques
        for price_field in ['value', 'prix', 'close', 'cours', 'prix_cloture', 'price']:
            try:
                # Prix BRVM range 100-100,000 FCFA
                count = coll.count_documents({
                    price_field: {'$gte': 100, '$lte': 100000, '$type': 'double'}
                })
                
                if count > 0:
                    print(f"  {coll_name}.{price_field}: {count} documents")
                    
                    # Vérifier si ce sont des données BRVM
                    sample = coll.find_one({price_field: {'$gte': 100, '$lte': 100000}})
                    if sample:
                        # Compter documents avec timestamps récents
                        import_count = 0
                        for ts_field in ['ts', 'timestamp', 'date', 'fetched_at', 'created_at']:
                            if ts_field in sample:
                                try:
                                    recent = coll.count_documents({
                                        price_field: {'$gte': 100, '$lte': 100000},
                                        ts_field: {'$exists': True}
                                    })
                                    if recent > import_count:
                                        import_count = recent
                                except:
                                    pass
                        
                        if import_count > 0:
                            sources_trouvees.append({
                                'type': 'MongoDB',
                                'collection': coll_name,
                                'field': price_field,
                                'count': import_count
                            })
            except:
                pass
    
    # 6. Vérifier logs de backup/dumps MongoDB
    print(f"\n[6/6] Recherche dumps/backups MongoDB...")
    
    dump_patterns = ['**/*dump*', '**/*backup*', '**/*bson', '**/*mongodump*']
    for pattern in dump_patterns:
        dumps = glob.glob(pattern, recursive=True)
        for dump in dumps:
            if os.path.isfile(dump):
                size = os.path.getsize(dump)
                if size > 0:
                    print(f"  Trouvé: {dump} ({size} bytes)")
                    sources_trouvees.append({
                        'type': 'DUMP',
                        'path': dump,
                        'size': size
                    })
    
    client.close()
    
    # Résumé
    print(f"\n[RÉSUMÉ SOURCES TROUVÉES]")
    print(f"Total sources: {len(sources_trouvees)}\n")
    
    par_type = {}
    for src in sources_trouvees:
        type_src = src['type']
        if type_src not in par_type:
            par_type[type_src] = []
        par_type[type_src].append(src)
    
    for type_src, sources in par_type.items():
        print(f"{type_src}: {len(sources)} sources")
        for src in sources[:5]:  # Premiers 5
            if 'path' in src:
                print(f"  - {src['path']}")
            elif 'collection' in src:
                print(f"  - {src['collection']} ({src['count']} docs)")
    
    # Sauvegarder pour analyse
    with open('sources_donnees_brvm.json', 'w', encoding='utf-8') as f:
        json.dump(sources_trouvees, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Sources sauvegardées dans: sources_donnees_brvm.json")
    
    return sources_trouvees

if __name__ == "__main__":
    try:
        sources = rechercher_toutes_sources()
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
