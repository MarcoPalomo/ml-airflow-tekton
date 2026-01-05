"""Module de préparation des données pour l'entraînement"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        
    def load_data(self, data_path: str) -> pd.DataFrame:
        """Charge les données depuis un fichier CSV ou Parquet"""
        try:
            if data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
            elif data_path.endswith('.parquet'):
                df = pd.read_parquet(data_path)
            else:
                raise ValueError(f"Format de fichier non supporté: {data_path}")
            
            logger.info(f"Données chargées: {df.shape[0]} lignes, {df.shape[1]} colonnes")
            return df
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            raise

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie les données (valeurs manquantes, outliers)"""
        # Suppression des lignes avec des valeurs manquantes critiques
        critical_columns = self.config.get('critical_columns', [])
        df_clean = df.dropna(subset=critical_columns)
        
        # Remplissage des valeurs manquantes pour les autres colonnes
        for column in df_clean.select_dtypes(include=[np.number]).columns:
            df_clean[column] = df_clean[column].fillna(df_clean[column].median())
        
        for column in df_clean.select_dtypes(include=['object']).columns:
            df_clean[column] = df_clean[column].fillna(df_clean[column].mode()[0])
        
        # Suppression des outliers (méthode IQR)
        numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
        for column in numeric_columns:
            Q1 = df_clean[column].quantile(0.25)
            Q3 = df_clean[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df_clean = df_clean[(df_clean[column] >= lower_bound) & (df_clean[column] <= upper_bound)]
        
        logger.info(f"Données après nettoyage: {df_clean.shape[0]} lignes")
        return df_clean

    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Création de nouvelles features"""
        df_features = df.copy()
        
        # Exemple: features temporelles si une colonne date existe
        date_columns = self.config.get('date_columns', [])
        for col in date_columns:
            if col in df_features.columns:
                df_features[col] = pd.to_datetime(df_features[col])
                df_features[f'{col}_year'] = df_features[col].dt.year
                df_features[f'{col}_month'] = df_features[col].dt.month
                df_features[f'{col}_dayofweek'] = df_features[col].dt.dayofweek
        
        # Exemple: features d'agrégation par client
        if 'customer_id' in df_features.columns and 'amount' in df_features.columns:
            customer_stats = df_features.groupby('customer_id')['amount'].agg([
                'mean', 'std', 'count', 'sum'
            ]).rename(columns={
                'mean': 'customer_avg_amount',
                'std': 'customer_std_amount',
                'count': 'customer_transaction_count',
                'sum': 'customer_total_amount'
            })
            df_features = df_features.merge(customer_stats, on='customer_id', how='left')
        
        return df_features

    def encode_features(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """Encode les variables catégorielles"""
        df_encoded = df.copy()
        
        categorical_columns = df_encoded.select_dtypes(include=['object']).columns
        target_column = self.config.get('target_column', 'target')
        
        # Exclure la colonne target de l'encodage
        categorical_columns = [col for col in categorical_columns if col != target_column]
        
        for column in categorical_columns:
            if is_training:
                # Créer et ajuster l'encodeur
                le = LabelEncoder()
                df_encoded[column] = le.fit_transform(df_encoded[column].astype(str))
                self.label_encoders[column] = le
            else:
                # Utiliser l'encodeur existant
                if column in self.label_encoders:
                    le = self.label_encoders[column]
                    # Gérer les valeurs non vues
                    mask = df_encoded[column].astype(str).isin(le.classes_)
                    df_encoded.loc[mask, column] = le.transform(df_encoded.loc[mask, column].astype(str))
                    df_encoded.loc[~mask, column] = -1  # Valeur pour les catégories inconnues
                
        return df_encoded

    def scale_features(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """Normalise les features numériques"""
        df_scaled = df.copy()
        target_column = self.config.get('target_column', 'target')
        
        # Identifier les colonnes numériques (exclure la target)
        numeric_columns = df_scaled.select_dtypes(include=[np.number]).columns
        feature_columns = [col for col in numeric_columns if col != target_column]
        
        if is_training:
            df_scaled[feature_columns] = self.scaler.fit_transform(df_scaled[feature_columns])
            self.feature_columns = feature_columns
        else:
            df_scaled[feature_columns] = self.scaler.transform(df_scaled[feature_columns])
        
        return df_scaled

    def prepare_dataframe(self, df: pd.DataFrame, is_training: bool = False) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Pipeline de préparation des données à partir d'un DataFrame existant.
        Utilisé principalement pour l'inférence (API).

        Args:
            df (pd.DataFrame): DataFrame contenant les données à préparer
            is_training (bool): Indique si on est en mode entraînement ou inférence

        Returns:
            Tuple[pd.DataFrame, pd.Series]: Features préparées et target (vide si pas de target)
        """
        # Nettoyage
        df_clean = self.clean_data(df)

        # Feature engineering
        df_features = self.feature_engineering(df_clean)

        # Encodage
        df_encoded = self.encode_features(df_features, is_training)

        # Scaling
        df_scaled = self.scale_features(df_encoded, is_training)

        # Séparation features/target
        target_column = self.config.get('target_column', 'target')

        if target_column in df_scaled.columns:
            X = df_scaled.drop(columns=[target_column])
            y = df_scaled[target_column]
        else:
            X = df_scaled
            y = pd.Series()

        logger.info(f"DataFrame préparé: {X.shape[0]} lignes, {X.shape[1]} features")
        return X, y

    def prepare_data(self, data_path: str, is_training: bool = True) -> Tuple[pd.DataFrame, pd.Series]:
        """Pipeline complet de préparation des données depuis un fichier"""
        # Chargement
        df = self.load_data(data_path)

        # Utilisation de prepare_dataframe pour le reste du pipeline
        return self.prepare_dataframe(df, is_training)

    def split_data(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, 
                   random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Divise les données en train/test"""
        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)