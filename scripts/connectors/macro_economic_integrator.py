"""
Intégrateur de données macro-économiques pour recommandations BRVM
Corrèle les actions avec les indicateurs WorldBank/IMF/UN
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from plateforme_centralisation.mongo import get_mongo_db

logger = logging.getLogger(__name__)


class MacroEconomicIntegrator:
    """Intègre les données macro-économiques dans l'analyse"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
        
        # Mapping secteurs BRVM -> Indicateurs macro
        self.sector_indicators = {
            'BANQUE': ['GDP', 'LENDING_RATE', 'INFLATION', 'M2'],
            'AGRICULTURE': ['AGRICULTURE_VALUE_ADDED', 'FOOD_PRICE_INDEX', 'RURAL_POPULATION'],
            'TELECOM': ['MOBILE_SUBSCRIPTIONS', 'INTERNET_USERS', 'ICT_EXPORTS'],
            'INDUSTRIE': ['MANUFACTURING_VALUE_ADDED', 'EXPORTS', 'FDI'],
            'DISTRIBUTION': ['HOUSEHOLD_CONSUMPTION', 'RETAIL_SALES', 'URBAN_POPULATION'],
            'ENERGIE': ['ENERGY_CONSUMPTION', 'OIL_PRICE', 'ELECTRICITY_ACCESS'],
            'TRANSPORT': ['FREIGHT_TRANSPORT', 'TRADE_BALANCE', 'LOGISTICS_INDEX'],
        }
        
        # Mapping actions -> Secteurs
        self.stock_sectors = {
            'BOAB': 'BANQUE', 'BOABF': 'BANQUE', 'BOAM': 'BANQUE', 'BOAC': 'BANQUE',
            'BNBC': 'BANQUE', 'CABC': 'BANQUE', 'CBIBF': 'BANQUE', 'ETIT': 'BANQUE',
            'SGBC': 'BANQUE', 'SIBC': 'BANQUE', 'STBC': 'BANQUE', 'CIEC': 'BANQUE',
            
            'PALC': 'AGRICULTURE', 'PHCC': 'AGRICULTURE', 'SCRC': 'AGRICULTURE',
            'SIVC': 'AGRICULTURE', 'SOGC': 'AGRICULTURE', 'SPHC': 'AGRICULTURE',
            
            'ABJC': 'TELECOM', 'SNTS': 'TELECOM', 'ORGT': 'TELECOM',
            
            'BICC': 'INDUSTRIE', 'FTSC': 'INDUSTRIE', 'NEIC': 'INDUSTRIE',
            'NTLC': 'INDUSTRIE', 'PRSC': 'INDUSTRIE', 'SDCC': 'INDUSTRIE',
            'SEMC': 'INDUSTRIE', 'SHEC': 'INDUSTRIE', 'SICC': 'INDUSTRIE',
            'SLBC': 'INDUSTRIE', 'SMBC': 'INDUSTRIE', 'SNCC': 'INDUSTRIE',
            'STAC': 'INDUSTRIE', 'SVOC': 'INDUSTRIE', 'TTLC': 'INDUSTRIE',
            'TTRC': 'INDUSTRIE', 'UNLC': 'INDUSTRIE',
            
            'CFAC': 'DISTRIBUTION', 'SGBSL': 'DISTRIBUTION', 'TTLS': 'DISTRIBUTION',
            
            'CIVC': 'ENERGIE', 'SAFC': 'ENERGIE', 'SDSC': 'ENERGIE',
            
            'ONTBF': 'TRANSPORT', 'TOTAL': 'TRANSPORT', 'SITAB': 'TRANSPORT',
        }
    
    def get_macro_context(self, symbol: str, days: int = 365) -> Dict:
        """
        Récupère le contexte macro-économique pour une action
        
        Returns:
            {
                'sector': 'BANQUE',
                'indicators': {
                    'GDP': {'value': 3.5, 'trend': 'UP', 'impact': 'POSITIVE'},
                    'INFLATION': {'value': 2.1, 'trend': 'DOWN', 'impact': 'POSITIVE'},
                },
                'macro_score': 65,  # -100 à +100
                'macro_signal': 'FAVORABLE'  # FAVORABLE / NEUTRAL / UNFAVORABLE
            }
        """
        try:
            # Déterminer le secteur
            sector = self.stock_sectors.get(symbol, 'UNKNOWN')
            if sector == 'UNKNOWN':
                return self._neutral_context()
            
            # Récupérer les indicateurs pertinents
            relevant_indicators = self.sector_indicators.get(sector, [])
            
            # Analyser chaque indicateur
            indicators_data = {}
            total_score = 0
            count = 0
            
            threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            for indicator in relevant_indicators:
                analysis = self._analyze_indicator(indicator, threshold_date)
                if analysis:
                    indicators_data[indicator] = analysis
                    total_score += analysis['impact_score']
                    count += 1
            
            # Score macro global
            macro_score = (total_score / count) if count > 0 else 0
            
            # Signal macro
            if macro_score >= 30:
                macro_signal = 'FAVORABLE'
            elif macro_score <= -30:
                macro_signal = 'UNFAVORABLE'
            else:
                macro_signal = 'NEUTRAL'
            
            return {
                'sector': sector,
                'indicators': indicators_data,
                'macro_score': round(macro_score, 1),
                'macro_signal': macro_signal,
                'indicators_count': count
            }
            
        except Exception as e:
            logger.error(f"Erreur contexte macro {symbol}: {e}")
            return self._neutral_context()
    
    def _analyze_indicator(self, indicator: str, threshold_date: str) -> Optional[Dict]:
        """Analyse un indicateur macro spécifique"""
        try:
            # Récupérer les données de l'indicateur
            # Chercher dans WorldBank, IMF, UN_SDG
            data = list(self.db.curated_observations.find({
                'key': {'$regex': indicator, '$options': 'i'},
                'ts': {'$gte': threshold_date}
            }).sort('ts', -1).limit(10))
            
            if len(data) < 2:
                return None
            
            # Calculer la tendance
            recent_values = [obs['value'] for obs in data[:5]]
            older_values = [obs['value'] for obs in data[5:]]
            
            recent_avg = sum(recent_values) / len(recent_values)
            older_avg = sum(older_values) / len(older_values) if older_values else recent_avg
            
            if recent_avg > older_avg * 1.05:
                trend = 'UP'
                trend_pct = ((recent_avg - older_avg) / older_avg) * 100
            elif recent_avg < older_avg * 0.95:
                trend = 'DOWN'
                trend_pct = ((recent_avg - older_avg) / older_avg) * 100
            else:
                trend = 'STABLE'
                trend_pct = 0
            
            # Déterminer l'impact selon l'indicateur
            impact_score = self._calculate_impact_score(indicator, trend, trend_pct)
            
            return {
                'value': round(recent_avg, 2),
                'trend': trend,
                'trend_pct': round(trend_pct, 2),
                'impact': 'POSITIVE' if impact_score > 0 else 'NEGATIVE' if impact_score < 0 else 'NEUTRAL',
                'impact_score': impact_score
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse indicateur {indicator}: {e}")
            return None
    
    def _calculate_impact_score(self, indicator: str, trend: str, trend_pct: float) -> float:
        """
        Calcule le score d'impact d'un indicateur sur le secteur
        Returns: -100 à +100
        """
        score = 0
        
        # Indicateurs positifs quand ils augmentent
        positive_indicators = [
            'GDP', 'EXPORTS', 'FDI', 'MANUFACTURING', 'AGRICULTURE_VALUE_ADDED',
            'MOBILE_SUBSCRIPTIONS', 'INTERNET_USERS', 'HOUSEHOLD_CONSUMPTION',
            'ELECTRICITY_ACCESS', 'URBAN_POPULATION', 'ICT_EXPORTS'
        ]
        
        # Indicateurs négatifs quand ils augmentent
        negative_indicators = [
            'INFLATION', 'LENDING_RATE', 'UNEMPLOYMENT', 'DEBT', 'POVERTY',
            'OIL_PRICE'  # Pour la plupart des secteurs sauf énergie
        ]
        
        is_positive = any(ind in indicator.upper() for ind in positive_indicators)
        is_negative = any(ind in indicator.upper() for ind in negative_indicators)
        
        if is_positive:
            if trend == 'UP':
                score = min(50, abs(trend_pct) * 5)
            elif trend == 'DOWN':
                score = -min(50, abs(trend_pct) * 5)
        
        elif is_negative:
            if trend == 'UP':
                score = -min(50, abs(trend_pct) * 5)
            elif trend == 'DOWN':
                score = min(50, abs(trend_pct) * 5)
        
        return score
    
    def _neutral_context(self) -> Dict:
        """Contexte neutre par défaut"""
        return {
            'sector': 'UNKNOWN',
            'indicators': {},
            'macro_score': 0,
            'macro_signal': 'NEUTRAL',
            'indicators_count': 0
        }
    
    def get_country_macro_snapshot(self, country_code: str = 'CI') -> Dict:
        """
        Snapshot macro-économique d'un pays (Côte d'Ivoire par défaut)
        
        Returns:
            {
                'country': 'CI',
                'gdp_growth': 3.5,
                'inflation': 2.1,
                'unemployment': 3.2,
                'overall_health': 'GOOD'  # EXCELLENT / GOOD / NEUTRAL / POOR
            }
        """
        try:
            snapshot = {'country': country_code}
            
            # GDP Growth
            gdp_data = list(self.db.curated_observations.find({
                'key': {'$regex': f'{country_code}.*GDP', '$options': 'i'}
            }).sort('ts', -1).limit(2))
            
            if len(gdp_data) >= 2:
                growth = ((gdp_data[0]['value'] - gdp_data[1]['value']) / gdp_data[1]['value']) * 100
                snapshot['gdp_growth'] = round(growth, 2)
            
            # Inflation
            inflation_data = list(self.db.curated_observations.find({
                'key': {'$regex': f'{country_code}.*INFLATION', '$options': 'i'}
            }).sort('ts', -1).limit(1))
            
            if inflation_data:
                snapshot['inflation'] = round(inflation_data[0]['value'], 2)
            
            # Overall health
            health_score = 0
            if snapshot.get('gdp_growth', 0) > 5:
                health_score += 2
            elif snapshot.get('gdp_growth', 0) > 3:
                health_score += 1
            
            if snapshot.get('inflation', 10) < 3:
                health_score += 2
            elif snapshot.get('inflation', 10) < 5:
                health_score += 1
            
            if health_score >= 4:
                snapshot['overall_health'] = 'EXCELLENT'
            elif health_score >= 2:
                snapshot['overall_health'] = 'GOOD'
            elif health_score >= 0:
                snapshot['overall_health'] = 'NEUTRAL'
            else:
                snapshot['overall_health'] = 'POOR'
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Erreur snapshot pays: {e}")
            return {'country': country_code, 'overall_health': 'UNKNOWN'}


if __name__ == "__main__":
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plateforme_centralisation.settings')
    import django
    django.setup()
    
    logging.basicConfig(level=logging.INFO)
    
    integrator = MacroEconomicIntegrator()
    
    # Test secteur bancaire
    print("\n=== Contexte Macro BOAM (Banque) ===")
    context = integrator.get_macro_context('BOAM', days=365)
    print(f"Secteur: {context['sector']}")
    print(f"Score macro: {context['macro_score']}/100")
    print(f"Signal: {context['macro_signal']}")
    print(f"Indicateurs analysés: {context['indicators_count']}")
    
    # Test pays
    print("\n=== Snapshot Côte d'Ivoire ===")
    snapshot = integrator.get_country_macro_snapshot('CI')
    print(f"PIB Growth: {snapshot.get('gdp_growth', 'N/A')}%")
    print(f"Inflation: {snapshot.get('inflation', 'N/A')}%")
    print(f"Santé économique: {snapshot.get('overall_health')}")
