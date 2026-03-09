#!/usr/bin/env python3
"""
MOTEUR D'ANALYSE IA & PRÉDICTIONS BRVM
=======================================

Lance l'analyse complète avec Intelligence Artificielle :
1. Collecte des données historiques réelles MongoDB
2. Analyse technique (SMA, RSI, MACD, Bollinger)
3. Prédictions ML (ARIMA, EMA, Regression)
4. Génération de recommandations (BUY/HOLD/SELL)
5. Détection d'alertes de trading
6. Calcul de scores de confiance

Utilise UNIQUEMENT les données réelles (data_quality='REAL_SCRAPER')
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
import pandas as pd

# Ajouter le projet au PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
import django
django.setup()

from plateforme_centralisation.mongo import get_mongo_db
from dashboard.ml_predictor import StockPricePredictor
from dashboard.prediction_service import PredictionService


def collecter_historique_action(db, symbol: str, jours: int = 60) -> pd.DataFrame:
    """
    Collecter l'historique d'une action depuis MongoDB
    """
    fin = datetime.now()
    debut = fin - timedelta(days=jours)
    
    cursor = db.curated_observations.find({
        'source': 'BRVM',
        'dataset': 'STOCK_PRICE',
        'key': symbol,
        'ts': {
            '$gte': debut.strftime('%Y-%m-%d'),
            '$lte': fin.strftime('%Y-%m-%d')
        },
        'attrs.data_quality': 'REAL_SCRAPER'  # CRITIQUE : Données réelles uniquement
    }).sort('ts', 1)
    
    data = []
    for doc in cursor:
        attrs = doc.get('attrs', {})
        data.append({
            'date': doc['ts'],
            'close': doc['value'],
            'open': attrs.get('open', doc['value']),
            'high': attrs.get('high', doc['value']),
            'low': attrs.get('low', doc['value']),
            'volume': attrs.get('volume', 0),
            'variation_pct': attrs.get('variation_pct', 0),
        })
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def calculer_indicateurs_techniques(df: pd.DataFrame) -> Dict:
    """
    Calculer tous les indicateurs techniques d'analyse
    """
    if len(df) < 20:
        return {'error': 'Historique insuffisant (min 20 jours)'}
    
    df = df.copy()
    
    # Moyennes mobiles
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean() if len(df) >= 50 else None
    df['EMA_12'] = df['close'].ewm(span=12).mean()
    df['EMA_26'] = df['close'].ewm(span=26).mean()
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
    
    # RSI (14 jours)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (2 * bb_std)
    df['BB_lower'] = df['BB_middle'] - (2 * bb_std)
    
    # Volatilité (écart-type sur 20 jours)
    returns = df['close'].pct_change()
    df['volatility_20d'] = returns.rolling(window=20).std() * np.sqrt(252) * 100  # Annualisée
    
    # Dernières valeurs
    latest = df.iloc[-1]
    
    return {
        'SMA_20': float(latest['SMA_20']) if pd.notna(latest['SMA_20']) else None,
        'SMA_50': float(latest['SMA_50']) if pd.notna(latest.get('SMA_50')) else None,
        'EMA_12': float(latest['EMA_12']),
        'EMA_26': float(latest['EMA_26']),
        'MACD': float(latest['MACD']),
        'MACD_signal': float(latest['MACD_signal']),
        'MACD_histogram': float(latest['MACD_histogram']),
        'RSI': float(latest['RSI']) if pd.notna(latest['RSI']) else None,
        'BB_upper': float(latest['BB_upper']) if pd.notna(latest['BB_upper']) else None,
        'BB_middle': float(latest['BB_middle']) if pd.notna(latest['BB_middle']) else None,
        'BB_lower': float(latest['BB_lower']) if pd.notna(latest['BB_lower']) else None,
        'volatility_annual': float(latest['volatility_20d']) if pd.notna(latest['volatility_20d']) else None,
        'current_price': float(latest['close']),
    }


def generer_predictions_ml(df: pd.DataFrame, horizons: List[int] = [7, 30]) -> Dict:
    """
    Générer prédictions Machine Learning
    """
    if len(df) < 30:
        return {'error': 'Historique insuffisant pour prédictions ML (min 30 jours)'}
    
    predictor = StockPricePredictor(df)
    
    predictions = {}
    
    for horizon in horizons:
        # Méthode 1: Lissage exponentiel (toujours disponible)
        pred_ema = predictor.predict_exponential_smoothing(days=horizon)
        predictions[f'{horizon}d_EMA'] = pred_ema
        
        # Méthode 2: Régression polynomiale
        try:
            pred_poly = predictor.predict_polynomial(days=horizon)
            predictions[f'{horizon}d_POLY'] = pred_poly
        except:
            pass
        
        # Méthode 3: ARIMA (si statsmodels installé)
        try:
            pred_arima = predictor.predict_arima(days=horizon)
            predictions[f'{horizon}d_ARIMA'] = pred_arima
        except:
            pass
    
    return predictions


def generer_recommandation(indicateurs: Dict, predictions: Dict, df: pd.DataFrame) -> Dict:
    """
    Générer recommandation BUY/HOLD/SELL basée sur analyse technique + ML
    """
    score = 0  # Score de -10 (forte vente) à +10 (fort achat)
    signaux = []
    
    current_price = indicateurs['current_price']
    
    # Signal 1: RSI
    rsi = indicateurs.get('RSI')
    if rsi:
        if rsi < 30:
            score += 2
            signaux.append(f"RSI survendu ({rsi:.1f})")
        elif rsi > 70:
            score -= 2
            signaux.append(f"RSI suracheté ({rsi:.1f})")
    
    # Signal 2: MACD
    macd_hist = indicateurs.get('MACD_histogram')
    if macd_hist:
        if macd_hist > 0:
            score += 1
            signaux.append("MACD haussier")
        else:
            score -= 1
            signaux.append("MACD baissier")
    
    # Signal 3: Bollinger Bands
    bb_upper = indicateurs.get('BB_upper')
    bb_lower = indicateurs.get('BB_lower')
    if bb_upper and bb_lower:
        if current_price < bb_lower:
            score += 2
            signaux.append("Prix sous bande de Bollinger inférieure")
        elif current_price > bb_upper:
            score -= 2
            signaux.append("Prix au-dessus bande de Bollinger supérieure")
    
    # Signal 4: Moyennes mobiles
    sma_20 = indicateurs.get('SMA_20')
    sma_50 = indicateurs.get('SMA_50')
    if sma_20 and sma_50:
        if current_price > sma_20 > sma_50:
            score += 2
            signaux.append("Tendance haussière (prix > SMA20 > SMA50)")
        elif current_price < sma_20 < sma_50:
            score -= 2
            signaux.append("Tendance baissière (prix < SMA20 < SMA50)")
    
    # Signal 5: Prédictions ML (consensus)
    pred_7d = predictions.get('7d_EMA', {})
    if 'predictions' in pred_7d and len(pred_7d['predictions']) > 0:
        pred_price_7d = pred_7d['predictions'][-1]
        variation_pred = ((pred_price_7d - current_price) / current_price) * 100
        
        if variation_pred > 3:
            score += 2
            signaux.append(f"ML prédit +{variation_pred:.1f}% en 7j")
        elif variation_pred < -3:
            score -= 2
            signaux.append(f"ML prédit {variation_pred:.1f}% en 7j")
    
    # Signal 6: Volatilité
    volatility = indicateurs.get('volatility_annual')
    if volatility:
        if volatility > 40:
            score -= 1
            signaux.append(f"Forte volatilité ({volatility:.1f}%)")
    
    # Décision finale
    if score >= 5:
        recommandation = 'BUY'
        confiance = min(score / 10, 1.0)
    elif score <= -5:
        recommandation = 'SELL'
        confiance = min(abs(score) / 10, 1.0)
    else:
        recommandation = 'HOLD'
        confiance = 1.0 - abs(score) / 10
    
    return {
        'recommandation': recommandation,
        'score': score,
        'confiance': round(confiance * 100, 1),
        'signaux': signaux,
        'prix_actuel': current_price,
        'prix_cible_7d': pred_7d.get('predictions', [None])[-1] if pred_7d.get('predictions') else None,
    }


def analyser_action(db, symbol: str) -> Dict:
    """
    Analyse complète IA d'une action
    """
    print(f"\n{'='*80}")
    print(f"📊 ANALYSE IA: {symbol}")
    print(f"{'='*80}")
    
    # 1. Collecter historique
    print("🔍 Collecte historique...")
    df = collecter_historique_action(db, symbol, jours=60)
    
    if df.empty:
        print(f"   ⚠️ Aucune donnée historique pour {symbol}")
        return {'error': 'Pas de données'}
    
    print(f"   ✅ {len(df)} jours d'historique")
    
    # 2. Calculer indicateurs techniques
    print("📈 Calcul indicateurs techniques...")
    indicateurs = calculer_indicateurs_techniques(df)
    
    if 'error' in indicateurs:
        print(f"   ⚠️ {indicateurs['error']}")
        return indicateurs
    
    print(f"   ✅ Prix actuel: {indicateurs['current_price']:,.0f} FCFA")
    if indicateurs.get('RSI'):
        print(f"   ✅ RSI: {indicateurs['RSI']:.1f}")
    if indicateurs.get('MACD'):
        print(f"   ✅ MACD: {indicateurs['MACD']:.2f}")
    
    # 3. Générer prédictions ML
    print("🤖 Prédictions Machine Learning...")
    predictions = generer_predictions_ml(df, horizons=[7, 30])
    
    if 'error' not in predictions:
        for key, pred in predictions.items():
            if 'predictions' in pred and len(pred['predictions']) > 0:
                horizon = key.split('_')[0]
                method = key.split('_')[1]
                prix_pred = pred['predictions'][-1]
                variation = ((prix_pred - indicateurs['current_price']) / indicateurs['current_price']) * 100
                print(f"   ✅ {method} {horizon}: {prix_pred:,.0f} FCFA ({variation:+.1f}%)")
    
    # 4. Générer recommandation
    print("🎯 Génération recommandation...")
    recommandation = generer_recommandation(indicateurs, predictions, df)
    
    print(f"\n{'='*80}")
    print(f"🎯 RECOMMANDATION: {recommandation['recommandation']}")
    print(f"📊 Score: {recommandation['score']}/10")
    print(f"💯 Confiance: {recommandation['confiance']}%")
    print(f"{'='*80}")
    
    print(f"\n📋 Signaux détectés:")
    for signal in recommandation['signaux']:
        print(f"   • {signal}")
    
    if recommandation.get('prix_cible_7d'):
        print(f"\n🎯 Prix cible 7j: {recommandation['prix_cible_7d']:,.0f} FCFA")
    
    return {
        'symbol': symbol,
        'date_analyse': datetime.now().isoformat(),
        'historique_jours': len(df),
        'indicateurs': indicateurs,
        'predictions': predictions,
        'recommandation': recommandation,
    }


def sauvegarder_analyse_mongodb(db, analyse: Dict):
    """
    Sauvegarder les résultats d'analyse dans MongoDB
    """
    if 'error' in analyse:
        return
    
    doc = {
        'source': 'AI_ANALYSIS',
        'dataset': 'STOCK_RECOMMENDATION',
        'key': analyse['symbol'],
        'ts': datetime.now().strftime('%Y-%m-%d'),
        'value': analyse['recommandation']['score'],
        'attrs': {
            'recommandation': analyse['recommandation']['recommandation'],
            'confiance': analyse['recommandation']['confiance'],
            'signaux': analyse['recommandation']['signaux'],
            'prix_actuel': analyse['recommandation']['prix_actuel'],
            'prix_cible_7d': analyse['recommandation'].get('prix_cible_7d'),
            'RSI': analyse['indicateurs'].get('RSI'),
            'MACD': analyse['indicateurs'].get('MACD'),
            'volatility': analyse['indicateurs'].get('volatility_annual'),
            'generated_at': analyse['date_analyse'],
        }
    }
    
    db.curated_observations.update_one(
        {'source': 'AI_ANALYSIS', 'key': analyse['symbol'], 'ts': doc['ts']},
        {'$set': doc},
        upsert=True
    )


def main():
    print("="*80)
    print("🤖 MOTEUR D'ANALYSE IA & PRÉDICTIONS BRVM")
    print("="*80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Connexion MongoDB
    client, db = get_mongo_db()
    
    # Récupérer actions avec données réelles
    actions = db.curated_observations.distinct('key', {
        'source': 'BRVM',
        'attrs.data_quality': 'REAL_SCRAPER'
    })
    
    print(f"\n📊 {len(actions)} actions avec données réelles")
    
    # TOP 10 actions (ou toutes si moins de 10)
    actions_a_analyser = actions[:10] if len(actions) > 10 else actions
    
    print(f"\n🎯 Analyse de {len(actions_a_analyser)} actions principales")
    
    resultats = []
    
    for symbol in actions_a_analyser:
        try:
            analyse = analyser_action(db, symbol)
            
            if 'error' not in analyse:
                sauvegarder_analyse_mongodb(db, analyse)
                resultats.append(analyse)
        except Exception as e:
            print(f"\n❌ Erreur {symbol}: {e}")
            continue
    
    # Résumé final
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES RECOMMANDATIONS")
    print("="*80)
    
    buy_count = sum(1 for r in resultats if r['recommandation']['recommandation'] == 'BUY')
    hold_count = sum(1 for r in resultats if r['recommandation']['recommandation'] == 'HOLD')
    sell_count = sum(1 for r in resultats if r['recommandation']['recommandation'] == 'SELL')
    
    print(f"\n🟢 BUY:  {buy_count}")
    print(f"🟡 HOLD: {hold_count}")
    print(f"🔴 SELL: {sell_count}")
    
    # Top recommandations
    if buy_count > 0:
        print(f"\n🎯 TOP OPPORTUNITÉS D'ACHAT:")
        buy_recs = sorted(
            [r for r in resultats if r['recommandation']['recommandation'] == 'BUY'],
            key=lambda x: x['recommandation']['confiance'],
            reverse=True
        )
        for rec in buy_recs[:5]:
            print(f"   {rec['symbol']:8s}: {rec['recommandation']['prix_actuel']:8,.0f} FCFA "
                  f"(Confiance: {rec['recommandation']['confiance']}%)")
    
    print("\n" + "="*80)
    print(f"✅ Analyse terminée - {len(resultats)} actions analysées")
    print("="*80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
