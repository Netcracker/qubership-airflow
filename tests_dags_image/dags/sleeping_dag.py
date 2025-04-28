from time import sleep

import datetime

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator

args = {
    "owner": "Airflow",
    "start_date": datetime.datetime(2025, 1, 1),
}

dag = DAG(
    dag_id="sleeping_dag",
    default_args=args,
    schedule=None,
    tags=["sleeping"],
    is_paused_upon_creation=False,
)


def sleep1():
    print("sleeping 1 min")
    sleep(60)
    print("end sleeping 1 min")


def sleep2():
    print("sleeping 2 min")
    sleep(120)
    print("end sleeping 2 min")


def sleep3():
    print("sleeping 3 min")
    sleep(180)
    print("end sleeping 3 min")


def sleep4():
    print("sleeping 4 min")
    sleep(240)
    print("end sleeping 4 min")


task1 = PythonOperator(
    task_id="sleep1",
    python_callable=sleep1,
    dag=dag,
)

task2 = PythonOperator(
    task_id="sleep2",
    python_callable=sleep2,
    dag=dag,
)

task3 = PythonOperator(
    task_id="sleep3",
    python_callable=sleep3,
    dag=dag,
)

task4 = PythonOperator(
    task_id="sleep4",
    python_callable=sleep4,
    dag=dag,
)


task5 = PythonOperator(
    task_id="task5",
    python_callable=sleep1,
    dag=dag,
)

task6 = PythonOperator(
    task_id="task6",
    python_callable=sleep2,
    dag=dag,
)

task7 = PythonOperator(
    task_id="task7",
    python_callable=sleep3,
    dag=dag,
)

task8 = PythonOperator(
    task_id="task8",
    python_callable=sleep4,
    dag=dag,
)

task1 >> task2 >> [task5, task6, task7, task8] >> task3 >> task4
