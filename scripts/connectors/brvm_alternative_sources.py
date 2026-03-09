"""
Collecteur de cours BRVM depuis sources alternatives fiables
Utilise Yahoo Finance et autres sources pour obtenir les vrais cours
"""
import sys
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

# Mapping BRVM -> Yahoo Finance symbols
BRVM_TO_YAHOO = {
    'BICC': 'BICC.CI',  # BICICI
    'BOAB': 'BOAB.PA',  # BOA Benin (Euronext)
    'ONTBF': 'ONTBF.CI',  # ONATEL
    'SNTS': 'SNTS.PA',  # Sonatel (Euronext Paris)
    'TTLS': 'TTLS.PA',  # Total Senegal
    # Ajouter d'autres mappings connus
}

def fetch_yahoo_finance(symbol: str) -> Dict[str, Any]:
    """Récupère le cours d'une action depuis Yahoo Finance"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {'interval': '1d', 'range': '1d'}
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            quote = result.get('indicators', {}).get('quote', [{}])[0]
            
            return {
                'close': meta.get('regularMarketPrice'),
                'open': quote.get('open', [None])[-1],
                'high': quote.get('high', [None])[-1],
                'low': quote.get('low', [None])[-1],
                'volume': quote.get('volume', [None])[-1],
                'change_pct': meta.get('regularMarketChangePercent'),
            }
    except Exception as e:
        logger.debug(f"Yahoo Finance error for {symbol}: {e}")
        return {}


def fetch_brvm_alternative_sources() -> List[Dict[str, Any]]:
    """
    Collecte les cours BRVM depuis sources alternatives
    
    Returns:
        Liste des cours collectés
    """
    logger.info("Collecte des cours BRVM depuis sources alternatives...")
    stocks = []
    now = datetime.now(timezone.utc)
    
    # Tentative 1: Yahoo Finance pour les actions disponibles
    yahoo_collected = 0
    for brvm_symbol, yahoo_symbol in BRVM_TO_YAHOO.items():
        logger.info(f"   {brvm_symbol} via Yahoo Finance...")
        data = fetch_yahoo_finance(yahoo_symbol)
        
        if data and data.get('close'):
            stocks.append({
                'symbol': brvm_symbol,
                'close': data['close'],
                'open': data.get('open', data['close']),
                'high': data.get('high', data['close']),
                'low': data.get('low', data['close']),
                'volume': int(data.get('volume', 0)) if data.get('volume') else 0,
                'day_change_pct': data.get('change_pct', 0),
                'ts': now.isoformat(),
                'source': 'YAHOO_FINANCE',
                'data_quality': 'REAL'
            })
            yahoo_collected += 1
    
    logger.info(f"Yahoo Finance: {yahoo_collected} actions")
    
    # Tentative 2: Investing.com API (non documentée mais accessible)
    try:
        investing_url = "https://api.investing.com/api/financialdata/"
        # Les symboles BRVM sur Investing.com
        investing_symbols = {
            'BICC': '941849',  # BICICI
            'SNTS': '941850',  # Sonatel
        }
        
        for brvm_symbol, investing_id in investing_symbols.items():
            if any(s['symbol'] == brvm_symbol for s in stocks):
                continue  # Déjà collecté via Yahoo
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Domain-Id': '1'
                }
                response = requests.get(
                    f"{investing_url}{investing_id}/historical/chart",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        logger.info(f"   Investing.com: {brvm_symbol}")
                        # Parser les données...
            except:
                continue
    except Exception as e:
        logger.debug(f"Investing.com error: {e}")
    
    return stocks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n" + "="*80)
    print("COLLECTE DES COURS BRVM - SOURCES ALTERNATIVES")
    print("="*80 + "\n")
    
    stocks = fetch_brvm_alternative_sources()
    
    if stocks:
        print(f"\nCollecté {len(stocks)} cours réels:\n")
        for stock in stocks:
            print(f"   {stock['symbol']:8s} | {stock['close']:10.2f} FCFA | Variation: {stock['day_change_pct']:+6.2f}% | Source: {stock['source']}")
    else:
        print("\nAucun cours collecté")
    
    print("\n" + "="*80 + "\n")
