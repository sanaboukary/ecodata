"""
Service de calcul des ratios financiers et scoring santé économique
Utilisé pour évaluer la solidité économique des pays CEDEAO
"""

from datetime import datetime, timedelta
from plateforme_centralisation.mongo import get_mongo_db
import numpy as np


class FinancialRatiosService:
    """Calcul ratios financiers et scoring santé économique"""
    
    # Seuils de référence (FMI/Banque Mondiale)
    THRESHOLDS = {
        'debt_to_gdp': {
            'excellent': 40,  # < 40%
            'good': 60,       # 40-60%
            'moderate': 90,   # 60-90%
            'high': 90        # > 90%
        },
        'fiscal_balance': {
            'excellent': -3,  # > -3%
            'good': -5,       # -3% à -5%
            'moderate': -8,   # -5% à -8%
            'high': -8        # < -8%
        },
        'inflation': {
            'excellent': 3,   # < 3%
            'good': 5,        # 3-5%
            'moderate': 10,   # 5-10%
            'high': 10        # > 10%
        },
        'current_account': {
            'excellent': -3,  # > -3%
            'good': -5,
            'moderate': -8,
            'high': -8
        },
        'reserves_months': {
            'excellent': 6,   # > 6 mois
            'good': 4,        # 4-6 mois
            'moderate': 3,    # 3-4 mois
            'low': 3          # < 3 mois
        }
    }
    
    def __init__(self):
        _, self.db = get_mongo_db()
    
    def get_latest_value(self, indicator, country, years=1):
        """Récupère valeur la plus récente d'un indicateur"""
        threshold = (datetime.now() - timedelta(days=years*365)).isoformat()
        
        # Requête avec source WorldBank et filtre sur attrs.country
        doc = self.db.curated_observations.find_one(
            {
                'source': 'WorldBank',
                'dataset': indicator,
                'attrs.country': country,
                'ts': {'$gte': threshold}
            },
            sort=[('ts', -1)]
        )
        
        if doc:
            return {
                'value': doc.get('value'),
                'date': doc.get('ts'),
                'source': doc.get('source')
            }
        return None
    
    def calculate_sovereign_ratios(self, country):
        """
        Calcule ratios souverains (crédit pays)
        
        Args:
            country: Code ISO3 (SEN, CIV, etc.)
        
        Returns:
            Dict avec ratios + scoring
        """
        ratios = {}
        
        # 1. Dette/PIB
        debt_data = self.get_latest_value('GC.DOD.TOTL.GD.ZS', country, years=2)
        if debt_data:
            ratios['debt_to_gdp'] = {
                'value': debt_data['value'],
                'unit': '% PIB',
                'date': debt_data['date'],
                'level': self._classify_ratio(debt_data['value'], 'debt_to_gdp'),
                'description': 'Dette publique totale en % du PIB'
            }
        
        # 2. Balance fiscale
        fiscal_data = self.get_latest_value('GC.BAL.CASH.GD.ZS', country, years=2)
        if fiscal_data:
            ratios['fiscal_balance'] = {
                'value': fiscal_data['value'],
                'unit': '% PIB',
                'date': fiscal_data['date'],
                'level': self._classify_ratio(fiscal_data['value'], 'fiscal_balance', reverse=True),
                'description': 'Balance budgétaire (déficit si négatif)'
            }
        
        # 3. Inflation
        inflation_data = self.get_latest_value('FP.CPI.TOTL.ZG', country, years=1)
        if inflation_data:
            ratios['inflation'] = {
                'value': inflation_data['value'],
                'unit': '%',
                'date': inflation_data['date'],
                'level': self._classify_ratio(inflation_data['value'], 'inflation'),
                'description': 'Taux d\'inflation annuel'
            }
        
        # 4. Compte courant
        current_account_data = self.get_latest_value('BN.CAB.XOKA.GD.ZS', country, years=2)
        if current_account_data:
            ratios['current_account'] = {
                'value': current_account_data['value'],
                'unit': '% PIB',
                'date': current_account_data['date'],
                'level': self._classify_ratio(current_account_data['value'], 'current_account', reverse=True),
                'description': 'Balance compte courant'
            }
        
        # 5. Réserves de change (en mois d'importations)
        reserves_data = self.get_latest_value('FI.RES.TOTL.MO', country, years=2)
        if reserves_data:
            ratios['reserves_months'] = {
                'value': reserves_data['value'],
                'unit': 'mois',
                'date': reserves_data['date'],
                'level': self._classify_ratio(reserves_data['value'], 'reserves_months', reverse=True),
                'description': 'Réserves en mois d\'importations'
            }
        
        # 6. Croissance PIB
        gdp_growth_data = self.get_latest_value('NY.GDP.MKTP.KD.ZG', country, years=1)
        if gdp_growth_data:
            ratios['gdp_growth'] = {
                'value': gdp_growth_data['value'],
                'unit': '%',
                'date': gdp_growth_data['date'],
                'level': 'excellent' if gdp_growth_data['value'] > 5 else 'good' if gdp_growth_data['value'] > 3 else 'moderate',
                'description': 'Croissance du PIB réel'
            }
        
        # Calcul scoring global
        score = self._calculate_health_score(ratios)
        
        return {
            'country': country,
            'ratios': ratios,
            'health_score': score,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_equity_ratios(self, stock_symbol):
        """
        Calcule ratios actions BRVM
        
        Args:
            stock_symbol: Code action (SNTS, BICC, etc.)
        
        Returns:
            Dict avec ratios valorisation
        """
        ratios = {}
        
        # Prix actuel
        price_data = self.get_latest_value('QUOTES', stock_symbol, years=1)
        if not price_data:
            return {'error': 'No price data found'}
        
        price = price_data['value']
        
        # Bénéfices (mock - nécessiterait données financières réelles)
        # En production: récupérer depuis bilans publiés BRVM
        ratios['price'] = {
            'value': price,
            'unit': 'FCFA',
            'date': price_data['date']
        }
        
        # Calculer variation YTD
        ytd_start = datetime(datetime.now().year, 1, 1).isoformat()
        ytd_price = self.db.curated_observations.find_one(
            {
                'dataset': 'QUOTES',
                'key': stock_symbol,
                'ts': {'$gte': ytd_start}
            },
            sort=[('ts', 1)]
        )
        
        if ytd_price:
            ytd_return = ((price - ytd_price['value']) / ytd_price['value']) * 100
            ratios['ytd_return'] = {
                'value': ytd_return,
                'unit': '%',
                'description': 'Performance depuis début année'
            }
        
        # Volatilité (écart-type 30 jours)
        threshold_30d = (datetime.now() - timedelta(days=30)).isoformat()
        prices_30d = list(self.db.curated_observations.find(
            {
                'dataset': 'QUOTES',
                'key': stock_symbol,
                'ts': {'$gte': threshold_30d}
            },
            sort=[('ts', 1)]
        ))
        
        if len(prices_30d) > 1:
            values = [p['value'] for p in prices_30d]
            returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualisée
            
            ratios['volatility'] = {
                'value': volatility,
                'unit': '%',
                'description': 'Volatilité annualisée (30j)'
            }
        
        return {
            'stock': stock_symbol,
            'ratios': ratios,
            'timestamp': datetime.now().isoformat()
        }
    
    def compare_countries_health(self, countries):
        """
        Compare santé économique de plusieurs pays
        
        Args:
            countries: Liste codes ISO3
        
        Returns:
            Dict avec comparaison + ranking
        """
        results = []
        
        for country in countries:
            analysis = self.calculate_sovereign_ratios(country)
            if 'health_score' in analysis:
                results.append({
                    'country': country,
                    'score': analysis['health_score']['score'],
                    'rating': analysis['health_score']['rating'],
                    'ratios_summary': {
                        k: v.get('level') for k, v in analysis['ratios'].items()
                    }
                })
        
        # Trier par score décroissant
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Ajouter rang
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return {
            'comparison': results,
            'best_performer': results[0] if results else None,
            'worst_performer': results[-1] if results else None,
            'average_score': np.mean([r['score'] for r in results]) if results else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def _classify_ratio(self, value, ratio_type, reverse=False):
        """
        Classifie un ratio selon seuils
        
        Args:
            value: Valeur du ratio
            ratio_type: Type de ratio (debt_to_gdp, etc.)
            reverse: Si True, plus petit = meilleur
        
        Returns:
            Niveau (excellent/good/moderate/high)
        """
        if value is None:
            return 'unknown'
        
        thresholds = self.THRESHOLDS.get(ratio_type, {})
        
        if reverse:
            # Pour ratios où plus petit = meilleur (ex: inflation)
            if value <= thresholds.get('excellent', 0):
                return 'excellent'
            elif value <= thresholds.get('good', 0):
                return 'good'
            elif value <= thresholds.get('moderate', 0):
                return 'moderate'
            else:
                return 'high'
        else:
            # Pour ratios où plus grand = meilleur (ex: réserves)
            if value >= thresholds.get('excellent', 100):
                return 'excellent'
            elif value >= thresholds.get('good', 100):
                return 'good'
            elif value >= thresholds.get('moderate', 100):
                return 'moderate'
            else:
                return 'low'
    
    def _calculate_health_score(self, ratios):
        """
        Calcule score santé économique 0-100
        
        Pondération:
            - Dette/PIB: 25%
            - Balance fiscale: 20%
            - Inflation: 20%
            - Compte courant: 15%
            - Réserves: 10%
            - Croissance: 10%
        """
        weights = {
            'debt_to_gdp': 0.25,
            'fiscal_balance': 0.20,
            'inflation': 0.20,
            'current_account': 0.15,
            'reserves_months': 0.10,
            'gdp_growth': 0.10
        }
        
        level_scores = {
            'excellent': 100,
            'good': 75,
            'moderate': 50,
            'high': 25,
            'low': 25,
            'unknown': 50
        }
        
        total_score = 0
        total_weight = 0
        
        for ratio_name, weight in weights.items():
            if ratio_name in ratios:
                level = ratios[ratio_name].get('level', 'unknown')
                score = level_scores.get(level, 50)
                total_score += score * weight
                total_weight += weight
        
        final_score = total_score / total_weight if total_weight > 0 else 50
        
        # Rating A-F
        if final_score >= 90:
            rating = 'A+'
        elif final_score >= 80:
            rating = 'A'
        elif final_score >= 70:
            rating = 'B+'
        elif final_score >= 60:
            rating = 'B'
        elif final_score >= 50:
            rating = 'C'
        elif final_score >= 40:
            rating = 'D'
        else:
            rating = 'F'
        
        return {
            'score': round(final_score, 1),
            'rating': rating,
            'interpretation': self._interpret_score(final_score)
        }
    
    def _interpret_score(self, score):
        """Interprétation textuelle du score"""
        if score >= 80:
            return "Excellente santé économique, risque souverain faible"
        elif score >= 60:
            return "Bonne santé économique, risque souverain modéré"
        elif score >= 40:
            return "Santé économique fragile, vigilance requise"
        else:
            return "Situation économique préoccupante, risque élevé"


# Singleton
financial_ratios_service = FinancialRatiosService()
