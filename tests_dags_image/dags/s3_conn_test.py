import datetime

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

args = {
    'owner': 'Airflow',
    'start_date': datetime.datetime(2025, 1, 1),
}

S3_FILENAME = "my-test-dag.py"
CONN_NAME = "test_s3"
BUCKET_NAME = "source"

dag = DAG(
    dag_id='s3_conn_test',
    default_args=args,
    schedule=None,
    tags=['check_s3'],
    is_paused_upon_creation=True
)


def create_s3_file(ds, **kwargs):
    # Upload current DAG file to Minio
    from pathlib import Path
    s3 = S3Hook(CONN_NAME)
    s3.load_file(str(Path(__file__).absolute()),
                 key=S3_FILENAME,
                 bucket_name=BUCKET_NAME)


def check_s3_file(ds, **kwargs):
    # Check file file presence in Minio
    s3 = S3Hook(CONN_NAME)
    if not s3.check_for_key(key=S3_FILENAME, bucket_name=BUCKET_NAME):
        raise ValueError("created file doesn't exist")


def delete_s3_file(ds, **kwargs):
    # Delete uploaded file from Minio
    s3 = S3Hook(CONN_NAME)
    s3.delete_objects(keys=S3_FILENAME,
                      bucket=BUCKET_NAME)


task1 = PythonOperator(
    task_id='create_s3_file',
    python_callable=create_s3_file,
    dag=dag,
)

task2 = PythonOperator(
    task_id='check_s3_file',
    python_callable=check_s3_file,
    dag=dag,
)

task3 = PythonOperator(
    task_id='delete_s3_file',
    python_callable=delete_s3_file,
    dag=dag,
)

task1 >> task2 >> task3
