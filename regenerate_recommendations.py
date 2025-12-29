"""Régénérer les recommandations avec stratégie de trading"""
import os
import sys
import numpy as np
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from dashboard.analytics.recommendation_engine import RecommendationEngine
from plateforme_centralisation.mongo import get_mongo_db
from datetime import datetime

# Fonction de conversion NumPy → Python
def convert_numpy_to_python(obj):
    """Convertit récursivement tous les types NumPy en types Python natifs"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_to_python(item) for item in obj]
    return obj

print('🔄 Régénération des recommandations avec stratégie de trading...')

engine = RecommendationEngine()
recommendations = engine.generate_recommendations(days=60, min_confidence=65)

# Convertir tous les types NumPy
recommendations_converted = convert_numpy_to_python(recommendations)

db_client, db = get_mongo_db()

# Sauvegarder avec les nouveaux champs
result = db.daily_recommendations.insert_one({
    'date': datetime.now(),
    'recommendations': recommendations_converted,
    'updated': True
})

print(f'✅ Nouvelles recommandations sauvegardées (ID: {result.inserted_id})')
print(f'📊 Signaux BUY: {len(recommendations.get("buy_signals", []))}')
print(f'📊 Signaux SELL: {len(recommendations.get("sell_signals", []))}')
