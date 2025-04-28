# basics from https://airflow.apache.org/docs/apache-airflow-providers-postgres/stable/operators
# /postgres_operator_howto_guide.html#the-complete-postgres-operator-dag

import datetime

from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.python import PythonOperator

DAG_ID = "postgres_operator_test_dag"


def check_awaited_message(ti, **kwargs):
    return_value = ti.xcom_pull(task_ids=['get_birth_date'], key='return_value')[0]
    print(f"awaited message:{len(return_value[1])}")
    if len(return_value[1]) < 4:
        raise ValueError("Wrong message received")


with DAG(
    dag_id=DAG_ID,
    start_date=datetime.datetime(2020, 2, 2),
    schedule="@once",
    catchup=False,
) as dag:
    create_pet_table = SQLExecuteQueryOperator(
        conn_id="postgres_test_conn",
        task_id="create_pet_table",
        sql="""
            CREATE TABLE IF NOT EXISTS pet (
            pet_id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            pet_type VARCHAR NOT NULL,
            birth_date DATE NOT NULL,
            OWNER VARCHAR NOT NULL);
          """,
    )
    populate_pet_table = SQLExecuteQueryOperator(
        conn_id="postgres_test_conn",
        task_id="populate_pet_table",
        sql="""
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Max', 'Dog', '2018-07-05', 'Jane');
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Susie', 'Cat', '2019-05-01', 'Phil');
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Lester', 'Hamster', '2020-06-23', 'Lily');
            INSERT INTO pet (name, pet_type, birth_date, OWNER)
            VALUES ( 'Quincy', 'Parrot', '2013-08-11', 'Anne');
            """,
    )
    get_all_pets = SQLExecuteQueryOperator(conn_id="postgres_test_conn",
                                           task_id="get_all_pets", sql="SELECT * FROM pet;")
    get_birth_date = SQLExecuteQueryOperator(
        conn_id="postgres_test_conn",
        task_id="get_birth_date",
        sql="SELECT * FROM pet WHERE birth_date BETWEEN SYMMETRIC %(begin_date)s AND %(end_date)s",
        parameters={"begin_date": "2010-01-01", "end_date": "2020-12-31"},
        hook_params={'options': '-c statement_timeout=3000ms'},
    )

    check_return = PythonOperator(
        task_id='check_return',
        python_callable=check_awaited_message,
    )

    create_pet_table >> populate_pet_table >> get_all_pets >> get_birth_date >> check_return
