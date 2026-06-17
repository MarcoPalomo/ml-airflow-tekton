"""
Tests d'intégration pour l'API FastAPI
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestClassifier

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.main import app


@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
def mock_model_and_preprocessor(monkeypatch, tmp_path):
    """Mock le modèle et le preprocessor pour les tests"""
    # Créer un modèle simple
    model = RandomForestClassifier(n_estimators=5, random_state=42)
    X_train = np.random.rand(50, 5)
    y_train = np.random.choice([0, 1], 50)
    model.fit(X_train, y_train)

    # Sauvegarder le modèle
    model_path = tmp_path / "test_model.joblib"
    joblib.dump(model, model_path)

    # Mock des variables d'environnement
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv(
        "PREPROCESSOR_PATH", "/nonexistent/path"
    )  # Pas de preprocessor pour simplifier

    # Recharger l'app pour prendre en compte les nouveaux env vars
    from api import main

    main.model = model
    main.preprocessor = None

    yield

    # Cleanup
    main.model = None
    main.preprocessor = None


class TestHealthEndpoint:
    """Tests pour l'endpoint de health check"""

    def test_health_endpoint_no_model(self, client):
        """Test du health check sans modèle chargé"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "timestamp" in data

    def test_health_endpoint_with_model(self, client, mock_model_and_preprocessor):
        """Test du health check avec modèle chargé"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True

    def test_health_endpoint_returns_timestamp(self, client):
        """Test que le health check retourne un timestamp"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        # Vérifier le format ISO
        assert "T" in data["timestamp"]


class TestPredictEndpoint:
    """Tests pour l'endpoint de prédiction unitaire"""

    def test_predict_without_model(self, client, api_test_request):
        """Test de prédiction sans modèle chargé"""
        response = client.post("/predict", json=api_test_request)

        assert response.status_code == 503
        assert "Modèle non disponible" in response.json()["detail"]

    def test_predict_with_model(self, client, mock_model_and_preprocessor):
        """Test de prédiction avec modèle chargé"""
        request_data = {
            "features": {
                "feature_1": 0.5,
                "feature_2": 0.3,
                "feature_3": 0.7,
                "feature_4": 0.2,
                "feature_5": 0.9,
            }
        }

        response = client.post("/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "probability" in data
        assert "timestamp" in data
        assert data["prediction"] in [0, 1]
        assert len(data["probability"]) == 2
        assert sum(data["probability"]) == pytest.approx(1.0, abs=0.01)

    def test_predict_invalid_input(self, client, mock_model_and_preprocessor):
        """Test avec des données d'entrée invalides"""
        invalid_request = {"features": "not a dict"}

        response = client.post("/predict", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_predict_missing_features(self, client, mock_model_and_preprocessor):
        """Test avec des features manquantes"""
        request_data = {
            "features": {
                "feature_1": 0.5
                # Features manquantes
            }
        }

        response = client.post("/predict", json=request_data)

        # Devrait retourner une erreur ou gérer les features manquantes
        assert response.status_code in [200, 400, 500]

    def test_predict_response_format(self, client, mock_model_and_preprocessor):
        """Test du format de la réponse"""
        request_data = {
            "features": {
                "feature_1": 0.5,
                "feature_2": 0.3,
                "feature_3": 0.7,
                "feature_4": 0.2,
                "feature_5": 0.9,
            }
        }

        response = client.post("/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Vérifier les types
        assert isinstance(data["prediction"], int)
        assert isinstance(data["probability"], list)
        assert isinstance(data["timestamp"], str)
        assert all(isinstance(p, float) for p in data["probability"])


class TestBatchPredictEndpoint:
    """Tests pour l'endpoint de prédiction par batch"""

    def test_batch_predict_without_model(self, client, api_batch_request):
        """Test de prédiction batch sans modèle"""
        response = client.post("/batch_predict", json=api_batch_request)

        assert response.status_code == 503
        assert "Modèle non disponible" in response.json()["detail"]

    def test_batch_predict_with_model(self, client, mock_model_and_preprocessor):
        """Test de prédiction batch avec modèle"""
        request_data = {
            "instances": [
                {
                    "feature_1": 0.5,
                    "feature_2": 0.3,
                    "feature_3": 0.7,
                    "feature_4": 0.2,
                    "feature_5": 0.9,
                },
                {
                    "feature_1": 0.1,
                    "feature_2": 0.8,
                    "feature_3": 0.4,
                    "feature_4": 0.6,
                    "feature_5": 0.3,
                },
            ]
        }

        response = client.post("/batch_predict", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2

        for result in data["results"]:
            assert "prediction" in result
            assert "probability" in result
            assert "timestamp" in result
            assert result["prediction"] in [0, 1]

    def test_batch_predict_empty_list(self, client, mock_model_and_preprocessor):
        """Test avec une liste vide"""
        request_data = {"instances": []}

        response = client.post("/batch_predict", json=request_data)

        # Devrait gérer le cas gracieusement
        assert response.status_code in [200, 400]

    def test_batch_predict_single_instance(self, client, mock_model_and_preprocessor):
        """Test avec une seule instance"""
        request_data = {
            "instances": [
                {
                    "feature_1": 0.5,
                    "feature_2": 0.3,
                    "feature_3": 0.7,
                    "feature_4": 0.2,
                    "feature_5": 0.9,
                }
            ]
        }

        response = client.post("/batch_predict", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_batch_predict_many_instances(self, client, mock_model_and_preprocessor):
        """Test avec beaucoup d'instances"""
        instances = [
            {
                "feature_1": i / 100,
                "feature_2": i / 100,
                "feature_3": i / 100,
                "feature_4": i / 100,
                "feature_5": i / 100,
            }
            for i in range(50)
        ]
        request_data = {"instances": instances}

        response = client.post("/batch_predict", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 50


class TestModelInfoEndpoint:
    """Tests pour l'endpoint d'information du modèle"""

    def test_model_info_without_model(self, client):
        """Test sans modèle chargé"""
        response = client.get("/model_info")

        assert response.status_code == 503
        assert "Modèle non disponible" in response.json()["detail"]

    def test_model_info_with_model(self, client, mock_model_and_preprocessor):
        """Test avec modèle chargé"""
        response = client.get("/model_info")

        assert response.status_code == 200
        data = response.json()
        assert "model_type" in data
        assert "timestamp" in data
        assert data["model_type"] == "RandomForestClassifier"

    def test_model_info_contains_features_count(self, client, mock_model_and_preprocessor):
        """Test que model_info contient le nombre de features"""
        response = client.get("/model_info")

        assert response.status_code == 200
        data = response.json()
        assert "features_count" in data
        assert data["features_count"] == 5

    def test_model_info_contains_classes(self, client, mock_model_and_preprocessor):
        """Test que model_info contient les classes"""
        response = client.get("/model_info")

        assert response.status_code == 200
        data = response.json()
        assert "classes" in data
        assert len(data["classes"]) == 2


class TestAPIIntegration:
    """Tests d'intégration de l'API"""

    def test_health_then_predict(self, client, mock_model_and_preprocessor):
        """Test du flow health check puis prédiction"""
        # 1. Health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["model_loaded"] is True

        # 2. Prédiction
        request_data = {
            "features": {
                "feature_1": 0.5,
                "feature_2": 0.3,
                "feature_3": 0.7,
                "feature_4": 0.2,
                "feature_5": 0.9,
            }
        }
        predict_response = client.post("/predict", json=request_data)
        assert predict_response.status_code == 200

    def test_multiple_predictions(self, client, mock_model_and_preprocessor):
        """Test de prédictions multiples successives"""
        request_data = {
            "features": {
                "feature_1": 0.5,
                "feature_2": 0.3,
                "feature_3": 0.7,
                "feature_4": 0.2,
                "feature_5": 0.9,
            }
        }

        # Faire plusieurs prédictions
        for _ in range(5):
            response = client.post("/predict", json=request_data)
            assert response.status_code == 200

    def test_predict_and_batch_predict(self, client, mock_model_and_preprocessor):
        """Test combinant prédiction unitaire et batch"""
        # Prédiction unitaire
        single_request = {
            "features": {
                "feature_1": 0.5,
                "feature_2": 0.3,
                "feature_3": 0.7,
                "feature_4": 0.2,
                "feature_5": 0.9,
            }
        }
        single_response = client.post("/predict", json=single_request)
        assert single_response.status_code == 200

        # Prédiction batch
        batch_request = {
            "instances": [
                {
                    "feature_1": 0.5,
                    "feature_2": 0.3,
                    "feature_3": 0.7,
                    "feature_4": 0.2,
                    "feature_5": 0.9,
                },
                {
                    "feature_1": 0.1,
                    "feature_2": 0.8,
                    "feature_3": 0.4,
                    "feature_4": 0.6,
                    "feature_5": 0.3,
                },
            ]
        }
        batch_response = client.post("/batch_predict", json=batch_request)
        assert batch_response.status_code == 200

    def test_all_endpoints(self, client, mock_model_and_preprocessor):
        """Test de tous les endpoints dans l'ordre"""
        # 1. Health
        assert client.get("/health").status_code == 200

        # 2. Model info
        assert client.get("/model_info").status_code == 200

        # 3. Predict
        predict_data = {
            "features": {
                "feature_1": 0.5,
                "feature_2": 0.3,
                "feature_3": 0.7,
                "feature_4": 0.2,
                "feature_5": 0.9,
            }
        }
        assert client.post("/predict", json=predict_data).status_code == 200

        # 4. Batch predict
        batch_data = {
            "instances": [
                {
                    "feature_1": 0.5,
                    "feature_2": 0.3,
                    "feature_3": 0.7,
                    "feature_4": 0.2,
                    "feature_5": 0.9,
                }
            ]
        }
        assert client.post("/batch_predict", json=batch_data).status_code == 200
