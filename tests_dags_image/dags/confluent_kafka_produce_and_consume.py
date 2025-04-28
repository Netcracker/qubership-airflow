import datetime

from airflow.providers.apache.kafka.operators.consume import ConsumeFromTopicOperator
from airflow.providers.apache.kafka.operators.produce import ProduceToTopicOperator
from airflow.providers.apache.kafka.sensors.kafka import AwaitMessageSensor
from airflow.providers.standard.operators.python import PythonOperator

from airflow.models import DAG


def producer_function():
    for i in range(3):
        yield f'key{i}', f'value{i}'


def consumer_function(message, prefix=None):
    key = message.key()
    value = message.value()
    print(f'consume, key: {key}, value: {value}')
    return


def await_function(message):
    value = message.value()
    if value.startswith(b"value"):
        return value


def check_awaited_message(ti, **kwargs):
    await_return_value = ti.xcom_pull(task_ids=['confluent_await_message_kafka'], key='return_value')[0]
    print(f"awaited message:{await_return_value}")
    if not await_return_value.startswith("b'value"):
        raise ValueError("Wrong message recieved")


args = {
    'owner': 'Airflow',
    'start_date': datetime.datetime(2025, 1, 1),
}

dag = DAG(
    dag_id='kafka_confluent_conn_test',
    default_args=args,
    schedule=None,
    tags=['confluent_send_kafka'],
    is_paused_upon_creation=True
)

task1 = ProduceToTopicOperator(
    task_id='confluent_produce_message_to_kafka',
    kafka_config_id='kafka_test_conn',
    topic='airflowtestkafkatestopic',
    producer_function="confluent_kafka_produce_and_consume.producer_function",
    dag=dag,
)

task2 = ConsumeFromTopicOperator(
    task_id='confluent_consume_messages_from_kafka',
    kafka_config_id="kafka_test_conn",
    topics=['airflowtestkafkatestopic'],
    apply_function="confluent_kafka_produce_and_consume.consumer_function",
    max_messages=2,
    max_batch_size=2,
    dag=dag,
)

task3 = AwaitMessageSensor(
    task_id='confluent_await_message_kafka',
    kafka_config_id='kafka_test_conn',
    topics=['airflowtestkafkatestopic'],
    apply_function="confluent_kafka_produce_and_consume.await_function",
    dag=dag,
)

task4 = PythonOperator(
    task_id='check_awaited_message',
    python_callable=check_awaited_message,
    dag=dag,
)

task1 >> task2 >> task3 >> task4
