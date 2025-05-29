*** Settings ***
Library  String
Library	 Collections
Library	 RequestsLibrary
Suite Setup  Prepare_ha
Resource  ../shared/shared.robot

*** Keywords ***
Prepare_ha
    Preparation
    Get Names Of Entities

*** Test Cases ***
Test HA Case With Worker Pods Sleep Dag
    [Tags]  ha  worker  airflow
    Skip If  "${EXECUTOR_TYPE}" != "CeleryExecutor"  Airflow deployed with not CeleryExecutor, can't perform test!
    ${count}=  Check Dags Amount
    Skip If  ${count} == 0  Airflow doesn't have available dags!
    Unpause DAG  sleeping_dag
    ${resp} =  Run DAG  sleeping_dag
    Sleep  10s
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get List Pod Names For Stateful Set
    ...  ELSE  Get List Pod Names For Deployment Entity
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get Active Statefulset Replicas
    ...  ELSE  Get Active Deployment Replicas
    FOR  ${pod}  IN  @{list_pods}
        Delete Pod By Pod Name  ${pod}  ${AIRFLOW_NAMESPACE}
        Log To Console  Delete ${pod}
    END
    Wait Until Keyword Succeeds  ${COUNT_OF_RETRY}  ${RETRY_INTERVAL}
    ...  Wait Until DAG Failed  sleeping_dag  ${resp['dag_run_id']}
    [Teardown]  Return Worker Pods

Test HA Case With Worker Pods Sleep Dag With Retries
    [Tags]  ha  worker  airflow
    Skip If  "${EXECUTOR_TYPE}" != "CeleryExecutor"  Airflow deployed with not CeleryExecutor, can't perform test!
    ${count}=  Check Dags Amount
    Skip If  ${count} == 0  Airflow doesn't have available dags!
    Unpause DAG  sleep_dag_with_retries
    ${resp} =  Run DAG  sleep_dag_with_retries
    Sleep  10s
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get List Pod Names For Stateful Set
    ...  ELSE  Get List Pod Names For Deployment Entity
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get Active Statefulset Replicas
    ...  ELSE  Get Active Deployment Replicas
    FOR  ${pod}  IN  @{list_pods}
        Delete Pod By Pod Name  ${pod}  ${AIRFLOW_NAMESPACE}
        Log To Console  Delete ${pod}
    END
    Wait Until Keyword Succeeds  ${COUNT_OF_RETRY}  20s
    ...  Wait Until DAG Succeed  sleep_dag_with_retries  ${resp['dag_run_id']}
    [Teardown]  Return Worker Pods

Test HA Case With Scheduler Pod Sleep Dag With Retries
    [Tags]  ha  scheduler  airflow
    ${count}=  Check Dags Amount
    Skip If  ${count} == 0  Airflow doesn't have available dags!
    Unpause DAG  sleep_dag_with_retries
    ${resp} =  Run DAG  sleep_dag_with_retries
    Sleep  10s
    @{scheduler_pod} =  Get Pod Names For Deployment Entity  ${SCHEDULER_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}
    Log to console  LIST_PODS: @{scheduler_pod}
    FOR  ${pod}  IN  @{scheduler_pod}
        Delete Pod By Pod Name  ${pod}  ${AIRFLOW_NAMESPACE}
        Log To Console  Delete ${pod}
    END
    Wait Until Keyword Succeeds  ${COUNT_OF_RETRY}  ${RETRY_INTERVAL}
    ...  Wait Until DAG Succeed  sleep_dag_with_retries  ${resp['dag_run_id']}
    [Teardown]  Set Replicas For Deployment Entity  ${SCHEDULER_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}  replicas=1

Test HA Case With WEB pod
    [Tags]  ha  web  airflow
    ${count}=  Check Dags Amount
    Skip If  ${count} == 0  Airflow doesn't have available dags!
    Unpause DAG  sleep_dag_with_retries
    ${resp} =  Run DAG  sleep_dag_with_retries
    @{web_pod} =  Get Pod Names For Deployment Entity  ${API_SERVICE_NAME}  ${AIRFLOW_NAMESPACE}
    Log to console  LIST_PODS: ${web_pod}
    FOR  ${pod}  IN  @{web_pod}
        Delete Pod By Pod Name  ${pod}  ${AIRFLOW_NAMESPACE}
        Log To Console  Delete ${pod}
    END
    Wait Until Keyword Succeeds  ${COUNT_OF_RETRY}  ${RETRY_INTERVAL}
    ...  Wait Until DAG Succeed  sleep_dag_with_retries  ${resp['dag_run_id']}
    [Teardown]  Set Replicas For Deployment Entity  ${API_SERVICE_NAME}  ${AIRFLOW_NAMESPACE}  replicas=1
