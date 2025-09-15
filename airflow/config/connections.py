from airflow.models import Connection
from airflow import settings

# Connexion Starburst Trino
trino_conn = Connection(
    conn_id='starburst_trino',
    conn_type='trino',
    host='starburst-coordinator.cluster.local',
    port=8080,
    schema='lakehouse',
    login='airflow-service-account',
    extra='{"auth": "basic", "verify": "/path/to/ca-cert.pem"}'
)

# Connexion S3 pour les modèles
s3_conn = Connection(
    conn_id='aws_s3',
    conn_type='aws',
    extra='{"aws_access_key_id": "XXX", "aws_secret_access_key": "YYY", "region_name": "eu-west-1"}'
)