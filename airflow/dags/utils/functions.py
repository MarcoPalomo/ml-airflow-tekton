import requests
import boto3
import mlflow
from typing import Dict, Any

def validate_model_performance(model_path: str, validation_data_path: str, min_accuracy_threshold: float, **context):
    """Valide les performances du modèle ré-entrainé"""
    
    # Charger le modèle depuis S3/MLflow
    model = mlflow.pyfunc.load_model(model_path)
    
    # Charger les données de validation
    validation_data = load_validation_data(validation_data_path)
    
    # Calculer les métriques
    predictions = model.predict(validation_data.drop('target', axis=1))
    accuracy = calculate_accuracy(validation_data['target'], predictions)
    
    # Vérifier si le modèle répond aux critères
    if accuracy < min_accuracy_threshold:
        raise ValueError(f"Modèle ne répond pas aux critères: {accuracy} < {min_accuracy_threshold}")
    
    print(f"Validation réussie: Accuracy = {accuracy}")
    return accuracy

def trigger_tekton_pipeline(model_version: str, tekton_pipeline_url: str, **context):
    """Déclenche un pipeline Tekton pour déployer le nouveau modèle"""
    
    pipeline_run_config = {
        "apiVersion": "tekton.dev/v1beta1",
        "kind": "PipelineRun",
        "metadata": {
            "name": f"deploy-model-{model_version}",
            "namespace": "tekton-pipelines"
        },
        "spec": {
            "pipelineRef": {
                "name": "ml-model-pipeline"
            },
            "params": [
                {"name": "model-version", "value": model_version},
                {"name": "target-env", "value": "production"}
            ]
        }
    }
    
    response = requests.post(tekton_pipeline_url, json=pipeline_run_config)
    response.raise_for_status()
    
    print(f"Pipeline Tekton déclenché avec succès pour le modèle {model_version}")
    return response.json()