"""
Génère un historique réaliste de prix BRVM pour les 60 derniers jours
Basé sur les cours actuels et des variations aléatoires faibles (±2% par jour)
"""
import sys
import os
import django
from datetime import datetime, timezone, timedelta
import random

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
django.setup()

from plateforme_centralisation.mongo import get_mongo_db

def generer_historique_brvm(jours=60):
    """Génère un historique réaliste de prix BRVM"""
    print("\n" + "="*80)
    print("📊 GÉNÉRATION D'HISTORIQUE BRVM RÉALISTE")
    print("="*80 + "\n")
    
    _, db = get_mongo_db()
    
    # Récupérer les cours actuels
    cours_actuels = list(db.curated_observations.find(
        {'source': 'BRVM'},
        {'key': 1, 'value': 1, 'attrs.volume': 1}
    ))
    
    print(f"📈 Actions BRVM: {len(cours_actuels)}")
    print(f"📅 Période: {jours} jours")
    print(f"⏳ Génération en cours...\n")
    
    observations_historiques = []
    now = datetime.now(timezone.utc)
    
    for stock in cours_actuels:
        symbol = stock['key']
        prix_actuel = stock['value']
        volume_actuel = stock.get('attrs', {}).get('volume', 1000)
        
        # Générer l'historique en partant d'aujourd'hui et en remontant
        for i in range(jours, 0, -1):
            date_historique = now - timedelta(days=i)
            
            # Variation aléatoire faible (-2% à +2%)
            variation_pct = random.uniform(-2.0, 2.0)
            
            # Prix avec tendance légère (les prix tendent vers le prix actuel)
            tendance = (jours - i) / jours  # 0 au début, 1 à la fin
            prix_base = prix_actuel * (1 - tendance * 0.05)  # Écart max 5%
            prix = prix_base * (1 + variation_pct/100)
            
            # Prix OHLC
            close = round(prix, 2)
            open_price = round(close * random.uniform(0.98, 1.02), 2)
            high = round(max(open_price, close) * random.uniform(1.0, 1.015), 2)
            low = round(min(open_price, close) * random.uniform(0.985, 1.0), 2)
            
            # Volume avec variation aléatoire
            volume = int(volume_actuel * random.uniform(0.5, 1.5))
            
            observation = {
                'source': 'BRVM',
                'dataset': 'STOCK_PRICE',
                'key': symbol,
                'ts': date_historique,
                'value': close,
                'attrs': {
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume,
                    'day_change': round(close - open_price, 2),
                    'day_change_pct': round((close - open_price) / open_price * 100, 2),
                    'data_quality': 'SIMULATED_HISTORY',
                    'note': 'Historique simulé pour analyse technique',
                }
            }
            observations_historiques.append(observation)
    
    # Supprimer l'ancien historique simulé
    result_delete = db.curated_observations.delete_many({
        'source': 'BRVM',
        'attrs.data_quality': 'SIMULATED_HISTORY'
    })
    
    print(f"🗑️  Ancien historique supprimé: {result_delete.deleted_count} observations\n")
    
    # Insérer le nouvel historique
    if observations_historiques:
        db.curated_observations.insert_many(observations_historiques)
        print(f"✅ {len(observations_historiques)} observations historiques générées\n")
        print(f"   {len(cours_actuels)} actions × {jours} jours = {len(cours_actuels) * jours} points de données")
    
    # Statistiques finales
    total_brvm = db.curated_observations.count_documents({'source': 'BRVM'})
    observations_reelles = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': 'REAL_MANUAL'
    })
    observations_estimees = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': {'$exists': False}
    })
    observations_simulees = db.curated_observations.count_documents({
        'source': 'BRVM',
        'attrs.data_quality': 'SIMULATED_HISTORY'
    })
    
    print(f"\n📊 ÉTAT FINAL DE LA BASE:\n")
    print(f"   Total observations BRVM: {total_brvm}")
    print(f"   ✅ Cours réels (manuels): {observations_reelles}")
    print(f"   ⚠️  Cours estimés: {observations_estimees}")
    print(f"   📈 Historique simulé: {observations_simulees}")
    
    print("\n" + "="*80)
    print("✅ HISTORIQUE GÉNÉRÉ - PRÊT POUR ANALYSE IA")
    print("="*80 + "\n")
    
    print("📍 Relancez l'analyse IA: python lancer_analyse_ia_complete.py\n")

if __name__ == "__main__":
    try:
        generer_historique_brvm(jours=60)
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        import traceback
        traceback.print_exc()
