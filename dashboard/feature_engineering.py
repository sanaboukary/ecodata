"""
Feature Engineering pour améliorer prédictions ML
Crée features avancées: lags, moving averages, ratios, trends
"""

from datetime import datetime, timedelta
from plateforme_centralisation.mongo import get_mongo_db
import numpy as np
import pandas as pd


class FeatureEngineer:
    """Création features ML avancées"""
    
    def __init__(self):
        _, self.db = get_mongo_db()
    
    def create_time_series_features(self, indicator, country, years=10):
        """
        Crée features séries temporelles complètes
        
        Args:
            indicator: Code indicateur
            country: Code pays
            years: Période historique
        
        Returns:
            DataFrame avec features originales + engineered
        """
        threshold = (datetime.now() - timedelta(days=years*365)).isoformat()
        
        # Récupérer données brutes
        docs = list(self.db.curated_observations.find(
            {
                'dataset': indicator,
                'key': {'$regex': f'^{country}'},
                'ts': {'$gte': threshold}
            },
            sort=[('ts', 1)]
        ))
        
        if len(docs) < 10:
            return {'error': 'Insufficient data (need at least 10 points)'}
        
        # Créer DataFrame
        df = pd.DataFrame([{
            'date': pd.to_datetime(d['ts']),
            'value': d['value']
        } for d in docs])
        
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        # 1. LAG FEATURES (valeurs précédentes)
        for lag in [1, 2, 3, 6, 12]:
            df[f'lag_{lag}'] = df['value'].shift(lag)
        
        # 2. MOVING AVERAGES (moyennes mobiles)
        for window in [3, 6, 12]:
            df[f'ma_{window}'] = df['value'].rolling(window=window).mean()
        
        # 3. EXPONENTIAL MOVING AVERAGES (plus de poids récent)
        for span in [3, 6, 12]:
            df[f'ema_{span}'] = df['value'].ewm(span=span).mean()
        
        # 4. ROLLING STATISTICS
        for window in [6, 12]:
            df[f'std_{window}'] = df['value'].rolling(window=window).std()
            df[f'min_{window}'] = df['value'].rolling(window=window).min()
            df[f'max_{window}'] = df['value'].rolling(window=window).max()
        
        # 5. DIFFERENCES (changements)
        df['diff_1'] = df['value'].diff(1)
        df['diff_12'] = df['value'].diff(12)
        df['pct_change_1'] = df['value'].pct_change(1) * 100
        df['pct_change_12'] = df['value'].pct_change(12) * 100
        
        # 6. TREND FEATURES
        df['value_ma3_ratio'] = df['value'] / df['ma_3']
        df['value_ma12_ratio'] = df['value'] / df['ma_12']
        df['short_long_ma_ratio'] = df['ma_3'] / df['ma_12']
        
        # 7. MOMENTUM INDICATORS
        df['momentum_3'] = df['value'] - df['lag_3']
        df['momentum_12'] = df['value'] - df['lag_12']
        df['acceleration'] = df['diff_1'].diff(1)
        
        # 8. VOLATILITY MEASURES
        df['volatility_6'] = df['std_6'] / df['ma_6']
        df['volatility_12'] = df['std_12'] / df['ma_12']
        
        # 9. RANGE FEATURES
        df['range_6'] = df['max_6'] - df['min_6']
        df['range_12'] = df['max_12'] - df['min_12']
        df['value_position_6'] = (df['value'] - df['min_6']) / (df['max_6'] - df['min_6'])
        
        # 10. TIME FEATURES (cycliques)
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # 11. TREND STRENGTH (R² sur fenêtre glissante)
        for window in [6, 12]:
            df[f'trend_strength_{window}'] = df['value'].rolling(window=window).apply(
                self._calculate_trend_strength, raw=False
            )
        
        return {
            'indicator': indicator,
            'country': country,
            'features': df,
            'feature_count': len(df.columns),
            'data_points': len(df),
            'feature_names': list(df.columns),
            'timestamp': datetime.now().isoformat()
        }
    
    def create_cross_indicator_features(self, country, indicators, years=5):
        """
        Crée features combinant plusieurs indicateurs
        
        Args:
            country: Code pays
            indicators: Liste codes indicateurs
            years: Période
        
        Returns:
            DataFrame avec features cross-indicateur
        """
        threshold = (datetime.now() - timedelta(days=years*365)).isoformat()
        
        # Récupérer toutes données
        dfs = []
        for indicator in indicators:
            docs = list(self.db.curated_observations.find(
                {
                    'dataset': indicator,
                    'key': {'$regex': f'^{country}'},
                    'ts': {'$gte': threshold}
                },
                sort=[('ts', 1)]
            ))
            
            if docs:
                df = pd.DataFrame([{
                    'date': pd.to_datetime(d['ts']),
                    indicator: d['value']
                } for d in docs])
                df.set_index('date', inplace=True)
                dfs.append(df)
        
        if len(dfs) < 2:
            return {'error': 'Need at least 2 indicators with data'}
        
        # Merge sur dates communes
        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how='inner')
        
        # Créer features combinées
        feature_df = result.copy()
        
        # Ratios entre indicateurs (si pertinent)
        if len(indicators) >= 2:
            ind1, ind2 = indicators[0], indicators[1]
            if ind1 in feature_df.columns and ind2 in feature_df.columns:
                feature_df[f'{ind1}_to_{ind2}_ratio'] = feature_df[ind1] / feature_df[ind2]
                feature_df[f'{ind1}_{ind2}_diff'] = feature_df[ind1] - feature_df[ind2]
        
        # Corrélations glissantes
        for window in [6, 12]:
            if len(indicators) >= 2:
                ind1, ind2 = indicators[0], indicators[1]
                feature_df[f'corr_{ind1}_{ind2}_{window}'] = feature_df[ind1].rolling(window=window).corr(feature_df[ind2])
        
        return {
            'country': country,
            'indicators': indicators,
            'features': feature_df,
            'feature_count': len(feature_df.columns),
            'timestamp': datetime.now().isoformat()
        }
    
    def prepare_ml_dataset(self, indicator, country, target_horizon=1, years=10):
        """
        Prépare dataset complet pour ML avec target
        
        Args:
            indicator: Indicateur à prédire
            country: Pays
            target_horizon: Horizon prédiction (1 = 1 période ahead)
            years: Données historiques
        
        Returns:
            Dict avec X (features) et y (target)
        """
        # Créer features
        feature_result = self.create_time_series_features(indicator, country, years)
        
        if 'error' in feature_result:
            return feature_result
        
        df = feature_result['features']
        
        # Créer target (valeur future)
        df['target'] = df['value'].shift(-target_horizon)
        
        # Retirer NaN
        df_clean = df.dropna()
        
        if len(df_clean) < 10:
            return {'error': 'Insufficient clean data after feature engineering'}
        
        # Séparer X et y
        target_col = 'target'
        feature_cols = [c for c in df_clean.columns if c != target_col]
        
        X = df_clean[feature_cols]
        y = df_clean[target_col]
        
        return {
            'X': X,
            'y': y,
            'feature_names': feature_cols,
            'samples': len(X),
            'features_count': len(feature_cols),
            'target_horizon': target_horizon,
            'indicator': indicator,
            'country': country,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_feature_importance(self, X, y, model_type='random_forest'):
        """
        Calcule importance features avec modèle ML
        
        Args:
            X: Features DataFrame
            y: Target Series
            model_type: Type modèle (random_forest, linear, gradient_boost)
        
        Returns:
            Dict avec importance scores
        """
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.linear_model import Ridge
        
        # Choisir modèle
        if model_type == 'random_forest':
            model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
        elif model_type == 'gradient_boost':
            model = GradientBoostingRegressor(n_estimators=50, max_depth=5, random_state=42)
        else:
            model = Ridge(alpha=1.0)
        
        # Entraîner
        model.fit(X, y)
        
        # Extraire importance
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
        else:
            return {'error': 'Model does not provide feature importance'}
        
        # Créer ranking
        feature_importance = [
            {
                'feature': name,
                'importance': float(imp),
                'rank': rank + 1
            }
            for rank, (name, imp) in enumerate(
                sorted(zip(X.columns, importances), key=lambda x: x[1], reverse=True)
            )
        ]
        
        return {
            'feature_importance': feature_importance,
            'top_5': feature_importance[:5],
            'model_type': model_type,
            'total_features': len(feature_importance),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_trend_strength(self, series):
        """Calcule force tendance (R² régression linéaire)"""
        if len(series) < 3:
            return np.nan
        
        X = np.arange(len(series)).reshape(-1, 1)
        y = series.values
        
        # Régression simple
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score
        
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        
        return r2_score(y, y_pred)


# Singleton
feature_engineer = FeatureEngineer()
