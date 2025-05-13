import datetime

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator

args = {
    "owner": "airflow",
    "start_date": datetime.datetime(2025, 1, 1),
}

dag = DAG(dag_id="noop_dag", default_args=args, schedule=None, tags=["noop"])


def noop1():
    print("Running no-op task number 1")


def noop2():
    print("Running no-op task number 2")


task1 = PythonOperator(
    task_id="noop1",
    python_callable=noop1,
    dag=dag,
)

task2 = PythonOperator(
    task_id="noop2",
    python_callable=noop2,
    dag=dag,
)

task1 >> task2
