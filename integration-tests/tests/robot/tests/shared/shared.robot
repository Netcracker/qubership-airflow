*** Variables ***
${AIRFLOW_USER}             %{AIRFLOW_USER}
${AIRFLOW_PASSWORD}         %{AIRFLOW_PASSWORD}
${AIRFLOW_HOST}             %{AIRFLOW_HOST}
${AIRFLOW_PORT}             %{AIRFLOW_PORT}
${AIRFLOW_NAMESPACE}        %{AIRFLOW_NAMESPACE}
${API_SERVICE_NAME}         %{API_SERVICE_NAME}
${SCHEDULER_DEPLOYMENT}     %{SCHEDULER_DEPLOYMENT}
${DAG_PROCESSOR_DEPLOYMENT}    %{DAG_PROCESSOR_DEPLOYMENT}
${WORKER_SERVICE_NAME}      %{WORKER_SERVICE_NAME}
${MANAGED_BY_OPERATOR}      true
${COUNT_OF_RETRY}           100x
${RETRY_INTERVAL}           5s
${EXECUTOR_TYPE}            %{EXECUTOR_TYPE}
${AUTH_ENDPOINT}            /auth/token

*** Settings ***
Library  String
Library  DateTime
Library	 Collections
Library	 RequestsLibrary
Library  PlatformLibrary  managed_by_operator=${MANAGED_BY_OPERATOR}


*** Keywords ***
Preparation
    Create Session    auth_session    http://${AIRFLOW_HOST}:${AIRFLOW_PORT}
    &{auth_data}=    Create Dictionary
    ...    username=${AIRFLOW_USER}
    ...    password=${AIRFLOW_PASSWORD}
    ${response}=    POST On Session    auth_session    ${AUTH_ENDPOINT}    json=${auth_data}
    Should Be Equal As Strings    ${response.status_code}    201
    ${airflow_token}=    Set Variable    ${response.json()}[access_token]
    ${headers_auth}=    Create Dictionary
    ...    Authorization=Bearer ${airflow_token}
    ...    Content-Type=application/json
    ${headers} =  Create Dictionary  Content-Type=application/json
    Set Global Variable  ${headers}
    Create Session    airflowsession    http://${AIRFLOW_HOST}:${AIRFLOW_PORT}    headers=${headers_auth}

Get Names Of Entities
    ${IF_WORKERS_STATEFULSET} =  Run Keyword And Return Status  Get Stateful Set  ${WORKER_SERVICE_NAME}  ${AIRFLOW_NAMESPACE}
    Set Suite Variable  ${IF_WORKERS_STATEFULSET}
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Get Workers On StatefulSet
    ...  ELSE  Get Workers On Deployments
    ${api_deployments} =  get_deployment_entity_names_by_service_name  ${API_SERVICE_NAME}  ${AIRFLOW_NAMESPACE}
    ${API_DEPLOYMENT} =  Get From List  ${api_deployments}  0
    Set Suite Variable  ${API_DEPLOYMENT}

Get Workers On StatefulSet
    ${statefulsets} =  get_stateful_set_names_by_label  namespace=${AIRFLOW_NAMESPACE}  label_value=worker  label_name=component
    ${WORKER} =  Get From List  ${statefulsets}  0
    Set Suite Variable  ${WORKER}

Get Workers On Deployments
    ${worker_deployment} =  get_deployment_entity_names_by_service_name  ${WORKER_SERVICE_NAME}  ${AIRFLOW_NAMESPACE}
    ${WORKER} =  Get From List  ${worker_deployment}  0
    Set Suite Variable  ${WORKER}

Execute PATCH request to DAG
    [Arguments]  ${DAG_ID}  ${body}
    ${resp} =  PATCH On Session  airflowsession  /api/v2/dags/${DAG_ID}  data=${body}  headers=${headers}
    Should Be Equal As Strings  ${resp.status_code}   200
    Log To Console  \nExecute PATCH Request To ${DAG_ID} With Status Code: ${resp.status_code}
    ${resp_json} =  Convert Json ${resp.content} To Type
    [Return]  ${resp_json}

Run DAG
    [Arguments]  ${DAG_ID}
    ${body}=    Evaluate    {"conf": {}, "logical_date": None}
    ${resp} =  POST On Session  airflowsession  /api/v2/dags/${DAG_ID}/dagRuns  json=${body}  headers=${headers}
    Should Be Equal As Strings  ${resp.status_code}   200
    Log To Console  \nDAG ${DAG_ID} Started With Status Code: ${resp.status_code}
    ${resp_json} =  Convert Json ${resp.content} To Type
    [Return]  ${resp_json}

Get Dag Status
    [Arguments]  ${DAG_ID}  ${dag_run_id}
    ${status} =  GET On Session  airflowsession  /api/v2/dags/${DAG_ID}/dagRuns/${dag_run_id}
    Should Be Equal As Strings  ${status.status_code}  200
    ${status_json} =  Convert Json ${status.content} To Type
    [Return]  ${status_json['state']}

Wait Until DAG Succeed
    [Arguments]  ${DAG_ID}  ${dag_run_id}
    ${status} =  Get Dag status  ${DAG_ID}  ${dag_run_id}
    Should Be Equal As Strings  ${status}  success

Wait Until DAG Failed
    [Arguments]  ${DAG_ID}  ${dag_run_id}
    ${status} =  Get Dag status  ${DAG_ID}  ${dag_run_id}
    Should Be Equal As Strings  ${status}  failed

Convert Json ${json} To Type
    ${json_dictionary} =  Evaluate  json.loads('''${json}''')  json
    [Return]  ${json_dictionary}

Return Worker Pods
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Set Replicas For Stateful Set  ${WORKER_SERVICE_NAME}  ${AIRFLOW_NAMESPACE}  replicas=${ACTIVE_WORKER}
    ...  ELSE  Set Replicas For Deployment Entity  ${WORKER}  ${AIRFLOW_NAMESPACE}  replicas=${ACTIVE_WORKER}
    Sleep  60s

Get Active Deployment Replicas
    ${ACTIVE_WORKER} =  Get Length  ${list_pods}
    Log to console  Workers On Deployments: ${ACTIVE_WORKER}
    Set Suite Variable  ${ACTIVE_WORKER}

Get Active Statefulset Replicas
    ${ACTIVE_WORKER} =  Get Stateful Set Replica Counts  ${WORKER}  ${AIRFLOW_NAMESPACE}
    Log to console  Workers On Statefulsets: ${ACTIVE_WORKER}
    Set Suite Variable  ${ACTIVE_WORKER}

Get List Pod Names For Stateful Set
     @{list_pods} =  Get Pod Names For Stateful Set  ${WORKER}  ${AIRFLOW_NAMESPACE}
     Log to console  LIST_PODS on Statefulset: @{list_pods}
     Set Suite Variable  @{list_pods}

Get List Pod Names For Deployment Entity
     @{list_pods} =  Get Pod Names For Deployment Entity  ${WORKER}  ${AIRFLOW_NAMESPACE}
     Log to console  LIST_PODS on Deployment: @{list_pods}
     Set Suite Variable  @{list_pods}

Unpause DAG
    [Arguments]  ${dag_name}
    ${body} =  Set Variable  {"is_paused": false}
    ${request} =  Execute PATCH request to DAG  ${dag_name}  ${body}

Check Dags Amount
    ${resp} =  GET On Session  airflowsession  /api/v2/dags
    ${resp_json} =  Convert Json ${resp.content} To Type
    ${dags_amount} =  Get Length  ${resp_json['dags']}
    Log to console  DAGS COUNT: ${dags_amount}
    [Return]  ${dags_amount}