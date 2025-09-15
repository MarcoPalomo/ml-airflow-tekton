FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY setup.py .

# Installation du package
RUN pip install -e .

# Variables d'environnement
ENV PYTHONPATH=/app
ENV MODEL_PATH=/app/models/model.joblib
ENV PREPROCESSOR_PATH=/app/models/preprocessor.joblib

# Création des répertoires
RUN mkdir -p /app/models /app/data /app/logs

# Utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 mluser && chown -R mluser:mluser /app
USER mluser

# Port pour l'API
EXPOSE 8000

# Commande par défaut (peut être surchargée)
CMD ["python", "src/api/main.py"]