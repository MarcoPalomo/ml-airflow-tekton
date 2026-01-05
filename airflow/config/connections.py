"""
Configuration des connexions Airflow

⚠️ AVERTISSEMENT DE SÉCURITÉ ⚠️
=====================================
Ce fichier contient des configurations de connexion avec des valeurs de placeholder.

ACTIONS REQUISES EN PRODUCTION:
1. NE JAMAIS hardcoder de credentials réels dans ce fichier
2. Utiliser un gestionnaire de secrets approprié:
   - Kubernetes Secrets
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager

3. Options recommandées pour gérer les connexions Airflow:
   a) Variables d'environnement:
      AIRFLOW_CONN_STARBURST_TRINO='trino://user:pass@host:port/schema'

   b) Airflow UI:
      Admin > Connections > Create

   c) Airflow CLI:
      airflow connections add 'starburst_trino' \
        --conn-type 'trino' \
        --conn-host 'host' \
        --conn-login 'user' \
        --conn-password 'password'

   d) Secrets Backend (recommandé):
      - Configurer dans airflow.cfg:
        [secrets]
        backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
        backend_kwargs = {"url": "vault_url", "token": "token"}

4. Les valeurs "XXX" et "YYY" ci-dessous sont des PLACEHOLDERS et doivent être remplacées

Pour plus d'infos: https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/
=====================================
"""

from airflow.models import Connection
from airflow import settings
import os

# ⚠️ SÉCURITÉ: Utiliser des variables d'environnement plutôt que des valeurs hardcodées
# Les valeurs par défaut ci-dessous sont des PLACEHOLDERS et NE DOIVENT PAS être utilisées en production

# Connexion Starburst Trino
trino_conn = Connection(
    conn_id='starburst_trino',
    conn_type='trino',
    host=os.getenv('TRINO_HOST', 'starburst-coordinator.cluster.local'),
    port=int(os.getenv('TRINO_PORT', '8080')),
    schema=os.getenv('TRINO_SCHEMA', 'lakehouse'),
    login=os.getenv('TRINO_USER', 'airflow-service-account'),
    password=os.getenv('TRINO_PASSWORD', None),  # ⚠️ À définir via variable d'environnement
    extra=os.getenv('TRINO_EXTRA', '{"auth": "basic", "verify": "/path/to/ca-cert.pem"}')
)

# Connexion S3 pour les modèles
# ⚠️ CRITIQUE: Remplacer "XXX" et "YYY" par vos vraies credentials OU utiliser IAM Roles
s3_conn = Connection(
    conn_id='aws_s3',
    conn_type='aws',
    extra=os.getenv(
        'AWS_S3_EXTRA',
        '{"aws_access_key_id": "' + os.getenv('AWS_ACCESS_KEY_ID', 'XXX') + '", '
        '"aws_secret_access_key": "' + os.getenv('AWS_SECRET_ACCESS_KEY', 'YYY') + '", '
        '"region_name": "' + os.getenv('AWS_DEFAULT_REGION', 'eu-west-1') + '"}'
    )
)

# Note: En production, préférer l'utilisation de IAM Roles pour EC2/EKS plutôt que des access keys