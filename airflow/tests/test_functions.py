"""
Tests unitaires pour les fonctions utilitaires Airflow
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import requests_mock

# Ajouter le chemin au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from dags.utils.functions import (
    calculate_accuracy,
    extract_from_multiple_sources,
    extract_with_trino,
    load_validation_data,
    trigger_tekton_pipeline,
    validate_model_performance,
)


class TestLoadValidationData:
    """Tests pour la fonction load_validation_data"""

    @pytest.fixture
    def sample_validation_csv(self, tmp_path):
        """Crée un fichier CSV de validation"""
        data = pd.DataFrame(
            {
                "feature_1": np.random.rand(50),
                "feature_2": np.random.rand(50),
                "target": np.random.choice([0, 1], 50),
            }
        )
        csv_path = tmp_path / "validation.csv"
        data.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.fixture
    def sample_validation_parquet(self, tmp_path):
        """Crée un fichier Parquet de validation"""
        data = pd.DataFrame(
            {
                "feature_1": np.random.rand(50),
                "feature_2": np.random.rand(50),
                "target": np.random.choice([0, 1], 50),
            }
        )
        parquet_path = tmp_path / "validation.parquet"
        data.to_parquet(parquet_path, index=False)
        return str(parquet_path)

    def test_load_csv_file(self, sample_validation_csv):
        """Test du chargement d'un fichier CSV"""
        df = load_validation_data(sample_validation_csv)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 50
        assert "feature_1" in df.columns
        assert "target" in df.columns

    def test_load_parquet_file(self, sample_validation_parquet):
        """Test du chargement d'un fichier Parquet"""
        df = load_validation_data(sample_validation_parquet)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 50
        assert "feature_1" in df.columns

    def test_load_unsupported_format(self):
        """Test avec un format non supporté"""
        with pytest.raises(ValueError, match="Format de fichier non supporté"):
            load_validation_data("/path/to/file.txt")

    def test_load_nonexistent_file(self):
        """Test avec un fichier inexistant"""
        with pytest.raises(Exception):
            load_validation_data("/nonexistent/path/data.csv")

    def test_load_s3_path_format(self, monkeypatch):
        """Test avec un chemin S3 (mock)"""

        # Mock pandas read_parquet pour S3
        def mock_read_parquet(path):
            return pd.DataFrame({"feature_1": [1, 2, 3], "target": [0, 1, 0]})

        monkeypatch.setattr(pd, "read_parquet", mock_read_parquet)

        df = load_validation_data("s3://bucket/path/data.parquet")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3


class TestCalculateAccuracy:
    """Tests pour la fonction calculate_accuracy"""

    def test_calculate_accuracy_perfect(self):
        """Test avec des prédictions parfaites"""
        y_true = pd.Series([0, 1, 0, 1, 0, 1])
        y_pred = pd.Series([0, 1, 0, 1, 0, 1])

        accuracy = calculate_accuracy(y_true, y_pred)

        assert accuracy == 1.0

    def test_calculate_accuracy_zero(self):
        """Test avec des prédictions totalement fausses"""
        y_true = pd.Series([0, 0, 0, 0, 0])
        y_pred = pd.Series([1, 1, 1, 1, 1])

        accuracy = calculate_accuracy(y_true, y_pred)

        assert accuracy == 0.0

    def test_calculate_accuracy_half(self):
        """Test avec 50% d'accuracy"""
        y_true = pd.Series([0, 1, 0, 1, 0, 1, 0, 1])
        y_pred = pd.Series([0, 1, 0, 1, 1, 0, 1, 0])

        accuracy = calculate_accuracy(y_true, y_pred)

        assert accuracy == 0.5

    def test_calculate_accuracy_random(self):
        """Test avec des données aléatoires"""
        np.random.seed(42)
        y_true = pd.Series(np.random.choice([0, 1], 100))
        y_pred = pd.Series(np.random.choice([0, 1], 100))

        accuracy = calculate_accuracy(y_true, y_pred)

        assert 0 <= accuracy <= 1

    def test_calculate_accuracy_different_lengths(self):
        """Test avec des séries de longueurs différentes"""
        y_true = pd.Series([0, 1, 0, 1])
        y_pred = pd.Series([0, 1])

        with pytest.raises(Exception):
            calculate_accuracy(y_true, y_pred)


class TestValidateModelPerformance:
    """Tests pour la fonction validate_model_performance"""

    @pytest.fixture
    def mock_mlflow_model(self, monkeypatch):
        """Mock MLflow model loading"""

        class MockModel:
            def predict(self, X):
                return np.random.choice([0, 1], len(X))

        def mock_load_model(path):
            return MockModel()

        import mlflow.pyfunc

        monkeypatch.setattr(mlflow.pyfunc, "load_model", mock_load_model)

    def test_validate_model_performance_success(self, tmp_path, mock_mlflow_model, monkeypatch):
        """Test de validation réussie"""
        # Créer des données de validation
        validation_data = pd.DataFrame(
            {
                "feature_1": np.random.rand(50),
                "feature_2": np.random.rand(50),
                "target": np.ones(50),  # Toutes les prédictions seront correctes avec le mock
            }
        )
        validation_path = tmp_path / "validation.parquet"
        validation_data.to_parquet(validation_path)

        # Mock pour que l'accuracy soit toujours au-dessus du seuil
        def mock_calculate_accuracy(y_true, y_pred):
            return 0.90

        monkeypatch.setattr("dags.utils.functions.calculate_accuracy", mock_calculate_accuracy)

        model_path = "s3://bucket/model"
        min_threshold = 0.85

        accuracy = validate_model_performance(
            model_path=model_path,
            validation_data_path=str(validation_path),
            min_accuracy_threshold=min_threshold,
        )

        assert accuracy >= min_threshold

    def test_validate_model_performance_failure(self, tmp_path, mock_mlflow_model, monkeypatch):
        """Test de validation échouée (accuracy insuffisante)"""
        # Créer des données de validation
        validation_data = pd.DataFrame(
            {
                "feature_1": np.random.rand(50),
                "feature_2": np.random.rand(50),
                "target": np.random.choice([0, 1], 50),
            }
        )
        validation_path = tmp_path / "validation.parquet"
        validation_data.to_parquet(validation_path)

        # Mock pour que l'accuracy soit en-dessous du seuil
        def mock_calculate_accuracy(y_true, y_pred):
            return 0.70

        monkeypatch.setattr("dags.utils.functions.calculate_accuracy", mock_calculate_accuracy)

        model_path = "s3://bucket/model"
        min_threshold = 0.85

        with pytest.raises(ValueError, match="Modèle ne répond pas aux critères"):
            validate_model_performance(
                model_path=model_path,
                validation_data_path=str(validation_path),
                min_accuracy_threshold=min_threshold,
            )


class TestTriggerTektonPipeline:
    """Tests pour la fonction trigger_tekton_pipeline"""

    def test_trigger_tekton_pipeline_success(self):
        """Test du déclenchement réussi d'un pipeline Tekton"""
        with requests_mock.Mocker() as m:
            tekton_url = (
                "http://tekton-dashboard:9097/api/v1/namespaces/tekton-pipelines/pipelineruns"
            )
            m.post(tekton_url, json={"metadata": {"name": "test-run"}}, status_code=201)

            result = trigger_tekton_pipeline(
                model_version="20240101", tekton_pipeline_url=tekton_url
            )

            assert result is not None
            assert "metadata" in result

    def test_trigger_tekton_pipeline_failure(self):
        """Test d'échec de déclenchement"""
        with requests_mock.Mocker() as m:
            tekton_url = (
                "http://tekton-dashboard:9097/api/v1/namespaces/tekton-pipelines/pipelineruns"
            )
            m.post(tekton_url, status_code=500)

            with pytest.raises(Exception):
                trigger_tekton_pipeline(model_version="20240101", tekton_pipeline_url=tekton_url)

    def test_trigger_tekton_pipeline_config_format(self):
        """Test du format de la configuration envoyée"""
        with requests_mock.Mocker() as m:
            tekton_url = (
                "http://tekton-dashboard:9097/api/v1/namespaces/tekton-pipelines/pipelineruns"
            )

            def check_request(request, context):
                data = request.json()
                # Vérifier la structure
                assert data["apiVersion"] == "tekton.dev/v1beta1"
                assert data["kind"] == "PipelineRun"
                assert "metadata" in data
                assert "spec" in data
                assert data["spec"]["pipelineRef"]["name"] == "ml-model-pipeline"
                # Vérifier les paramètres
                params = data["spec"]["params"]
                assert len(params) == 2
                assert any(p["name"] == "model-version" for p in params)
                assert any(p["name"] == "target-env" for p in params)
                return {"metadata": {"name": "test-run"}}

            m.post(tekton_url, json=check_request, status_code=201)

            trigger_tekton_pipeline(model_version="20240101", tekton_pipeline_url=tekton_url)


class TestExtractWithTrino:
    """Tests pour la fonction extract_with_trino"""

    def test_extract_with_trino_mock(self, monkeypatch):
        """Test d'extraction avec Trino (mock)"""

        # Mock pour sqlalchemy et pandas
        def mock_read_sql(query, connection):
            return pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        monkeypatch.setattr(pd, "read_sql", mock_read_sql)

        # Mock create_engine
        class MockEngine:
            def connect(self):
                class MockConnection:
                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        pass

                return MockConnection()

        def mock_create_engine(*args, **kwargs):
            return MockEngine()

        monkeypatch.setattr("dags.utils.functions.create_engine", mock_create_engine)

        df = extract_with_trino(
            query="SELECT * FROM table", host="trino-host", port=8080, user="test_user"
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "id" in df.columns

    def test_extract_with_trino_with_password(self, monkeypatch):
        """Test avec authentification par password"""

        def mock_read_sql(query, connection):
            return pd.DataFrame({"col": [1, 2]})

        monkeypatch.setattr(pd, "read_sql", mock_read_sql)

        class MockEngine:
            def connect(self):
                class MockConnection:
                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        pass

                return MockConnection()

        monkeypatch.setattr(
            "dags.utils.functions.create_engine", lambda *args, **kwargs: MockEngine()
        )

        df = extract_with_trino(query="SELECT * FROM table", host="trino-host", password="secret")

        assert isinstance(df, pd.DataFrame)


class TestExtractFromMultipleSources:
    """Tests pour extract_from_multiple_sources"""

    def test_extract_from_multiple_sources(self, monkeypatch):
        """Test d'extraction depuis plusieurs sources"""

        def mock_extract_with_trino(**kwargs):
            return pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

        monkeypatch.setattr("dags.utils.functions.extract_with_trino", mock_extract_with_trino)

        queries = {
            "hive.default": "SELECT * FROM table1",
            "postgres.public": "SELECT * FROM table2",
        }

        results = extract_from_multiple_sources(queries=queries, host="trino-host")

        assert isinstance(results, dict)
        assert len(results) == 2
        assert "hive.default" in results
        assert "postgres.public" in results
        assert all(isinstance(df, pd.DataFrame) for df in results.values())

    def test_extract_from_multiple_sources_single_catalog(self, monkeypatch):
        """Test avec un seul catalogue (pas de schéma)"""

        def mock_extract_with_trino(**kwargs):
            return pd.DataFrame({"col": [1, 2]})

        monkeypatch.setattr("dags.utils.functions.extract_with_trino", mock_extract_with_trino)

        queries = {"hive": "SELECT * FROM table1"}

        results = extract_from_multiple_sources(queries=queries, host="trino-host")

        assert len(results) == 1
        assert "hive" in results
