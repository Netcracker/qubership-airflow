This page describes DAG behavior upon DAG code update during DAG run.

## DAG Bundles

DAG update behavior when using DAG bundles was not tested by qubership yet. Based on airflow documentation, if DAG bundle supports versioning, by default the DAG tasks will run the same code version through the whole DAG run. This can be disabled, however, using `disable_bundle_versioning` (env `AIRFLOW__DAG_PROCESSOR__DISABLE_BUNDLE_VERSIONING`) parameter. With it disabled, the latest DAG code will be used for task execution.

It is also worth noting, that some existing DAG bundles implementations do not support DAG versioning at the moment, for example `airflow.dag_processing.bundles.local.LocalDagBundle` and `airflow.providers.amazon.aws.bundles.s3.S3DagBundle`. With such DAG bundles the latest DAG code will be used for task execution regardless of `disable_bundle_versioning` parameter. To support DAG bundles, bundle class must implement `get_current_version` method. For more information, refer to the [official Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)

## UI DAG version

DAG version is also present in airflow UI:

However, when DAG bundle with versioning is not used, DAG version in UI can be a bit inconsistent. For example DAG version for a task will be updated to a new one if DAG got reparsed during task execution, however task will still continue to execute an old code version.

## DAG behavior on DAG code update

In short DAG update can be described as DAG updates immediately except for running tasks, that finish with the old version. 

More detailed case description:

| case                                                                                                                                 | result                                                                                                                                                                                                                            |
|--------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DAG structure changes after running task but task code does not change.                                                              | Running task completes successfully and DAG continues after the task with a new structure                                                                                                                                         |
| DAG structure changes so some previous and subsequent tasks become parallel to the running task, but tasks themselves do not change. | Previous already completed tasks that become parallel do not restart, running task continues, subsequent (not started) tasks that become parallel start.                                                                          |
| DAG structure changes so some previous and subsequent tasks become parallel to the running task and the tasks themselves change.     | Previous already completed tasks that become parallel do not restart(remain on the old version), running task continues (with the old version), subsequent (not started) tasks that become parallel start (with the new version). |
| Group of parallel running tasks becomes sequential .                                                                                 | Running tasks continue with the old version (even though the structure is displayed as sequential), than the subsequent tasks after the parallel group in question start.                                                         |
| New tasks added before the ones already executed.                                                                                    | If new task is added directly before running task, it starts executing. otherwise it's not getting started                                                                                                                        |
| Running/completed task logic changes so there's a new XCOM value.                                                                    | XCOM value is not updated                                                                                                                                                                                                         |
| A new subsequent task is added that relies on the XCOM from another new(or already executed but with no XCOM)                        | XCOM will not be available ( None value will be returned )                                                                                                                                                                        |
| A completed task with XCOM is removed from DAG structure                                                                             | XCOM value is still available for subsequent tasks.                                                                                                                                                                               |
| A running task with retries has a bug that will fail the task, but the DAG code is getting updated to fix the bug                    | Currently running attept will fail with expected error, the task will restart with new version and complete successfully .                                                                                                        |
| Running Task changes task_id                                                                                                         | Task start executing from the beginning with new task_id . Old task_id is not visible in the UI, but XCOMs from this task are available.                                                                                          |
| Finished Task changes task_id                                                                                                        | Old task_id goes to removed state, new task_id is not executed                                                                                                                                                                    |

**Note**: task groups were not extensively tested, however in the task group tasks are still separate, in other words, in a task group of 2 sequential tasks if DAG gets updated while first task is executing, the first task will still execute the old code version and the second task will start with a new version.