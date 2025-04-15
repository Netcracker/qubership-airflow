from time import sleep
from datetime import timedelta

from airflow.utils.dates import days_ago

from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator

args = {
    'owner': 'Airflow',
    'start_date': days_ago(2),
    'retries': 3,
    'retry_delay': timedelta(minutes=1)
}

dag = DAG(
    dag_id='sleep_dag_with_retries',
    default_args=args,
    schedule_interval=None,
    tags=['sleeping']
)

# def sleep1():
#     print("sleeping 1 min")
#     t=randint(0,2)
#     if t == 0 or t ==1:
#         raise Exception("UNLUCKY")
#     print("end sleeping 1 min")


def sleep1():
    print("sleeping 1 min")
    sleep(60)
    print("end sleeping 1 min")


def sleep2():
    print("sleeping 1 min")
    sleep(60)
    print("end sleeping 1 min")


def sleep3():
    print("sleeping 1 min")
    sleep(60)
    print("end sleeping 1 min")


task1 = PythonOperator(
    task_id='sleep1',
    python_callable=sleep1,
    dag=dag,
)

task2 = PythonOperator(
    task_id='task2',
    python_callable=sleep2,
    dag=dag,
)


task3 = PythonOperator(
    task_id='task3',
    python_callable=sleep3,
    dag=dag,
)

task1 >> task2 >> task3
