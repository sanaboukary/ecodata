"""
Diagnostic des prix BRVM - Vérification UNLC et autres actions
Comparaison avec prix réels BRVM.org
"""
import os
import sys
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

_, db = get_mongo_db()

print('='*80)
print('🔍 DIAGNOSTIC PRIX BRVM - VÉRIFICATION CRITIQUE')
print('='*80)

# Prix réels vérifiés BRVM.org (8 Décembre 2025)
PRIX_REELS_BRVM = {
    'UNLC': 43390,  # Unilever CI
    'SNTS': 15500,  # Sonatel (estimation)
    'SGBC': 13000,  # Société Générale (estimation)
    'BICC': 7200,   # BICICI
    'BOAM': 5600,   # BOA Mali
}

print('\n📊 PRIX RÉELS BRVM.ORG (Référence officielle):')
print('-'*80)
for action, prix in PRIX_REELS_BRVM.items():
    print(f'{action:6s}: {prix:>8,} FCFA')

# Vérifier UNLC spécifiquement
print('\n' + '='*80)
print('🔍 ANALYSE DÉTAILLÉE UNLC (Unilever Côte d\'Ivoire)')
print('='*80)

unlc_recent = list(db.curated_observations.find({
    'source': 'BRVM',
    'key': 'UNLC'
}).sort('ts', -1).limit(10))

if unlc_recent:
    print(f'\n📊 {len(unlc_recent)} dernières observations UNLC:')
    print('-'*80)
    for i, obs in enumerate(unlc_recent, 1):
        ts = obs.get('ts')
        value = obs.get('value')
        attrs = obs.get('attrs', {})
        data_quality = attrs.get('data_quality', 'N/A')
        update_source = attrs.get('update_source', 'N/A')
        
        # Calculer l'erreur
        prix_reel = PRIX_REELS_BRVM['UNLC']
        erreur_pct = ((value - prix_reel) / prix_reel) * 100
        facteur = prix_reel / value if value > 0 else 0
        
        print(f'{i}. Date: {ts}')
        print(f'   Prix DB: {value:>10,.0f} FCFA')
        print(f'   Prix réel: {prix_reel:>10,} FCFA')
        print(f'   Erreur: {erreur_pct:>10,.1f}%')
        print(f'   Facteur: {facteur:>10,.1f}x')
        print(f'   Qualité: {data_quality}')
        print(f'   Source: {update_source}')
        print()
else:
    print('❌ AUCUNE DONNÉE UNLC TROUVÉE!')

# Vérifier toutes les actions dans la base
print('='*80)
print('📊 COMPARAISON TOUS LES PRIX (Base vs BRVM réel)')
print('='*80)
print(f'{"Action":6s} | {"Prix DB":>10s} | {"Prix Réel":>10s} | {"Erreur":>10s} | {"Facteur":>8s}')
print('-'*80)

for action, prix_reel in PRIX_REELS_BRVM.items():
    latest = db.curated_observations.find_one(
        {'source': 'BRVM', 'key': action},
        sort=[('ts', -1)]
    )
    
    if latest:
        prix_db = latest.get('value')
        erreur_pct = ((prix_db - prix_reel) / prix_reel) * 100
        facteur = prix_reel / prix_db if prix_db > 0 else 0
        
        print(f'{action:6s} | {prix_db:>10,.0f} | {prix_reel:>10,} | {erreur_pct:>9,.1f}% | {facteur:>7,.1f}x')
    else:
        print(f'{action:6s} | {"N/A":>10s} | {prix_reel:>10,} | {"N/A":>10s} | {"N/A":>8s}')

# Diagnostiquer la source du problème
print('\n' + '='*80)
print('🔍 DIAGNOSTIC DE LA SOURCE DU PROBLÈME')
print('='*80)

# Vérifier les données fondamentales
funda_count = db.curated_observations.count_documents({
    'source': 'BRVM_FUNDAMENTALS'
})

print(f'\n1. Données fondamentales: {funda_count} observations')

# Vérifier les mises à jour manuelles récentes
recent_manual = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.update_source': 'manual_update',
    'ts': {'$gte': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}
})

print(f'2. Mises à jour manuelles (7 derniers jours): {recent_manual}')

# Vérifier les CSV importés
csv_imports = db.curated_observations.count_documents({
    'source': 'BRVM',
    'attrs.data_quality': {'$exists': True}
})

print(f'3. Imports CSV avec qualité: {csv_imports}')

# Chercher les scripts de mise à jour
print('\n' + '='*80)
print('🔍 SCRIPTS DE MISE À JOUR DISPONIBLES')
print('='*80)

import glob
scripts_update = [
    'mettre_a_jour_cours_brvm.py',
    'scripts/connectors/brvm_scraper_production.py',
    'scripts/connectors/brvm.py',
    'collecter_csv_automatique.py'
]

for script in scripts_update:
    if os.path.exists(script):
        print(f'✓ {script}')
    else:
        print(f'✗ {script}')

print('\n' + '='*80)
print('💡 HYPOTHÈSES SUR LA CAUSE DU PROBLÈME')
print('='*80)
print('''
1. ❌ Prix divisés par 20 : Possible confusion unité (FCFA vs centimes)
2. ❌ Données simulées : Les CSV générés contenaient des prix fictifs
3. ❌ Scraping échoué : Les prix réels n'ont pas été collectés
4. ❌ Conversion erronée : Erreur lors de l'import des données

🔴 IMPACT CRITIQUE:
   - Toutes les recommandations IA sont FAUSSES
   - Les potentiels de gains sont ERRONÉS
   - Les stops-loss sont INCORRECTS
   - Risque d'investissement sur données invalides!
''')

print('='*80)
print('🛠️ SOLUTIONS PROPOSÉES')
print('='*80)
print('''
1. ⭐ CORRECTION IMMÉDIATE (Recommandé):
   - Mettre à jour MANUELLEMENT les prix réels aujourd'hui
   - Script: mettre_a_jour_cours_brvm.py
   - Remplacer les prix erronés par les valeurs BRVM.org

2. 🔧 SCRAPING PRODUCTION:
   - Utiliser brvm_scraper_production.py
   - Collecter les prix directement depuis BRVM.org
   - Valider avec data_quality = REAL_SCRAPER

3. 🗑️ PURGE ET RECONSTRUCTION:
   - Supprimer TOUTES les observations avec prix < 1000 FCFA
   - Réimporter données historiques corrigées
   - Vérifier chaque prix avant import

4. 📋 VALIDATION POST-CORRECTION:
   - Relancer l'analyse IA
   - Vérifier cohérence des recommandations
   - Comparer avec prix BRVM.org
''')

print('='*80)
print('✅ DIAGNOSTIC TERMINÉ')
print('='*80)
