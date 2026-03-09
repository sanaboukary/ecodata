"""
📊 RAPPORT SUR LA COLLECTE AUTOMATIQUE BRVM
"""

print("=" * 90)
print("🤖 ÉTAT DE LA COLLECTE AUTOMATIQUE DES DONNÉES BRVM")
print("=" * 90)

print("\n1️⃣ CONFIGURATION ACTUELLE:")
print("   ✅ DAG Airflow: brvm_collecte_horaire_REELLE.py")
print("   ⏰ Fréquence: Toutes les heures de 9h à 16h (heures de bourse)")
print("   📅 Jours: Lundi à Vendredi (jours ouvrables)")
print("   🔴 Politique: DONNÉES RÉELLES UNIQUEMENT (zéro tolérance)")

print("\n2️⃣ MÉTHODES DE COLLECTE AUTORISÉES:")
print("   1. Scraping du site BRVM officiel (automatique)")
print("   2. Saisie manuelle via script (si scraping échoue)")
print("   3. Import CSV (pour historique)")
print("   ❌ JAMAIS de simulation automatique de données")

print("\n3️⃣ STATUT AIRFLOW:")
import subprocess
import os

try:
    # Vérifier si Airflow tourne
    result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True)
    airflow_running = 'airflow' in result.stdout.lower()
    
    if airflow_running:
        print("   ✅ Airflow EST EN COURS D'EXÉCUTION")
        print("   📊 Interface web: http://localhost:8080")
        print("   👤 Login: admin / admin")
    else:
        print("   ❌ Airflow N'EST PAS EN COURS D'EXÉCUTION")
        print("\n   Pour démarrer Airflow:")
        print("   → Double-cliquez sur: start_airflow_background.bat")
        print("   → Ou exécutez: airflow standalone")
except Exception as e:
    print(f"   ⚠️  Impossible de vérifier le statut: {e}")

print("\n4️⃣ DERNIÈRE COLLECTE:")
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime, timedelta

client, db = get_mongo_db()

# Dernières données BRVM
derniere_obs = db.curated_observations.find_one(
    {'source': 'BRVM'},
    sort=[('ts', -1)]
)

if derniere_obs:
    date_derniere = derniere_obs.get('ts', 'N/A')
    action_derniere = derniere_obs.get('key', 'N/A')
    prix_dernier = derniere_obs.get('value', 'N/A')
    qualite = derniere_obs.get('attrs', {}).get('data_quality', 'UNKNOWN')
    
    print(f"   📅 Date: {date_derniere}")
    print(f"   📈 Action: {action_derniere}")
    print(f"   💰 Prix: {prix_dernier} FCFA")
    print(f"   ✅ Qualité: {qualite}")
    
    # Vérifier si c'est aujourd'hui
    date_aujourdhui = datetime.now().strftime('%Y-%m-%d')
    if isinstance(date_derniere, str):
        date_derniere_str = date_derniere.split('T')[0]
    else:
        date_derniere_str = date_derniere.strftime('%Y-%m-%d')
    
    if date_derniere_str == date_aujourdhui:
        print("   ✅ Données d'AUJOURD'HUI disponibles")
    else:
        diff_jours = (datetime.now() - datetime.strptime(date_derniere_str, '%Y-%m-%d')).days
        print(f"   ⚠️  Données datent de {diff_jours} jour(s)")
else:
    print("   ❌ Aucune donnée BRVM trouvée")

print("\n5️⃣ STATISTIQUES AUJOURD'HUI:")
date_aujourdhui = datetime.now().strftime('%Y-%m-%d')

total_aujourdhui = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': date_aujourdhui
})

reelles_aujourdhui = db.curated_observations.count_documents({
    'source': 'BRVM',
    'ts': date_aujourdhui,
    'attrs.data_quality': {'$in': ['REAL_MANUAL', 'REAL_SCRAPER']}
})

if total_aujourdhui > 0:
    pct_reel = (reelles_aujourdhui / total_aujourdhui) * 100
    print(f"   📊 Total observations: {total_aujourdhui}")
    print(f"   ✅ Données RÉELLES: {reelles_aujourdhui} ({pct_reel:.1f}%)")
    print(f"   ⚠️  Données suspectes: {total_aujourdhui - reelles_aujourdhui}")
    
    if pct_reel >= 100:
        print("   🎉 100% de données RÉELLES - Excellent !")
    elif pct_reel >= 80:
        print("   👍 Bonne qualité de données")
    else:
        print("   ⚠️  Attention: Nettoyer les données simulées")
else:
    print(f"   ℹ️  Aucune donnée pour aujourd'hui ({date_aujourdhui})")
    print("   💡 Lancez la collecte: python collecter_quotidien_intelligent.py")

print("\n" + "=" * 90)
print("📝 ACTIONS RECOMMANDÉES:")
print("=" * 90)

if not airflow_running:
    print("\n🚨 PRIORITAIRE:")
    print("   1. Démarrer Airflow: start_airflow_background.bat")
    print("   2. Vérifier le DAG dans l'interface: http://localhost:8080")
    print("   3. S'assurer que 'brvm_collecte_horaire_REELLE' est activé (toggle ON)")

if total_aujourdhui == 0:
    print("\n📊 COLLECTE IMMÉDIATE:")
    print("   Option A - Script intelligent (recommandé):")
    print("   → python collecter_quotidien_intelligent.py")
    print()
    print("   Option B - Saisie manuelle:")
    print("   → python mettre_a_jour_cours_brvm.py")
    print()
    print("   Option C - Import CSV:")
    print("   → python collecter_csv_automatique.py")

if reelles_aujourdhui < total_aujourdhui:
    print("\n🧹 NETTOYAGE:")
    print("   → Supprimer les données simulées/suspectes")
    print("   → Garder uniquement data_quality = REAL_MANUAL ou REAL_SCRAPER")

print("\n" + "=" * 90)
print("✅ POUR UNE COLLECTE 100% AUTOMATIQUE:")
print("=" * 90)
print("   1. Airflow doit tourner en arrière-plan (start_airflow_background.bat)")
print("   2. DAG 'brvm_collecte_horaire_REELLE' activé dans l'interface")
print("   3. Scraper fonctionnel: scripts/connectors/brvm_scraper_production.py")
print("   4. Si scraper échoue → notification + saisie manuelle requise")
print("=" * 90)
