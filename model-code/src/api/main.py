"""API FastAPI pour le serving du modèle"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import logging
from typing import List, Dict, Any
import os
from datetime import datetime

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ML Model API",
    description="API de prédiction pour le modèle ML",
    version="1.0.0"
)

# Variables globales
model = None
preprocessor = None

class PredictionRequest(BaseModel):
    features: Dict[str, Any]
    
class PredictionResponse(BaseModel):
    prediction: int
    probability: List[float]
    timestamp: str

class BatchPredictionRequest(BaseModel):
    instances: List[Dict[str, Any]]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: str

@app.on_event("startup")
async def load_model():
    """Charge le modèle au démarrage"""
    global model, preprocessor
    
    try:
        model_path = os.environ.get('MODEL_PATH', '/app/models/model.joblib')
        preprocessor_path = os.environ.get('PREPROCESSOR_PATH', '/app/models/preprocessor.joblib')
        
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

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de santé"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        timestamp=datetime.now().isoformat()
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
            df_processed, _ = preprocessor.prepare_data(df, is_training=False)
        else:
            df_processed = df
        
        # Prédiction
        prediction = model.predict(df_processed)[0]
        probabilities = model.predict_proba(df_processed)[0].tolist()
        
        return PredictionResponse(
            prediction=int(prediction),
            probability=probabilities,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch_predict")
async def batch_predict(request: BatchPredictionRequest):
    """Endpoint de prédiction par lot"""
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non disponible")
    
    try:
        # Conversion en DataFrame
        df = pd.DataFrame(request.instances)
        
        # Préprocessing si disponible
        if preprocessor is not None:
            df_processed, _ = preprocessor.prepare_data(df, is_training=False)
        else:
            df_processed = df
        
        # Prédictions
        predictions = model.predict(df_processed).tolist()
        probabilities = model.predict_proba(df_processed).tolist()
        
        results = [
            {
                "prediction": int(pred),
                "probability": prob,
                "timestamp": datetime.now().isoformat()
            }
            for pred, prob in zip(predictions, probabilities)
        ]
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction par lot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model_info")
async def model_info():
    """Informations sur le modèle"""
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non disponible")
    
    info = {
        "model_type": type(model).__name__,
        "features_count": getattr(model, 'n_features_in_', 'Unknown'),
        "classes": getattr(model, 'classes_', []).tolist() if hasattr(model, 'classes_') else [],
        "timestamp": datetime.now().isoformat()
    }
    
    return info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)