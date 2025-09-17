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

# Tâche 2.1: Validation initiale des données
validate_raw_data = TrinoOperator(
    task_id='validate_raw_data_quality',
    trino_conn_id='starburst_trino',
    sql="""
        -- Vérification de la qualité des données brutes
        CREATE TABLE lakehouse.ml_datasets.data_quality_metrics_{{ ds_nodash }} AS
        WITH stats AS (
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT customer_id) as unique_customers,
                SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_ids,
                SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amounts,
                SUM(CASE WHEN amount <= 0 THEN 1 ELSE 0 END) as non_positive_amounts,
                SUM(CASE WHEN transaction_date IS NULL THEN 1 ELSE 0 END) as null_dates,
                MIN(transaction_date) as min_date,
                MAX(transaction_date) as max_date
            FROM lakehouse.ml_datasets.raw_data_{{ ds_nodash }}
        )
        SELECT 
            'raw_data' as dataset_type,
            total_rows,
            unique_customers,
            null_customer_ids,
            null_amounts,
            non_positive_amounts,
            null_dates,
            min_date,
            max_date,
            ROUND(null_customer_ids * 100.0 / NULLIF(total_rows, 0), 2) as pct_null_customers,
            ROUND(null_amounts * 100.0 / NULLIF(total_rows, 0), 2) as pct_null_amounts,
            ROUND(non_positive_amounts * 100.0 / NULLIF(total_rows, 0), 2) as pct_non_positive_amounts
        FROM stats;
    """,
    dag=dag,
)

# Tâche 2.2: Nettoyage et transformation avancée
transform_data = TrinoOperator(
    task_id='transform_and_clean_data',
    trino_conn_id='starburst_trino',
    sql="""
        -- Étape 1: Création d'une table temporaire avec nettoyage initial
        CREATE TABLE lakehouse.ml_datasets.intermediate_data_{{ ds_nodash }} AS
        WITH cleaned_transactions AS (
            SELECT 
                customer_id,
                -- Nettoyage des montants
                CASE 
                    WHEN amount <= 0 THEN NULL  -- Exclure les montants non positifs
                    WHEN amount > 1000000 THEN NULL  -- Valeurs aberrantes extrêmes
                    ELSE amount 
                END as amount,
                -- Validation des dates
                CASE 
                    WHEN transaction_date < DATE '2010-01-01' THEN NULL  -- Date trop ancienne
                    WHEN transaction_date > CURRENT_DATE + INTERVAL '1' DAY THEN NULL  -- Date future
                    ELSE transaction_date 
                END as transaction_date,
                -- Nettoyage des segments clients
                CASE 
                    WHEN TRIM(customer_segment) = '' THEN 'Unknown'
                    WHEN customer_segment IS NULL THEN 'Unknown'
                    ELSE customer_segment 
                END as customer_segment,
                campaign_id,
                channel
            FROM lakehouse.ml_datasets.raw_data_{{ ds_nodash }}
            WHERE customer_id IS NOT NULL
        ),
        -- Agrégation des données par client
        customer_metrics AS (
            SELECT 
                customer_id,
                AVG(amount) as avg_transaction_amount,
                MEDIAN(amount) as median_transaction_amount,
                STDDEV_POP(amount) as std_transaction_amount,
                COUNT(*) as transaction_count,
                MAX(transaction_date) as last_transaction_date,
                MIN(transaction_date) as first_transaction_date,
                customer_segment,
                COUNT(DISTINCT campaign_id) as campaign_exposure_count,
                COUNT(DISTINCT channel) as channel_count,
                -- Détection des valeurs aberrantes avec méthode IQR
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY amount) as q1_amount,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount) as q3_amount
            FROM cleaned_transactions
            WHERE amount IS NOT NULL
            GROUP BY customer_id, customer_segment
            HAVING COUNT(*) >= 5  -- Au moins 5 transactions valides
        )
        -- Création de la table finale avec features supplémentaires
        SELECT 
            customer_id,
            avg_transaction_amount,
            median_transaction_amount,
            std_transaction_amount,
            transaction_count,
            last_transaction_date,
            first_transaction_date,
            DATE_DIFF('day', first_transaction_date, last_transaction_date) as customer_duration_days,
            customer_segment,
            campaign_exposure_count,
            channel_count,
            -- Détection des valeurs aberrantes
            CASE 
                WHEN avg_transaction_amount < (q1_amount - 1.5 * (q3_amount - q1_amount)) 
                     OR avg_transaction_amount > (q3_amount + 1.5 * (q3_amount - q1_amount))
                THEN TRUE 
                ELSE FALSE 
            END as is_outlier
        FROM customer_metrics;
    """,
    dag=dag,
)

# Tâche 2.3: Validation des données nettoyées
validate_clean_data = TrinoOperator(
    task_id='validate_clean_data_quality',
    trino_conn_id='starburst_trino',
    sql="""
        -- Vérification de la qualité des données nettoyées
        INSERT INTO lakehouse.ml_datasets.data_quality_metrics_{{ ds_nodash }}
        WITH stats AS (
            SELECT 
                'clean_data' as dataset_type,
                COUNT(*) as total_rows,
                COUNT(DISTINCT customer_id) as unique_customers,
                0 as null_customer_ids,  -- Déjà filtré
                SUM(CASE WHEN avg_transaction_amount IS NULL THEN 1 ELSE 0 END) as null_amounts,
                SUM(CASE WHEN is_outlier = TRUE THEN 1 ELSE 0 END) as outlier_customers,
                MIN(last_transaction_date) as min_date,
                MAX(last_transaction_date) as max_date,
                AVG(transaction_count) as avg_transactions_per_customer,
                AVG(avg_transaction_amount) as avg_amount_per_customer
            FROM lakehouse.ml_datasets.intermediate_data_{{ ds_nodash }}
        )
        SELECT 
            dataset_type,
            total_rows,
            unique_customers,
            null_customer_ids,
            null_amounts,
            0 as non_positive_amounts,  -- Déjà filtré
            0 as null_dates,  -- Déjà validé
            min_date,
            max_date,
            0 as pct_null_customers,
            ROUND(null_amounts * 100.0 / NULLIF(total_rows, 0), 2) as pct_null_amounts,
            0 as pct_non_positive_amounts,
            avg_transactions_per_customer,
            avg_amount_per_customer,
            outlier_customers,
            ROUND(outlier_customers * 100.0 / NULLIF(total_rows, 0), 2) as pct_outliers
        FROM stats;
        
        -- Création de la table finale pour l'entraînement
        CREATE TABLE lakehouse.ml_datasets.clean_training_data_{{ ds_nodash }} AS
        SELECT 
            customer_id,
            avg_transaction_amount,
            median_transaction_amount,
            std_transaction_amount,
            transaction_count,
            customer_duration_days,
            customer_segment,
            campaign_exposure_count,
            channel_count,
            -- Features temporelles
            DATE_DIFF('day', last_transaction_date, CURRENT_DATE) as days_since_last_transaction,
            -- Normalisation des montants
            (avg_transaction_amount - MIN(avg_transaction_amount) OVER ()) / 
                NULLIF(MAX(avg_transaction_amount) OVER () - MIN(avg_transaction_amount) OVER (), 0) as normalized_amount,
            -- Encodage one-hot des segments (exemple pour 3 segments)
            CASE WHEN customer_segment = 'Premium' THEN 1 ELSE 0 END as is_premium,
            CASE WHEN customer_segment = 'Standard' THEN 1 ELSE 0 END as is_standard,
            -- Indicateur de valeur aberrante
            is_outlier
        FROM lakehouse.ml_datasets.intermediate_data_{{ ds_nodash }}
        WHERE is_outlier = FALSE;  -- Exclusion des valeurs aberrantes pour l'entraînement
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
extract_data >> validate_raw_data >> transform_data >> validate_clean_data >> retrain_model >> validate_model >> trigger_deployment