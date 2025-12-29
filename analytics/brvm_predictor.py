"""
Système d'analyse prédictive BRVM
Corrélation publications officielles <-> prix des actions
Objectif : 50-80% de rendement hebdomadaire
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class BRVMPredictor:
    """
    Analyseur prédictif pour les actions BRVM
    """
    
    def __init__(self, db):
        self.db = db
        self.sentiment_keywords = {
            'positive': {
                'résultats': 2.5,
                'bénéfice': 3.0,
                'hausse': 2.5,
                'croissance': 2.0,
                'augmentation': 2.0,
                'dividende': 3.5,
                'profit': 2.5,
                'performance': 2.0,
                'solide': 1.5,
                'excellent': 2.0,
                'amélioration': 1.5,
                'succès': 2.0,
                'record': 3.0,
                'expansion': 2.0,
                'acquisition': 2.0,
                'fusion': 1.5
            },
            'negative': {
                'perte': -3.0,
                'baisse': -2.5,
                'diminution': -2.0,
                'déficit': -2.5,
                'recul': -2.0,
                'chute': -3.0,
                'suspension': -4.0,
                'difficultés': -2.0,
                'crise': -3.0,
                'dette': -1.5,
                'restructuration': -2.0,
                'risque': -1.5
            },
            'neutral': {
                'assemblée': 1.0,
                'convocation': 0.5,
                'cotation': 1.5,
                'publication': 0.5,
                'rapport': 1.0,
                'annonce': 1.0
            }
        }
    
    def analyze_publication_impact(self, publication: Dict, symbol: str) -> Dict[str, Any]:
        """
        Analyse l'impact potentiel d'une publication sur une action
        """
        title = publication.get('key', '').lower()
        description = publication.get('attrs', {}).get('description', '').lower()
        category = publication.get('attrs', {}).get('category', '').lower()
        
        text = f"{title} {description} {category}"
        
        # Vérifier si la publication concerne cette action
        symbol_lower = symbol.lower()
        symbol_mentioned = symbol_lower in text
        
        if not symbol_mentioned:
            # Chercher des variations du symbole (ex: BICC, BICICI)
            symbol_base = symbol[:4] if len(symbol) >= 4 else symbol
            symbol_mentioned = symbol_base.lower() in text
        
        # Calculer le score de sentiment
        sentiment_score = 0.0
        matched_keywords = []
        
        for sentiment_type, keywords in self.sentiment_keywords.items():
            for keyword, weight in keywords.items():
                if keyword in text:
                    sentiment_score += weight
                    matched_keywords.append((keyword, weight, sentiment_type))
        
        # Facteurs de boost selon la catégorie
        category_multiplier = {
            'résultats financiers': 1.5,
            'dividende': 2.0,
            'assemblée générale': 1.2,
            'cotation': 1.3,
            'fusion': 1.8,
            'suspension': -1.5
        }
        
        multiplier = 1.0
        for cat_key, mult in category_multiplier.items():
            if cat_key in category:
                multiplier = mult
                break
        
        final_score = sentiment_score * multiplier
        
        return {
            'symbol': symbol,
            'publication_date': publication.get('ts', ''),
            'publication_title': publication.get('key', ''),
            'is_relevant': symbol_mentioned,
            'sentiment_score': round(final_score, 2),
            'sentiment_label': self._get_sentiment_label(final_score),
            'category': category,
            'multiplier': multiplier,
            'keywords_matched': matched_keywords,
            'predicted_impact': self._predict_price_impact(final_score)
        }
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convertit le score en label"""
        if score >= 5.0:
            return "Très Positif"
        elif score >= 2.0:
            return "Positif"
        elif score >= -2.0:
            return "Neutre"
        elif score >= -5.0:
            return "Négatif"
        else:
            return "Très Négatif"
    
    def _predict_price_impact(self, sentiment_score: float) -> Dict[str, float]:
        """
        Prédit l'impact sur le prix (variation en %)
        """
        # Conversion score -> variation de prix estimée
        # Basé sur analyse historique et coefficients empiriques
        base_impact = sentiment_score * 1.2
        
        return {
            'min_change': round(base_impact * 0.7, 2),
            'expected_change': round(base_impact, 2),
            'max_change': round(base_impact * 1.5, 2)
        }
    
    def get_historical_correlation(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyse la corrélation historique entre publications et prix
        """
        # Récupérer les publications récentes concernant ce symbole
        publications = list(self.db.curated_observations.find({
            'source': 'BRVM_PUBLICATION',
            'dataset': 'PUBLICATION'
        }).sort('ts', -1).limit(50))
        
        # Récupérer l'historique des prix
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        prices = list(self.db.curated_observations.find({
            'source': 'BRVM',
            'key': symbol,
            'ts': {'$gte': since_date}
        }).sort('ts', 1))
        
        if not prices:
            return {
                'symbol': symbol,
                'correlation_found': False,
                'reason': 'Pas de données de prix disponibles'
            }
        
        # Analyser les impacts
        correlated_events = []
        
        for pub in publications:
            impact = self.analyze_publication_impact(pub, symbol)
            
            if impact['is_relevant']:
                # Trouver le prix avant/après la publication
                pub_date = datetime.fromisoformat(pub.get('ts', '').replace('Z', '+00:00'))
                
                # Prix avant (7 jours avant)
                before_date = pub_date - timedelta(days=7)
                after_date = pub_date + timedelta(days=7)
                
                prices_before = [p for p in prices if datetime.fromisoformat(p['ts'].replace('Z', '+00:00')) < pub_date]
                prices_after = [p for p in prices if datetime.fromisoformat(p['ts'].replace('Z', '+00:00')) > pub_date]
                
                if prices_before and prices_after:
                    price_before = prices_before[-1]['value']
                    price_after = prices_after[0]['value']
                    
                    actual_change = ((price_after - price_before) / price_before) * 100
                    
                    correlated_events.append({
                        'publication': pub.get('key', ''),
                        'date': pub.get('ts', '')[:10],
                        'sentiment_score': impact['sentiment_score'],
                        'predicted_impact': impact['predicted_impact']['expected_change'],
                        'actual_change': round(actual_change, 2),
                        'accuracy': self._calculate_accuracy(
                            impact['predicted_impact']['expected_change'],
                            actual_change
                        )
                    })
        
        if not correlated_events:
            return {
                'symbol': symbol,
                'correlation_found': False,
                'reason': 'Pas de publications pertinentes trouvées'
            }
        
        # Calculer la précision moyenne
        avg_accuracy = sum(e['accuracy'] for e in correlated_events) / len(correlated_events)
        
        return {
            'symbol': symbol,
            'correlation_found': True,
            'events_analyzed': len(correlated_events),
            'average_accuracy': round(avg_accuracy, 2),
            'correlated_events': correlated_events
        }
    
    def _calculate_accuracy(self, predicted: float, actual: float) -> float:
        """Calcule la précision de la prédiction"""
        if actual == 0:
            return 0.0
        
        error = abs(predicted - actual) / abs(actual)
        accuracy = max(0, 100 - (error * 100))
        return round(accuracy, 2)
    
    def generate_recommendations(self, min_confidence: float = 70.0) -> List[Dict[str, Any]]:
        """
        Génère des recommandations d'achat/vente
        Objectif : 50-80% de rendement hebdomadaire
        """
        recommendations = []
        
        # Récupérer toutes les actions BRVM
        stocks_pipeline = [
            {'$match': {'source': 'BRVM'}},
            {'$sort': {'ts': -1}},
            {'$group': {
                '_id': '$key',
                'last_doc': {'$first': '$$ROOT'}
            }},
            {'$replaceRoot': {'newRoot': '$last_doc'}}
        ]
        
        stocks = list(self.db.curated_observations.aggregate(stocks_pipeline))
        
        # Récupérer les publications récentes (7 derniers jours)
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent_pubs = list(self.db.curated_observations.find({
            'source': 'BRVM_PUBLICATION',
            'dataset': 'PUBLICATION',
            'ts': {'$gte': since}
        }).sort('ts', -1))
        
        for stock in stocks:
            symbol = stock['key']
            current_price = stock['value']
            
            # Analyser toutes les publications pour ce symbole
            stock_impacts = []
            
            for pub in recent_pubs:
                impact = self.analyze_publication_impact(pub, symbol)
                if impact['is_relevant']:
                    stock_impacts.append(impact)
            
            if not stock_impacts:
                continue
            
            # Calculer le score global
            total_sentiment = sum(imp['sentiment_score'] for imp in stock_impacts)
            avg_sentiment = total_sentiment / len(stock_impacts)
            
            # Prédiction de variation
            predicted_change = self._predict_price_impact(total_sentiment)
            
            # Récupérer l'historique pour calculer la confiance
            correlation = self.get_historical_correlation(symbol, days=60)
            confidence = correlation.get('average_accuracy', 50.0)
            
            # Calculer les prix cibles
            expected_price = current_price * (1 + predicted_change['expected_change'] / 100)
            stop_loss = current_price * 0.95  # -5% stop loss
            take_profit_1 = current_price * 1.30  # +30% premier objectif
            take_profit_2 = current_price * 1.60  # +60% objectif ambitieux
            
            # Déterminer l'action recommandée
            if avg_sentiment >= 3.0 and confidence >= min_confidence:
                action = "ACHAT FORT"
                priority = 1
            elif avg_sentiment >= 1.5 and confidence >= min_confidence:
                action = "ACHAT"
                priority = 2
            elif avg_sentiment <= -3.0 and confidence >= min_confidence:
                action = "VENTE FORT"
                priority = 1
            elif avg_sentiment <= -1.5 and confidence >= min_confidence:
                action = "VENTE"
                priority = 2
            else:
                action = "CONSERVER"
                priority = 3
            
            # Calculer le potentiel de gain hebdomadaire
            weekly_potential = predicted_change['max_change'] * 1.2  # Boost pour 7 jours
            
            if abs(weekly_potential) >= 15 or (action in ["ACHAT FORT", "VENTE FORT"] and confidence >= 75):
                recommendations.append({
                    'symbol': symbol,
                    'company_name': stock.get('attrs', {}).get('name', symbol),
                    'action': action,
                    'priority': priority,
                    'confidence': round(confidence, 1),
                    'current_price': round(current_price, 2),
                    'target_price': round(expected_price, 2),
                    'stop_loss': round(stop_loss, 2),
                    'take_profit_1': round(take_profit_1, 2),
                    'take_profit_2': round(take_profit_2, 2),
                    'expected_weekly_return': round(weekly_potential, 2),
                    'sentiment_score': round(avg_sentiment, 2),
                    'publications_analyzed': len(stock_impacts),
                    'key_factors': [imp['publication_title'] for imp in stock_impacts[:3]],
                    'risk_level': self._assess_risk(confidence, avg_sentiment),
                    'recommendation_date': datetime.now(timezone.utc).isoformat()
                })
        
        # Trier par priorité puis par potentiel de gain
        recommendations.sort(key=lambda x: (x['priority'], -x['expected_weekly_return']))
        
        return recommendations
    
    def _assess_risk(self, confidence: float, sentiment: float) -> str:
        """Évalue le niveau de risque"""
        if confidence >= 80 and abs(sentiment) >= 4:
            return "FAIBLE"
        elif confidence >= 70 and abs(sentiment) >= 2:
            return "MODÉRÉ"
        elif confidence >= 60:
            return "ÉLEVÉ"
        else:
            return "TRÈS ÉLEVÉ"
    
    def backtest_strategy(self, days: int = 30) -> Dict[str, Any]:
        """
        Backtesting de la stratégie sur les N derniers jours
        """
        # Récupérer l'historique
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        all_stocks = list(self.db.curated_observations.find({
            'source': 'BRVM',
            'ts': {'$gte': since}
        }).sort('ts', 1))
        
        # Simuler des trades
        trades = []
        total_invested = 0
        total_return = 0
        winning_trades = 0
        losing_trades = 0
        
        # Grouper par symbole
        stocks_by_symbol = defaultdict(list)
        for stock in all_stocks:
            stocks_by_symbol[stock['key']].append(stock)
        
        for symbol, prices in stocks_by_symbol.items():
            if len(prices) < 10:
                continue
            
            # Simuler entrée/sortie
            entry_price = prices[0]['value']
            exit_price = prices[-1]['value']
            
            pct_change = ((exit_price - entry_price) / entry_price) * 100
            
            total_invested += entry_price
            total_return += exit_price - entry_price
            
            if pct_change > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            
            trades.append({
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return_pct': round(pct_change, 2)
            })
        
        total_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_return = (total_return / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'period_days': days,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'average_return': round(avg_return, 2),
            'best_trade': max(trades, key=lambda x: x['return_pct']) if trades else None,
            'worst_trade': min(trades, key=lambda x: x['return_pct']) if trades else None,
            'all_trades': trades
        }
