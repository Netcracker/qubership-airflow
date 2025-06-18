import datetime

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.apache.hdfs.hooks.webhdfs import WebHDFSHook

# for this DAG to work the webhdfs_default connection must be configured

args = {
    "owner": "Airflow",
    "start_date": datetime.datetime(2025, 1, 1),
}

dag = DAG(
    dag_id="hdfs_conn_test",
    default_args=args,
    schedule=None,
    tags=["check_hdfs"],
    is_paused_upon_creation=True,
)

AIRFLOW_TEST_FOLDER_PATH = "/airflow_test/path/folder"


def create_hdfs_folder(ds, **kwargs):
    hdfs_hook = WebHDFSHook(webhdfs_conn_id="webhdfs_default")
    if hdfs_hook.check_for_path(AIRFLOW_TEST_FOLDER_PATH):
        print("found old folder, deleting...")
        hdfs_hook.get_conn().delete(AIRFLOW_TEST_FOLDER_PATH, recursive=True)
        print("old folder deleted...")
    print("creating folder ...")
    hdfs_hook.get_conn().makedirs(AIRFLOW_TEST_FOLDER_PATH)
    return "airflow can create hdfs folders"


def check_hdfs_folder(ds, **kwargs):
    hdfs_hook = WebHDFSHook(webhdfs_conn_id="webhdfs_default")
    print("checking created folder ...")
    if hdfs_hook.check_for_path(AIRFLOW_TEST_FOLDER_PATH):
        return "created folder exist"
    else:
        raise ValueError("created folder doesn't exist")


task1 = PythonOperator(
    task_id="create_hdfs_folder",
    python_callable=create_hdfs_folder,
    dag=dag,
)

task2 = PythonOperator(
    task_id="check_hdfs_folder",
    python_callable=check_hdfs_folder,
    dag=dag,
)

task1 >> task2
