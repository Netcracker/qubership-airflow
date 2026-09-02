*** Settings ***
Library   String
Library   Collections
Library   RequestsLibrary
Suite Setup   Preparation
Resource   ../shared/shared.robot
Library   ../shared/lib/airflowLibrary.py

*** Keywords ***
Create Trino Connection
    [Arguments]   ${TRINO_HOST}   ${TRINO_PORT}   ${TRINO_USER}
    &{data}=   Create Dictionary   connection_id=trino_default   conn_type=http   description=Trino connection   host=${TRINO_HOST}   login=${TRINO_USER}   port=${TRINO_PORT}   schema=https
    &{headers}=   Create Dictionary   Content-Type=application/json   Accept=application/json
    ${resp}=   POST On Session   airflowsession   /api/v2/connections   json=${data}   headers=${headers}
    Should Be Equal As Integers   ${resp.status_code}   201
    Log To Console   \nTrino connection created: ${TRINO_HOST}:${TRINO_PORT}

Delete Trino Connection
    ${resp}=   DELETE On Session   airflowsession   /api/v2/connections/trino_default   expected_status=any
    Should Contain   ${{ [204, 404] }}   ${resp.status_code}
    Log To Console   \nTrino connection deleted

Set Trino Catalog Variable
    [Arguments]   ${CATALOG_CONFIG_JSON}
    &{variable_data}=   Create Dictionary   key=trino_catalog_config   value=${CATALOG_CONFIG_JSON}
    &{headers}=   Create Dictionary   Content-Type=application/json   Accept=application/json
    ${resp}=   POST On Session   airflowsession   /api/v2/variables   json=${variable_data}   headers=${headers}
    Should Be Equal As Integers   ${resp.status_code}   201
    Log To Console   \nTrino catalog variable created

Delete Trino Catalog Variable
    ${resp}=   DELETE On Session   airflowsession   /api/v2/variables/trino_catalog_config   expected_status=any
    Should Contain   ${{ [204, 404] }}   ${resp.status_code}
    Log To Console   \nTrino catalog variable deleted

*** Test Cases ***
Run DAG To Check Trino Connection
    [Tags]   smoke   airflow   trino_connection_dag
    ${count}=   Check Dags Amount
    Skip If   ${count} == 0   Airflow doesn't have available dags!

    # Get Trino connection details from shared keyword
    ${TRINO_HOST}   ${TRINO_PORT}   ${TRINO_USER}   ${CATALOG_CONFIG_JSON}=   Get Trino Connection Properties
    Skip If   $TRINO_HOST is None or $TRINO_HOST == ''   Trino connection not configured in secrets

    # Create connection and variable
    Create Trino Connection   ${TRINO_HOST}   ${TRINO_PORT}   ${TRINO_USER}
    Set Trino Catalog Variable   ${CATALOG_CONFIG_JSON}

    # Run the DAG
    Unpause DAG   sql_trino_variable_catalog
    ${resp}=   Run DAG   sql_trino_variable_catalog
    Wait Until Keyword Succeeds   ${COUNT_OF_RETRY}   ${RETRY_INTERVAL}
    ...   Wait Until DAG Succeed   sql_trino_variable_catalog   ${resp['dag_run_id']}

    [Teardown]   Run Keywords
    ...   Delete Trino Connection
    ...   Delete Trino Catalog Variable