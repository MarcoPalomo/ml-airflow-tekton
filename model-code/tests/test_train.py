"""
Tests unitaires pour le module de training
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from models.train import ModelTrainer


class TestModelTrainer:
    """Tests pour la classe ModelTrainer"""

    @pytest.fixture
    def trainer_config_rf(self):
        """Configuration pour RandomForest"""
        return {
            'model_type': 'random_forest',
            'n_estimators': 10,
            'max_depth': 5,
            'random_state': 42
        }

    @pytest.fixture
    def trainer_config_lr(self):
        """Configuration pour LogisticRegression"""
        return {
            'model_type': 'logistic_regression',
            'max_iter': 100,
            'random_state': 42
        }

    @pytest.fixture
    def sample_train_data(self):
        """Données d'entraînement de test"""
        np.random.seed(42)
        X_train = pd.DataFrame({
            'feature_1': np.random.rand(100),
            'feature_2': np.random.rand(100),
            'feature_3': np.random.rand(100)
        })
        y_train = pd.Series(np.random.choice([0, 1], 100))
        return X_train, y_train

    @pytest.fixture
    def sample_test_data(self):
        """Données de test"""
        np.random.seed(43)
        X_test = pd.DataFrame({
            'feature_1': np.random.rand(30),
            'feature_2': np.random.rand(30),
            'feature_3': np.random.rand(30)
        })
        y_test = pd.Series(np.random.choice([0, 1], 30))
        return X_test, y_test

    def test_init(self, trainer_config_rf):
        """Test de l'initialisation du trainer"""
        trainer = ModelTrainer(trainer_config_rf)

        assert trainer.config == trainer_config_rf
        assert trainer.model is None
        assert isinstance(trainer.model_metrics, dict)
        assert len(trainer.model_metrics) == 0

    def test_create_model_random_forest(self, trainer_config_rf):
        """Test de la création d'un modèle RandomForest"""
        trainer = ModelTrainer(trainer_config_rf)
        model = trainer.create_model()

        assert isinstance(model, RandomForestClassifier)
        assert model.n_estimators == 10
        assert model.max_depth == 5
        assert model.random_state == 42

    def test_create_model_logistic_regression(self, trainer_config_lr):
        """Test de la création d'un modèle LogisticRegression"""
        trainer = ModelTrainer(trainer_config_lr)
        model = trainer.create_model()

        assert isinstance(model, LogisticRegression)
        assert model.max_iter == 100
        assert model.random_state == 42

    def test_create_model_unsupported_type(self):
        """Test avec un type de modèle non supporté"""
        config = {'model_type': 'unsupported_model'}
        trainer = ModelTrainer(config)

        with pytest.raises(ValueError, match="Type de modèle non supporté"):
            trainer.create_model()

    def test_create_model_default_random_forest(self):
        """Test de la création d'un modèle avec config par défaut"""
        trainer = ModelTrainer({})
        model = trainer.create_model()

        assert isinstance(model, RandomForestClassifier)
        assert model.n_estimators == 100  # Valeur par défaut
        assert model.random_state == 42

    def test_train_random_forest(self, trainer_config_rf, sample_train_data, mock_mlflow_run):
        """Test de l'entraînement d'un RandomForest"""
        X_train, y_train = sample_train_data
        trainer = ModelTrainer(trainer_config_rf)

        model = trainer.train(X_train, y_train)

        assert model is not None
        assert trainer.model is not None
        assert hasattr(model, 'predict')
        assert hasattr(model, 'predict_proba')

    def test_train_logistic_regression(self, trainer_config_lr, sample_train_data, mock_mlflow_run):
        """Test de l'entraînement d'une LogisticRegression"""
        X_train, y_train = sample_train_data
        trainer = ModelTrainer(trainer_config_lr)

        model = trainer.train(X_train, y_train)

        assert model is not None
        assert trainer.model is not None
        assert isinstance(model, LogisticRegression)

    def test_train_model_can_predict(self, trainer_config_rf, sample_train_data,
                                     sample_test_data, mock_mlflow_run):
        """Test que le modèle entraîné peut faire des prédictions"""
        X_train, y_train = sample_train_data
        X_test, _ = sample_test_data

        trainer = ModelTrainer(trainer_config_rf)
        trainer.train(X_train, y_train)

        predictions = trainer.model.predict(X_test)

        assert len(predictions) == len(X_test)
        assert all(pred in [0, 1] for pred in predictions)

    def test_evaluate_without_training(self, trainer_config_rf, sample_test_data):
        """Test de l'évaluation sans entraînement préalable"""
        X_test, y_test = sample_test_data
        trainer = ModelTrainer(trainer_config_rf)

        with pytest.raises(ValueError, match="Le modèle doit être entraîné"):
            trainer.evaluate(X_test, y_test)

    def test_evaluate(self, trainer_config_rf, sample_train_data, sample_test_data, mock_mlflow_run):
        """Test de l'évaluation du modèle"""
        X_train, y_train = sample_train_data
        X_test, y_test = sample_test_data

        trainer = ModelTrainer(trainer_config_rf)
        trainer.train(X_train, y_train)
        metrics = trainer.evaluate(X_test, y_test)

        assert isinstance(metrics, dict)
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics

        # Vérifier que les métriques sont dans des plages valides
        for metric_name, metric_value in metrics.items():
            if metric_name not in ['confusion_matrix']:
                assert 0 <= metric_value <= 1

    def test_evaluate_metrics_values(self, trainer_config_rf, sample_train_data,
                                    sample_test_data, mock_mlflow_run):
        """Test des valeurs des métriques"""
        X_train, y_train = sample_train_data
        X_test, y_test = sample_test_data

        trainer = ModelTrainer(trainer_config_rf)
        trainer.train(X_train, y_train)
        metrics = trainer.evaluate(X_test, y_test)

        # L'accuracy devrait être raisonnable même pour des données random
        assert 0 <= metrics['accuracy'] <= 1
        assert trainer.model_metrics == metrics

    def test_save_model(self, trainer_config_rf, sample_train_data, mock_mlflow_run, tmp_path):
        """Test de la sauvegarde du modèle"""
        X_train, y_train = sample_train_data
        trainer = ModelTrainer(trainer_config_rf)
        trainer.train(X_train, y_train)

        model_path = tmp_path / "test_model.joblib"
        trainer.save_model(str(model_path))

        assert model_path.exists()

        # Vérifier qu'on peut recharger le modèle
        loaded_model = joblib.load(model_path)
        assert loaded_model is not None
        assert hasattr(loaded_model, 'predict')

    def test_save_model_without_training(self, trainer_config_rf, tmp_path):
        """Test de la sauvegarde sans entraînement"""
        trainer = ModelTrainer(trainer_config_rf)
        model_path = tmp_path / "test_model.joblib"

        with pytest.raises(ValueError, match="Le modèle doit être entraîné"):
            trainer.save_model(str(model_path))

    def test_load_model(self, temp_model_file, trainer_config_rf):
        """Test du chargement d'un modèle"""
        trainer = ModelTrainer(trainer_config_rf)
        trainer.load_model(temp_model_file)

        assert trainer.model is not None
        assert hasattr(trainer.model, 'predict')

    def test_load_model_file_not_found(self, trainer_config_rf):
        """Test du chargement d'un fichier inexistant"""
        trainer = ModelTrainer(trainer_config_rf)

        with pytest.raises(Exception):
            trainer.load_model('/path/to/nonexistent/model.joblib')

    def test_predict(self, trainer_config_rf, sample_train_data, sample_test_data, mock_mlflow_run):
        """Test de la prédiction"""
        X_train, y_train = sample_train_data
        X_test, _ = sample_test_data

        trainer = ModelTrainer(trainer_config_rf)
        trainer.train(X_train, y_train)
        predictions = trainer.predict(X_test)

        assert len(predictions) == len(X_test)
        assert all(isinstance(pred, (int, np.integer)) for pred in predictions)

    def test_predict_proba(self, trainer_config_rf, sample_train_data, sample_test_data, mock_mlflow_run):
        """Test de la prédiction de probabilités"""
        X_train, y_train = sample_train_data
        X_test, _ = sample_test_data

        trainer = ModelTrainer(trainer_config_rf)
        trainer.train(X_train, y_train)
        probabilities = trainer.predict_proba(X_test)

        assert probabilities.shape[0] == len(X_test)
        assert probabilities.shape[1] == 2  # Binaire
        # Chaque ligne devrait sommer à ~1
        assert all(abs(row.sum() - 1.0) < 0.01 for row in probabilities)

    def test_predict_without_training(self, trainer_config_rf, sample_test_data):
        """Test de prédiction sans entraînement"""
        X_test, _ = sample_test_data
        trainer = ModelTrainer(trainer_config_rf)

        with pytest.raises(ValueError, match="Le modèle doit être entraîné"):
            trainer.predict(X_test)

    def test_full_pipeline(self, trainer_config_rf, sample_train_data,
                          sample_test_data, mock_mlflow_run, tmp_path):
        """Test d'intégration du pipeline complet"""
        X_train, y_train = sample_train_data
        X_test, y_test = sample_test_data

        # 1. Initialisation
        trainer = ModelTrainer(trainer_config_rf)

        # 2. Entraînement
        trainer.train(X_train, y_train)

        # 3. Évaluation
        metrics = trainer.evaluate(X_test, y_test)
        assert 'accuracy' in metrics

        # 4. Sauvegarde
        model_path = tmp_path / "pipeline_model.joblib"
        trainer.save_model(str(model_path))
        assert model_path.exists()

        # 5. Chargement
        new_trainer = ModelTrainer(trainer_config_rf)
        new_trainer.load_model(str(model_path))

        # 6. Prédiction avec le modèle rechargé
        predictions = new_trainer.predict(X_test)
        assert len(predictions) == len(X_test)

    def test_model_reproducibility(self, trainer_config_rf, sample_train_data, mock_mlflow_run):
        """Test de la reproductibilité avec random_state"""
        X_train, y_train = sample_train_data

        # Premier entraînement
        trainer1 = ModelTrainer(trainer_config_rf)
        trainer1.train(X_train, y_train)
        pred1 = trainer1.predict(X_train.head(10))

        # Deuxième entraînement avec même random_state
        trainer2 = ModelTrainer(trainer_config_rf)
        trainer2.train(X_train, y_train)
        pred2 = trainer2.predict(X_train.head(10))

        # Les prédictions devraient être identiques
        assert all(pred1 == pred2)
