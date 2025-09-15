from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.trino.operators.trino import TrinoOperator
from airflow.providers.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

default_args = {
    'owner': 'ml-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ml_model_retraining',
    default_args=default_args,
    description='Pipeline de re-entrainement du modèle ML',
    schedule_interval='0 2 * * *',  # Chaque jour à 2h du matin
    catchup=False,
    max_active_runs=1,
)

# Tâche 1: Extraction des données
extract_data = TrinoOperator(
    task_id='extract_latest_data',
    trino_conn_id='starburst_trino',
    sql="""
        CREATE TABLE lakehouse.ml_datasets.raw_data_{{ ds_nodash }} AS
        SELECT 
            s.transaction_id,
            s.customer_id,
            s.product_id,
            s.amount,
            s.transaction_date,
            m.campaign_id,
            m.channel,
            c.customer_segment
        FROM sales_db.transactions s
        LEFT JOIN marketing_lake.campaigns m ON s.customer_id = m.customer_id
        LEFT JOIN customer_db.profiles c ON s.customer_id = c.customer_id
        WHERE s.transaction_date >= DATE '{{ ds }}' - INTERVAL '30' DAY
    """,
    dag=dag,
)

# Tâche 2: Transformation et nettoyage
transform_data = TrinoOperator(
    task_id='transform_and_clean_data',
    trino_conn_id='starburst_trino',
    sql="""
        CREATE TABLE lakehouse.ml_datasets.clean_training_data_{{ ds_nodash }} AS
        SELECT 
            customer_id,
            AVG(amount) as avg_transaction_amount,
            COUNT(*) as transaction_count,
            MAX(transaction_date) as last_transaction_date,
            COALESCE(customer_segment, 'Unknown') as customer_segment,
            COUNT(DISTINCT campaign_id) as campaign_exposure_count
        FROM lakehouse.ml_datasets.raw_data_{{ ds_nodash }}
        WHERE amount > 0 AND customer_id IS NOT NULL
        GROUP BY customer_id, customer_segment
        HAVING COUNT(*) >= 5  -- Au moins 5 transactions
    """,
    dag=dag,
)

# Tâche 3: Re-entrainement du modèle
retrain_model = KubernetesPodOperator(
    task_id='retrain_ml_model',
    name='ml-retraining-pod',
    namespace='ml-workloads',
    image='your-registry/ml-training:latest',
    env_vars={
        'TRAINING_DATA_PATH': 's3://ml-bucket/training-data/{{ ds_nodash }}/',
        'MODEL_OUTPUT_PATH': 's3://ml-bucket/models/{{ ds_nodash }}/',
        'MLFLOW_TRACKING_URI': 'http://mlflow-server:5000',
    },
    cmds=['python'],
    arguments=['train_model.py', '--data-date', '{{ ds_nodash }}'],
    get_logs=True,
    dag=dag,
)

# Tâche 4: Validation du nouveau modèle
validate_model = PythonOperator(
    task_id='validate_retrained_model',
    python_callable=validate_model_performance,
    op_kwargs={
        'model_path': 's3://ml-bucket/models/{{ ds_nodash }}/',
        'validation_data_path': 's3://ml-bucket/validation-data/',
        'min_accuracy_threshold': 0.85,
    },
    dag=dag,
)

# Tâche 5: Déclenchement du déploiement Tekton (si validation OK)
trigger_deployment = PythonOperator(
    task_id='trigger_tekton_deployment',
    python_callable=trigger_tekton_pipeline,
    op_kwargs={
        'model_version': '{{ ds_nodash }}',
        'tekton_pipeline_url': 'http://tekton-dashboard:9097/api/v1/namespaces/tekton-pipelines/pipelineruns',
    },
    dag=dag,
)

# Définition des dépendances
extract_data >> transform_data >> retrain_model >> validate_model >> trigger_deployment