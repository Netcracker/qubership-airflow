*** Variables ***
${PROMETHEUS_HOST}                          %{PROMETHEUS_HOST}
${PROMETHEUS_PORT}                          %{PROMETHEUS_PORT}
${WORKER_STATEFULSET_DEGRADED_ALERT_NAME}   WorkerStatefulsetIsDegraded
${WORKER_DEPLOYMENT_DEGRADED_ALERT_NAME}    ThereAreUnavailableWorkers
${WORKER_DOWN_ALERT_NAME}                   WorkerError
${SCHEDULER_DOWN_ALERT_NAME}                SchedulerError
${API_DOWN_ALERT_NAME}                      APIerror
${FIRING_STATE}                             firing
${PENDING_STATE}                            pending
${INACTIVE_STATE}                           inactive
${RETRY}                                    100x
${INTERVAL}                                 5s

*** Settings ***
Library  String
Library	 Collections
Library	 RequestsLibrary
Library  MonitoringLibrary  host=http://${PROMETHEUS_HOST}:${PROMETHEUS_PORT}
Resource  ../shared/shared.robot
Suite Setup  Prepare_alerts

*** Keywords ***
Check That Alert In Right Status
    [Arguments]  ${alert_name}  ${state}
    ${status} =  Get Alert Status  ${alert_name}  ${AIRFLOW_NAMESPACE}
    Should Be Equal As Strings  ${status}  ${state}

Prepare_alerts
    Get Names Of Entities

Set Worker Replicas
    [Arguments]  ${how_replicas}
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Set Replicas For Stateful Set  ${WORKER_SERVICE_NAME}  ${AIRFLOW_NAMESPACE}  replicas=${how_replicas}
    ...  ELSE  Set Replicas For Deployment Entity  ${WORKER}  ${AIRFLOW_NAMESPACE}  replicas=${how_replicas}
    Sleep  60s

Wait Worker Deployment Degraded
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_DEPLOYMENT_DEGRADED_ALERT_NAME}  ${PENDING_STATE}

Wait Worker Statefulset Degraded
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_STATEFULSET_DEGRADED_ALERT_NAME}  ${PENDING_STATE}

Wait Worker Deployment In Right Status
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_DEPLOYMENT_DEGRADED_ALERT_NAME}  ${INACTIVE_STATE}

Wait Worker Statefulset In Right Status
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_STATEFULSET_DEGRADED_ALERT_NAME}  ${INACTIVE_STATE}

*** Test Cases ***
Test Alert Worker Statefulset/Deployment Is Degraded
    [Tags]  alert  worker_degraded  airflow
    Skip If  "${EXECUTOR_TYPE}" != "CeleryExecutor"  Airflow deployed with not CeleryExecutor, can't perform test!
    Run Keyword If  ${IF_WORKERS_STATEFULSET} != True  Get List Pod Names For Deployment Entity
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get Active Statefulset Replicas
    ...  ELSE  Get Active Deployment Replicas
    Run Keyword If  ${ACTIVE_WORKER} > 0  Set Worker Replicas  50
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Wait Worker Statefulset Degraded
    ...  ELSE  Wait Worker Deployment Degraded
    Log To Console  Alert triggered. Return state
    Return Worker Pods
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Wait Worker Statefulset In Right Status
    ...  ELSE  Wait Worker Deployment In Right Status
    [Teardown]  Return Worker Pods

Test Alert Worker Error
    [Tags]  alert  worker_down  airflow
    Skip If  "${EXECUTOR_TYPE}" != "CeleryExecutor"  Airflow deployed with not CeleryExecutor, can't perform test!
    Run Keyword If  ${IF_WORKERS_STATEFULSET} != True  Get List Pod Names For Deployment Entity
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get Active Statefulset Replicas
    ...  ELSE  Get Active Deployment Replicas
    Run Keyword If  ${ACTIVE_WORKER} > 0  Set Worker Replicas  0
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_DOWN_ALERT_NAME}  ${PENDING_STATE}
    Log To Console  Alert triggered. Return state
    Return Worker Pods
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_DOWN_ALERT_NAME}  ${INACTIVE_STATE}
    [Teardown]  Return Worker Pods

Test Alert Worker Error With Firing State
    [Tags]  alert  worker_down_firing  airflow
    Skip If  "${EXECUTOR_TYPE}" != "CeleryExecutor"  Airflow deployed with not CeleryExecutor, can't perform test!
    Run Keyword If  ${IF_WORKERS_STATEFULSET} != True  Get List Pod Names For Deployment Entity
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get Active Statefulset Replicas
    ...  ELSE  Get Active Deployment Replicas
    Run Keyword If  ${ACTIVE_WORKER} > 0  Set Worker Replicas  0
    Sleep  60s
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_DOWN_ALERT_NAME}  ${FIRING_STATE}
    Log To Console  Alert triggered. Return state
    Return Worker Pods
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${WORKER_DOWN_ALERT_NAME}  ${INACTIVE_STATE}
    [Teardown]  Return Worker Pods

Test Alert Scheduler error
    [Tags]  alert  scheduler_down  airflow
    Set Replicas For Deployment Entity  ${SCHEDULER_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}  replicas=0
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${SCHEDULER_DOWN_ALERT_NAME}  ${PENDING_STATE}
    Log To Console  Alert triggered. Return state
    Set Replicas For Deployment Entity  ${SCHEDULER_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}  replicas=1
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${SCHEDULER_DOWN_ALERT_NAME}  ${INACTIVE_STATE}
    [Teardown]  Set Replicas For Deployment Entity  ${SCHEDULER_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}  replicas=1

Test Alert Web error
    [Tags]  alert  api_down  airflow
    Set Replicas For Deployment Entity  ${API_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}  replicas=0
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${API_DOWN_ALERT_NAME}  ${PENDING_STATE}
    Log To Console  Alert triggered. Return state
    Set Replicas For Deployment Entity  ${API_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}  replicas=1
    Wait Until Keyword Succeeds  ${RETRY}  ${INTERVAL}
    ...  Check That Alert In Right Status  ${API_DOWN_ALERT_NAME}  ${INACTIVE_STATE}
    [Teardown]  Set Replicas For Deployment Entity  ${API_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}  replicas=1
