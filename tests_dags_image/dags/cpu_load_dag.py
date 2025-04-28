import math
import datetime

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator

args = {
    'owner': 'Airflow',
    'start_date': datetime.datetime(2025, 1, 1),
}

dag = DAG(
    dag_id='cpu_load_dag',
    default_args=args,
    schedule_interval=None,
    tags=['cpu_load'],
    is_paused_upon_creation=False
)


# see https://github.com/TheAlgorithms/Python/blob/master/maths/sieve_of_eratosthenes.py
def prime_sieve(num: int) -> list[int]:

    if num <= 0:
        msg = f"{num}: Invalid input, please enter a positive integer."
        raise ValueError(msg)

    sieve = [True] * (num + 1)
    prime = []
    start = 2
    end = int(math.sqrt(num))

    while start <= end:
        # If start is a prime
        if sieve[start] is True:
            prime.append(start)

            # Set multiples of start be False
            for i in range(start * start, num + 1, start):
                if sieve[i] is True:
                    sieve[i] = False

        start += 1

    for j in range(end + 1, num + 1):
        if sieve[j] is True:
            prime.append(j)

    return prime


def prime100000000():
    result = prime_sieve(100000000)
    print(result)


def prime200000000():
    result = prime_sieve(200000000)
    print(result)


def prime300000000():
    result = prime_sieve(300000000)
    print(result)


def prime400000000():
    result = prime_sieve(400000000)
    print(result)


prime100000000_1 = PythonOperator(
    task_id='prime100000000_1',
    python_callable=prime100000000,
    dag=dag,
)

prime200000000_1 = PythonOperator(
    task_id='prime200000000_1',
    python_callable=prime200000000,
    dag=dag,
)

prime300000000_1 = PythonOperator(
    task_id='prime300000000_1',
    python_callable=prime300000000,
    dag=dag,
)

prime400000000_1 = PythonOperator(
    task_id='prime400000000_1',
    python_callable=prime400000000,
    dag=dag,
)


prime100000000_2 = PythonOperator(
    task_id='prime100000000_2',
    python_callable=prime100000000,
    dag=dag,
)

prime200000000_2 = PythonOperator(
    task_id='prime200000000_2',
    python_callable=prime200000000,
    dag=dag,
)

prime300000000_2 = PythonOperator(
    task_id='prime300000000_2',
    python_callable=prime300000000,
    dag=dag,
)

prime400000000_2 = PythonOperator(
    task_id='prime400000000_2',
    python_callable=prime400000000,
    dag=dag,
)

prime100000000_1 >> prime200000000_1 >> \
    [prime100000000_2, prime200000000_2, prime300000000_2, prime400000000_2] >> \
    prime300000000_1 >> prime400000000_1
