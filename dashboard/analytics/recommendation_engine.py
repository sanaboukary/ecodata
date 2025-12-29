"""
Moteur de recommandations d'investissement BRVM
Basé sur l'analyse des données réelles de la base MongoDB
Intègre: NLP sentiment, RSI, MACD, Bollinger Bands, ATR, Fondamentaux, Macro
"""
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from plateforme_centralisation.mongo import get_mongo_db
import numpy as np

from .sentiment_analyzer import PublicationSentimentAnalyzer
from .technical_indicators import TechnicalIndicators

# Import macro integrator
sys.path.insert(0, 'e:/DISQUE C/Desktop/Implementation plateforme')
from scripts.connectors.macro_economic_integrator import MacroEconomicIntegrator

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Moteur d'analyse et de recommandations pour les actions BRVM"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        self.sentiment_analyzer = PublicationSentimentAnalyzer()
        self.technical = TechnicalIndicators()
        self.macro_integrator = MacroEconomicIntegrator()
    
    def generate_recommendations(self, days=30, min_confidence=60) -> Dict[str, Any]:
        """
        Génère des recommandations d'investissement basées sur les données réelles
        
        Args:
            days: Nombre de jours d'historique à analyser
            min_confidence: Score de confiance minimum (0-100)
        
        Returns:
            Dict contenant les recommandations par catégorie
        """
        try:
            # Calculer la date seuil
            threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Récupérer toutes les actions avec leurs données récentes
            actions = self.db.curated_observations.distinct('key', {'source': 'BRVM'})
            
            buy_signals = []
            sell_signals = []
            hold_signals = []
            high_potential = []
            
            for action in actions:
                analysis = self._analyze_action(action, threshold_date)
                
                if not analysis:
                    continue
                
                # Classifier selon le signal
                if analysis['signal'] == 'BUY' and analysis['confidence'] >= min_confidence:
                    buy_signals.append(analysis)
                    
                    # Actions à fort potentiel (confiance > 75% et potentiel > 15%)
                    if analysis['confidence'] >= 75 and analysis['potential_gain'] >= 15:
                        high_potential.append(analysis)
                        
                elif analysis['signal'] == 'SELL' and analysis['confidence'] >= min_confidence:
                    sell_signals.append(analysis)
                    
                elif analysis['signal'] == 'HOLD':
                    hold_signals.append(analysis)
            
            # Trier par confiance et potentiel
            buy_signals.sort(key=lambda x: (x['confidence'], x['potential_gain']), reverse=True)
            sell_signals.sort(key=lambda x: x['confidence'], reverse=True)
            high_potential.sort(key=lambda x: (x['confidence'], x['potential_gain']), reverse=True)
            
            return {
                'generated_at': datetime.now().isoformat(),
                'analysis_period_days': days,
                'total_actions_analyzed': len(actions),
                'buy_signals': buy_signals[:20],  # Top 20
                'sell_signals': sell_signals[:20],
                'hold_signals': hold_signals[:10],
                'premium_opportunities': high_potential[:10],  # Top 10 à fort potentiel
                'market_summary': self._get_market_summary(),
                'statistics': {
                    'total_buy': len(buy_signals),
                    'total_sell': len(sell_signals),
                    'total_hold': len(hold_signals),
                    'high_potential': len(high_potential)
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
            return self._empty_recommendations()
    
    def _analyze_action(self, symbol: str, threshold_date: str) -> Dict[str, Any]:
        """Analyse une action spécifique avec indicateurs avancés"""
        try:
            # Récupérer l'historique des prix
            price_data = list(self.db.curated_observations.find(
                {
                    'source': 'BRVM',
                    'key': symbol,
                    'ts': {'$gte': threshold_date}
                }
            ).sort('ts', 1))
            
            if len(price_data) < 5:  # Besoin d'au moins 5 observations
                return None
            
            # Extraire les prix et volumes
            prices = [obs['value'] for obs in price_data]
            dates = [obs['ts'][:10] for obs in price_data]
            volumes = [obs.get('attrs', {}).get('volume', 0) for obs in price_data]
            
            # Préparer high/low/close pour ATR
            highs = [obs.get('attrs', {}).get('high', obs['value']) for obs in price_data]
            lows = [obs.get('attrs', {}).get('low', obs['value']) for obs in price_data]
            closes = prices
            
            current_price = prices[-1]
            
            # === INDICATEURS BASIQUES ===
            sma_5 = np.mean(prices[-5:]) if len(prices) >= 5 else current_price
            sma_10 = np.mean(prices[-10:]) if len(prices) >= 10 else current_price
            sma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else current_price
            
            # Volatilité
            returns = np.diff(prices) / prices[:-1] * 100
            volatility = np.std(returns) if len(returns) > 0 else 0
            
            # Tendance
            if len(prices) >= 10:
                x = np.arange(len(prices[-10:]))
                y = prices[-10:]
                slope = np.polyfit(x, y, 1)[0]
                trend = 'UP' if slope > 0 else 'DOWN'
            else:
                trend = 'NEUTRAL'
            
            # Volume
            avg_volume = np.mean(volumes) if volumes else 0
            recent_volume = volumes[-1] if volumes else 0
            volume_ratio = (recent_volume / avg_volume) if avg_volume > 0 else 1
            
            # === INDICATEURS AVANCÉS ===
            
            # RSI
            rsi = self.technical.calculate_rsi(prices, period=14)
            
            # MACD
            macd = self.technical.calculate_macd(prices)
            
            # Bollinger Bands
            bollinger = self.technical.calculate_bollinger_bands(prices, period=20)
            
            # ATR
            atr = self.technical.calculate_atr(highs, lows, closes, period=14)
            
            # Support/Résistance
            recent_high = max(prices[-20:]) if len(prices) >= 20 else max(prices)
            recent_low = min(prices[-20:]) if len(prices) >= 20 else min(prices)
            
            distance_to_high = (recent_high - current_price) / recent_high * 100
            distance_to_low = (current_price - recent_low) / current_price * 100
            
            # === ANALYSE NLP DES PUBLICATIONS ===
            publication_analysis = self._check_publications_nlp(symbol, threshold_date)
            
            # === GÉNÉRATION DU SIGNAL COMPOSITE ===
            signal_score = 0
            reasons = []
            confidence_boost = 0
            
            # Moyennes mobiles (poids: 20%)
            if current_price > sma_5 > sma_10:
                signal_score += 20
                reasons.append("✓ Tendance haussière (prix > SMA5 > SMA10)")
            elif current_price < sma_5 < sma_10:
                signal_score -= 20
                reasons.append("⚠ Tendance baissière (prix < SMA5 < SMA10)")
            
            # RSI (poids: 25%)
            if rsi is not None:
                confidence_boost += 10
                if rsi < 30:
                    signal_score += 30
                    reasons.append(f"🔥 RSI en survente: {rsi:.1f} < 30")
                elif rsi < 40:
                    signal_score += 15
                    reasons.append(f"📊 RSI bas: {rsi:.1f}")
                elif rsi > 70:
                    signal_score -= 30
                    reasons.append(f"⚠️ RSI en surachat: {rsi:.1f} > 70")
                elif rsi > 60:
                    signal_score -= 15
                    reasons.append(f"📊 RSI élevé: {rsi:.1f}")
            
            # MACD (poids: 25%)
            if macd is not None:
                confidence_boost += 15
                if macd['trend'] == 'BULLISH':
                    signal_score += 25
                    reasons.append(f"✓ MACD haussier (histogram: {macd['histogram']:+.4f})")
                else:
                    signal_score -= 25
                    reasons.append(f"⚠ MACD baissier (histogram: {macd['histogram']:+.4f})")
                
                if macd.get('crossover') == 'BULLISH_CROSSOVER':
                    signal_score += 20
                    reasons.append("🚀 Croisement MACD haussier détecté!")
                    confidence_boost += 10
                elif macd.get('crossover') == 'BEARISH_CROSSOVER':
                    signal_score -= 20
                    reasons.append("📉 Croisement MACD baissier détecté!")
                    confidence_boost += 10
            
            # Bollinger Bands (poids: 15%)
            if bollinger is not None:
                confidence_boost += 10
                if bollinger['signal'] == 'OVERSOLD':
                    signal_score += 25
                    reasons.append(f"🔥 Prix sous bande Bollinger: {bollinger['current_price']} < {bollinger['lower']}")
                elif bollinger['signal'] == 'NEAR_OVERSOLD':
                    signal_score += 12
                    reasons.append("📊 Prix proche bande inférieure Bollinger")
                elif bollinger['signal'] == 'OVERBOUGHT':
                    signal_score -= 25
                    reasons.append(f"⚠️ Prix au-dessus bande Bollinger: {bollinger['current_price']} > {bollinger['upper']}")
                elif bollinger['signal'] == 'NEAR_OVERBOUGHT':
                    signal_score -= 12
                    reasons.append("⚠ Prix proche bande supérieure Bollinger")
                
                if bollinger['squeeze']:
                    reasons.append("⚡ Compression Bollinger - Breakout imminent!")
                    confidence_boost += 5
            
            # Volume (poids: 10%)
            if volume_ratio > 1.5:
                signal_score += 15
                reasons.append(f"📈 Volume exceptionnel: {volume_ratio:.1f}x la moyenne")
                confidence_boost += 5
            
            # Momentum (poids: 10%)
            if len(prices) >= 5:
                momentum = (prices[-1] - prices[-5]) / prices[-5] * 100
                if momentum > 5:
                    signal_score += 15
                    reasons.append(f"🚀 Momentum positif 5j: +{momentum:.1f}%")
                elif momentum < -5:
                    signal_score -= 15
                    reasons.append(f"📉 Momentum négatif 5j: {momentum:.1f}%")
            
            # Support/Résistance (poids: 10%)
            if distance_to_low < 5:
                signal_score += 10
                reasons.append(f"✓ Proche du support ({distance_to_low:.1f}% du plus bas)")
            if distance_to_high < 5:
                signal_score -= 10
                reasons.append(f"⚠ Proche de la résistance ({distance_to_high:.1f}% du plus haut)")
            
            # ATR / Volatilité (ajustement confiance)
            if atr is not None:
                if atr['volatility'] == 'HIGH':
                    confidence_boost -= 10
                    reasons.append(f"⚠️ Volatilité élevée: {atr['atr_percent']:.1f}%")
                elif atr['volatility'] == 'LOW':
                    confidence_boost += 10
                    reasons.append(f"✓ Faible volatilité: {atr['atr_percent']:.1f}%")
            
            # === ANALYSE NLP DES PUBLICATIONS (poids: 15%) ===
            if publication_analysis and publication_analysis['impact_level'] != 'LOW':
                pub_score = publication_analysis['sentiment_score']
                
                if pub_score > 50:
                    signal_score += 20
                    confidence_boost += 15
                    reasons.append(f"📰 Publication très positive ({pub_score:.0f}/100)")
                    reasons.extend(publication_analysis['key_signals'][:2])
                elif pub_score > 20:
                    signal_score += 12
                    confidence_boost += 10
                    reasons.append(f"📰 Publication positive ({pub_score:.0f}/100)")
                elif pub_score < -50:
                    signal_score -= 20
                    confidence_boost += 15
                    reasons.append(f"📰 Publication très négative ({pub_score:.0f}/100)")
                    reasons.extend(publication_analysis['key_signals'][:2])
                elif pub_score < -20:
                    signal_score -= 12
                    confidence_boost += 10
                    reasons.append(f"📰 Publication négative ({pub_score:.0f}/100)")
            
            # === ANALYSE FONDAMENTAUX (poids: 20%) ===
            fundamentals = self._get_fundamentals(symbol)
            if fundamentals:
                # P/E Ratio
                if fundamentals.get('pe_ratio'):
                    pe = fundamentals['pe_ratio']
                    if pe < 8:  # Sous-évalué
                        signal_score += 20
                        confidence_boost += 10
                        reasons.append(f"💎 P/E très bas: {pe:.1f} (sous-évalué)")
                    elif pe < 12:
                        signal_score += 10
                        reasons.append(f"✓ P/E attractif: {pe:.1f}")
                    elif pe > 20:
                        signal_score -= 10
                        reasons.append(f"⚠ P/E élevé: {pe:.1f} (surévalué)")
                
                # ROE (Return on Equity)
                if fundamentals.get('roe'):
                    roe = fundamentals['roe']
                    if roe > 15:
                        signal_score += 15
                        reasons.append(f"💪 ROE excellent: {roe:.1f}%")
                    elif roe > 10:
                        signal_score += 8
                        reasons.append(f"✓ ROE bon: {roe:.1f}%")
                    elif roe < 5:
                        signal_score -= 10
                        reasons.append(f"⚠ ROE faible: {roe:.1f}%")
                
                # Ratio d'endettement
                if fundamentals.get('debt_ratio'):
                    debt = fundamentals['debt_ratio']
                    if debt < 30:
                        signal_score += 10
                        confidence_boost += 5
                        reasons.append(f"✓ Dette faible: {debt:.1f}%")
                    elif debt > 50:
                        signal_score -= 10
                        confidence_boost -= 5
                        reasons.append(f"⚠ Endettement élevé: {debt:.1f}%")
                
                # Dividende
                if fundamentals.get('dividend_yield'):
                    div_yield = fundamentals['dividend_yield']
                    if div_yield > 5:
                        signal_score += 15
                        reasons.append(f"💰 Dividende attractif: {div_yield:.1f}%")
                    elif div_yield > 3:
                        signal_score += 8
                        reasons.append(f"✓ Bon dividende: {div_yield:.1f}%")
            
            # === CONTEXTE MACRO-ÉCONOMIQUE (poids: 15%) ===
            macro_context = self.macro_integrator.get_macro_context(symbol, days=365)
            if macro_context and macro_context['macro_signal'] != 'NEUTRAL':
                macro_score = macro_context['macro_score']
                
                if macro_score > 50:
                    signal_score += 20
                    confidence_boost += 10
                    reasons.append(f"🌍 Contexte macro très favorable ({macro_context['sector']})")
                elif macro_score > 20:
                    signal_score += 12
                    confidence_boost += 5
                    reasons.append(f"🌍 Contexte macro favorable ({macro_context['sector']})")
                elif macro_score < -50:
                    signal_score -= 20
                    confidence_boost -= 5
                    reasons.append(f"🌍 Contexte macro défavorable ({macro_context['sector']})")
                elif macro_score < -20:
                    signal_score -= 12
                    reasons.append(f"🌍 Contexte macro neutre-négatif ({macro_context['sector']})")
                
                # Ajouter détails macro si disponibles
                if macro_context.get('indicators'):
                    for ind_name, ind_data in list(macro_context['indicators'].items())[:2]:
                        if ind_data['impact'] == 'POSITIVE':
                            reasons.append(f"  → {ind_name}: {ind_data['trend']} ({ind_data['trend_pct']:+.1f}%)")
            
            # === SIGNAL FINAL ===
            signal_score = max(-100, min(100, signal_score))
            
            # Déterminer le signal
            if signal_score >= 50:
                signal = 'STRONG_BUY'
                base_confidence = 85
                potential_gain = distance_to_high * 0.8
            elif signal_score >= 25:
                signal = 'BUY'
                base_confidence = 70
                potential_gain = distance_to_high * 0.6
            elif signal_score <= -50:
                signal = 'STRONG_SELL'
                base_confidence = 85
                potential_gain = -distance_to_low * 0.6
            elif signal_score <= -25:
                signal = 'SELL'
                base_confidence = 70
                potential_gain = -distance_to_low * 0.4
            else:
                signal = 'HOLD'
                base_confidence = 50
                potential_gain = 0
            
            # Confiance finale
            confidence = min(95, base_confidence + confidence_boost)
            
            # Prix cible et stop loss
            if signal in ['STRONG_BUY', 'BUY']:
                target_price = current_price * (1 + potential_gain / 100)
                stop_loss = current_price * 0.93  # -7% stop loss
                if atr:
                    stop_loss = current_price - (atr['atr'] * 2)  # ATR-based stop
            elif signal in ['STRONG_SELL', 'SELL']:
                target_price = current_price * (1 + potential_gain / 100)
                stop_loss = current_price * 1.07  # +7% stop
            else:
                target_price = current_price
                stop_loss = current_price * 0.95
            
            return {
                'symbol': symbol,
                'signal': signal,
                'confidence': round(confidence, 1),
                'signal_score': round(signal_score, 1),
                'current_price': round(current_price, 2),
                'target_price': round(target_price, 2),
                'stop_loss': round(stop_loss, 2),
                'potential_gain': round(potential_gain, 2),
                
                # Indicateurs basiques
                'volatility': round(volatility, 2),
                'volume_ratio': round(volume_ratio, 2),
                'trend': trend,
                'sma_5': round(sma_5, 2),
                'sma_10': round(sma_10, 2),
                'sma_20': round(sma_20, 2),
                
                # Indicateurs avancés
                'rsi': rsi,
                'macd': macd,
                'bollinger': bollinger,
                'atr': atr,
                
                # Support/Résistance
                'recent_high': round(recent_high, 2),
                'recent_low': round(recent_low, 2),
                
                # Publication analysis
                'publication_sentiment': publication_analysis,
                
                # Fondamentaux
                'fundamentals': fundamentals,
                
                # Macro context
                'macro_context': macro_context,
                
                # Explications
                'reasons': reasons[:10],  # Top 10 raisons
                'data_points': len(price_data),
                'last_update': dates[-1]
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse action {symbol}: {e}")
            return None
    
    def _check_publications_nlp(self, symbol: str, threshold_date: str) -> Dict[str, Any]:
        """Analyse NLP des publications concernant une action"""
        try:
            # Chercher des publications récentes
            publications = list(self.db.curated_observations.find(
                {
                    'source': 'BRVM_PUBLICATION',
                    'ts': {'$gte': threshold_date}
                }
            ))
            
            if not publications:
                return None
            
            # Analyser chaque publication
            best_analysis = None
            max_impact = 0
            
            for pub in publications:
                title = pub.get('key', '')
                description = pub.get('attrs', {}).get('description', '')
                category = pub.get('attrs', {}).get('category', '')
                
                # Vérifier si le symbole est mentionné
                full_text = f"{title} {description}".lower()
                if symbol.lower() in full_text:
                    # Analyser avec NLP
                    analysis = self.sentiment_analyzer.analyze_publication(
                        title, description, category
                    )
                    
                    # Garder l'analyse avec le plus grand impact
                    impact_score = abs(analysis['sentiment_score'])
                    if impact_score > max_impact:
                        max_impact = impact_score
                        best_analysis = analysis
            
            return best_analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse NLP publications: {e}")
            return None
    
    def _get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Récupère les données fondamentales d'une action"""
        try:
            fundamentals = {}
            
            # P/E Ratio
            pe_data = self.db.curated_observations.find_one(
                {'source': 'BRVM_FUNDAMENTALS', 'dataset': 'PE_RATIO', 'key': symbol},
                sort=[('ts', -1)]
            )
            if pe_data:
                fundamentals['pe_ratio'] = pe_data['value']
            
            # ROE
            roe_data = self.db.curated_observations.find_one(
                {'source': 'BRVM_FUNDAMENTALS', 'dataset': 'ROE', 'key': symbol},
                sort=[('ts', -1)]
            )
            if roe_data:
                fundamentals['roe'] = roe_data['value']
            
            # Debt Ratio
            debt_data = self.db.curated_observations.find_one(
                {'source': 'BRVM_FUNDAMENTALS', 'dataset': 'DEBT_RATIO', 'key': symbol},
                sort=[('ts', -1)]
            )
            if debt_data:
                fundamentals['debt_ratio'] = debt_data['value']
            
            # Dividend
            div_data = self.db.curated_observations.find_one(
                {'source': 'BRVM_FUNDAMENTALS', 'dataset': 'DIVIDEND', 'key': symbol},
                sort=[('ts', -1)]
            )
            if div_data:
                fundamentals['dividend_yield'] = div_data['attrs'].get('yield_percent', 0)
                fundamentals['dividend_amount'] = div_data['value']
            
            # Market Cap
            cap_data = self.db.curated_observations.find_one(
                {'source': 'BRVM_FUNDAMENTALS', 'dataset': 'MARKET_CAP', 'key': symbol},
                sort=[('ts', -1)]
            )
            if cap_data:
                fundamentals['market_cap'] = cap_data['value']
            
            return fundamentals if fundamentals else None
            
        except Exception as e:
            logger.error(f"Erreur récupération fondamentaux {symbol}: {e}")
            return None
    
    def _check_publications(self, symbol: str, threshold_date: str) -> str:
        """Vérifie s'il y a des publications concernant une action"""
        try:
            # Chercher des publications mentionnant le symbole
            publications = list(self.db.curated_observations.find(
                {
                    'source': 'BRVM_PUBLICATION',
                    'ts': {'$gte': threshold_date}
                }
            ))
            
            positive_keywords = ['dividende', 'résultats', 'bénéfice', 'croissance', 'augmentation']
            negative_keywords = ['suspension', 'perte', 'baisse', 'déficit', 'alerte']
            
            for pub in publications:
                title = pub.get('key', '').lower()
                
                # Vérifier si le symbole est mentionné
                if symbol.lower() in title:
                    # Analyser le sentiment
                    if any(word in title for word in positive_keywords):
                        return 'POSITIVE'
                    elif any(word in title for word in negative_keywords):
                        return 'NEGATIVE'
            
            return 'NEUTRAL'
            
        except Exception as e:
            logger.error(f"Erreur vérification publications: {e}")
            return 'NEUTRAL'
    
    def _get_market_summary(self) -> Dict[str, Any]:
        """Résumé général du marché"""
        try:
            # Calculer les statistiques du marché
            today = datetime.now().strftime('%Y-%m-%d')
            
            pipeline = [
                {'$match': {'source': 'BRVM', 'ts': {'$gte': today}}},
                {'$group': {
                    '_id': None,
                    'avg_price': {'$avg': '$value'},
                    'total_volume': {'$sum': '$attrs.volume'},
                    'count': {'$sum': 1}
                }}
            ]
            
            result = list(self.db.curated_observations.aggregate(pipeline))
            
            if result:
                stats = result[0]
                return {
                    'average_price': round(stats.get('avg_price', 0), 2),
                    'total_volume': int(stats.get('total_volume', 0)),
                    'active_stocks': stats.get('count', 0),
                    'market_status': 'OPEN' if datetime.now().hour < 16 else 'CLOSED'
                }
            
            return {
                'average_price': 0,
                'total_volume': 0,
                'active_stocks': 0,
                'market_status': 'UNKNOWN'
            }
            
        except Exception as e:
            logger.error(f"Erreur résumé marché: {e}")
            return {}
    
    def _empty_recommendations(self) -> Dict[str, Any]:
        """Retourne une structure vide en cas d'erreur"""
        return {
            'generated_at': datetime.now().isoformat(),
            'analysis_period_days': 0,
            'total_actions_analyzed': 0,
            'buy_signals': [],
            'sell_signals': [],
            'hold_signals': [],
            'premium_opportunities': [],
            'market_summary': {},
            'statistics': {
                'total_buy': 0,
                'total_sell': 0,
                'total_hold': 0,
                'high_potential': 0
            },
            'error': 'Impossible de générer les recommandations'
        }
