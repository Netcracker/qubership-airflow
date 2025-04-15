from airflow.utils.dates import days_ago

from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator

args = {
    'owner': 'airflow',
    'start_date': days_ago(2),
}

dag = DAG(
    dag_id='noop_dag',
    default_args=args,
    schedule_interval=None,
    tags=['noop']
)


def noop1():
    print("Running no-op task number 1")


def noop2():
    print("Running no-op task number 2")


task1 = PythonOperator(
    task_id='noop1',
    python_callable=noop1,
    dag=dag,
)

task2 = PythonOperator(
    task_id='noop2',
    python_callable=noop2,
    dag=dag,
)

task1 >> task2
