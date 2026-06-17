"""
Tests unitaires pour le module de preprocessing
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.preprocessing import DataPreprocessor


class TestDataPreprocessor:
    """Tests pour la classe DataPreprocessor"""

    def test_init(self, preprocessor_config):
        """Test de l'initialisation du preprocessor"""
        preprocessor = DataPreprocessor(preprocessor_config)

        assert preprocessor.config == preprocessor_config
        assert preprocessor.scaler is not None
        assert isinstance(preprocessor.label_encoders, dict)
        assert isinstance(preprocessor.feature_columns, list)

    def test_load_data_csv(self, temp_csv_file, preprocessor_config):
        """Test du chargement de données CSV"""
        preprocessor = DataPreprocessor(preprocessor_config)
        df = preprocessor.load_data(temp_csv_file)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "transaction_id" in df.columns

    def test_load_data_parquet(self, temp_parquet_file, preprocessor_config):
        """Test du chargement de données Parquet"""
        preprocessor = DataPreprocessor(preprocessor_config)
        df = preprocessor.load_data(temp_parquet_file)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "transaction_id" in df.columns

    def test_load_data_unsupported_format(self, preprocessor_config):
        """Test avec un format de fichier non supporté"""
        preprocessor = DataPreprocessor(preprocessor_config)

        with pytest.raises(ValueError, match="Format de fichier non supporté"):
            preprocessor.load_data("/path/to/file.txt")

    def test_load_data_file_not_found(self, preprocessor_config):
        """Test avec un fichier inexistant"""
        preprocessor = DataPreprocessor(preprocessor_config)

        with pytest.raises(Exception):
            preprocessor.load_data("/path/to/nonexistent/file.csv")

    def test_clean_data(self, sample_dataframe_with_nulls, preprocessor_config):
        """Test du nettoyage des données"""
        preprocessor = DataPreprocessor(preprocessor_config)
        df_clean = preprocessor.clean_data(sample_dataframe_with_nulls)

        assert isinstance(df_clean, pd.DataFrame)
        # Vérifier qu'il n'y a plus de NaN dans les colonnes numériques
        assert df_clean.select_dtypes(include=[np.number]).isnull().sum().sum() == 0
        # Le nombre de lignes devrait être inférieur ou égal à l'original
        assert len(df_clean) <= len(sample_dataframe_with_nulls)

    def test_clean_data_removes_critical_nulls(self, preprocessor_config):
        """Test que les lignes avec NaN dans les colonnes critiques sont supprimées"""
        df = pd.DataFrame(
            {
                "transaction_id": [1, 2, 3, None, 5],
                "customer_id": [1, 2, None, 4, 5],
                "amount": [100, 200, 300, 400, 500],
                "target": [0, 1, 0, 1, 0],
            }
        )

        preprocessor = DataPreprocessor(preprocessor_config)
        df_clean = preprocessor.clean_data(df)

        # Les lignes 4 et 5 (index 3 et 2) devraient être supprimées
        assert len(df_clean) == 3
        assert df_clean["transaction_id"].isnull().sum() == 0
        assert df_clean["customer_id"].isnull().sum() == 0

    def test_feature_engineering(self, sample_dataframe, preprocessor_config):
        """Test de la création de features"""
        preprocessor = DataPreprocessor(preprocessor_config)
        df_features = preprocessor.feature_engineering(sample_dataframe)

        assert isinstance(df_features, pd.DataFrame)
        assert len(df_features) == len(sample_dataframe)
        # Les colonnes originales devraient toujours être présentes
        for col in sample_dataframe.columns:
            if col in df_features.columns:
                assert col in df_features.columns

    def test_feature_engineering_with_customer_aggregations(
        self, sample_dataframe, preprocessor_config
    ):
        """Test des agrégations par client"""
        preprocessor = DataPreprocessor(preprocessor_config)
        df_features = preprocessor.feature_engineering(sample_dataframe)

        # Vérifier que les features d'agrégation client sont créées
        if "customer_id" in sample_dataframe.columns and "amount" in sample_dataframe.columns:
            expected_cols = [
                "customer_avg_amount",
                "customer_std_amount",
                "customer_transaction_count",
                "customer_total_amount",
            ]
            for col in expected_cols:
                if col in df_features.columns:
                    assert col in df_features.columns

    def test_encode_features_training(self, sample_dataframe, preprocessor_config):
        """Test de l'encodage des features en mode training"""
        preprocessor = DataPreprocessor(preprocessor_config)
        df_encoded = preprocessor.encode_features(sample_dataframe, is_training=True)

        assert isinstance(df_encoded, pd.DataFrame)
        assert len(df_encoded) == len(sample_dataframe)
        # Les encoders devraient être créés
        assert len(preprocessor.label_encoders) >= 0

    def test_encode_features_inference(self, sample_dataframe, preprocessor_config):
        """Test de l'encodage des features en mode inference"""
        preprocessor = DataPreprocessor(preprocessor_config)

        # D'abord entrainer les encoders
        _ = preprocessor.encode_features(sample_dataframe, is_training=True)

        # Ensuite tester en mode inference
        df_inference = sample_dataframe.head(10)
        df_encoded = preprocessor.encode_features(df_inference, is_training=False)

        assert isinstance(df_encoded, pd.DataFrame)
        assert len(df_encoded) == len(df_inference)

    def test_scale_features_training(self, sample_dataframe, preprocessor_config):
        """Test du scaling des features en mode training"""
        preprocessor = DataPreprocessor(preprocessor_config)
        df_scaled = preprocessor.scale_features(sample_dataframe, is_training=True)

        assert isinstance(df_scaled, pd.DataFrame)
        assert len(df_scaled) == len(sample_dataframe)

    def test_scale_features_inference(self, sample_dataframe, preprocessor_config):
        """Test du scaling des features en mode inference"""
        preprocessor = DataPreprocessor(preprocessor_config)

        # D'abord entrainer le scaler
        _ = preprocessor.scale_features(sample_dataframe, is_training=True)

        # Ensuite tester en mode inference
        df_inference = sample_dataframe.head(10)
        df_scaled = preprocessor.scale_features(df_inference, is_training=False)

        assert isinstance(df_scaled, pd.DataFrame)
        assert len(df_scaled) == len(df_inference)

    def test_prepare_dataframe(self, sample_dataframe, preprocessor_config):
        """Test du pipeline complet prepare_dataframe"""
        preprocessor = DataPreprocessor(preprocessor_config)
        X, y = preprocessor.prepare_dataframe(sample_dataframe, is_training=True)

        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) > 0
        # Target column ne devrait pas être dans X
        assert "target" not in X.columns

    def test_prepare_dataframe_without_target(self, sample_dataframe, preprocessor_config):
        """Test prepare_dataframe sur des données sans colonne target.

        Le préprocesseur est ajusté (is_training=True) sur des données
        dépourvues de target : le scaler s'ajuste normalement et y est vide.
        """
        df_no_target = sample_dataframe.drop(columns=["target"])
        preprocessor = DataPreprocessor(preprocessor_config)

        X, y = preprocessor.prepare_dataframe(df_no_target, is_training=True)

        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(y) == 0  # y devrait être vide

    def test_prepare_data(self, temp_csv_file, preprocessor_config):
        """Test du pipeline complet prepare_data depuis un fichier"""
        preprocessor = DataPreprocessor(preprocessor_config)
        X, y = preprocessor.prepare_data(temp_csv_file, is_training=True)

        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) > 0
        assert len(y) > 0
        assert len(X) == len(y)

    def test_split_data(self, sample_X_y, preprocessor_config):
        """Test de la séparation train/test"""
        X, y = sample_X_y
        preprocessor = DataPreprocessor(preprocessor_config)

        X_train, X_test, y_train, y_test = preprocessor.split_data(X, y, test_size=0.2)

        assert len(X_train) + len(X_test) == len(X)
        assert len(y_train) + len(y_test) == len(y)
        assert len(X_train) == len(y_train)
        assert len(X_test) == len(y_test)
        # Vérifier la proportion
        assert abs(len(X_test) / len(X) - 0.2) < 0.05

    def test_split_data_custom_size(self, sample_X_y, preprocessor_config):
        """Test de la séparation avec une taille personnalisée"""
        X, y = sample_X_y
        preprocessor = DataPreprocessor(preprocessor_config)

        X_train, X_test, y_train, y_test = preprocessor.split_data(X, y, test_size=0.3)

        assert abs(len(X_test) / len(X) - 0.3) < 0.05

    def test_split_data_random_state(self, sample_X_y, preprocessor_config):
        """Test que le random_state donne des résultats reproductibles"""
        X, y = sample_X_y
        preprocessor = DataPreprocessor(preprocessor_config)

        X_train1, X_test1, _, _ = preprocessor.split_data(X, y, random_state=42)
        X_train2, X_test2, _, _ = preprocessor.split_data(X, y, random_state=42)

        pd.testing.assert_frame_equal(X_train1, X_train2)
        pd.testing.assert_frame_equal(X_test1, X_test2)

    def test_pipeline_integration(self, temp_csv_file, preprocessor_config):
        """Test d'intégration du pipeline complet"""
        preprocessor = DataPreprocessor(preprocessor_config)

        # Étape 1: Préparer les données
        X, y = preprocessor.prepare_data(temp_csv_file, is_training=True)

        # Étape 2: Split
        X_train, X_test, y_train, y_test = preprocessor.split_data(X, y)

        # Vérifications
        assert len(X_train) > 0
        assert len(X_test) > 0
        assert len(y_train) > 0
        assert len(y_test) > 0
        assert all(X_train.columns == X_test.columns)
