# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# Modified in 2025 by NetCracker Technology Corp.
"""
This is an example DAG which uses SparkKubernetesOperator and SparkKubernetesSensor.
In this example, we create two tasks which execute sequentially.
The first task is to submit sparkApplication on Kubernetes cluster(the example uses spark-pi application).
and the second task is to check the final state of the sparkApplication that submitted in the first state.

Spark-on-k8s operator is required to be already installed on Kubernetes
https://github.com/GoogleCloudPlatform/spark-on-k8s-operator
"""

from datetime import timedelta

# [START import_module]
# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

from airflow.models import Variable

# Operators; we need this to operate!
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import (
    SparkKubernetesOperator,
)
from airflow.providers.cncf.kubernetes.sensors.spark_kubernetes import (
    SparkKubernetesSensor,
)
import datetime

# [END import_module]

# [START default_args]
# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "max_active_runs": 1,
}
# [END default_args]

# [START instantiate_dag]

dag = DAG(
    dag_id="spark_streaming-kafka-word-count-spark-operator",
    default_args=default_args,
    description="submit spark-streaming-kafka-word-count as sparkApplication on kubernetes",
    schedule=timedelta(days=1),
    start_date=datetime.datetime(2025, 1, 1),
)

# airflow variable to set spark applications namespace. By default the namespace is "spark-apps".
spark_app_namespace = Variable.get("spark_app_namespace", "spark-apps")

t1 = SparkKubernetesOperator(
    task_id="spark_streaming_submit",
    namespace=spark_app_namespace,
    application_file="./spark-apps-cr/spark-streaming-word-count.yaml",
    kubernetes_conn_id="kubernetes_default",
    do_xcom_push=True,
    dag=dag,
)

t2 = SparkKubernetesSensor(
    task_id="spark_streaming_monitor",
    namespace=spark_app_namespace,
    attach_log=True,
    mode="reschedule",
    application_name="{{ task_instance.xcom_pull(task_ids='spark_streaming_submit')['metadata']['name'] }}",
    kubernetes_conn_id="kubernetes_default",
    dag=dag,
)
t1 >> t2
