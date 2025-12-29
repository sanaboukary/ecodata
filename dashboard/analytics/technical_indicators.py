"""
Indicateurs Techniques Avancés pour Analyse des Actions BRVM
RSI, MACD, Bollinger Bands, ATR, Fibonacci
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calcule les indicateurs techniques avancés"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calcule le RSI (Relative Strength Index)
        
        RSI < 30 = Survente (ACHAT)
        RSI > 70 = Surachat (VENTE)
        
        Returns: Valeur RSI entre 0 et 100, ou None si données insuffisantes
        """
        if len(prices) < period + 1:
            return None
        
        try:
            prices = np.array(prices)
            deltas = np.diff(prices)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception as e:
            logger.error(f"Erreur calcul RSI: {e}")
            return None
    
    @staticmethod
    def calculate_macd(prices: List[float], 
                       fast: int = 12, 
                       slow: int = 26, 
                       signal: int = 9) -> Optional[Dict]:
        """
        Calcule le MACD (Moving Average Convergence Divergence)
        
        MACD > Signal = Haussier (ACHAT)
        MACD < Signal = Baissier (VENTE)
        
        Returns:
            {
                'macd': valeur MACD,
                'signal': ligne de signal,
                'histogram': histogramme (MACD - Signal),
                'trend': 'BULLISH'|'BEARISH',
                'strength': force du signal (0-100)
            }
        """
        if len(prices) < slow + signal:
            return None
        
        try:
            prices = np.array(prices)
            
            # EMA rapide et lente
            ema_fast = TechnicalIndicators._ema(prices, fast)
            ema_slow = TechnicalIndicators._ema(prices, slow)
            
            # MACD
            macd_line = ema_fast - ema_slow
            
            # Ligne de signal
            signal_line = TechnicalIndicators._ema(macd_line, signal)
            
            # Histogramme
            histogram = macd_line - signal_line
            
            # Déterminer la tendance
            current_macd = macd_line[-1]
            current_signal = signal_line[-1]
            current_histogram = histogram[-1]
            
            if current_macd > current_signal:
                trend = 'BULLISH'
                strength = min(100, abs(current_histogram) * 10)
            else:
                trend = 'BEARISH'
                strength = min(100, abs(current_histogram) * 10)
            
            # Détecter les croisements
            previous_histogram = histogram[-2] if len(histogram) > 1 else 0
            crossover = None
            
            if previous_histogram < 0 and current_histogram > 0:
                crossover = 'BULLISH_CROSSOVER'
            elif previous_histogram > 0 and current_histogram < 0:
                crossover = 'BEARISH_CROSSOVER'
            
            return {
                'macd': round(current_macd, 4),
                'signal': round(current_signal, 4),
                'histogram': round(current_histogram, 4),
                'trend': trend,
                'strength': round(strength, 1),
                'crossover': crossover
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul MACD: {e}")
            return None
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], 
                                  period: int = 20, 
                                  std_dev: float = 2.0) -> Optional[Dict]:
        """
        Calcule les Bandes de Bollinger
        
        Prix > Upper Band = Surachat (VENTE)
        Prix < Lower Band = Survente (ACHAT)
        
        Returns:
            {
                'upper': bande supérieure,
                'middle': moyenne mobile,
                'lower': bande inférieure,
                'current_price': prix actuel,
                'percent_b': position dans les bandes (0-1),
                'bandwidth': largeur des bandes (volatilité),
                'signal': 'OVERBOUGHT'|'OVERSOLD'|'NEUTRAL',
                'squeeze': True si compression (breakout à venir)
            }
        """
        if len(prices) < period:
            return None
        
        try:
            prices = np.array(prices)
            recent_prices = prices[-period:]
            
            # Moyenne mobile (bande du milieu)
            middle = np.mean(recent_prices)
            
            # Écart-type
            std = np.std(recent_prices)
            
            # Bandes supérieure et inférieure
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            
            # Prix actuel
            current_price = prices[-1]
            
            # %B (position du prix dans les bandes)
            if upper != lower:
                percent_b = (current_price - lower) / (upper - lower)
            else:
                percent_b = 0.5
            
            # Bandwidth (largeur relative)
            bandwidth = (upper - lower) / middle * 100
            
            # Signal
            if percent_b > 1.0:
                signal = 'OVERBOUGHT'
            elif percent_b < 0.0:
                signal = 'OVERSOLD'
            elif percent_b > 0.8:
                signal = 'NEAR_OVERBOUGHT'
            elif percent_b < 0.2:
                signal = 'NEAR_OVERSOLD'
            else:
                signal = 'NEUTRAL'
            
            # Squeeze (compression = volatilité faible = breakout à venir)
            squeeze = bandwidth < 10  # Seuil arbitraire
            
            return {
                'upper': round(upper, 2),
                'middle': round(middle, 2),
                'lower': round(lower, 2),
                'current_price': round(current_price, 2),
                'percent_b': round(percent_b, 3),
                'bandwidth': round(bandwidth, 2),
                'signal': signal,
                'squeeze': squeeze,
                'std_dev': round(std, 2)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul Bollinger: {e}")
            return None
    
    @staticmethod
    def calculate_atr(highs: List[float], 
                     lows: List[float], 
                     closes: List[float], 
                     period: int = 14) -> Optional[Dict]:
        """
        Calcule l'ATR (Average True Range) - mesure de volatilité
        
        Returns:
            {
                'atr': valeur ATR,
                'atr_percent': ATR en % du prix,
                'volatility': 'HIGH'|'MEDIUM'|'LOW',
                'stop_loss_distance': distance recommandée pour stop-loss
            }
        """
        if len(closes) < period + 1:
            return None
        
        try:
            highs = np.array(highs[-period-1:])
            lows = np.array(lows[-period-1:])
            closes = np.array(closes[-period-1:])
            
            # True Range
            tr1 = highs[1:] - lows[1:]
            tr2 = np.abs(highs[1:] - closes[:-1])
            tr3 = np.abs(lows[1:] - closes[:-1])
            
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # ATR (moyenne du True Range)
            atr = np.mean(true_range[-period:])
            
            # ATR en pourcentage du prix actuel
            current_price = closes[-1]
            atr_percent = (atr / current_price) * 100
            
            # Classification de la volatilité
            if atr_percent > 5:
                volatility = 'HIGH'
            elif atr_percent > 2:
                volatility = 'MEDIUM'
            else:
                volatility = 'LOW'
            
            # Distance stop-loss recommandée (2x ATR)
            stop_loss_distance = atr * 2
            
            return {
                'atr': round(atr, 2),
                'atr_percent': round(atr_percent, 2),
                'volatility': volatility,
                'stop_loss_distance': round(stop_loss_distance, 2),
                'risk_level': 'HIGH' if atr_percent > 5 else 'MEDIUM' if atr_percent > 2 else 'LOW'
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul ATR: {e}")
            return None
    
    @staticmethod
    def calculate_fibonacci_levels(high: float, low: float) -> Dict:
        """
        Calcule les niveaux de Fibonacci pour support/résistance
        
        Returns:
            {
                '0.0': prix haut,
                '23.6': niveau 23.6%,
                '38.2': niveau 38.2%,
                '50.0': niveau 50%,
                '61.8': niveau 61.8%,
                '100.0': prix bas
            }
        """
        try:
            diff = high - low
            
            return {
                '0.0': round(high, 2),
                '23.6': round(high - diff * 0.236, 2),
                '38.2': round(high - diff * 0.382, 2),
                '50.0': round(high - diff * 0.500, 2),
                '61.8': round(high - diff * 0.618, 2),
                '100.0': round(low, 2)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul Fibonacci: {e}")
            return {}
    
    @staticmethod
    def calculate_stochastic(highs: List[float], 
                           lows: List[float], 
                           closes: List[float], 
                           period: int = 14) -> Optional[Dict]:
        """
        Calcule l'Oscillateur Stochastique
        
        %K < 20 = Survente (ACHAT)
        %K > 80 = Surachat (VENTE)
        
        Returns:
            {
                'k': valeur %K,
                'd': valeur %D (moyenne de %K),
                'signal': 'OVERBOUGHT'|'OVERSOLD'|'NEUTRAL'
            }
        """
        if len(closes) < period:
            return None
        
        try:
            highs = np.array(highs[-period:])
            lows = np.array(lows[-period:])
            closes = np.array(closes[-period:])
            
            # %K
            highest_high = np.max(highs)
            lowest_low = np.min(lows)
            current_close = closes[-1]
            
            if highest_high == lowest_low:
                k = 50
            else:
                k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
            
            # %D (moyenne sur 3 périodes, simplifié ici)
            d = k  # Simplification
            
            # Signal
            if k < 20:
                signal = 'OVERSOLD'
            elif k > 80:
                signal = 'OVERBOUGHT'
            else:
                signal = 'NEUTRAL'
            
            return {
                'k': round(k, 2),
                'd': round(d, 2),
                'signal': signal
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul Stochastic: {e}")
            return None
    
    @staticmethod
    def generate_composite_signal(rsi: Optional[float],
                                  macd: Optional[Dict],
                                  bollinger: Optional[Dict],
                                  atr: Optional[Dict]) -> Dict:
        """
        Génère un signal composite basé sur tous les indicateurs
        
        Returns:
            {
                'signal': 'STRONG_BUY'|'BUY'|'HOLD'|'SELL'|'STRONG_SELL',
                'score': -100 à +100,
                'confidence': 0-100,
                'reasons': [liste des raisons]
            }
        """
        score = 0
        confidence = 0
        reasons = []
        
        # RSI
        if rsi is not None:
            confidence += 20
            if rsi < 30:
                score += 30
                reasons.append(f"RSI en survente ({rsi:.1f})")
            elif rsi < 40:
                score += 15
                reasons.append(f"RSI bas ({rsi:.1f})")
            elif rsi > 70:
                score -= 30
                reasons.append(f"RSI en surachat ({rsi:.1f})")
            elif rsi > 60:
                score -= 15
                reasons.append(f"RSI élevé ({rsi:.1f})")
        
        # MACD
        if macd is not None:
            confidence += 25
            if macd['trend'] == 'BULLISH':
                score += 25
                reasons.append(f"MACD haussier ({macd['histogram']:+.4f})")
            else:
                score -= 25
                reasons.append(f"MACD baissier ({macd['histogram']:+.4f})")
            
            if macd.get('crossover') == 'BULLISH_CROSSOVER':
                score += 20
                reasons.append("Croisement MACD haussier détecté")
            elif macd.get('crossover') == 'BEARISH_CROSSOVER':
                score -= 20
                reasons.append("Croisement MACD baissier détecté")
        
        # Bollinger
        if bollinger is not None:
            confidence += 20
            signal = bollinger['signal']
            
            if signal == 'OVERSOLD':
                score += 25
                reasons.append(f"Prix sous bande inférieure ({bollinger['current_price']} < {bollinger['lower']})")
            elif signal == 'NEAR_OVERSOLD':
                score += 15
                reasons.append("Prix proche bande inférieure")
            elif signal == 'OVERBOUGHT':
                score -= 25
                reasons.append(f"Prix au-dessus bande supérieure ({bollinger['current_price']} > {bollinger['upper']})")
            elif signal == 'NEAR_OVERBOUGHT':
                score -= 15
                reasons.append("Prix proche bande supérieure")
            
            if bollinger['squeeze']:
                reasons.append("⚡ Compression Bollinger - Breakout imminent")
        
        # ATR (volatilité)
        if atr is not None:
            confidence += 15
            if atr['volatility'] == 'HIGH':
                confidence -= 10  # Moins confiant en haute volatilité
                reasons.append(f"⚠️ Volatilité élevée ({atr['atr_percent']:.1f}%)")
            elif atr['volatility'] == 'LOW':
                confidence += 10
                reasons.append(f"✓ Faible volatilité ({atr['atr_percent']:.1f}%)")
        
        # Normaliser le score
        score = max(-100, min(100, score))
        confidence = max(0, min(100, confidence))
        
        # Déterminer le signal
        if score >= 50:
            signal = 'STRONG_BUY'
        elif score >= 20:
            signal = 'BUY'
        elif score >= -20:
            signal = 'HOLD'
        elif score >= -50:
            signal = 'SELL'
        else:
            signal = 'STRONG_SELL'
        
        return {
            'signal': signal,
            'score': round(score, 1),
            'confidence': round(confidence, 1),
            'reasons': reasons
        }
    
    @staticmethod
    def _ema(prices: np.ndarray, period: int) -> np.ndarray:
        """Calcule l'EMA (Exponential Moving Average)"""
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        multiplier = 2 / (period + 1)
        
        for i in range(1, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
