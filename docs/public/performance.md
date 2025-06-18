**Note** The information in this section is applicable for Airflow version  1.10.x.

Airflow performance can be affected by Airflow inner parameters. For more information, refer to [https://airflow.apache.org/docs/apache-airflow/1.10.15/faq.html#how-can-my-airflow-dag-run-faster](https://airflow.apache.org/docs/apache-airflow/1.10.15/faq.html#how-can-my-airflow-dag-run-faster).

The main performance relevant parameters when using celery executor are:

|Airflow name|How to set it via Charts|Default Value|Description|
|---|---|---|---|
|parallelism|`airflow.config.AIRFLOW__CORE__PARALLELISM`|32|The maximum number of task instances that should run simultaneously on this Airflow installation.|
|dag_concurrency|`airflow.config.AIRFLOW__CORE__DAG_CONCURRENCY`|16|The number of task instances allowed to run concurrently by the scheduler. You can define it on your DAG too.|
|max_active_runs_per_dag|`airflow.config.AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG`|16|The maximum number of active DAG runs per DAG. You can define on your DAG too with `max_active_runs` param.|
|worker_concurrency|`workers.celery.instances`|16|The number of task instances that a celery worker takes at the same time.|
|task_concurrency|must be set in the DAG|Limited by other parameters|Specifies the number of concurrent running task instances across dag_runs per task|

Changing the above parameters along with the number of workers can influence the consumed resources and times of DAG completion. Here are examples of the time consumed and resources for the DAG consisting of 20 branches with 20 simple python print tasks in it. In this case, no more than 20 tasks are executed at the same time:

|Airflow Changed Parameters|Worker Pods|Worker: Max Resources Consumed|Scheduler: Max Resources Consumed|Overall (with Flower): Max Resources Consumed|Time Consumed (minutes)|
|---|---|---|---|---|---|
|Default|1|3.3 GiB, 3.5 CPU|380 MiB, 1.25 CPU|5 GiB, 4.8 CPU|10:17|
|Default|3|2.3 GiB, 2.75 CPU|380 MiB, 1.1 CPU|6.5 GiB, 7.5 CPU|6:34|
|Default|5|1.5 GiB, 1.6 CPU|380 MiB, 1.1 CPU|8.5 GiB, 8 CPU|6:29|
|parallelism=64, dag_concurrency=64, max_active_runs_per_dag=64, worker_concurrency=64|1|7 GiB, 3.1 CPU|350 MiB, 0.85 CPU|8 GiB, 4.0 CPU|11:39|
|parallelism=4, dag_concurrency=4, max_active_runs_per_dag=4, worker_concurrency=4|1|1.1 GiB, 1.4 CPU|350 MiB, 0.85 CPU|2.5 GiB, 2.5 CPU|28:32|
|parallelism=20, dag_concurrency=20, max_active_runs_per_dag=20, worker_concurrency=4|5|1.1 GiB, 1.5 CPU|350 MiB, 0.85 CPU|6.6 GiB, 6.5 CPU|6:39|

When working with Airflow one must take into account Redis and Postgres resources. Too many workers and processes per worker can require a lot of PostgreSQL connections. Also not enough resources limits on Airflow worker pods might result in Airflow workers restarting under load, so the limits must be set accordingly.