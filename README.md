This repo contains images and helm charts to install and run [Apache Airflow](https://airflow.apache.org/) on Kubernetes. For helm charts [Airflow official helm chart templates](https://github.com/apache/airflow/tree/main/chart) are reused with some minor changes. The helm changes are described below. As the main image for airflow components a custom image based on [airflow-slim image](https://hub.docker.com/r/apache/airflow/tags) is used. It also includes some additional packages/scripts for integrations with LDAP, Keycloak, Postgres, Redis, Qubership DBaaS and other services. The image Dockerfile can be found [here](docker/Dockerfile). Additionally, this repo contains images that can be used with airflow:

* [docker-transsfer image](docker-transfer) - This image can be used to extract the charts and other artifacts.
* [Integration tests image](integration-tests) - This image is used to run Qubership Platform integration tests for airflow.
* [Rclone image](rclone-image) - This image is based on the official [Rclone image](https://rclone.org/). It can be used as an alternative for gitSync in airflow helm chart.
* [site-manager](site-manager) - This image can be used to help running airflow in DR setup.
* [tests_dags_image](tests_dags_image) - This image contains some test DAGs in order to test some basic airflow providers and basic airflow functionality.

These images can be found on [packages tab](https://github.com/orgs/Netcracker/packages?repo_name=qubership-airflow).

## Table of Contents

* [Installation Guide](/docs/public/installation.md)
* [Maintenance Guide](/docs/public/maintenance.md)
* [Audit Logs](/docs/public/audit-logs.md)
* [Running Spark Applications](/docs/public/how-to-run-spark-apps.md)
* [Monitoring](/docs/public/monitoring.md)
* [Performance](/docs/public/performance.md)
* [Troubleshooting Guide](/docs/public/troubleshooting.md)
* [Airflow Site Manager](/docs/public/airflow-site-manager.md)

Apache airflow engine and helm charts.  
For more information see

* https://github.com/apache/airflow
* https://github.com/apache/airflow/tree/main/chart

## Helm Chart modifications

Helm chart includes the files from [Airflow official helm chart](https://github.com/apache/airflow/tree/main/chart) , but some files are changed, some files are added and some files are removed.


The file modification include the following:
* Adding custom configurable labels for Qubership release to deployments and to services. These changes are present in the files: `pod-template-file.kubernetes-helm-yaml`, `cleanup-cronjob.yaml`, `dag-processor-deployment.yaml`, `flower-deployment.yaml`, `flower-service.yaml`, `create-user-job.yaml`, `migrate-database-job.yaml`, `scheduler-deployment.yaml`, `scheduler-service.yaml`, `statsd-deployment.yaml`, ,`statsd-service.yaml`, `triggerer-deployment.yaml`, `triggerer-service.yaml`, `webserver-deployment.yaml`, `webserver-service.yaml`, `worker-deployment.yaml`, `worker-service.yaml`.
* Adding custom configurable update strategies. These changes are present in the following files: `scheduler-deployment.yaml`, `triggerer-deployment.yaml`, `worker-deployment.yaml`.
* Adding custom metrics to StatD exporter. This change is present in `statsd-mappings.yml` file.
* Adding possibility to use rclone image instead of gitsync image. This change is present in `_helpers.tpl` file.
* Adding APP_URL_LOGOUT environment variable to airflow pods containing airflow ingress host from parameters. This change is present in `_helpers.tpl` file.
* New local subchart dependencies were added to `Chart.yaml` file. Old dependency to Postgres chart was removed.
* `values.yaml` parameters changed to different default values for some parameters.

**Note**: Modification in the files are noted with `#---Qubership custom change: Change description---`, except for values.yaml file.

The following folders/files were added to the chart:
* Two local subcharts were added, with [qubership site-manager](/chart/helm/airflow/charts/airflow-site-manager) and [qubership integration tests](/chart/helm/airflow/charts/integrationTests).
* Files for custom preinstall job are added. Files can be found [here](/chart/helm/airflow/templates/qspreinstallhooks).
* [TLS certificate object for integration with cert-manager](/chart/helm/airflow/templates/qspreinstallhooks/airflow-services-tls-certificate.yaml)
* Python files with custom logging configuration and keyckoak integration were added to the chart, so they can be loaded in values.yaml. They can be found [here](/chart/helm/airflow/qs_files). Logging configuration is a bit modified default Airflow logging configuration.
* Files for custom monitoring are added(Grafana dashboard, service monitors and prometheus alerts). The dashboard content can be found [here](/chart/helm/airflow/qs_files), other files can be found [here](/chart/helm/airflow/templates/qsmonitoring).
* [Custom helpers file](/chart/helm/airflow/templates/_qs_helpers.tpl) was added.

Main values.yaml file changes:

* Security context modified.
* Image parameters are customized to use the ones built in this repo.
* `app.kubernetes.io/part-of: 'airflow'` label is added to all objects.
* Web server ingress is enabled by default.
* Custom logging config is used in `airflowLocalSettings`.
* `env`, `extraSecrets`, `extraEnvFrom`, `metadataSecretName`, `brokerUrlSecretName` parameters are modified to support Qubership DBaaS.
* Some of `enableBuiltInSecretEnvVars` disabled for DBaaS support.
* Persistence is disabled by default and volume size is set to 10 gb.
* Triggerer is disabled by default.
* Internal Redis, PG are disabled.
* Airflow config is modified to support new loging config, secrets backend.
* Airflow config is modified in order to set different images for k8s executor pods.
* New parameters related to custom Qubership certManager integration, monitoring, Site-Manager, integration tests, statusProvisioner and pre-install job are added.

For more information about the helm chart changes, please refer to [installation.md](/docs/public/installation.md).
