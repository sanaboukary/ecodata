"""
Service de prédictions ML pour tendances historiques et forecasting
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

from plateforme_centralisation.mongo import get_mongo_db


class PredictionService:
    """Service pour analyse tendances et prédictions ML"""
    
    def __init__(self):
        self.client, self.db = get_mongo_db()
    
    def get_historical_data(
        self, 
        indicator: str, 
        country: Optional[str] = None,
        years: int = 10,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupérer données historiques pour un indicateur
        
        Args:
            indicator: Code indicateur (SP.POP.TOTL, NY.GDP.MKTP.CD, etc.)
            country: Code pays (BEN, CIV, etc.)
            years: Nombre d'années d'historique
            source: Filtrer par source (WorldBank, IMF, etc.)
        
        Returns:
            Dict avec dates, values, metadata
        """
        threshold = (datetime.now(timezone.utc) - timedelta(days=years*365)).isoformat()
        
        query = {
            'dataset': indicator,
            'ts': {'$gte': threshold}
        }
        
        if country:
            query['key'] = {'$regex': f'^{country}'}
        
        if source:
            query['source'] = source
        
        docs = list(
            self.db.curated_observations
            .find(query)
            .sort('ts', 1)
            .limit(5000)
        )
        
        if not docs:
            return {'error': 'No data found'}
        
        # Extraire dates et valeurs
        dates = []
        values = []
        
        for doc in docs:
            ts = doc.get('ts')
            value = doc.get('value')
            
            if ts and value is not None:
                dates.append(ts.split('T')[0] if isinstance(ts, str) else ts.strftime('%Y-%m-%d'))
                values.append(float(value))
        
        return {
            'dates': dates,
            'values': values,
            'count': len(values),
            'indicator': indicator,
            'country': country,
            'source': source
        }
    
    def calculate_trend(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculer tendance linéaire avec régression
        
        Args:
            data: Données historiques (dates, values)
        
        Returns:
            Dict avec slope, intercept, r2_score, trend_line
        """
        dates = data.get('dates', [])
        values = data.get('values', [])
        
        if len(values) < 3:
            return {'error': 'Insufficient data (need at least 3 points)'}
        
        # Convertir dates en numéros (jours depuis première date)
        date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        first_date = date_objects[0]
        X = np.array([(d - first_date).days for d in date_objects]).reshape(-1, 1)
        y = np.array(values)
        
        # Régression linéaire
        model = LinearRegression()
        model.fit(X, y)
        
        # Prédictions sur données existantes
        y_pred = model.predict(X)
        
        # Métriques
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        # Tendance (positive/negative/stable)
        slope = model.coef_[0]
        trend_direction = 'positive' if slope > 0 else 'negative' if slope < 0 else 'stable'
        
        return {
            'slope': float(slope),
            'intercept': float(model.intercept_),
            'r2_score': float(r2),
            'rmse': float(rmse),
            'direction': trend_direction,  # Nom cohérent avec tests
            'trend_direction': trend_direction,  # Compatibilité
            'trend_line': y_pred.tolist(),
            'model': model,  # Pour prédictions futures
            'X': X,
            'first_date': first_date
        }
    
    def predict_future(
        self, 
        trend_data: Dict[str, Any], 
        months: int = 12
    ) -> Dict[str, Any]:
        """
        Prédire valeurs futures basées sur tendance
        
        Args:
            trend_data: Résultat de calculate_trend()
            months: Nombre de mois à prédire
        
        Returns:
            Dict avec dates futures, valeurs prédites, intervalles confiance
        """
        if 'error' in trend_data:
            return trend_data
        
        model = trend_data.get('model')
        first_date = trend_data.get('first_date')
        last_X = trend_data['X'][-1][0]
        
        # Générer dates futures
        future_dates = []
        future_X = []
        
        for i in range(1, months + 1):
            # Convertir numpy.int64 en int pour timedelta
            days_offset = int(last_X) + (i * 30)
            future_date = first_date + timedelta(days=days_offset)
            future_dates.append(future_date.strftime('%Y-%m-%d'))
            future_X.append([days_offset])
        
        future_X = np.array(future_X)
        
        # Prédictions
        predictions = model.predict(future_X)
        
        # Intervalle de confiance (approximation avec RMSE)
        rmse = trend_data.get('rmse', 0)
        confidence_lower = (predictions - 1.96 * rmse).tolist()
        confidence_upper = (predictions + 1.96 * rmse).tolist()
        
        return {
            'dates': future_dates,
            'predictions': predictions.tolist(),
            'confidence_interval': {
                'lower': confidence_lower,
                'upper': confidence_upper
            },
            'rmse': float(rmse)
        }
    
    def seasonal_decomposition(self, data: Dict[str, Any], period: int = 12) -> Dict[str, Any]:
        """
        Décomposition saisonnière (trend, seasonal, residual)
        
        Args:
            data: Données historiques
            period: Période saisonnière (12 pour mensuel)
        
        Returns:
            Dict avec composantes trend, seasonal, residual
        """
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
        except ImportError:
            return {'error': 'statsmodels not installed'}
        
        values = data.get('values', [])
        
        if len(values) < 2 * period:
            return {'error': f'Insufficient data (need at least {2*period} points for period={period})'}
        
        try:
            # Décomposition
            result = seasonal_decompose(values, model='additive', period=period, extrapolate_trend='freq')
            
            return {
                'trend': result.trend.tolist(),
                'seasonal': result.seasonal.tolist(),
                'residual': result.resid.tolist(),
                'observed': values
            }
        except Exception as e:
            return {'error': f'Decomposition failed: {str(e)}'}
    
    def analyze_volatility(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyser volatilité des données
        
        Args:
            data: Données historiques
        
        Returns:
            Dict avec std, cv, volatility_level
        """
        values = np.array(data.get('values', []))
        
        if len(values) < 2:
            return {'error': 'Insufficient data'}
        
        mean = np.mean(values)
        std = np.std(values)
        cv = (std / mean * 100) if mean != 0 else 0
        
        # Classification volatilité
        if cv < 5:
            volatility_level = 'low'
        elif cv < 15:
            volatility_level = 'medium'
        else:
            volatility_level = 'high'
        
        return {
            'mean': float(mean),
            'std': float(std),
            'coefficient_variation': float(cv),
            'volatility_level': volatility_level,
            'min': float(np.min(values)),
            'max': float(np.max(values))
        }
    
    def get_complete_analysis(
        self, 
        indicator: str, 
        country: Optional[str] = None,
        years: int = 5,
        forecast_months: int = 12
    ) -> Dict[str, Any]:
        """
        Analyse complète: historique + tendance + prédictions + volatilité
        
        Args:
            indicator: Code indicateur
            country: Code pays
            years: Années historique
            forecast_months: Mois à prédire
        
        Returns:
            Dict avec toutes analyses
        """
        # Récupérer historique
        historical = self.get_historical_data(indicator, country, years)
        
        if 'error' in historical:
            return historical
        
        # Tendance
        trend = self.calculate_trend(historical)
        
        # Prédictions
        predictions = {}
        if 'error' not in trend:
            predictions = self.predict_future(trend, forecast_months)
        
        # Volatilité
        volatility = self.analyze_volatility(historical)
        
        # Décomposition saisonnière (si assez de données)
        seasonal = {}
        if len(historical.get('values', [])) >= 24:
            seasonal = self.seasonal_decomposition(historical, period=12)
        
        return {
            'historical': {
                'dates': historical['dates'],
                'values': historical['values'],
                'count': historical['count']
            },
            'trend': {
                'direction': trend.get('trend_direction'),
                'slope': trend.get('slope'),
                'r2_score': trend.get('r2_score'),
                'rmse': trend.get('rmse'),
                'trend_line': trend.get('trend_line')
            },
            'predictions': predictions,
            'volatility': volatility,
            'seasonal': seasonal if 'error' not in seasonal else None,
            'metadata': {
                'indicator': indicator,
                'country': country,
                'years_analyzed': years,
                'forecast_horizon': forecast_months
            }
        }
    
    def compare_models(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comparer plusieurs modèles de prédiction
        
        Args:
            data: Données historiques
        
        Returns:
            Dict avec performance de chaque modèle
        """
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.tree import DecisionTreeRegressor
        
        dates = data.get('dates', [])
        values = data.get('values', [])
        
        if len(values) < 10:
            return {'error': 'Insufficient data for model comparison'}
        
        # Préparer données
        date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        first_date = date_objects[0]
        X = np.array([(d - first_date).days for d in date_objects]).reshape(-1, 1)
        y = np.array(values)
        
        # Split train/test (80/20)
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        models = {
            'Linear Regression': LinearRegression(),
            'Decision Tree': DecisionTreeRegressor(max_depth=5, random_state=42),
            'Random Forest': RandomForestRegressor(n_estimators=10, max_depth=5, random_state=42)
        }
        
        results = {}
        
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                
                results[name] = {
                    'r2_score': float(r2),
                    'rmse': float(rmse),
                    'predictions': y_pred.tolist()
                }
            except Exception as e:
                results[name] = {'error': str(e)}
        
        return results
    
    def detect_anomalies(self, data: Dict[str, Any], threshold: float = 2.0) -> Dict[str, Any]:
        """
        Détecter anomalies dans série temporelle (Z-score)
        
        Args:
            data: Données historiques
            threshold: Seuil Z-score (défaut 2.0 = 95% confiance)
        
        Returns:
            Dict avec indices anomalies, valeurs, dates
        """
        values = np.array(data.get('values', []))
        dates = data.get('dates', [])
        
        if len(values) < 3:
            return {'error': 'Insufficient data'}
        
        # Calcul Z-scores
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return {'anomalies': []}
        
        z_scores = np.abs((values - mean) / std)
        
        # Identifier anomalies
        anomalies = []
        for i, z in enumerate(z_scores):
            if z > threshold:
                anomalies.append({
                    'index': i,
                    'date': dates[i],
                    'value': float(values[i]),
                    'z_score': float(z),
                    'deviation': float((values[i] - mean) / mean * 100)
                })
        
        return {
            'anomalies': anomalies,
            'count': len(anomalies),
            'threshold': threshold
        }
    
    def __del__(self):
        """Fermer connexion MongoDB"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except:
            pass


# Singleton
prediction_service = PredictionService()
