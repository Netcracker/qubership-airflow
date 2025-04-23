The following topics describe the architectural features of the Airflow service.

* [Overview](#overview)
  * [Qubership Version Modifications and Additional Features](#qubership-version-modifications-and-additional-features)
  * [Useful Features](#useful-features)
  * [Overview of Airflow Components](#overview-of-airflow-components)
  * [Scheduler](#scheduler)
  * [Executor](#executor)
  * [Workers](#workers)
  * [Webserver](#webserver)
  * [DAG Storage](#dag-storage)
  * [StatsD Exporter](#statsd-exporter)
  * [DR Site Manager](#dr-site-manager)
* [Supported Deployment Schemas](#supported-deployment-schemas)
  * [On-Prem](#on-prem)
    * [What Does Airflow Look Like in Kubernetes?](#what-does-airflow-look-like-in-kubernetes)
    * [Non-HA Deployment Scheme](#non-ha-deployment-scheme)
    * [HA Deployment Scheme](#ha-deployment-scheme)
    * [DR Deployment Schema](#dr-deployment-schema)
  * [Integration With Managed Services](#integration-with-managed-services)
    * [Google Cloud](#google-cloud)
    * [AWS](#aws)
    * [Azure](#azure)
    * [Other](#other)

# Overview

Airflow can be described as a workflow engine, where workflows are direct acyclic graphs or DAGs. Airflow is commonly used to orchestrate big data and machine learning workflows. For a complete Airflow overview, refer to the official Airflow documentation at [https://airflow.apache.org/docs/apache-airflow/stable/index.html#](https://airflow.apache.org/docs/apache-airflow/stable/index.html#).

## Qubership Version Modifications and Additional Features

The Qubership version provides deployment to Kubernetes/OpenShift using the official Airflow helm chart with some modifications and additional features.
The modifications and additional features include the following:

* Support of DR deployment.
* Custom pre-install job support (can be used to create database directly or through qubership DBAAS).
* Custom Airflow secrets backend to get Airflow Redis, PG and Kafka connections from Qubesrhip DBaaS/MaaS. For more information, refer to [https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html).
* Additional Python logging configuration to support writing logs to stdout.
* LDAP and IDP(Keycloak) security integrations.
* Monitoring integrations for [official Airflow metrics](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/metrics.html) and [Airflow plugin](https://github.com/epoch8/airflow-exporter).
* Custom [Rclone](https://rclone.org/) image that can be used to sync DAGs from remote cloud storages or HTTP. It can be used as GitSync alternative.

## Useful Features

The Airflow service has the following useful features:

* Variables and connections - Allows parameterizing tasks and connections to remote systems.
* X-coms - An airflow mechanism that allows Airflow tasks to pass data to other tasks. For more information, refer to [https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html).
* extraSecrets/extraConfigmaps/extraVolumes/extraVolumeMounts - Helm chart parameters that allow to create custom configmaps/secrets and pass them to pods during the deployments.
* Airflow releases a set of Python libraries (providers) that can be used by 
technologies being used by this application.
* It is possible to use Rclone or GitSync to load DAGs from remote storages.

## Overview of Airflow Components

![alt text](/docs/public/images/airflow_hl_overview.drawio.png "High Level Airflow Overview")

For more information, refer to [https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html).

## Scheduler 

This mandatory Airflow component is responsible for scheduling DAGs and submitting DAG tasks to the Airflow executor. 

## Executor

This mandatory Airflow component is responsible for running tasks. In K8s deployments, it specifies passing tasks to workers. Also, since Qubership Version only provides K8s deployments, executors are running in the same containers as the scheduler. Qubership version usually used only with Celery and Kubernetes executors.

## Workers

Workers are responsible for executing the task logic.

## Webserver

This Airflow component provides the UI for monitoring and managing DAGs. With an additional third-party plugin, it can provide Prometheus metrics.

## DAG Storage

The DAG storage is responsible for storing DAGs. In the current Qubership deployments DAGs can be stored in the following:

* Airflow docker image
* Remote Git repository (when using GitSync)
* Remote Cloud repository (when using Rclone)
* Downloadable ZIP archive (when using Rclone)

## StatsD Exporter

It is optional third party service that can be deployed by the chart. Airflow by default provides metrics in the StatsD format and this service is responsible for converting metrics provided in the StatsD format to the Prometheus format.

## DR Site Manager

It is an optional service provided by Qubership. It is responsible for managing Airflow in DR.

# Supported Deployment Schemas

## On-Prem

### What Does Airflow Look Like in Kubernetes?

The Qubership version supports two executors for the Airflow deployment: `celeryExecutor` and `kubernetesExecutor`. K8s deployment schemas for these executors are as follows:

**Celery executor**:

![alt text](/docs/public/images/airflow_arch_celery.drawio.png "Airflow Celery Executor Kubernetes deployment")

**Kubernetes executor**:

![alt text](/docs/public/images/airflow_arch_kubernetes.drawio.png "Airflow Kubernetes Executor Kubernetes deployment")

Following the above pictures, let us describe the main parts of the Airflow K8s deployment:

* Predeploy jobs - There are 3 jobs that can optionally run during the Airflow deployment and before the main components of Airflow are deployed. The jobs are:
  * Custom startup job, which can be used to execute the custom logic (for example, creating database, integration with DBaaS).
  * Migrate database job, which updates the Airflow database.
  * Create user job, which creates a user in the Airflow database when the webserver does not use security integrations for users.
* Scheduler - The scheduler can consist of one (or more for HA) pod and in a K8s scheduler pod, it also includes an executor.
* Workers - In case of a **Celery executor**, there are a constant number of worker pods and every worker pod represents itself as a celery worker. In case of a **Kubernetes executor**, the executor creates a worker pod for every running Airflow task, so the number of pods is dynamic, and when there are no running tasks, there are no worker pods. No broker is needed in this case. Depending on the configuration, it can store task logs internally, or on a PVC, or send them to stdout, or to S3 storage.
* Webserver - It consists of one (or more for HA) pods. Depending on the configuration, it can get the task logs from S3 or from the workers directly.
* Flower - It is used only for a Celery executor, and not recommended for production. It helps to monitor Celery tasks in a Celery executor.
* StatsD exporter (one pod) - It converts the metrics provided by Airflow in the StatsD format to the Prometheus format.
* DR site manager - (**Optional**) It is the component that is used for the DR deployment. The DR deployment is described in the [DR Deployment Schema](#dr-deployment-schema) section.

### Non-HA Deployment Scheme

For a non-HA deployment scheme, it is possible to use one pod of each component and no storage for logs.

### HA Deployment Scheme

For HA deployment, it is possible to deploy multiple scheduler/webserver/worker (celery executor) pods. For task log storage for HA, it is possible to use:

* PVC - In this case, the logs will still be available after the pod restarts. However, unless a shared PV is used, the logs are only available while the worker pod that executed the task is up.
* S3 Storage - In this case, the logs are sent to a remote S3 storage. When configured, the webserver can read logs from the remote S3 storage.
* Writing (or duplicating) task logs to stdout - In this case, the logs should be available in Graylog. Note that the Web UI cannot read the logs from Graylog. So if you want the logs to be available in Graylog, you should also duplicate the logs to one of the other storages.

### DR Deployment Schema

In DR deployment, Airflow uses the same database on both sides, but on one side, Airflow pods are scaled down (PG database is replicated using PG mechanisms). For DR deployment, the sitemanager Airflow pod is used. After PG switchover, the DR sitemanager downscales Airflow pods on one side and upscales it on the other. The deployment schema is as shown in the following image:

![alt text](/docs/public/images/dr_design.drawio.png "DR airflow schema")

For more information, refer to the qubership [Airflow Site Manager](/docs/public/airflow-site-manager.md) section.

## Integration With Managed Services

### Google Cloud

**Deployment Integration**

Google Cloud offers the Cloud Composer service that is built on Apache Airflow. For more information, refer to the official Google Cloud documentation at [https://cloud.google.com/composer](https://cloud.google.com/composer).

**Functionality Integration**

Airflow providers include the apache-airflow-providers-google provider that has many Google Cloud operators. 
For more information about the apache-airflow-providers-google provider, refer to [https://airflow.apache.org/docs/apache-airflow-providers-google/stable/index.html](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/index.html).
For more information about Google Cloud operators, refer to [https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/index.html](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/index.html).

### AWS

**Deployment Integration**

It is possible to deploy Qubership Airflow version to AWS Kubernetes. ElasticCache (non-HA) for Redis and/or Amazon RDS PG (including Aurora PostgreSQL) for metadata database is supported.

AWS offers Amazon Managed Workflows for Apache Airflow. For more information, refer to the official AWS documentation at [https://aws.amazon.com/managed-workflows-for-apache-airflow/](https://aws.amazon.com/managed-workflows-for-apache-airflow/).

**Functionality Integration**

Airflow providers include the apache-airflow-providers-amazon provider that has many AWS operators. 
For more information about the apache-airflow-providers-amazon provider, refer to [https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/index.html](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/index.html). 
For more information about AWS operators, refer to [https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/index.html](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/index.html).

### Azure

**Deployment Integration**

Microsoft Azure offers Azure Data Factory Managed Airflow. For more information, refer to the official Microsoft documentation at [https://learn.microsoft.com/en-us/azure/data-factory/concept-managed-airflow](https://learn.microsoft.com/en-us/azure/data-factory/concept-managed-airflow).

**Functionality Integration**

Airflow providers include the apache-airflow-providers-microsoft-azure provider that has many Microsoft Azure operators. 
For more information about the apache-airflow-providers-microsoft-azure provider, refer to [https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/index.html](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/index.html). 
For more information about Microsoft Azure operators, refer to [https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/operators/index.html](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/operators/index.html).

### Other

**Functionality Integration**

The full list of Airflow providers can be found at [https://airflow.apache.org/docs/apache-airflow-providers/packages-ref.html](https://airflow.apache.org/docs/apache-airflow-providers/packages-ref.html).
