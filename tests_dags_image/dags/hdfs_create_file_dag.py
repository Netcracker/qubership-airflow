import datetime
import os
import uuid

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.apache.hdfs.hooks.webhdfs import WebHDFSHook

# for this DAG to work the webhdfs_default connection must be configured

args = {
    "owner": "Airflow",
    "start_date": datetime.datetime(2025, 1, 1),
}

dag = DAG(
    dag_id="hdfs_create_file_dag",
    default_args=args,
    schedule="* * * * *",
    tags=["check_hdfs"],
    is_paused_upon_creation=True,
    catchup=False,
)

AIRFLOW_TEST_FOLDER_PATH = "/airflow_upload_files_test"


def create_hdfs_file(ds, **kwargs):
    hdfs_hook = WebHDFSHook(webhdfs_conn_id="webhdfs_default")
    if hdfs_hook.check_for_path(AIRFLOW_TEST_FOLDER_PATH):
        print("found old folder, using it")
    else:
        print("creating folder ...")
        hdfs_hook.get_conn().makedirs(AIRFLOW_TEST_FOLDER_PATH)
    randomfile = str(uuid.uuid4())
    filesize = os.getenv("HDFS_FILE_SIZE", 1000)
    with open(randomfile, "wb") as f:
        f.write(os.urandom(filesize))
    hdfs_hook.load_file(randomfile, AIRFLOW_TEST_FOLDER_PATH)
    os.remove(randomfile)
    return "random file was created and uploaded to HDFS"


task1 = PythonOperator(
    task_id="generate_and_upload_file",
    python_callable=create_hdfs_file,
    dag=dag,
)

task1
