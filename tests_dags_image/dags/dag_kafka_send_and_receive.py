import datetime
import os

from airflow.models import DAG
from airflow.providers.standard.operators.python import PythonOperator

args = {
    "owner": "Airflow",
    "start_date": datetime.datetime(2025, 1, 1),
}

dag = DAG(
    dag_id="kafka_conn_test",
    default_args=args,
    schedule=None,
    tags=["send_kafka"],
    is_paused_upon_creation=True,
)


def send_message_to_kafka(ds, **kwargs):
    from kafka import KafkaProducer

    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        api_version=(0, 10, 1),
        request_timeout_ms=5000,
        max_block_ms=5000,
    )

    producer.send(topic="topic_for_tests_airflow", value=b"testvvvalue", partition=0)
    print(str(ds))
    producer.close()
    return "airflow can send messages to kafka"


def get_message_from_kafka(ds, **kwargs):
    from kafka import KafkaConsumer

    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    consumer = KafkaConsumer(
        bootstrap_servers=kafka_bootstrap_servers,
        api_version=(0, 10, 1),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        consumer_timeout_ms=5000,
    )

    # consumer.assign([TopicPartition('operator_name', 0)])
    consumer.subscribe(topics=["topic_for_tests_airflow"])
    # print(next(consumer))
    counter = 0
    print("receiving messages...")
    for msg in consumer:
        print("received message: " + str(msg.value))
        counter = counter + 1

    consumer.close()
    if counter == 0:
        raise ValueError("no messages were received")
    return "airflow can receive messages from kafka"


task1 = PythonOperator(
    task_id="send_message_to_kafka",
    python_callable=send_message_to_kafka,
    dag=dag,
)

task2 = PythonOperator(
    task_id="get_message_from_kafka",
    python_callable=get_message_from_kafka,
    dag=dag,
)

task1 >> task2
