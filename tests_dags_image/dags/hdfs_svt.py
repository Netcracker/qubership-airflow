import datetime

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.apache.hdfs.hooks.webhdfs import WebHDFSHook

from airflow.models import Variable

import os


def create_dag(branch_count, branch_length, file_size):
    args = {
        'owner': 'airflow',
        'start_date': datetime.datetime(2025, 1, 1),
    }

    dag = DAG(
        dag_id=dag_id,
        default_args=args,
        # schedule_interval="*/1 * * * *",
        schedule=None,
        tags=['check_hdfs_svt'],
        catchup=False
    )

    def load_file(ds, **kwargs):
        hdfs_hook = WebHDFSHook(webhdfs_conn_id='webhdfs_default')
        file = open("testfile", "wb")
        file.write(os.urandom(file_size))  # generate 100MB random content file by default
        file.close()
        cwd = os.getcwd() + '/testfile'
        path = kwargs['task'].task_id
        if hdfs_hook.check_for_path(path):
            print("found old folder, deleting...")
            hdfs_hook.get_conn().delete(path, recursive=True)
            print("old folder deleted...")
        print("creating folder ...")
        hdfs_hook.get_conn().makedirs(path)
        print("Loading file ...")
        hdfs_hook.load_file(cwd, path)
        print("File uploaded successfully")

    for i in range(0, branch_count):
        branch = []
        for j in range(0, branch_length):
            task_id = f"{branch_count}_{branch_length}_task_{i}_{j}"
            task = PythonOperator(
                task_id=task_id,
                python_callable=load_file,
                dag=dag,
            )
            branch.append(task)

            if j > 0:
                branch[j - 1] >> branch[j]

    return dag


file_size = Variable.get("file_size", 100000000)
BRANCHES_COUNT = [1, 5]
BRANCHES_LENGTH = [1, 5]

for branch_count in BRANCHES_COUNT:
    for branch_length in BRANCHES_LENGTH:
        dag_id = "hdfs_svt_%s_%s" % (branch_count, branch_length)
        globals()[dag_id] = create_dag(branch_count, branch_length, file_size)
