import datetime
import os
import pwd

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator

args = {
    "owner": "airflow",
    "start_date": datetime.datetime(2025, 1, 1),
}

dag = DAG(dag_id="check_user_dag", default_args=args, schedule=None, tags=["check_user"])


def check_user_1():
    try:
        print(f"USERNAME: {pwd.getpwuid(os.getuid())[0]}")
    except KeyError:
        print(f"USERNAME NOT FOUND")


def check_user_2():
    try:
        print(f"USERNAME: {pwd.getpwuid(os.getuid())[0]}")
    except KeyError:
        print(f"USERNAME NOT FOUND")


task1 = PythonOperator(
    task_id="check_user_1",
    python_callable=check_user_1,
    dag=dag,
)

task2 = PythonOperator(
    task_id="check_user_2",
    python_callable=check_user_2,
    dag=dag,
)

task1 >> task2