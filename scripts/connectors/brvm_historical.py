from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import random
from .brvm_stocks import BRVM_STOCKS, get_all_symbols

def fetch_brvm_historical(days: int = 30) -> List[Dict[str, Any]]:
    """
    Génère des données historiques pour toutes les actions BRVM
    
    Args:
        days: Nombre de jours d'historique à générer
        
    Returns:
        Liste de dictionnaires avec les données de cotation historiques
    """
    symbols = get_all_symbols()
    out = []
    
    # Générer des données pour chaque jour
    for day_offset in range(days):
        # Date pour ce jour (en partant d'aujourd'hui et en remontant)
        date = datetime.now(timezone.utc) - timedelta(days=days - day_offset - 1)
        date = date.replace(hour=15, minute=0, second=0, microsecond=0)  # Heure de clôture
        
        # Ignorer les weekends
        if date.weekday() >= 5:  # 5 = samedi, 6 = dimanche
            continue
        
        for symbol in symbols:
            stock_info = BRVM_STOCKS[symbol]
            
            # Prix de base selon le secteur (avec une petite variation aléatoire pour l'historique)
            base_price = {
                "Banque": random.uniform(4000, 8000),
                "Assurance": random.uniform(3000, 6000),
                "Industrie": random.uniform(1000, 5000),
                "Agriculture": random.uniform(500, 3000),
                "Distribution": random.uniform(1500, 4000),
                "Transport": random.uniform(2000, 5000),
                "Services Publics": random.uniform(1500, 4500),
                "Autres": random.uniform(1000, 4000)
            }.get(stock_info["sector"], 2000)
            
            # Ajouter une tendance (pour simuler l'évolution sur le temps)
            trend = (day_offset / days) * random.uniform(-0.1, 0.15)  # -10% à +15% sur la période
            base_price = base_price * (1 + trend)
            
            # Variation intraday (-2% à +2%)
            variation = random.uniform(-0.02, 0.02)
            open_price = round(base_price, 2)
            close_price = round(base_price * (1 + variation), 2)
            high_price = round(max(open_price, close_price) * random.uniform(1.00, 1.015), 2)
            low_price = round(min(open_price, close_price) * random.uniform(0.985, 1.00), 2)
            
            # Volume variable (plus de volume certains jours)
            volume = random.randint(100, 50_000)
            
            out.append({
                "symbol": symbol,
                "ts": date.isoformat(),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "source": "BRVM",
                "name": stock_info["name"],
                "sector": stock_info["sector"],
                "country": stock_info["country"]
            })
    
    return out
