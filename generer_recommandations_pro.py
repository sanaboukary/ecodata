#!/usr/bin/env python3
"""
Générateur de Recommandations PROFESSIONNEL
Avec indicateurs techniques standards (RSI, MACD, SMA, Bollinger)
Approche ingénieur analyste financier
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import statistics
import json

def calculate_sma(prices, period):
    """Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    """Relative Strength Index"""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices):
    """MACD (Moving Average Convergence Divergence)"""
    if len(prices) < 26:
        return None, None
    
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    
    if ema12 is None or ema26 is None:
        return None, None
    
    macd_line = ema12 - ema26
    
    # Signal line (EMA 9 du MACD) - simplifié
    signal_line = macd_line  # Approximation
    
    return macd_line, signal_line

def calculate_ema(prices, period):
    """Exponential Moving Average"""
    if len(prices) < period:
        return None
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # SMA initiale
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Bandes de Bollinger"""
    if len(prices) < period:
        return None, None, None
    
    sma = calculate_sma(prices, period)
    std = statistics.stdev(prices[-period:])
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band, sma, lower_band

print("=" * 80)
print("📊 GÉNÉRATEUR RECOMMANDATIONS PROFESSIONNEL")
print("=" * 80)
print("Approche: Ingénieur Analyste Financier")
print("Indicateurs: RSI, MACD, SMA, Bandes de Bollinger")

client = MongoClient('mongodb://localhost:27017/')
db = client['centralisation_db']

# Dates
today = datetime.now()
date_today = today.strftime('%Y-%m-%d')
dates_60j = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(60)]

print(f"\n📅 Analyse période: {dates_60j[-1]} à {date_today}")

# Récupérer toutes les actions du jour
data_today = list(db.curated_observations.find({
    'source': 'BRVM',
    'ts': date_today
}))

print(f"📊 Actions disponibles aujourd'hui: {len(data_today)}")

recommendations = []

for obs_today in data_today:
    symbol = obs_today['key']
    price_today = obs_today['value']
    
    # Skip indices
    if symbol in ['BRVM-C.BC', 'BRVM-30.BC', 'BRVM-PRES.BC']:
        continue
    
    # Récupérer historique 60 jours
    historical_prices = []
    historical_volumes = []
    
    for date in reversed(dates_60j):  # Du plus ancien au plus récent
        obs = db.curated_observations.find_one({
            'source': 'BRVM',
            'key': symbol,
            'ts': date
        })
        if obs:
            historical_prices.append(obs['value'])
            historical_volumes.append(obs['attrs'].get('volume', 0))
    
    # Besoin minimum 20 jours pour indicateurs
    if len(historical_prices) < 20:
        continue
    
    # ===== CALCUL INDICATEURS TECHNIQUES =====
    
    # 1. SMA (Moyennes Mobiles)
    sma_20 = calculate_sma(historical_prices, 20)
    sma_50 = calculate_sma(historical_prices, 50) if len(historical_prices) >= 50 else None
    
    # 2. RSI
    rsi = calculate_rsi(historical_prices, 14)
    
    # 3. MACD
    macd_line, signal_line = calculate_macd(historical_prices)
    
    # 4. Bandes de Bollinger
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(historical_prices, 20)
    
    # 5. Volume (moyenne 20j)
    avg_volume_20 = sum(historical_volumes[-20:]) / 20 if len(historical_volumes) >= 20 else 0
    volume_today = historical_volumes[-1] if historical_volumes else 0
    
    # 6. Volatilité
    volatility_20 = (statistics.stdev(historical_prices[-20:]) / statistics.mean(historical_prices[-20:])) * 100
    
    # ===== SCORING PROFESSIONNEL (100 points) =====
    
    score = 0
    signals = []
    
    # === TECHNIQUE (40 points) ===
    
    # Momentum 7j (15 points)
    if len(historical_prices) >= 7:
        price_7j = historical_prices[-7]
        momentum_7j = ((price_today - price_7j) / price_7j) * 100
        
        if momentum_7j >= 10:
            score += 15
            signals.append(f"Momentum fort +{momentum_7j:.1f}%")
        elif momentum_7j >= 5:
            score += 12
            signals.append(f"Momentum bon +{momentum_7j:.1f}%")
        elif momentum_7j >= 2:
            score += 8
            signals.append(f"Momentum positif +{momentum_7j:.1f}%")
        elif momentum_7j >= 0:
            score += 4
    else:
        momentum_7j = 0
    
    # RSI optimal (10 points)
    if rsi:
        if 50 <= rsi <= 70:  # Zone optimale
            score += 10
            signals.append(f"RSI optimal {rsi:.1f}")
        elif 40 <= rsi < 50:
            score += 7
        elif 30 <= rsi < 40:  # Survente (opportunité)
            score += 5
            signals.append(f"RSI survente {rsi:.1f} (opportunité)")
        elif rsi > 70:  # Suracheté (danger)
            score += 2
            signals.append(f"RSI suracheté {rsi:.1f} (prudence)")
    
    # MACD haussier (10 points)
    if macd_line is not None and signal_line is not None:
        if macd_line > signal_line and macd_line > 0:
            score += 10
            signals.append("MACD haussier confirmé")
        elif macd_line > signal_line:
            score += 5
            signals.append("MACD croisement récent")
    
    # Volume confirmation (5 points)
    if avg_volume_20 > 0 and volume_today > avg_volume_20:
        score += 5
        signals.append("Volume supérieur moyenne")
    elif avg_volume_20 > 0 and volume_today > avg_volume_20 * 0.8:
        score += 3
    
    # === TENDANCE (25 points) ===
    
    # Croisement SMA (12 points)
    if sma_20 and sma_50:
        if sma_20 > sma_50:  # Golden cross
            score += 12
            signals.append("SMA20 > SMA50 (tendance haussière)")
        elif sma_20 > sma_50 * 0.98:
            score += 6
    elif sma_20 and price_today > sma_20:
        score += 8
        signals.append("Prix > SMA20")
    
    # Position Bollinger (13 points)
    if bb_lower and bb_upper:
        bb_position = (price_today - bb_lower) / (bb_upper - bb_lower)
        if 0.2 <= bb_position <= 0.5:  # Zone optimale (proche bande basse)
            score += 13
            signals.append("Position Bollinger optimale (rebond attendu)")
        elif 0.5 <= bb_position <= 0.8:
            score += 8
        elif bb_position > 0.9:  # Trop haut
            score += 2
            signals.append("Proche bande haute (prudence)")
    
    # === RISQUE AJUSTÉ (20 points) ===
    
    # Volatilité acceptable (10 points)
    if volatility_20 <= 10:  # Faible volatilité = stable
        score += 10
        signals.append(f"Volatilité faible {volatility_20:.1f}%")
    elif volatility_20 <= 20:
        score += 7
    elif volatility_20 <= 30:
        score += 4
    else:
        score += 0
        signals.append(f"Volatilité élevée {volatility_20:.1f}% (risque)")
    
    # Sharpe ratio approximé (10 points)
    if len(historical_prices) >= 20:
        returns = [(historical_prices[i] - historical_prices[i-1]) / historical_prices[i-1] for i in range(1, len(historical_prices))]
        avg_return = statistics.mean(returns) * 100
        std_return = statistics.stdev(returns) * 100
        
        sharpe_approx = avg_return / std_return if std_return > 0 else 0
        
        if sharpe_approx >= 2:
            score += 10
        elif sharpe_approx >= 1:
            score += 7
        elif sharpe_approx >= 0.5:
            score += 4
    
    # === LIQUIDITÉ (15 points) ===
    
    # Volume moyen acceptable (15 points)
    if avg_volume_20 >= 5000:
        score += 15
        signals.append("Excellente liquidité")
    elif avg_volume_20 >= 1000:
        score += 10
        signals.append("Bonne liquidité")
    elif avg_volume_20 >= 500:
        score += 5
    
    # === FILTRES QUALITÉ ===
    
    # Rejeter si:
    disqualified = False
    if volatility_20 > 40:  # Trop volatil
        disqualified = True
        signals.append("REJETÉ: Volatilité excessive")
    if rsi and rsi > 80:  # Trop suracheté
        disqualified = True
        signals.append("REJETÉ: RSI suracheté extrême")
    if avg_volume_20 < 100:  # Pas assez liquide
        disqualified = True
        signals.append("REJETÉ: Liquidité insuffisante")
    
    # Seuil minimum: 60 points (professionnel)
    if score >= 60 and not disqualified:
        recommendations.append({
            'symbol': symbol,
            'score': score,
            'prix_actuel': price_today,
            'momentum_7j': round(momentum_7j, 2) if 'momentum_7j' in locals() else 0,
            'rsi': round(rsi, 2) if rsi else None,
            'macd': round(macd_line, 2) if macd_line else None,
            'sma_20': round(sma_20, 2) if sma_20 else None,
            'sma_50': round(sma_50, 2) if sma_50 else None,
            'volatility_20j': round(volatility_20, 2),
            'volume_avg': int(avg_volume_20),
            'nb_jours_data': len(historical_prices),
            'signals': signals,
            'confiance': 'HAUTE' if score >= 80 else 'MOYENNE' if score >= 70 else 'ACCEPTABLE'
        })

# Trier par score
recommendations.sort(key=lambda x: x['score'], reverse=True)
top5 = recommendations[:5]

print(f"\n🏆 TOP 5 RECOMMANDATIONS PROFESSIONNELLES")
print(f"   (sur {len(recommendations)} actions qualifiées / {len(data_today)} analysées)")
print("=" * 80)

for i, reco in enumerate(top5, 1):
    print(f"\n{i}. {reco['symbol']} - SCORE: {reco['score']}/100 - {reco['confiance']}")
    print(f"   Prix:         {reco['prix_actuel']:>10,.0f} FCFA")
    print(f"   Momentum 7j:  {reco['momentum_7j']:>10.2f}%")
    print(f"   RSI (14):     {reco['rsi']:>10.2f}" if reco['rsi'] else "   RSI:          Non calculable")
    print(f"   SMA 20:       {reco['sma_20']:>10,.0f}" if reco['sma_20'] else "   SMA 20:       N/A")
    print(f"   Volatilité:   {reco['volatility_20j']:>10.2f}%")
    print(f"   Volume moy:   {reco['volume_avg']:>10,}")
    print(f"   Données:      {reco['nb_jours_data']} jours")
    
    if reco['signals']:
        print(f"\n   🔔 SIGNAUX:")
        for signal in reco['signals'][:5]:
            print(f"      • {signal}")

# Sauvegarder
rapport = {
    'date_generation': datetime.now().isoformat(),
    'date_donnees': date_today,
    'strategie': 'TRADING_PROFESSIONNEL_INDICATEURS_TECHNIQUES',
    'approche': 'Ingénieur Analyste Financier',
    'indicateurs_utilises': ['RSI', 'MACD', 'SMA', 'Bollinger Bands', 'Volume'],
    'seuil_score': 60,
    'actions_analysees': len(data_today),
    'actions_qualifiees': len(recommendations),
    'top_5': top5,
    'scoring': {
        'technique': '40 points (momentum, RSI, MACD, volume)',
        'tendance': '25 points (SMA, Bollinger)',
        'risque_ajuste': '20 points (volatilité, Sharpe)',
        'liquidite': '15 points (volume moyen)'
    }
}

filename = f"top5_pro_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(rapport, f, indent=2, ensure_ascii=False)

print(f"\n📄 Rapport sauvegardé: {filename}")

print("\n" + "=" * 80)
print("✅ RECOMMANDATIONS PROFESSIONNELLES GÉNÉRÉES")
print("=" * 80)
print("Basées sur:")
print("  ✅ RSI (Relative Strength Index)")
print("  ✅ MACD (Moving Average Convergence Divergence)")
print("  ✅ SMA 20/50 (Simple Moving Averages)")
print("  ✅ Bandes de Bollinger")
print("  ✅ Analyse de volume")
print("  ✅ Gestion du risque (volatilité, liquidité)")
print("\nÀ FAIRE:")
print("  ⏳ Backtest rigoureux sur 60 jours")
print("  ⏳ Validation Win Rate ≥60%")
print("=" * 80)

client.close()
