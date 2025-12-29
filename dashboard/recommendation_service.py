"""
Service de recommandations d'investissement BRVM
Interface entre l'analyseur prédictif et les vues Django
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from analytics.brvm_predictor import BRVMPredictor

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service pour générer et gérer les recommandations d'investissement
    """
    
    @staticmethod
    def get_recommendations(db, min_confidence: float = 70.0) -> Dict[str, Any]:
        """
        Obtenir les recommandations actuelles
        """
        predictor = BRVMPredictor(db)
        
        try:
            recommendations = predictor.generate_recommendations(min_confidence)
            
            # Organiser par catégorie
            strong_buys = [r for r in recommendations if r['action'] == 'ACHAT FORT']
            buys = [r for r in recommendations if r['action'] == 'ACHAT']
            strong_sells = [r for r in recommendations if r['action'] == 'VENTE FORT']
            sells = [r for r in recommendations if r['action'] == 'VENTE']
            holds = [r for r in recommendations if r['action'] == 'CONSERVER']
            
            # Trier par potentiel de gain
            strong_buys.sort(key=lambda x: x['expected_weekly_return'], reverse=True)
            buys.sort(key=lambda x: x['expected_weekly_return'], reverse=True)
            
            # Actions à fort potentiel (>50% de gain hebdomadaire attendu)
            high_potential = [r for r in recommendations if r['expected_weekly_return'] >= 50.0]
            high_potential.sort(key=lambda x: x['expected_weekly_return'], reverse=True)
            
            # Opportunités premium (>70% de confiance et >40% de gain)
            premium_opportunities = [
                r for r in recommendations 
                if r['confidence'] >= 70.0 and r['expected_weekly_return'] >= 40.0
            ]
            premium_opportunities.sort(key=lambda x: (x['confidence'], x['expected_weekly_return']), reverse=True)
            
            # Calculer des statistiques
            total_recs = len(recommendations)
            avg_confidence = sum(r['confidence'] for r in recommendations) / total_recs if total_recs > 0 else 0
            avg_potential = sum(r['expected_weekly_return'] for r in recommendations) / total_recs if total_recs > 0 else 0
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_recommendations': total_recs,
                'average_confidence': round(avg_confidence, 1),
                'average_weekly_potential': round(avg_potential, 2),
                'strong_buys': strong_buys,
                'buys': buys,
                'strong_sells': strong_sells,
                'sells': sells,
                'holds': holds,
                'high_potential_stocks': high_potential,  # Actions à fort potentiel
                'premium_opportunities': premium_opportunities,  # Opportunités premium
                'top_opportunities': strong_buys[:5],  # Top 5 meilleures opportunités
                'min_confidence_threshold': min_confidence,
                'statistics': {
                    'total_high_potential': len(high_potential),
                    'total_premium': len(premium_opportunities),
                    'total_strong_buys': len(strong_buys),
                    'total_buys': len(buys),
                    'total_holds': len(holds),
                    'total_sells': len(sells),
                    'total_strong_sells': len(strong_sells)
                }
            }
        
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_recommendations': 0
            }
    
    @staticmethod
    def get_stock_analysis(db, symbol: str) -> Dict[str, Any]:
        """
        Analyse détaillée d'une action spécifique
        """
        predictor = BRVMPredictor(db)
        
        try:
            # Récupérer les données de l'action
            stock = db.curated_observations.find_one({
                'source': 'BRVM',
                'key': symbol
            }, sort=[('ts', -1)])
            
            if not stock:
                return {'error': f'Action {symbol} non trouvée'}
            
            # Analyse de corrélation
            correlation = predictor.get_historical_correlation(symbol, days=60)
            
            # Publications récentes concernant cette action
            recent_pubs = list(db.curated_observations.find({
                'source': 'BRVM_PUBLICATION',
                'dataset': 'PUBLICATION'
            }).sort('ts', -1).limit(20))
            
            relevant_pubs = []
            for pub in recent_pubs:
                impact = predictor.analyze_publication_impact(pub, symbol)
                if impact['is_relevant']:
                    relevant_pubs.append(impact)
            
            # Générer recommandation
            recommendations = predictor.generate_recommendations(min_confidence=60.0)
            stock_rec = next((r for r in recommendations if r['symbol'] == symbol), None)
            
            return {
                'symbol': symbol,
                'company_name': stock.get('attrs', {}).get('name', symbol),
                'current_price': stock['value'],
                'last_update': stock.get('ts', ''),
                'correlation_analysis': correlation,
                'relevant_publications': relevant_pubs[:5],
                'recommendation': stock_rec,
                'total_relevant_publications': len(relevant_pubs)
            }
        
        except Exception as e:
            logger.error(f"Erreur analyse action {symbol}: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_performance_report(db) -> Dict[str, Any]:
        """
        Rapport de performance du système de recommandations
        """
        predictor = BRVMPredictor(db)
        
        try:
            # Backtesting sur différentes périodes
            backtest_7d = predictor.backtest_strategy(days=7)
            backtest_30d = predictor.backtest_strategy(days=30)
            backtest_90d = predictor.backtest_strategy(days=90)
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'backtest_7_days': backtest_7d,
                'backtest_30_days': backtest_30d,
                'backtest_90_days': backtest_90d,
                'model_accuracy': {
                    '7_days': backtest_7d.get('average_return', 0),
                    '30_days': backtest_30d.get('average_return', 0),
                    '90_days': backtest_90d.get('average_return', 0)
                }
            }
        
        except Exception as e:
            logger.error(f"Erreur rapport performance: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_portfolio_suggestions(db, investment_amount: float = 1000000, risk_profile: str = "balanced") -> Dict[str, Any]:
        """
        Suggestions de portefeuille diversifié
        
        Args:
            investment_amount: Montant à investir (en FCFA)
            risk_profile: conservative, balanced, aggressive
        """
        predictor = BRVMPredictor(db)
        
        # Ajuster les seuils selon le profil de risque
        confidence_thresholds = {
            'conservative': 80.0,
            'balanced': 70.0,
            'aggressive': 60.0
        }
        
        min_confidence = confidence_thresholds.get(risk_profile, 70.0)
        
        try:
            recommendations = predictor.generate_recommendations(min_confidence)
            
            # Sélectionner les meilleures opportunités
            strong_buys = [r for r in recommendations if r['action'] == 'ACHAT FORT']
            buys = [r for r in recommendations if r['action'] == 'ACHAT']
            
            # Allocation selon le profil
            if risk_profile == 'conservative':
                # 70% strong buys, 30% buys
                portfolio_picks = strong_buys[:5] + buys[:2]
                allocation_weights = [0.7 / len(strong_buys[:5])] * len(strong_buys[:5]) + [0.3 / len(buys[:2])] * len(buys[:2])
            
            elif risk_profile == 'aggressive':
                # 100% strong buys
                portfolio_picks = strong_buys[:8]
                allocation_weights = [1.0 / len(portfolio_picks)] * len(portfolio_picks)
            
            else:  # balanced
                # 60% strong buys, 40% buys
                portfolio_picks = strong_buys[:4] + buys[:3]
                allocation_weights = [0.6 / len(strong_buys[:4])] * len(strong_buys[:4]) + [0.4 / len(buys[:3])] * len(buys[:3])
            
            # Calculer les montants par action
            portfolio = []
            total_expected_return = 0
            
            for pick, weight in zip(portfolio_picks, allocation_weights):
                amount = investment_amount * weight
                shares = int(amount / pick['current_price'])
                actual_investment = shares * pick['current_price']
                expected_value = actual_investment * (1 + pick['expected_weekly_return'] / 100)
                expected_profit = expected_value - actual_investment
                
                portfolio.append({
                    'symbol': pick['symbol'],
                    'company': pick['company_name'],
                    'action': pick['action'],
                    'confidence': pick['confidence'],
                    'allocation_pct': round(weight * 100, 1),
                    'amount_to_invest': round(actual_investment, 0),
                    'shares_to_buy': shares,
                    'current_price': pick['current_price'],
                    'target_price': pick['target_price'],
                    'stop_loss': pick['stop_loss'],
                    'take_profit_1': pick['take_profit_1'],
                    'expected_weekly_return': pick['expected_weekly_return'],
                    'expected_profit': round(expected_profit, 0),
                    'risk_level': pick['risk_level']
                })
                
                total_expected_return += expected_profit
            
            total_invested = sum(p['amount_to_invest'] for p in portfolio)
            portfolio_return_pct = (total_expected_return / total_invested * 100) if total_invested > 0 else 0
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'risk_profile': risk_profile,
                'total_investment': round(total_invested, 0),
                'available_cash': round(investment_amount - total_invested, 0),
                'portfolio': portfolio,
                'expected_weekly_return': round(portfolio_return_pct, 2),
                'expected_weekly_profit': round(total_expected_return, 0),
                'diversification': len(portfolio),
                'average_confidence': round(sum(p['confidence'] for p in portfolio) / len(portfolio), 1) if portfolio else 0
            }
        
        except Exception as e:
            logger.error(f"Erreur suggestions portefeuille: {e}")
            return {'error': str(e)}
