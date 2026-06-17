FROM python:3.12-slim

WORKDIR /app

# Dépendances système (compilation de certaines wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY src/ ./src/

# Variables d'environnement
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/models/model.joblib \
    PREPROCESSOR_PATH=/app/models/preprocessor.joblib

# Répertoires de travail + utilisateur non-root pour la sécurité
RUN mkdir -p /app/models /app/data /app/logs \
    && useradd -m -u 1000 mluser \
    && chown -R mluser:mluser /app
USER mluser

# Port pour l'API
EXPOSE 8000

# Lancement de l'API via uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
