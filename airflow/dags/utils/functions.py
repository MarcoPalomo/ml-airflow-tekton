import requests
import boto3
import mlflow
import pandas as pd
from sqlalchemy import create_engine
from typing import Dict, Any, List, Union
from urllib.parse import quote_plus

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

def extract_with_trino(
    query: str,
    host: str,
    port: int = 8080,
    user: str = "user",
    catalog: str = "hive",
    schema: str = "default",
    password: str = None,
    **kwargs
) -> pd.DataFrame:
    """
    Exécute une requête SQL sur Trino Stardust et retourne les résultats dans un DataFrame pandas.
    
    Args:
        query (str): Requête SQL à exécuter
        host (str): Hôte du serveur Trino
        port (int, optional): Port du serveur Trino. Par défaut 8080
        user (str, optional): Nom d'utilisateur. Par défaut "user"
        catalog (str, optional): Catalogue à utiliser. Par défaut "hive"
        schema (str, optional): Schéma à utiliser. Par défaut "default"
        password (str, optional): Mot de passe si nécessaire
        **kwargs: Arguments supplémentaires pour la connexion SQLAlchemy
        
    Returns:
        pd.DataFrame: Résultats de la requête sous forme de DataFrame
    """
    try:
        # Construction de l'URL de connexion
        if password:
            # Si authentification par mot de passe
            conn_url = f"trino://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{catalog}/{schema}"
        else:
            # Sans authentification
            conn_url = f"trino://{user}@{host}:{port}/{catalog}/{schema}"
        
        # Création du moteur SQLAlchemy
        engine = create_engine(
            conn_url,
            connect_args={
                "http_scheme": "https" if port == 443 else "http",
                "session_properties": {
                    "query_max_run_time": "2h",
                    "query_priority": "1"
                },
                **kwargs
            }
        )
        
        # Exécution de la requête
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
            
        return df
        
    except Exception as e:
        print(f"Erreur lors de l'exécution de la requête Trino: {str(e)}")
        raise

def extract_from_multiple_sources(
    queries: Dict[str, str],
    host: str,
    port: int = 8080,
    user: str = "user",
    password: str = None,
    **kwargs
) -> Dict[str, pd.DataFrame]:
    """
    Exécute plusieurs requêtes sur différentes sources de données via Trino Stardust.
    
    Args:
        queries (Dict[str, str]): Dictionnaire où les clés sont des identifiants de source
                                et les valeurs sont des requêtes SQL
        host (str): Hôte du serveur Trino
        port (int, optional): Port du serveur Trino. Par défaut 8080
        user (str, optional): Nom d'utilisateur. Par défaut "user"
        password (str, optional): Mot de passe si nécessaire
        **kwargs: Arguments supplémentaires pour la connexion
        
    Returns:
        Dict[str, pd.DataFrame]: Dictionnaire contenant les DataFrames résultants
    """
    results = {}
    
    for source, query in queries.items():
        try:
            # Extraction du catalogue et du schéma à partir du nom de la source
            # Format attendu: "catalog.schema" ou simplement "catalog"
            parts = source.split('.')
            catalog = parts[0]
            schema = parts[1] if len(parts) > 1 else 'default'
            
            print(f"Extraction depuis {catalog}.{schema}...")
            
            # Exécution de la requête
            df = extract_with_trino(
                query=query,
                host=host,
                port=port,
                user=user,
                catalog=catalog,
                schema=schema,
                password=password,
                **kwargs
            )
            
            results[source] = df
            print(f"  - {len(df)} lignes extraites de {source}")
            
        except Exception as e:
            print(f"Erreur lors de l'extraction depuis {source}: {str(e)}")
            raise
    
    return results