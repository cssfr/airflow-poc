from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator

# Default arguments for the DAG
default_args = {
    'owner': 'poc-2',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'poc2_test_dag',
    default_args=default_args,
    description='POC-2 Test DAG to verify Airflow is working',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['poc-2', 'test'],
)

def test_supabase_connection():
    """Test function to verify Supabase connection"""
    try:
        from supabase import create_client
        import os
        
        # Get environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            return f"Missing environment variables: URL={bool(supabase_url)}, KEY={bool(supabase_key)}"
        
        # Test connection
        client = create_client(supabase_url, supabase_key)
        result = client.table('strategies').select('id, name').limit(1).execute()
        
        return f"✅ Supabase connection successful! Found {len(result.data)} strategies"
        
    except Exception as e:
        return f"❌ Supabase connection failed: {str(e)}"

def test_minio_connection():
    """Test function to verify MinIO connection"""
    try:
        import duckdb
        import os
        
        # Get environment variables
        minio_endpoint = os.getenv('MINIO_ENDPOINT')
        minio_access_key = os.getenv('MINIO_ACCESS_KEY')
        minio_secret_key = os.getenv('MINIO_SECRET_KEY')
        minio_bucket = os.getenv('MINIO_BUCKET')
        
        if not all([minio_endpoint, minio_access_key, minio_secret_key, minio_bucket]):
            return "Missing MinIO environment variables"
        
        # Test connection with MinIO-specific settings
        conn = duckdb.connect(':memory:')
        conn.execute("INSTALL httpfs")
        conn.execute("LOAD httpfs")
        conn.execute(f"SET s3_endpoint='{minio_endpoint}'")
        conn.execute(f"SET s3_access_key_id='{minio_access_key}'")
        conn.execute(f"SET s3_secret_access_key='{minio_secret_key}'")
        conn.execute("SET s3_use_ssl=true")  # Force HTTPS for MinIO
        conn.execute("SET s3_url_style='path'")  # MinIO uses path-style URLs
        conn.execute("SET s3_region='us-east-1'")  # MinIO default region
        
        # Try to read the specific file that exists
        result = conn.execute(f"SELECT COUNT(*) FROM read_parquet('s3://{minio_bucket}/ohlcv/1Y/symbol=DAX/year=2025/DAX_2025.parquet')").fetchone()
        
        return f"✅ MinIO connection successful! Found data in bucket"
        
    except Exception as e:
        return f"❌ MinIO connection failed: {str(e)}"

# Define tasks
start_task = DummyOperator(
    task_id='start',
    dag=dag,
)

test_supabase_task = PythonOperator(
    task_id='test_supabase_connection',
    python_callable=test_supabase_connection,
    dag=dag,
)

test_minio_task = PythonOperator(
    task_id='test_minio_connection',
    python_callable=test_minio_connection,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end',
    dag=dag,
)

# Define task dependencies
start_task >> [test_supabase_task, test_minio_task] >> end_task
