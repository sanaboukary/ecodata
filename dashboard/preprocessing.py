"""
MODULE DE PRÉTRAITEMENT DES DONNÉES
====================================
Nettoyage, validation et transformation des données brutes avant analyse.
Réutilisable pour toutes les sources : BRVM, WorldBank, IMF, AfDB, UN SDG.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Classe principale de prétraitement des données brutes.
    
    Fonctionnalités :
    - Nettoyage des données (doublons, valeurs invalides)
    - Gestion des valeurs manquantes (interpolation, forward/backward fill)
    - Détection et traitement des outliers (Z-score, IQR)
    - Validation des données (cohérence, plages valides)
    - Normalisation et standardisation
    - Agrégation temporelle (jour → semaine → mois → année)
    """
    
    def __init__(self, source: str, validate_ranges: bool = True):
        """
        Initialise le préprocesseur pour une source donnée.
        
        Args:
            source: Source des données (BRVM, WorldBank, IMF, AfDB, UN_SDG)
            validate_ranges: Activer la validation des plages de valeurs
        """
        self.source = source
        self.validate_ranges = validate_ranges
        self.stats = {
            'total_records': 0,
            'cleaned_records': 0,
            'duplicates_removed': 0,
            'missing_values_filled': 0,
            'outliers_detected': 0,
            'invalid_records': 0
        }
    
    def clean_raw_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Nettoie les données brutes MongoDB.
        
        Args:
            raw_data: Liste de documents MongoDB
            
        Returns:
            DataFrame pandas nettoyé
        """
        self.stats['total_records'] = len(raw_data)
        
        if not raw_data:
            logger.warning(f"Aucune donnée brute pour {self.source}")
            return pd.DataFrame()
        
        # Conversion en DataFrame
        df = pd.DataFrame(raw_data)

        # Normaliser le schéma (ex: BRVM prices_daily -> key/ts/value)
        df = self._normalize_schema(df)

        # 1. Supprimer les doublons (tolérant si certaines colonnes n'existent pas)
        initial_count = len(df)
        dup_subset = [c for c in ['source', 'key', 'ts'] if c in df.columns]
        if dup_subset:
            df = df.drop_duplicates(subset=dup_subset, keep='first')
        self.stats['duplicates_removed'] = initial_count - len(df)
        
        # 2. Conversion des types
        df = self._convert_types(df)
        
        # 3. Validation des valeurs
        if self.validate_ranges:
            df = self._validate_values(df)
        
        # 4. Tri chronologique
        sort_cols = [c for c in ['key', 'ts'] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)
        
        self.stats['cleaned_records'] = len(df)
        
        logger.info(f"Nettoyage {self.source}: {self.stats['total_records']} → {self.stats['cleaned_records']} records")
        logger.info(f"  - Doublons supprimés: {self.stats['duplicates_removed']}")
        logger.info(f"  - Valeurs invalides: {self.stats['invalid_records']}")
        
        return df

    def _normalize_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalise les noms de colonnes pour le pipeline dashboard.

        Le prétraitement historique attend un schéma proche de `curated_observations`:
        - key (identifiant série), ts (timestamp), value (valeur)

        Or certaines vues (ex: BRVM) utilisent des collections dédiées comme `prices_daily`:
        - symbol, date, close, volume, ...
        """
        if df.empty:
            return df

        # BRVM prices_daily -> champs attendus
        if 'key' not in df.columns and 'symbol' in df.columns:
            df['key'] = df['symbol']

        if 'ts' not in df.columns:
            if 'date' in df.columns:
                df['ts'] = df['date']
            elif 'datetime' in df.columns:
                df['ts'] = df['datetime']
            elif 'timestamp' in df.columns:
                df['ts'] = df['timestamp']

        if 'value' not in df.columns:
            if 'close' in df.columns:
                df['value'] = df['close']
            elif 'price' in df.columns:
                df['value'] = df['price']

        # Source/dataset par défaut (utile pour drop_duplicates/aggregate_temporal)
        if 'source' not in df.columns:
            df['source'] = self.source

        if 'dataset' not in df.columns:
            df['dataset'] = self.source

        return df
    
    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convertit les types de données (ts → datetime, value → float)."""
        # Conversion timestamp
        if 'ts' in df.columns:
            df['ts'] = pd.to_datetime(df['ts'], errors='coerce')
            # Supprimer les lignes avec dates invalides
            invalid_dates = df['ts'].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"  - {invalid_dates} dates invalides supprimées")
                df = df.dropna(subset=['ts'])
        
        # Conversion valeur numérique
        if 'value' in df.columns:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        return df
    
    def _validate_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valide les valeurs selon des plages acceptables par type d'indicateur.
        """
        if 'value' not in df.columns or 'key' not in df.columns:
            return df
        
        # Règles de validation par type d'indicateur
        validation_rules = {
            # Pourcentages (0-100)
            'percentage': {
                'patterns': ['_ZS', 'RPCH', 'PCH', 'TOTL.IN.ZS', 'GDP.ZS', 'GNI.ZS'],
                'min': -100,  # Certains peuvent être négatifs (croissance)
                'max': 500    # Tolérance pour outliers exceptionnels
            },
            # Indices (0-1000)
            'index': {
                'patterns': ['_IX', 'INDEX'],
                'min': 0,
                'max': 10000
            },
            # Ratios (0-10)
            'ratio': {
                'patterns': ['RATIO', 'PER_'],
                'min': 0,
                'max': 100
            }
        }
        
        # Marquer les valeurs invalides
        df['is_valid'] = True
        
        for rule_type, rule in validation_rules.items():
            # Identifier les colonnes matchant les patterns
            mask = df['key'].str.contains('|'.join(rule['patterns']), case=False, na=False)
            
            # Valider la plage
            invalid_mask = mask & ((df['value'] < rule['min']) | (df['value'] > rule['max']))
            df.loc[invalid_mask, 'is_valid'] = False
        
        # Compter et supprimer les valeurs invalides
        invalid_count = (~df['is_valid']).sum()
        if invalid_count > 0:
            logger.warning(f"  - {invalid_count} valeurs hors plage détectées")
            self.stats['invalid_records'] = invalid_count
            # Option : supprimer ou marquer
            # df = df[df['is_valid']]  # Supprimer
            df.loc[~df['is_valid'], 'value'] = np.nan  # Marquer comme manquant
        
        df = df.drop(columns=['is_valid'])
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, method: str = 'interpolate') -> pd.DataFrame:
        """
        Gère les valeurs manquantes.
        
        Args:
            df: DataFrame avec valeurs manquantes
            method: Méthode de remplissage
                - 'interpolate': Interpolation linéaire
                - 'ffill': Forward fill (propagation avant)
                - 'bfill': Backward fill (propagation arrière)
                - 'mean': Remplir par la moyenne
                - 'drop': Supprimer les lignes manquantes
                
        Returns:
            DataFrame avec valeurs manquantes traitées
        """
        if 'value' not in df.columns:
            return df
        
        initial_missing = df['value'].isna().sum()
        
        if initial_missing == 0:
            return df
        
        if method == 'interpolate':
            # Interpolation linéaire par série (key)
            df['value'] = df.groupby('key')['value'].transform(
                lambda x: x.interpolate(method='linear', limit_direction='both')
            )
        
        elif method == 'ffill':
            df['value'] = df.groupby('key')['value'].ffill()
        
        elif method == 'bfill':
            df['value'] = df.groupby('key')['value'].bfill()
        
        elif method == 'mean':
            df['value'] = df.groupby('key')['value'].transform(
                lambda x: x.fillna(x.mean())
            )
        
        elif method == 'drop':
            df = df.dropna(subset=['value'])
        
        final_missing = df['value'].isna().sum()
        filled = initial_missing - final_missing
        self.stats['missing_values_filled'] = filled
        
        if filled > 0:
            logger.info(f"  - Valeurs manquantes remplies ({method}): {filled}")
        
        return df
    
    def detect_outliers(self, df: pd.DataFrame, method: str = 'iqr', threshold: float = 3.0) -> pd.DataFrame:
        """
        Détecte les outliers (valeurs aberrantes).
        
        Args:
            df: DataFrame à analyser
            method: Méthode de détection
                - 'iqr': Interquartile Range (Q1-1.5*IQR, Q3+1.5*IQR)
                - 'zscore': Z-score (|z| > threshold)
            threshold: Seuil pour Z-score (défaut: 3.0)
            
        Returns:
            DataFrame avec colonne 'is_outlier'
        """
        if 'value' not in df.columns:
            return df
        
        df['is_outlier'] = False
        
        if method == 'iqr':
            # Détection par IQR pour chaque série
            for key in df['key'].unique():
                mask = df['key'] == key
                values = df.loc[mask, 'value']
                
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = mask & ((df['value'] < lower_bound) | (df['value'] > upper_bound))
                df.loc[outlier_mask, 'is_outlier'] = True
        
        elif method == 'zscore':
            # Détection par Z-score pour chaque série
            for key in df['key'].unique():
                mask = df['key'] == key
                values = df.loc[mask, 'value']
                
                mean = values.mean()
                std = values.std()
                
                if std > 0:
                    z_scores = np.abs((values - mean) / std)
                    outlier_mask = mask & (z_scores > threshold)
                    df.loc[outlier_mask, 'is_outlier'] = True
        
        outlier_count = df['is_outlier'].sum()
        self.stats['outliers_detected'] = outlier_count
        
        if outlier_count > 0:
            logger.info(f"  - Outliers détectés ({method}): {outlier_count}")
        
        return df
    
    def normalize_values(self, df: pd.DataFrame, method: str = 'minmax') -> pd.DataFrame:
        """
        Normalise les valeurs (mise à l'échelle).
        
        Args:
            df: DataFrame à normaliser
            method: Méthode de normalisation
                - 'minmax': Min-Max scaling (0-1)
                - 'zscore': Standardisation (moyenne=0, écart-type=1)
                - 'robust': Robust scaling (médiane, IQR)
                
        Returns:
            DataFrame avec colonne 'value_normalized'
        """
        if 'value' not in df.columns:
            return df
        
        df['value_normalized'] = df['value'].copy()
        
        if method == 'minmax':
            # Normalisation Min-Max par série
            for key in df['key'].unique():
                mask = df['key'] == key
                values = df.loc[mask, 'value']
                
                min_val = values.min()
                max_val = values.max()
                
                if max_val > min_val:
                    df.loc[mask, 'value_normalized'] = (values - min_val) / (max_val - min_val)
        
        elif method == 'zscore':
            # Standardisation Z-score par série
            for key in df['key'].unique():
                mask = df['key'] == key
                values = df.loc[mask, 'value']
                
                mean = values.mean()
                std = values.std()
                
                if std > 0:
                    df.loc[mask, 'value_normalized'] = (values - mean) / std
        
        elif method == 'robust':
            # Robust scaling par série
            for key in df['key'].unique():
                mask = df['key'] == key
                values = df.loc[mask, 'value']
                
                median = values.median()
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                
                if IQR > 0:
                    df.loc[mask, 'value_normalized'] = (values - median) / IQR
        
        logger.info(f"  - Normalisation appliquée ({method})")
        
        return df
    
    def aggregate_temporal(self, df: pd.DataFrame, freq: str = 'M') -> pd.DataFrame:
        """
        Agrège les données par période temporelle.
        
        Args:
            df: DataFrame avec timestamp
            freq: Fréquence d'agrégation
                - 'D': Jour
                - 'W': Semaine
                - 'M': Mois
                - 'Q': Trimestre
                - 'Y': Année
                
        Returns:
            DataFrame agrégé
        """
        if 'ts' not in df.columns or 'value' not in df.columns:
            return df
        
        # Grouper par key et période
        df_agg = df.set_index('ts').groupby(['key', pd.Grouper(freq=freq)]).agg({
            'value': ['mean', 'min', 'max', 'std', 'count'],
            'source': 'first',
            'dataset': 'first'
        }).reset_index()
        
        # Aplatir les colonnes multi-niveaux
        df_agg.columns = ['key', 'ts', 'value_mean', 'value_min', 'value_max', 'value_std', 'count', 'source', 'dataset']
        
        logger.info(f"  - Agrégation temporelle ({freq}): {len(df)} → {len(df_agg)} records")
        
        return df_agg
    
    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de prétraitement."""
        return {
            **self.stats,
            'success_rate': (self.stats['cleaned_records'] / self.stats['total_records'] * 100) 
                           if self.stats['total_records'] > 0 else 0
        }


def preprocess_for_dashboard(raw_data: List[Dict[str, Any]], 
                             source: str,
                             fill_missing: bool = True,
                             detect_outliers: bool = True,
                             temporal_aggregation: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Pipeline complet de prétraitement pour un dashboard.
    
    Args:
        raw_data: Données brutes MongoDB
        source: Source des données
        fill_missing: Remplir les valeurs manquantes
        detect_outliers: Détecter les outliers
        temporal_aggregation: Fréquence d'agrégation (None, 'M', 'Q', 'Y')
        
    Returns:
        (DataFrame prétraité, Statistiques du prétraitement)
    """
    preprocessor = DataPreprocessor(source=source)
    
    # 1. Nettoyage
    df = preprocessor.clean_raw_data(raw_data)
    
    if df.empty:
        return df, preprocessor.get_preprocessing_stats()
    
    # 2. Gestion des valeurs manquantes
    if fill_missing:
        df = preprocessor.handle_missing_values(df, method='interpolate')
    
    # 3. Détection des outliers
    if detect_outliers:
        df = preprocessor.detect_outliers(df, method='iqr')
    
    # 4. Agrégation temporelle (optionnel)
    if temporal_aggregation:
        df = preprocessor.aggregate_temporal(df, freq=temporal_aggregation)
    
    stats = preprocessor.get_preprocessing_stats()
    
    return df, stats
