"""
Service de gestion des widgets pour dashboard personnalisable
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from plateforme_centralisation.mongo import get_mongo_db


class WidgetService:
    """Service pour gérer les widgets du dashboard personnalisable"""
    
    WIDGET_TYPES = {
        'kpi': {
            'name': 'KPI Card',
            'icon': '📊',
            'description': 'Carte affichant une valeur clé avec variation',
            'default_size': {'w': 2, 'h': 2},
            'config_schema': ['indicator', 'country', 'color', 'show_variation']
        },
        'line_chart': {
            'name': 'Graphique Ligne',
            'icon': '📈',
            'description': 'Graphique d\'évolution temporelle',
            'default_size': {'w': 4, 'h': 3},
            'config_schema': ['indicator', 'country', 'period', 'color']
        },
        'bar_chart': {
            'name': 'Graphique Barres',
            'icon': '📊',
            'description': 'Comparaison entre pays/indicateurs',
            'default_size': {'w': 4, 'h': 3},
            'config_schema': ['indicator', 'countries', 'color']
        },
        'pie_chart': {
            'name': 'Graphique Circulaire',
            'icon': '🥧',
            'description': 'Répartition en parts',
            'default_size': {'w': 3, 'h': 3},
            'config_schema': ['indicator', 'countries', 'colors']
        },
        'data_table': {
            'name': 'Tableau de Données',
            'icon': '📋',
            'description': 'Tableau avec dernières valeurs',
            'default_size': {'w': 4, 'h': 3},
            'config_schema': ['indicators', 'country', 'limit']
        },
        'map': {
            'name': 'Carte Choroplèthe',
            'icon': '🗺️',
            'description': 'Carte colorée selon indicateur',
            'default_size': {'w': 6, 'h': 4},
            'config_schema': ['indicator', 'colors']
        },
        'alert_list': {
            'name': 'Liste Alertes',
            'icon': '🔔',
            'description': 'Dernières alertes déclenchées',
            'default_size': {'w': 3, 'h': 3},
            'config_schema': ['limit', 'show_resolved']
        },
        'stock_ticker': {
            'name': 'Ticker BRVM',
            'icon': '💹',
            'description': 'Cours temps réel actions',
            'default_size': {'w': 4, 'h': 2},
            'config_schema': ['stocks', 'refresh_interval']
        }
    }
    
    PREDEFINED_LAYOUTS = {
        'gestionnaire_portefeuille': {
            'name': 'Gestionnaire Portefeuille',
            'description': 'Vue complète BRVM + alertes',
            'widgets': [
                {
                    'type': 'stock_ticker',
                    'position': {'x': 0, 'y': 0, 'w': 6, 'h': 2},
                    'config': {'stocks': ['SNTS', 'ORAC', 'BICC', 'SGBC'], 'refresh_interval': 60}
                },
                {
                    'type': 'line_chart',
                    'position': {'x': 6, 'y': 0, 'w': 6, 'h': 3},
                    'config': {'indicator': 'QUOTES', 'country': 'CIV', 'period': '7d', 'color': '#3b82f6'}
                },
                {
                    'type': 'alert_list',
                    'position': {'x': 0, 'y': 2, 'w': 3, 'h': 3},
                    'config': {'limit': 10, 'show_resolved': False}
                },
                {
                    'type': 'kpi',
                    'position': {'x': 3, 'y': 2, 'w': 3, 'h': 2},
                    'config': {'indicator': 'VOLUMES', 'country': 'CIV', 'color': '#10b981', 'show_variation': True}
                }
            ]
        },
        'economiste_pays': {
            'name': 'Économiste Pays',
            'description': 'Analyse macro-économique approfondie',
            'widgets': [
                {
                    'type': 'kpi',
                    'position': {'x': 0, 'y': 0, 'w': 2, 'h': 2},
                    'config': {'indicator': 'NY.GDP.MKTP.CD', 'country': 'SEN', 'color': '#3b82f6', 'show_variation': True}
                },
                {
                    'type': 'kpi',
                    'position': {'x': 2, 'y': 0, 'w': 2, 'h': 2},
                    'config': {'indicator': 'SP.POP.TOTL', 'country': 'SEN', 'color': '#10b981', 'show_variation': True}
                },
                {
                    'type': 'kpi',
                    'position': {'x': 4, 'y': 0, 'w': 2, 'h': 2},
                    'config': {'indicator': 'FP.CPI.TOTL.ZG', 'country': 'SEN', 'color': '#ef4444', 'show_variation': True}
                },
                {
                    'type': 'line_chart',
                    'position': {'x': 0, 'y': 2, 'w': 6, 'h': 3},
                    'config': {'indicator': 'NY.GDP.MKTP.KD.ZG', 'country': 'SEN', 'period': '1y', 'color': '#3b82f6'}
                },
                {
                    'type': 'data_table',
                    'position': {'x': 6, 'y': 0, 'w': 6, 'h': 5},
                    'config': {'indicators': ['SP.POP.TOTL', 'NY.GDP.MKTP.CD', 'FP.CPI.TOTL.ZG'], 'country': 'SEN', 'limit': 10}
                }
            ]
        },
        'analyste_regional': {
            'name': 'Analyste Régional',
            'description': 'Comparaison CEDEAO multi-pays',
            'widgets': [
                {
                    'type': 'map',
                    'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4},
                    'config': {'indicator': 'NY.GDP.MKTP.KD.ZG', 'colors': ['#ef4444', '#fbbf24', '#10b981']}
                },
                {
                    'type': 'bar_chart',
                    'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4},
                    'config': {'indicator': 'NY.GDP.MKTP.CD', 'countries': ['BEN', 'CIV', 'SEN', 'MLI', 'NER'], 'color': '#3b82f6'}
                },
                {
                    'type': 'bar_chart',
                    'position': {'x': 0, 'y': 4, 'w': 6, 'h': 3},
                    'config': {'indicator': 'SP.POP.TOTL', 'countries': ['BEN', 'CIV', 'SEN', 'MLI', 'NER'], 'color': '#10b981'}
                },
                {
                    'type': 'pie_chart',
                    'position': {'x': 6, 'y': 4, 'w': 6, 'h': 3},
                    'config': {'indicator': 'NY.GDP.MKTP.CD', 'countries': ['BEN', 'CIV', 'SEN', 'MLI', 'NER'], 'colors': ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']}
                }
            ]
        },
        'investisseur': {
            'name': 'Investisseur',
            'description': 'Dette + croissance + marchés',
            'widgets': [
                {
                    'type': 'kpi',
                    'position': {'x': 0, 'y': 0, 'w': 3, 'h': 2},
                    'config': {'indicator': 'GC.DOD.TOTL.GD.ZS', 'country': 'CIV', 'color': '#ef4444', 'show_variation': True}
                },
                {
                    'type': 'kpi',
                    'position': {'x': 3, 'y': 0, 'w': 3, 'h': 2},
                    'config': {'indicator': 'NY.GDP.MKTP.KD.ZG', 'country': 'CIV', 'color': '#10b981', 'show_variation': True}
                },
                {
                    'type': 'stock_ticker',
                    'position': {'x': 6, 'y': 0, 'w': 6, 'h': 2},
                    'config': {'stocks': ['SNTS', 'ORAC', 'SGBC', 'BICC', 'PALC'], 'refresh_interval': 30}
                },
                {
                    'type': 'line_chart',
                    'position': {'x': 0, 'y': 2, 'w': 6, 'h': 3},
                    'config': {'indicator': 'GC.DOD.TOTL.GD.ZS', 'country': 'CIV', 'period': '1y', 'color': '#ef4444'}
                },
                {
                    'type': 'bar_chart',
                    'position': {'x': 6, 'y': 2, 'w': 6, 'h': 3},
                    'config': {'indicator': 'NY.GDP.MKTP.KD.ZG', 'countries': ['BEN', 'CIV', 'SEN', 'GHA', 'NGA'], 'color': '#10b981'}
                }
            ]
        }
    }
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
    
    def get_available_widgets(self) -> List[Dict[str, Any]]:
        """Retourner la liste des types de widgets disponibles"""
        return [
            {
                'type': widget_type,
                'name': widget_info['name'],
                'icon': widget_info['icon'],
                'description': widget_info['description'],
                'default_size': widget_info['default_size'],
                'config_schema': widget_info['config_schema']
            }
            for widget_type, widget_info in self.WIDGET_TYPES.items()
        ]
    
    def get_predefined_layouts(self) -> List[Dict[str, Any]]:
        """Retourner les layouts prédéfinis"""
        return [
            {
                'id': layout_id,
                'name': layout_info['name'],
                'description': layout_info['description'],
                'preview': f'/static/img/layouts/{layout_id}.png'  # À créer
            }
            for layout_id, layout_info in self.PREDEFINED_LAYOUTS.items()
        ]
    
    def get_layout_widgets(self, layout_id: str) -> List[Dict[str, Any]]:
        """Récupérer les widgets d'un layout prédéfini"""
        layout = self.PREDEFINED_LAYOUTS.get(layout_id)
        if not layout:
            return []
        return layout['widgets']
    
    def get_widget_data(self, widget_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Récupérer les données pour un widget selon son type et config"""
        
        if widget_type == 'kpi':
            return self._get_kpi_data(config)
        elif widget_type == 'line_chart':
            return self._get_line_chart_data(config)
        elif widget_type == 'bar_chart':
            return self._get_bar_chart_data(config)
        elif widget_type == 'pie_chart':
            return self._get_pie_chart_data(config)
        elif widget_type == 'data_table':
            return self._get_table_data(config)
        elif widget_type == 'map':
            return self._get_map_data(config)
        elif widget_type == 'alert_list':
            return self._get_alerts_data(config)
        elif widget_type == 'stock_ticker':
            return self._get_stock_ticker_data(config)
        else:
            return {'error': 'Unknown widget type'}
    
    def _get_kpi_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données pour widget KPI"""
        indicator = config.get('indicator')
        country = config.get('country')
        show_variation = config.get('show_variation', True)
        
        # Dernière valeur
        query = {'dataset': indicator}
        if country:
            query['key'] = {'$regex': f'^{country}'}
        
        latest = self.db.curated_observations.find(query).sort('ts', -1).limit(1)
        latest_list = list(latest)
        
        if not latest_list:
            return {'error': 'No data'}
        
        current = latest_list[0]
        result = {
            'value': current.get('value'),
            'date': current.get('ts', '').split('T')[0],
            'indicator': indicator,
            'country': country
        }
        
        # Variation si demandée
        if show_variation:
            # Valeur précédente (30 jours avant)
            threshold = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            previous = self.db.curated_observations.find({
                **query,
                'ts': {'$lt': threshold}
            }).sort('ts', -1).limit(1)
            
            previous_list = list(previous)
            if previous_list:
                prev_value = previous_list[0].get('value')
                if prev_value and current.get('value'):
                    variation = ((current['value'] - prev_value) / prev_value) * 100
                    result['variation'] = round(variation, 2)
        
        return result
    
    def _get_line_chart_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données pour graphique ligne"""
        indicator = config.get('indicator')
        country = config.get('country')
        period = config.get('period', '30d')
        
        # Calcul threshold selon période
        days_map = {'7d': 7, '30d': 30, '90d': 90, '1y': 365}
        days = days_map.get(period, 30)
        threshold = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        query = {
            'dataset': indicator,
            'ts': {'$gte': threshold}
        }
        if country:
            query['key'] = {'$regex': f'^{country}'}
        
        docs = self.db.curated_observations.find(query).sort('ts', 1).limit(500)
        
        data = []
        for doc in docs:
            data.append({
                'date': doc.get('ts', '').split('T')[0],
                'value': doc.get('value')
            })
        
        return {
            'labels': [d['date'] for d in data],
            'values': [d['value'] for d in data],
            'indicator': indicator,
            'country': country
        }
    
    def _get_bar_chart_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données pour graphique barres (comparaison pays)"""
        indicator = config.get('indicator')
        countries = config.get('countries', [])
        
        result = {
            'labels': [],
            'values': [],
            'indicator': indicator
        }
        
        for country in countries:
            latest = self.db.curated_observations.find({
                'dataset': indicator,
                'key': {'$regex': f'^{country}'}
            }).sort('ts', -1).limit(1)
            
            latest_list = list(latest)
            if latest_list:
                result['labels'].append(country)
                result['values'].append(latest_list[0].get('value'))
        
        return result
    
    def _get_pie_chart_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données pour graphique circulaire"""
        # Similaire à bar_chart mais formaté pour pie
        bar_data = self._get_bar_chart_data(config)
        return {
            'labels': bar_data['labels'],
            'values': bar_data['values'],
            'colors': config.get('colors', []),
            'indicator': bar_data['indicator']
        }
    
    def _get_table_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données pour tableau"""
        indicators = config.get('indicators', [])
        country = config.get('country')
        limit = config.get('limit', 10)
        
        rows = []
        for indicator in indicators:
            query = {'dataset': indicator}
            if country:
                query['key'] = {'$regex': f'^{country}'}
            
            docs = self.db.curated_observations.find(query).sort('ts', -1).limit(limit)
            
            for doc in docs:
                rows.append({
                    'indicator': indicator,
                    'country': country,
                    'date': doc.get('ts', '').split('T')[0],
                    'value': doc.get('value')
                })
        
        return {'rows': rows[:limit]}
    
    def _get_map_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données pour carte choroplèthe"""
        indicator = config.get('indicator')
        
        # Récupérer dernière valeur pour chaque pays CEDEAO
        country_codes = ['BEN', 'BFA', 'CIV', 'CPV', 'GMB', 'GHA', 'GIN', 'GNB', 'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO']
        
        data = {}
        for country in country_codes:
            latest = self.db.curated_observations.find({
                'dataset': indicator,
                'key': {'$regex': f'^{country}'}
            }).sort('ts', -1).limit(1)
            
            latest_list = list(latest)
            if latest_list:
                data[country] = latest_list[0].get('value')
        
        return {
            'indicator': indicator,
            'data': data,
            'colors': config.get('colors', ['#ef4444', '#fbbf24', '#10b981'])
        }
    
    def _get_alerts_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données pour liste alertes (nécessite models Alert)"""
        limit = config.get('limit', 10)
        show_resolved = config.get('show_resolved', False)
        
        # TODO: Intégrer avec Alert model du Case 2
        # Pour l'instant retourner mock
        return {
            'alerts': [
                {
                    'indicator': 'FP.CPI.TOTL.ZG',
                    'country': 'BEN',
                    'message': 'Inflation supérieure à 5%',
                    'date': datetime.now(timezone.utc).isoformat(),
                    'severity': 'warning'
                }
            ]
        }
    
    def _get_stock_ticker_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Données ticker actions BRVM"""
        stocks = config.get('stocks', [])
        
        result = []
        for stock in stocks:
            latest = self.db.curated_observations.find({
                'dataset': 'QUOTES',
                'key': stock
            }).sort('ts', -1).limit(2)
            
            latest_list = list(latest)
            if len(latest_list) >= 1:
                current = latest_list[0]
                variation = 0
                if len(latest_list) == 2:
                    prev = latest_list[1]
                    if prev.get('value') and current.get('value'):
                        variation = ((current['value'] - prev['value']) / prev['value']) * 100
                
                result.append({
                    'symbol': stock,
                    'price': current.get('value'),
                    'variation': round(variation, 2),
                    'date': current.get('ts', '').split('T')[0]
                })
        
        return {'stocks': result}
    
    def __del__(self):
        """Fermer connexion MongoDB"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except:
            pass


# Singleton
widget_service = WidgetService()
