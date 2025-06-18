This section provides information about the HA scenarios for airflow Service.

For execute HA cases we would use sleeping custom dag from https://github.com/Netcracker/qubership-airflow/blob/main/tests_dags_image/dags/sleeping_dag.py .

# Loss of one of the workers during sleeping Dag executed

You can trigger sleeping Dag and wait when start execute task5, task6, task7 and task8 in parallel. After that you need kill with force flag one of workers (for example, killed worker-0).

ER:
* Workers is up and running.
* Tasks which executed on worker-0 have error state. 
* Tasks which executed on worker-1 have success state.
* Tasks that run after tasks5-tasks8 have state upstream_failed.

If you want to continue DAG execution then you need clear all failed tasks and after that the DAG will continue to execute automatically. For clearing tasks you can go to "Details" tab in Dag page.

*Attention:* Tasks which failed when workers restart haven't information about hostname in "List Task Instance" tab. But after restarting tasks, it information appears.
