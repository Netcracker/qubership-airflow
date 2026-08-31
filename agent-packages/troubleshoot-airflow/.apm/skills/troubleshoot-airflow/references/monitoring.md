This section provides information about the dashboards and metrics for the Airflow service.

# Airflow Overview Dashboard

The Airflow Overview dashboard provides information about Airflow status, pods, the Airflow scheduler, executor, DAG parser, DAGs, and tasks. This dashboard is based on both the [third‑party Airflow plugin](https://github.com/epoch8/airflow-exporter) and the [official Airflow metrics](https://airflow.apache.org/docs/apache-airflow/3.3.0/logging-monitoring/metrics.html), combined with the [statsd_exporter](https://github.com/prometheus/statsd_exporter). Additionally, the dashboard uses Kubernetes metrics.

## Dashboard Variables

The following is a list of dashboard variables:

* `datasource` – Specifies the data source for the dashboard.
* `airflow_namespace` – Specifies the Airflow namespace.
* `dag_id` – Specifies the DAG ID.
* `task_id` – Specifies the task ID.
* `statsd_pod` – Specifies the StatsD exporter pod to collect metrics from. The current StatsD pod can be seen in the *StatsD pod availability* panel.
* `dag_file` – Specifies the DAG file for DAG‑parsing metrics. This differs from the `dag_id` variable because a single DAG file may contain multiple DAGs and the file name is not necessarily the same as the DAG name.
* `cluster` – Specifies the Kubernetes cluster name when Airflow is deployed in a DR scheme. It enables monitoring of both active and standby Airflow instances using a single dashboard.

## Airflow Status and Resources

This section is based on the third‑party Airflow plugin and shows the status of Airflow pods and the resources they use. The following panels are available:

* `Airflow State` – Displays the overall Airflow status. If no scheduler, API, worker, or DAG‑processor pod is available, the status is shown as `DOWN`. If at least one pod of each type is present but any scheduler, API, or worker pod is not in the `running` state, the status is shown as `DEGRADED`. Otherwise, the status is displayed as `UP`.
* `Unavailable Pods Count` – Shows the number of unavailable scheduler, API, worker, or DAG‑processor pods in the Airflow namespace.
* `Available Scheduler/Worker/API/Flower Pods Count` – Shows the number of available Scheduler, Worker, API, and Flower pods.
* `Failed job runs` – Displays the number of failed jobs in the Airflow namespace.
* `CPU/Memory usage` – Shows CPU and memory usage per pod.
* `CPU/Memory limits usage` – Shows CPU and memory limits usage per pod.
* `Receive/Transmit Bandwidth` – Displays network statistics for the namespace.
* `Rate of Received/Transmitted Packets` – Shows the overall incoming and outgoing network packets per second.

## Airflow DAGs and Task Status

This section is based on the third‑party Airflow plugin and shows the status of Airflow DAGs and tasks. The following panels are available:

* `Last DAG run` - Displays the status of the latest DAG run for DAGs.
* `Number of failed DAGs` - Displays the number of failed DAGs in the selected time period.
* `Currently Running DAGs max duration` - Displays the maximum duration of currently running DAGs for each DAG.
* `Airflow DAG runs per second` - Displays the successful and failed Airflow DAG runs per second.
* `Airflow running DAGs` - Displays the Airflow running DAGs.
* `Airflow task runs per second` – Displays the number of Airflow task runs per second, broken down by status (`successful`, `failed`, `upstream failed`, `skipped`).
* `Airflow active tasks` - Displays the number of current Airflow tasks in `running`, `queued`, `scheduled`, `up for retry` and `none` states.

## StatsD Scheduler and Executor Metrics

This section is based on the official Airflow metrics and shows metrics related to the scheduler and executor. The following panels are available:

* `Airflow executor queued tasks` - Shows queued tasks for Airflow executor.
* `Airflow executor open slots` - Shows the number of open slots in Airflow executor.
* `Starving tasks scheduler` - Shows the number of tasks that cannot be scheduled because of no open slot in pool.
* `Executable tasks scheduler` - Shows the number of tasks, that scheduler considers to be ready for execution.
* `Scheduler heartbeats per second` - Shows the number of scheduler heartbeats per second.
* `Executor running tasks` - Shows the number of running tasks.

## StatsD DAG Processing

This section is based on the official Airflow metrics and shows metrics related to DAG files parsing. The following panels are available:

* `DAGbag size` - Shows Airflow DAG bag size.
* `DAG import errors` - Shows the number of dag import errors.
* `DAG processing total parse time` - Shows seconds taken to scan and import all DAG files once.
* `DAG processing last run seconds ago` - Shows time in seconds since last DAG processing.
* `Average dag processing duration` - Shows milliseconds taken to load the given DAG file.

## StatsD DAG and Task Execution Metrics

This section is based on the official Airflow metrics and shows metrics related to DAG and task execution. The following panels are available:

* `Airflow Schedule Delay` - Shows the seconds of delay between the scheduled DagRun start date and the actual DagRun start date.
* `Airflow latest DAG run duration` - Shows latest DAGrun duration in seconds.
* `Airflow latest run task duration` - Shows latest task run duration in seconds.
* `Number of started and finished tasks` - Shows the number of started and finished tasks.
* `Failed tasks` - Shows number of failed tasks. Note that other metrics in this panel currently do not work correctly.
* `Task max CPU usage percent` - Shows task max CPU usage percent for the latest task run.
* `Task max memory usage percent` - Shows task max memory usage percent for the latest task run.

## Airflow Site Manager Overview

It displays the overall information about the Airflow Site Manager service.

![Airflow SM Overview](/docs/public/images/airflow_sm_overview.png)

* `Airflow Site Manager State` - Displays the state of the Airflow Site Manager. The states are `UP`, `DOWN`, and `Not Installed`.
* `Pod Status` - Displays the status of an Airflow Site Manager pod. The possible values are `Failed`, `Pending`, `Running`, `Succeeded`, and `Unknown`. 
* `CPU Usage` - Displays the amount of CPU used by an Airflow Site Manager pod.
* `Memory Usage` - Displays the amount of memory used by an Airflow Site Manager pod.

# Kubernetes Alerts

Airflow Kubernetes alerts are based on Kubernetes metrics that displays the pod status.
This section describes the existing Prometheus alerts and the methods of resolution.

**Note**: If required, it is possible to add custom alerts with the installation parameters.

|Alert|Possible Reason|
|---|---|
|No kube metrics for Airflow namespace|Platform monitoring that gathers Kubernetes metrics for Airflow namespace is disabled or not working.|

**Solution**:

Check if the platform monitoring is working and has permissions for Airflow namespace.

|Alert|Possible Reason|
|---|---|
|Problematic pods|There are pods in Airflow namespace that are not working for some reason.|

**Solution**:

Check if there are failed or not working pods in Airflow. This could be caused by not working database, wrong connection parameters or resources usage.

|Alert|Possible Reason|
|---|---|
| Scheduler CPU load | Scheduler does not have enough CPU resources. |

**Solution**:

Increase the CPU resources for the scheduler.

| Alert | Possible Reason |
|---|---|
| Scheduler error | Scheduler is down. |

**Solution**:

Check the scheduler state and logs to determine the error.

| Alert | Possible Reason |
|---|---|
| Scheduler memory load | Scheduler does not have enough memory resources. |

**Solution**:

Increase the memory resources for the scheduler.

| Alert     | Possible Reason     |
|-----------|---------------------|
| API error | API server is down. |

**Solution**:

Check the API server state and logs to determine the error.

| Alert | Possible Reason |
|---|---|
| StatsD Prometheus exporter is not available | The StatsD Prometheus exporter was installed but is no longer available. |

**Solution**:

Check the StatsD Prometheus exporter state and logs to determine the error.

| Alert | Possible Reason |
|------|-----------------|
| Worker CPU load | Worker does not have enough CPU resources. |

**Solution**:

Increase the CPU resources for the workers or increase the number of workers. Also consider decreasing the `celery.worker_concurrency` value defined using the `workers.celery.instances` in the Helm chart parameter.

| Alert | Possible Reason |
|---|---|
| Worker error | All workers are down. |

**Solution**:

Check workers state and logs to determine the error.

| Alert | Possible Reason |
|---|---|
| Worker memory load | Worker does not have enough memory resources. |

**Solution**:

Increase the memory resources for workers or increase the number of workers. Also consider decreasing the `celery.worker_concurrency` value defined using the `workers.celery.instances` in the Helm chart parameter.

| Alert | Possible Reason |
|---|---|
| Worker StatefulSet is degraded | Some workers are experiencing problems. |

**Solution**:

Check workers state and logs of the problem workers to determine the error.

| Alert | Possible Reason |
|---|---|
| Some DAG runs longer than `[number]` seconds | Some DAGs are running for an unusually long time. |

**Solution**:

Check if some DAGs are stuck for some reason. If some DAGs can run for a long time, you might want to increase the `.Values.prometheusRule.dagAlerts.maxDagRunDuration` parameter.

| Alert | Possible Reason |
|---|---|
| Some DAG failed | There are failed DAGs in Airflow. |

**Solution**:

There are failed DAG runs in Airflow. To fix the alert, delete these runs or manually change their state.

| Alert | Possible Reason |
|---|---|
| Some task failed | There are failed tasks in Airflow. |

**Solution**:

There are failed task runs in Airflow. To fix the alert, fix the task, or delete these runs, or manually change their state.

| Alert | Possible Reason |
|------|-----------------|
| There are failed jobs in the Airflow namespace | Some jobs (likely the cleanup‑database CronJob) have failed. |

**Solution**:

Check cleanup database job logs.

| Alert | Possible Reason |
|---|---|
| Cleanup database CronJob takes too long to complete | The cleanup‑database CronJob became stuck. |

**Solution**:

Check cleanup database job logs.
