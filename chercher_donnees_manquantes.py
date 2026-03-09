#!/usr/bin/env python3
"""
Recherche ciblée des données pour période manquante : 2025-12-13 → 2026-01-06
"""
import os
import csv
from pathlib import Path
from datetime import datetime, timedelta

print("\n" + "="*100)
print("          RECHERCHE DONNÉES PÉRIODE MANQUANTE : 2025-12-13 → 2026-01-06")
print("="*100 + "\n")

base_dir = Path(r"e:\DISQUE C\Desktop\Implementation plateforme")

# Chercher TOUS les fichiers CSV
tous_csv = list(base_dir.rglob("*.csv"))

print(f"📂 Total fichiers CSV trouvés : {len(tous_csv)}\n")
print(f"🎯 RECHERCHE FICHIERS CONTENANT DÉCEMBRE 2025 ou JANVIER 2026 :\n")
print("-"*100)

fichiers_pertinents = []

for fichier in tous_csv:
    # Skip gros fichiers ou dossiers système
    if fichier.stat().st_size > 10*1024*1024:  # Skip > 10MB
        continue
    
    if 'node_modules' in str(fichier) or '.git' in str(fichier):
        continue
    
    try:
        # Lire les premières lignes
        with open(fichier, 'r', encoding='utf-8', errors='ignore') as f:
            contenu = f.read(5000)  # Premiers 5000 caractères
        
        # Rechercher des patterns de dates
        has_dec_2025 = '2025-12' in contenu or '12-2025' in contenu or '12/2025' in contenu or 'dec-2025' in contenu.lower() or 'déc-2025' in contenu.lower()
        has_jan_2026 = '2026-01' in contenu or '01-2026' in contenu or '01/2026' in contenu or 'jan-2026' in contenu.lower()
        
        if has_dec_2025 or has_jan_2026:
            # Compter les lignes
            with open(fichier, 'r', encoding='utf-8', errors='ignore') as f:
                nb_lignes = sum(1 for _ in f) - 1  # -1 pour header
            
            # Vérifier si c'est un fichier de données BRVM
            with open(fichier, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().lower()
                is_brvm = any(x in first_line for x in ['ticker', 'symbole', 'action', 'cours', 'brvm'])
            
            fichiers_pertinents.append({
                'chemin': fichier,
                'nom': fichier.name,
                'dec_2025': has_dec_2025,
                'jan_2026': has_jan_2026,
                'lignes': nb_lignes,
                'is_brvm': is_brvm,
                'taille': fichier.stat().st_size
            })
    
    except Exception as e:
        continue

# Trier par pertinence
fichiers_pertinents.sort(key=lambda x: (x['is_brvm'], x['dec_2025'] and x['jan_2026'], x['lignes']), reverse=True)

if fichiers_pertinents:
    print(f"✅ {len(fichiers_pertinents)} fichiers potentiellement pertinents :\n")
    
    for i, f in enumerate(fichiers_pertinents[:20], 1):  # Top 20
        statut = "🎯" if f['is_brvm'] else "📄"
        periode = []
        if f['dec_2025']:
            periode.append("DEC-2025")
        if f['jan_2026']:
            periode.append("JAN-2026")
        periode_str = " + ".join(periode)
        
        chemin_relatif = str(f['chemin'].relative_to(base_dir))
        
        print(f"{statut} {i:2d}. {f['nom']}")
        print(f"       Chemin  : {chemin_relatif}")
        print(f"       Période : {periode_str}")
        print(f"       Lignes  : {f['lignes']:,}")
        print(f"       Taille  : {f['taille']:,} bytes")
        print()
else:
    print("❌ Aucun fichier CSV trouvé pour cette période\n")

# Chercher aussi dans MongoDB
print("="*100)
print("🔍 VÉRIFICATION BASE DE DONNÉES MONGODB :\n")
print("-"*100)

try:
    import sys
    sys.path.insert(0, str(base_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plateforme_centralisation.settings")
    import django
    django.setup()
    from plateforme_centralisation.mongo import get_mongo_db
    
    _, db = get_mongo_db()
    
    # Chercher toutes les données entre 2025-12-13 et 2026-01-06
    pipeline = [
        {'$match': {
            'dataset': 'STOCK_PRICE',
            'ts': {
                '$gte': '2025-12-13',
                '$lte': '2026-01-06'
            }
        }},
        {'$group': {
            '_id': {'source': '$source', 'ts': '$ts'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id.ts': 1}}
    ]
    
    resultats = list(db.curated_observations.aggregate(pipeline))
    
    if resultats:
        print(f"✅ Données trouvées en base pour cette période :\n")
        current_source = None
        for r in resultats:
            source = r['_id']['source']
            date = r['_id']['ts']
            count = r['count']
            
            if source != current_source:
                print(f"\n  📁 Source : {source}")
                current_source = source
            
            print(f"     {date} : {count:>3} observations")
        
        total_periode = sum(r['count'] for r in resultats)
        print(f"\n  Total période manquante : {total_periode:,} observations")
    else:
        print("❌ Aucune donnée trouvée en base pour cette période")

except Exception as e:
    print(f"❌ Erreur lors de la vérification MongoDB : {e}")

print("\n" + "="*100)
print("📋 RECOMMANDATIONS :")
print("-"*100)

if fichiers_pertinents:
    print("\n✅ FICHIERS CSV À IMPORTER :\n")
    for f in fichiers_pertinents[:10]:
        if f['is_brvm']:
            chemin_relatif = str(f['chemin'].relative_to(base_dir))
            print(f"   • {chemin_relatif}")
    
    print("\n💡 Utiliser le script d'importation pour restaurer ces fichiers")
else:
    print("\n❌ Aucun backup CSV trouvé pour cette période")
    print("\n💡 OPTIONS :")
    print("   1. Vérifier s'il existe un backup MongoDB (dump)")
    print("   2. Vérifier si la BRVM permet de télécharger l'historique")
    print("   3. Accepter la perte de ces 25 jours")

print("\n" + "="*100 + "\n")
