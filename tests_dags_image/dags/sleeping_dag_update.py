from time import sleep

import datetime
from datetime import timedelta

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator

args = {
    "owner": "Airflow",
    "start_date": datetime.datetime(2025, 1, 1),
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
}

dag = DAG(
    dag_id="sleeping_dag_update",
    default_args=args,
    schedule=None,
    tags=["sleeping"],
    is_paused_upon_creation=False,
)

DAG_VERSION = "v1"
SLEEP_TIME = 180


def sleep0(ds, **kwargs):
    print(f"DAG Version is {DAG_VERSION}")
    sleep_0_value = "sleep_0_value"
    print(f"xcom0value_push{sleep_0_value}")
    kwargs["ti"].xcom_push(key="sleep0", value=sleep_0_value)
    print(f"sleeping {SLEEP_TIME/60} min")
    sleep(SLEEP_TIME)
    print(f"end sleeping {SLEEP_TIME/60} min")


def sleep1(ds, **kwargs):
    print(f"DAG Version is {DAG_VERSION}")
    sleep_1_value = "sleep_1_value"
    print(f"xcom1value_push{sleep_1_value}")
    kwargs["ti"].xcom_push(key="sleep1", value=sleep_1_value)
    print(f"sleeping {SLEEP_TIME/60} min")
    sleep(SLEEP_TIME)
    print(f"end sleeping {SLEEP_TIME/60} min")
    # raise Exception("OLD DAG VERSION")


def sleep2(ds, **kwargs):
    print(f"DAG Version is {DAG_VERSION}")
    sleep_2_value = "sleep_2_value"
    print(f"xcom2value_push{sleep_2_value}")
    kwargs["ti"].xcom_push(key="sleep2", value=sleep_2_value)
    xcom1value = kwargs["ti"].xcom_pull(key="sleep1", task_ids="sleep1")
    print(f"xcom1value_pull{xcom1value}")
    xcom0value = kwargs["ti"].xcom_pull(key="sleep0", task_ids="sleep0")
    print(f"xcom0value_pull{xcom0value}")
    print(f"sleeping {SLEEP_TIME/60} min")
    sleep(SLEEP_TIME)
    print(f"end sleeping {SLEEP_TIME/60} min")


def sleep3(ds, **kwargs):
    print(f"DAG Version is {DAG_VERSION}")
    sleep_3_value = "sleep_3_value"
    print(f"xcom3value_push{sleep_3_value}")
    kwargs["ti"].xcom_push(key="sleep3", value=sleep_3_value)
    xcom1value = kwargs["ti"].xcom_pull(key="sleep1", task_ids="sleep1")
    print(f"xcom1value_pull{xcom1value}")
    xcom2value = kwargs["ti"].xcom_pull(key="sleep2", task_ids="sleep2")
    print(f"xcom2value_pull{xcom2value}")
    print(f"sleeping {SLEEP_TIME/60} min")
    sleep(SLEEP_TIME)
    print(f"end sleeping {SLEEP_TIME/60} min")


def sleep4():
    print(f"DAG Version is {DAG_VERSION}")
    print(f"sleeping {SLEEP_TIME/60} min")
    sleep(SLEEP_TIME)
    print(f"end sleeping {SLEEP_TIME/60} min")


task1 = PythonOperator(
    task_id="sleep1.01",
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

# task1 >> task2 >> [task5, task6, task7, task8] >> task3 >> task4

task1 >> task2 >> task5 >> task6 >> task7 >> task8 >> task3 >> task4

# task0 = PythonOperator(
#     task_id="sleep0",
#     python_callable=sleep0,
#     dag=dag,
# )
#
# task0 >> task1 >> task2 >> task5 >> task6 >> task7 >> task8 >> task3 >> task4
