#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BRVM - Analyse IA & Recommandations (script moderne, autonome)
- Analyse technique, fondamentaux, NLP, macro (si modules dispos)
- Résumé clair des signaux BUY/HOLD/SELL
"""
import os
# Initialisation Django settings pour MongoDB
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("analyse_brvm_modern")

# --- MongoDB ---
try:
    from plateforme_centralisation.mongo import get_mongo_db
except ImportError:
    logger.error("MongoDB connector not found. Exiting.")
    sys.exit(1)

# --- Modules avancés (optionnels) ---
try:
    from sentiment_analyzer import PublicationSentimentAnalyzer
except ImportError:
    PublicationSentimentAnalyzer = None
try:
    from scripts.connectors.macro_economic_integrator import MacroEconomicIntegrator
except ImportError:
    MacroEconomicIntegrator = None

# --- Indicateurs techniques simples ---
def sma(series, window):
    return series.rolling(window=window).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

# --- Analyse d'une action ---
def analyze_action(df: pd.DataFrame, symbol: str, sentiment_model=None, macro_model=None) -> Dict[str, Any]:
    data = df[df['key'] == symbol].sort_values('ts')
    if data.shape[0] < 10:
        return None
    prices = data['value']
    result = {'symbol': symbol, 'current_price': prices.iloc[-1]}
    result['sma20'] = sma(prices, 20).iloc[-1]
    result['rsi14'] = rsi(prices, 14).iloc[-1]
    macd_line, signal_line, hist = macd(prices)
    result['macd'] = macd_line.iloc[-1]
    result['macd_hist'] = hist.iloc[-1]
    # Sentiment (optionnel)
    if sentiment_model:
        result['sentiment'] = sentiment_model.analyze(symbol)
    # Macro (optionnel)
    if macro_model:
        result['macro'] = macro_model.get_macro_context(symbol)
    # Simple rules
    score = 0
    if result['rsi14'] < 30:
        score += 2
    elif result['rsi14'] > 70:
        score -= 2
    if result['macd_hist'] > 0:
        score += 1
    else:
        score -= 1
    if result['current_price'] > result['sma20']:
        score += 1
    else:
        score -= 1
    # Sentiment
    if 'sentiment' in result and result['sentiment'] == 'positive':
        score += 1
    elif 'sentiment' in result and result['sentiment'] == 'negative':
        score -= 1
    # Macro
    if 'macro' in result and result['macro'].get('macro_signal') == 'POSITIVE':
        score += 1
    elif 'macro' in result and result['macro'].get('macro_signal') == 'NEGATIVE':
        score -= 1
    # Decision
    if score >= 3:
        reco = 'BUY'
    elif score <= -3:
        reco = 'SELL'
    else:
        reco = 'HOLD'
    result['recommendation'] = reco
    result['score'] = score
    return result

# --- Main ---
def main():
    print("="*80)
    print("ANALYSE IA & RECOMMANDATIONS BRVM (moderne)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    _, db = get_mongo_db()
    # Charger toutes les données actions BRVM
    rows = list(db.curated_observations.find({'source': 'BRVM'}))
    if not rows:
        print("Aucune donnée trouvée.")
        return
    df = pd.DataFrame(rows)
    if 'value' not in df or 'key' not in df or 'ts' not in df:
        print("Colonnes manquantes dans les données.")
        return
    sentiment_model = PublicationSentimentAnalyzer() if PublicationSentimentAnalyzer else None
    macro_model = MacroEconomicIntegrator() if MacroEconomicIntegrator else None
    results = []
    for symbol in df['key'].unique():
        res = analyze_action(df, symbol, sentiment_model, macro_model)
        if res:
            results.append(res)
    # Résumé
    buy = [r for r in results if r['recommendation'] == 'BUY']
    hold = [r for r in results if r['recommendation'] == 'HOLD']
    sell = [r for r in results if r['recommendation'] == 'SELL']
    print(f"\nBUY:  {len(buy)}")
    print(f"HOLD: {len(hold)}")
    print(f"SELL: {len(sell)}")
    print(f"\nTOP ACHATS:")
    for r in sorted(buy, key=lambda x: x['score'], reverse=True)[:5]:
        print(f"   {r['symbol']:10s} Prix: {r['current_price']:,.0f} Score: {r['score']} RSI: {r['rsi14']:.1f}")
    print(f"\n{len(results)} actions analysées.")

if __name__ == "__main__":
    main()
