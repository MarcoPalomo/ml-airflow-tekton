"""API FastAPI pour le serving du modèle"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales
model = None
preprocessor = None


def load_model() -> None:
    """Charge le modèle et le preprocessor depuis le disque."""
    global model, preprocessor

    try:
        model_path = os.environ.get("MODEL_PATH", "/app/models/model.joblib")
        preprocessor_path = os.environ.get("PREPROCESSOR_PATH", "/app/models/preprocessor.joblib")

        if os.path.exists(model_path):
            model = joblib.load(model_path)
            logger.info(f"Modèle chargé depuis {model_path}")
        else:
            logger.warning(f"Modèle non trouvé: {model_path}")

        if os.path.exists(preprocessor_path):
            preprocessor = joblib.load(preprocessor_path)
            logger.info(f"Preprocessor chargé depuis {preprocessor_path}")
        else:
            logger.warning(f"Preprocessor non trouvé: {preprocessor_path}")

    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie de l'application : chargement du modèle au démarrage."""
    load_model()
    yield


app = FastAPI(
    title="ML Model API",
    description="API de prédiction pour le modèle ML",
    version="1.0.0",
    lifespan=lifespan,
)


class PredictionRequest(BaseModel):
    features: dict[str, Any]


class PredictionResponse(BaseModel):
    prediction: int
    probability: list[float]
    timestamp: str


class BatchPredictionRequest(BaseModel):
    instances: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de santé"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Endpoint de prédiction unitaire"""
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non disponible")

    try:
        # Conversion en DataFrame
        df = pd.DataFrame([request.features])

        # Préprocessing si disponible
        if preprocessor is not None:
            df_processed, _ = preprocessor.prepare_dataframe(df, is_training=False)
        else:
            df_processed = df

        # Prédiction
        prediction = model.predict(df_processed)[0]
        probabilities = model.predict_proba(df_processed)[0].tolist()

        return PredictionResponse(
            prediction=int(prediction),
            probability=probabilities,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/batch_predict")
async def batch_predict(request: BatchPredictionRequest):
    """Endpoint de prédiction par lot"""
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non disponible")

    if not request.instances:
        raise HTTPException(status_code=400, detail="La liste 'instances' est vide")

    try:
        # Conversion en DataFrame
        df = pd.DataFrame(request.instances)

        # Préprocessing si disponible
        if preprocessor is not None:
            df_processed, _ = preprocessor.prepare_dataframe(df, is_training=False)
        else:
            df_processed = df

        # Prédictions
        predictions = model.predict(df_processed).tolist()
        probabilities = model.predict_proba(df_processed).tolist()

        results = [
            {"prediction": int(pred), "probability": prob, "timestamp": datetime.now().isoformat()}
            for pred, prob in zip(predictions, probabilities, strict=False)
        ]

        return {"results": results}

    except Exception as e:
        logger.error(f"Erreur lors de la prédiction par lot: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/model_info")
async def model_info():
    """Informations sur le modèle"""
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non disponible")

    info = {
        "model_type": type(model).__name__,
        "features_count": getattr(model, "n_features_in_", "Unknown"),
        "classes": getattr(model, "classes_", []).tolist() if hasattr(model, "classes_") else [],
        "timestamp": datetime.now().isoformat(),
    }

    return info


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
