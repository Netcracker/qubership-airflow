*** Settings ***
Library  String
Library	 Collections
Library	 RequestsLibrary
Suite Setup  Preparation
Resource  ../shared/shared.robot

*** Keywords ***
Check Airflow API Status
    ${resp} =  GET On Session  airflowsession  /api/v2/dags
    Should Be Equal As Strings  ${resp.status_code}   200
    [Return]  ${resp.status_code}


*** Test Cases ***
Check Status API
    [Tags]  smoke  airflow
    ${resp} =  Check Airflow API Status
    Should Be Equal As Strings  ${resp}  200

Run noop_dag
    [Tags]  smoke  airflow
    ${count}=  Check Dags Amount
    Skip If  ${count} == 0  Airflow doesn't have available dags!
    Unpause DAG  noop_dag
    ${resp} =  Run DAG  noop_dag
    Wait Until Keyword Succeeds  ${COUNT_OF_RETRY}  ${RETRY_INTERVAL}
    ...  Wait Until DAG Succeed  noop_dag  ${resp['dag_run_id']}
