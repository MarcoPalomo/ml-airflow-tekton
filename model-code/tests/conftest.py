"""
Configuration pytest pour les tests
Fixtures communes à tous les tests
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


@pytest.fixture
def sample_dataframe():
    """Génère un DataFrame de test avec des données synthétiques"""
    np.random.seed(42)
    n_samples = 100

    data = {
        'transaction_id': range(1, n_samples + 1),
        'customer_id': np.random.randint(1, 20, n_samples),
        'amount': np.random.uniform(10, 1000, n_samples),
        'merchant_category': np.random.choice(['retail', 'food', 'transport', 'online'], n_samples),
        'transaction_hour': np.random.randint(0, 24, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'is_weekend': np.random.choice([0, 1], n_samples),
        'distance_from_home': np.random.uniform(0, 100, n_samples),
        'target': np.random.choice([0, 1], n_samples, p=[0.8, 0.2])
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_dataframe_with_nulls():
    """Génère un DataFrame de test avec des valeurs manquantes"""
    np.random.seed(42)
    n_samples = 50

    data = {
        'transaction_id': range(1, n_samples + 1),
        'customer_id': np.random.randint(1, 20, n_samples),
        'amount': np.random.uniform(10, 1000, n_samples),
        'merchant_category': np.random.choice(['retail', 'food', 'transport', None], n_samples),
        'transaction_hour': np.random.randint(0, 24, n_samples),
        'target': np.random.choice([0, 1], n_samples)
    }

    df = pd.DataFrame(data)
    # Ajouter des valeurs manquantes
    df.loc[df.sample(frac=0.1).index, 'amount'] = np.nan

    return df


@pytest.fixture
def preprocessor_config():
    """Configuration pour le DataPreprocessor"""
    return {
        'critical_columns': ['transaction_id', 'customer_id', 'amount'],
        'date_columns': [],
        'categorical_columns': ['merchant_category'],
        'target_column': 'target',
        'test_size': 0.2,
        'random_state': 42
    }


@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Crée un fichier CSV temporaire avec des données de test"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f.name, index=False)
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_parquet_file(sample_dataframe):
    """Crée un fichier Parquet temporaire avec des données de test"""
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        sample_dataframe.to_parquet(f.name, index=False)
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def trained_model():
    """Crée un modèle simple entraîné pour les tests"""
    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = np.random.choice([0, 1], 100)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    return model


@pytest.fixture
def temp_model_file(trained_model):
    """Crée un fichier de modèle temporaire"""
    with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as f:
        joblib.dump(trained_model, f.name)
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_preprocessor_file():
    """Crée un fichier de preprocessor temporaire"""
    scaler = StandardScaler()
    scaler.fit(np.random.rand(100, 5))

    with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as f:
        joblib.dump(scaler, f.name)
        yield f.name
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def api_test_request():
    """Requête de test pour l'API"""
    return {
        "features": {
            "customer_id": 5,
            "amount": 250.50,
            "merchant_category": "retail",
            "transaction_hour": 14,
            "day_of_week": 3,
            "is_weekend": 0,
            "distance_from_home": 15.5
        }
    }


@pytest.fixture
def api_batch_request():
    """Requête batch de test pour l'API"""
    return {
        "instances": [
            {
                "customer_id": 5,
                "amount": 250.50,
                "merchant_category": "retail",
                "transaction_hour": 14
            },
            {
                "customer_id": 8,
                "amount": 89.99,
                "merchant_category": "food",
                "transaction_hour": 19
            }
        ]
    }


@pytest.fixture
def mock_mlflow_run(monkeypatch):
    """Mock MLflow pour les tests"""
    class MockRun:
        def __init__(self):
            self.info = type('obj', (object,), {'run_id': 'test_run_123'})

    def mock_start_run(*args, **kwargs):
        return MockRun()

    def mock_log_param(*args, **kwargs):
        pass

    def mock_log_metric(*args, **kwargs):
        pass

    def mock_log_artifact(*args, **kwargs):
        pass

    def mock_sklearn_log_model(*args, **kwargs):
        pass

    import mlflow
    monkeypatch.setattr(mlflow, 'start_run', mock_start_run)
    monkeypatch.setattr(mlflow, 'log_param', mock_log_param)
    monkeypatch.setattr(mlflow, 'log_metric', mock_log_metric)
    monkeypatch.setattr(mlflow, 'log_artifact', mock_log_artifact)
    monkeypatch.setattr(mlflow.sklearn, 'log_model', mock_sklearn_log_model)


@pytest.fixture
def sample_X_y():
    """Génère des features et target pour les tests de modèle"""
    np.random.seed(42)
    X = pd.DataFrame({
        'feature_1': np.random.rand(100),
        'feature_2': np.random.rand(100),
        'feature_3': np.random.rand(100),
        'feature_4': np.random.rand(100),
        'feature_5': np.random.rand(100)
    })
    y = pd.Series(np.random.choice([0, 1], 100))

    return X, y
