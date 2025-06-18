*** Variables ***
${IMAGES_TO_TEST}         %{IMAGES_TO_TEST}

*** Settings ***
Resource  ../shared/shared.robot
Library  ../shared/lib/airflowLibrary.py

*** Keywords ***
Check Image Correctness
    [Arguments]  ${type}  ${name}  ${container_name}  ${manifest_image}
    ${resource_image}=  Get Resource Image  ${type}  ${name}  %{AIRFLOW_NAMESPACE}  ${container_name}
    Should Be Equal  ${resource_image}  ${manifest_image}

Get Resource Details
    [Arguments]  ${sevice_name}
    ${stripped_resources}=  Strip String  ${IMAGES_TO_TEST}  characters=,  mode=right
    @{list_resources} =  Split String	${stripped_resources} 	,
    FOR  ${resource}  IN  @{list_resources}
      ${name}  ${container_name}  ${manifest_image}=  Split String	${resource}
      Exit For Loop IF  "${name}" == "${sevice_name}"
    END
    [Return]  ${name}  ${container_name}  ${manifest_image}

Get Manager Of Dags
    ${dags_manager}=  Identify Dags Manager  ${SCHEDULER_DEPLOYMENT}  ${AIRFLOW_NAMESPACE}
    ${name}  ${container_name}  ${manifest_image}=  Run Keyword If  "${dags_manager}" == "gitsync"  Get Resource Details  git-sync
    ...  ELSE IF  "${dags_manager}" == "rclone"  Get Resource Details  rclone
    [Return]  ${dags_manager}  ${container_name}  ${manifest_image}

*** Test Cases ***
Test Hardcoded Images In Worker
    [Tags]  airflow  airflow_images  airflow_images_worker
    Skip If  "${EXECUTOR_TYPE}" != "CeleryExecutor"  Airflow deployed with not CeleryExecutor, can't perform test!
    Get Names Of Entities
    ${name}  ${container_name}  ${manifest_image}=  Get Resource Details  ${WORKER_SERVICE_NAME}
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Check Image Correctness  statefulset  ${name}  ${container_name}  ${manifest_image}
    ...  ELSE  Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}
    ${dags_manager}  ${container_name}  ${manifest_image}=  Get Manager Of Dags
    Pass Execution If  "${dags_manager}" == "${None}"  There is no dags manager, passed!
    Run Keyword If  ${IF_WORKERS_STATEFULSET} == True  Check Image Correctness  statefulset  ${name}  ${container_name}  ${manifest_image}
    ...  ELSE  Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}

Test Hardcoded Images In Scheduler
    [Tags]  airflow  airflow_images  airflow_images_scheduler
    ${name}  ${container_name}  ${manifest_image}=  Get Resource Details  ${SCHEDULER_DEPLOYMENT}
    Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}
    ${dags_manager}  ${container_name}  ${manifest_image}=  Get Manager Of Dags
    Pass Execution If  "${dags_manager}" == "${None}"  There is no dags manager, passed!
    Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}

Test Hardcoded Images In DAG processor
    [Tags]  airflow  airflow_images  airflow_images_dag_processor
    ${name}  ${container_name}  ${manifest_image}=  Get Resource Details  ${DAG_PROCESSOR_DEPLOYMENT}
    Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}
    ${dags_manager}  ${container_name}  ${manifest_image}=  Get Manager Of Dags
    Pass Execution If  "${dags_manager}" == "${None}"  There is no dags manager, passed!
    Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}

Test Hardcoded Images In Apiserver
    [Tags]  airflow  airflow_images  airflow_images_apiserver
    ${name}  ${container_name}  ${manifest_image}=  Get Resource Details  ${API_SERVICE_NAME}
    Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}

Test Hardcoded Images In Tests
    [Tags]  airflow  airflow_images  airflow_images_tests
    ${name}  ${container_name}  ${manifest_image}=  Get Resource Details  airflow-integration-tests
    Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}

Test Hardcoded Images In Statsd
    [Tags]  airflow  airflow_images  airflow_images_statsd
    ${IF_STATSD} =  Run Keyword And Return Status  Get Deployment Entity  airflow-statsd  ${AIRFLOW_NAMESPACE}
    Skip If  "${IF_STATSD}" != "True"  Airflow statsd is not installed, can't perform test!
    ${name}  ${container_name}  ${manifest_image}=  Get Resource Details  airflow-statsd
    Check Image Correctness  deployment  ${name}  ${container_name}  ${manifest_image}


