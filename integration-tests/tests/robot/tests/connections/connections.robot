*** Settings ***
Library  String
Library	 Collections
Library	 RequestsLibrary
Suite Setup  Preparation
Resource  ../shared/shared.robot
Library  ../shared/lib/airflowLibrary.py

*** Keywords ***
Create PG Connection
    [Arguments]  ${PG_HOST}  ${PG_USER}  ${PG_PASSWORD}  ${PG_DATABASE}
    &{data}=  Create Dictionary  connection_id=postgres_test_conn  conn_type=postgres  description=PG connection  host=${PG_HOST}  login=${PG_USER}  schema=${PG_DATABASE}  port=${5432}  password=${PG_PASSWORD}
    &{headers}=  Create Dictionary  Content-Type=application/json  Accept=application/json
    ${resp}=  POST On Session  airflowsession  /api/v2/connections  json=${data}  headers=${headers}
    Should Be Equal  ${resp.status_code}  ${201}

Delete PG Connection
    ${resp}=  DELETE On Session  airflowsession  /api/v2/connections/postgres_test_conn
    Should Be Equal  ${resp.status_code}  ${204}


*** Test Cases ***
Run Dag To Check PG Connection
    [Tags]  smoke  airflow  pg_connection_dag
    ${count}=  Check Dags Amount
    Skip If  ${count} == 0  Airflow doesn't have available dags!
    ${PG_HOST}  ${PG_USER}  ${PG_PASSWORD}  ${PG_DATABASE} =  Get Pg Connection Properties  ${AIRFLOW_NAMESPACE}
    Create PG Connection  ${PG_HOST}  ${PG_USER}  ${PG_PASSWORD}  ${PG_DATABASE}
    Unpause DAG  postgres_operator_test_dag
    ${resp} =  Run DAG  postgres_operator_test_dag
    Wait Until Keyword Succeeds  ${COUNT_OF_RETRY}  ${RETRY_INTERVAL}
    ...  Wait Until DAG Succeed  postgres_operator_test_dag  ${resp['dag_run_id']}
    [Teardown]  Delete PG Connection
