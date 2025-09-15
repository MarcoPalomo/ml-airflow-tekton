"""Module d'entraînement du modèle ML"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import mlflow
import mlflow.sklearn
from typing import Dict, Any, Tuple
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self.model_metrics = {}
        
    def create_model(self) -> Any:
        """Crée le modèle selon la configuration"""
        model_type = self.config.get('model_type', 'random_forest')
        
        if model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=self.config.get('n_estimators', 100),
                max_depth=self.config.get('max_depth', None),
                random_state=self.config.get('random_state', 42),
                n_jobs=-1
            )
        elif model_type == 'logistic_regression':
            model = LogisticRegression(
                random_state=self.config.get('random_state', 42),
                max_iter=self.config.get('max_iter', 1000)
            )
        else:
            raise ValueError(f"Type de modèle non supporté: {model_type}")
        
        logger.info(f"Modèle créé: {model_type}")
        return model

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> Any:
        """Entraîne le modèle"""
        with mlflow.start_run():
            # Log des paramètres
            mlflow.log_params(self.config)
            
            # Création et entraînement
            self.model = self.create_model()
            
            logger.info("Début de l'entraînement...")
            start_time = datetime.now()
            
            self.model.fit(X_train, y_train)
            
            training_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Entraînement terminé en {training_time:.2f} secondes")
            
            # Log du temps d'entraînement
            mlflow.log_metric("training_time_seconds", training_time)
            
            return self.model

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Évalue le modèle sur les données de test"""
        if self.model is None:
            raise ValueError("Le modèle doit être entraîné avant l'évaluation")
        
        # Prédictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)
        
        # Calcul des métriques
        accuracy = accuracy_score(y_test, y_pred)
        
        # Métriques détaillées
        from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
        }
        
        # AUC si binaire ou multiclass
        if len(np.unique(y_test)) == 2:
            metrics['auc'] = roc_auc_score(y_test, y_pred_proba[:, 1])
        else:
            metrics['auc'] = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
        
        self.model_metrics = metrics
        
        # Log des métriques dans MLflow
        mlflow.log_metrics(metrics)
        
        # Log du modèle
        mlflow.sklearn.log_model(self.model, "model")
        
        # Rapport détaillé
        logger.info("Métriques d'évaluation:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")
        
        # Classification report
        report = classification_report(y_test, y_pred)
        logger.info(f"Classification Report:\n{report}")
        
        return metrics

    def save_model(self, model_path: str) -> str:
        """Sauvegarde le modèle"""
        if self.model is None:
            raise ValueError("Aucun modèle à sauvegarder")
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Sauvegarde avec joblib
        joblib.dump(self.model, model_path)
        
        # Sauvegarde des métriques
        metrics_path = model_path.replace('.joblib', '_metrics.json')
        import json
        with open(metrics_path, 'w') as f:
            json.dump(self.model_metrics, f, indent=2)
        
        logger.info(f"Modèle sauvegardé: {model_path}")
        logger.info(f"Métriques sauvegardées: {metrics_path}")
        
        return model_path

    @staticmethod
    def load_model(model_path: str) -> Any:
        """Charge un modèle sauvegardé"""
        model = joblib.load(model_path)
        logger.info(f"Modèle chargé: {model_path}")
        return model