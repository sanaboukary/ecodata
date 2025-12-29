#!/usr/bin/env python3
"""
📊 RÉSUMÉ COMPLET SYSTÈME PUBLICATIONS + ÉTAT DES DONNÉES
"""
import os
import sys
import io
import django

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'plateforme_centralisation.settings'
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

print("\n" + "="*80)
print("📊 ÉTAT COMPLET DU SYSTÈME - 22 DÉCEMBRE 2025")
print("="*80)
print()

client, db = get_mongo_db()

# 1. DONNÉES BRVM
print("1️⃣  DONNÉES BRVM (COURS & PRIX)")
print("-" * 80)

brvm_total = db.curated_observations.count_documents({'source': 'BRVM'})
brvm_real = db.curated_observations.count_documents({
    'source': 'BRVM',
    'data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})
actions = len(db.curated_observations.distinct('key', {'source': 'BRVM'}))

print(f"✓ Total observations: {brvm_total:,}")
print(f"✓ Données RÉELLES: {brvm_real:,} ({brvm_real/brvm_total*100:.1f}%)")
print(f"✓ Actions distinctes: {actions}")

# Sample
sample = db.curated_observations.find_one({'source': 'BRVM'})
if sample:
    dates = list(db.curated_observations.aggregate([
        {'$match': {'source': 'BRVM'}},
        {'$group': {'_id': None, 'min': {'$min': '$ts'}, 'max': {'$max': '$ts'}}}
    ]))
    if dates:
        print(f"✓ Période: {dates[0]['min']} → {dates[0]['max']}")

print()

# 2. PUBLICATIONS BRVM
print("2️⃣  PUBLICATIONS BRVM (NLP)")
print("-" * 80)

bulletins = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'BULLETINS_OFFICIELS'
})

bulletins_nlp = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'BULLETINS_OFFICIELS',
    'attrs.sentiment_label': {'$exists': True}
})

ag = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'CONVOCATIONS_AG'
})

rapports = db.curated_observations.count_documents({
    'source': 'BRVM_PUBLICATIONS',
    'dataset': 'RAPPORTS_SOCIETES'
})

print(f"✓ Bulletins officiels: {bulletins} (NLP: {bulletins_nlp})")
print(f"✓ Convocations AG: {ag}")
print(f"✓ Rapports sociétés: {rapports}")
print(f"✓ Total publications: {bulletins + ag + rapports}")

print()

# 3. INFRASTRUCTURE
print("3️⃣  INFRASTRUCTURE CRÉÉE")
print("-" * 80)

fichiers_cles = [
    ('parser_bulletins_cote.py', 'Parser bulletins officiels'),
    ('parser_convocations_ag.py', 'Parser convocations AG'),
    ('analyse_nlp_production.py', 'Analyse NLP sentiment'),
    ('generer_recommandations_hebdo.py', 'Générateur Top 5'),
    ('afficher_dashboard_hebdo.py', 'Dashboard visualisation')
]

for fichier, desc in fichiers_cles:
    if os.path.exists(fichier):
        print(f"✓ {desc:<35} ({fichier})")
    else:
        print(f"✗ {desc:<35} (MANQUANT)")

print()

# 4. PROCHAINES ÉTAPES
print("4️⃣  TODOS RESTANTS")
print("-" * 80)

todos = [
    ("✓", "Scraper publications (28 rapports + 10 bulletins + 7 AG)"),
    ("✓", "Infrastructure NLP sentiment (analyse_nlp_production.py)"),
    ("✓", "Données BRVM 60 jours (5,971 observations, 118 actions)"),
    ("⚠️ ", "Générateur recommandations (bug: fichiers JSON vides)"),
    ("⬜", "Intégrer scores NLP dans recommandations"),
    ("⬜", "Backtesting précision 85-95%"),
    ("⬜", "Automatisation Airflow DAG quotidien")
]

for status, desc in todos:
    print(f"{status} {desc}")

print()

# 5. DIAGNOSTIC PROBLÈME ACTUEL
print("5️⃣  DIAGNOSTIC PROBLÈME GÉNÉRATEUR")
print("-" * 80)

# Test rapide une action
test = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': 'ECOC.BC',
    'data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
}).limit(10))

print(f"Test ECOC.BC: {len(test)} observations trouvées")

if len(test) > 0:
    print(f"  ✓ Exemple: {test[0]['ts']}: {test[0]['value']:,.0f} FCFA")
    print(f"  ✓ Structure OK - data_quality = {test[0]['data_quality']}")
    print()
    print("🔍 CAUSE PROBABLE:")
    print("  Le générateur fonctionne MAIS ne trouve pas assez de momentum")
    print("  OU il y a un bug dans le calcul des scores")
else:
    print(f"  ✗ PROBLÈME: Aucune donnée trouvée avec ce filtre")
    print()
    print("🔍 SOLUTION:")
    print("  Vérifier la query dans generer_recommandations_hebdo.py")

print()

# 6. ACTION IMMÉDIATE
print("6️⃣  ACTION RECOMMANDÉE")
print("-" * 80)
print()
print("Option A: DEBUG GÉNÉRATEUR")
print("  → python test_reco_simple.py")
print("  → Identifier pourquoi aucun résultat généré")
print()
print("Option B: VERSION SIMPLIFIÉE FONCTIONNELLE")
print("  → Créer générateur sans dépendances complexes")
print("  → Utiliser seulement momentum 5 jours")
print()
print("Option C: UTILISER ANALYSE IA EXISTANTE")
print("  → python lancer_analyse_ia_complete.py")
print("  → 14 BUY signals déjà générés (PALC +51%, SMBC +49%)")
print()

client.close()

print("="*80)
print()
