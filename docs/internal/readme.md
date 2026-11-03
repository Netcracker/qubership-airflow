[[_TOC_]]

## Repository structure

* `.github/workflows` - folder related to Qubership platform Airflow pipeline config.
* `chart` - Qubership platform helm charts for Airflow. Also includes custom python logging configuration and python IDP integration configuration(used as part of the chart).
* `docker` - dockerfile for Qubership platform airflow docker image and related files. This includes python scripts for database creation(manual and with DBAAS). Also includes DBAAS integration package.
* `docs` - Qubership platform airflow documentation.
* `integration-tests` - files related to Qubership platform airflow integration tests.
* `rclone-image` - dockerfile and related filed for rclone image used in some Qubership platform airflow deployments.
* `site-manager` - files related to Qubership platform airflow site manager
* `tests_dags_image` - test airflow DAGs and airflow image that includes these DAGs and necessary python libraries to run these DAGs.

## How to start

Airflow Qubership platform distribution is largely based on airflow official slim image and includes airflow community helm chart with minor changes and some additions. Airflow Qubership platform distribution also includes rclone/gitsync images for syncing DAGs, site manager, status provisioner that is based on Qubership platform common status provisioner, tests image that is based on Qubership platform common tests image.

### Useful links:
Official airflow docs:

* https://airflow.apache.org/docs/ - general airflow documentation
* https://airflow.apache.org/docs/docker-stack/index.html - community airflow docker images information
* https://airflow.apache.org/docs/helm-chart/stable/index.html - airflow helm chart documentation
* https://airflow.apache.org/docs/helm-chart/stable/production-guide.html - production guide for airflow helm chart
* https://github.com/apache/airflow/tree/main - airflow repository
* https://github.com/apache/airflow/tree/main/chart - airflow community helm chart location
* https://github.com/apache/airflow/tree/main/providers/src/airflow/providers - airflow providers location
* https://github.com/apache/airflow/blob/main/airflow/config_templates/airflow_local_settings.py - airflow default logging config

Rclone and gitSync:

* https://github.com/rclone/rclone - official rclone github repository
* https://rclone.org/ - official rclone docs.
* https://github.com/kubernetes/git-sync - official gitsync github repository.

Internal docs of services that airflow uses or has integration with:

* https://github.com/Netcracker/qubership-dbaas/tree/main/docs - Qubership DBAAS docs (mostly useful for airflow is rest api).
* https://github.com/Netcracker/qubership-maas/ - Qubership MAAS repository.
* https://www.keycloak.org/documentation - Keycloak dicumentation
* https://github.com/Netcracker/qubership-deployment-status-provisioner - Qubership status provisioner
* https://github.com/Netcracker/qubership-docker-integration-tests - Qubership integration tests image
* https://github.com/Netcracker/qubership-disaster-recovery-daemon - qubership disaster recovery daemon, used as a GO lirbrary in qubership airflow site manager
* https://github.com/Netcracker/DRNavigator - Qubership site manager

### Build

Qubership platform airflow can deploy the following images:

* Qubership platform airflow base image - this image is based on community airflow slim image and needs to be built.
* Airflow site manager image - this image contains airflow logic to work with qubership site manager. This image needs to be built.
* Rclone image - this image is based on community rclone image and includes some additional logic to work similarly to gitSync in airflow deployment. This image needs to be built.
* Integration tests image - this image contains integration tests for airflow and is based on qubership integration tests image.
* Gitsync image - gitsync community image. Community image is reused, build is not needed.
* Statsd Prometheus exporter - StatSD prometheus community image used for monitoring. Community image is reused, no build is needed.
* Status provisioner image - image that is used to report status for deployer. Qubership status provisioner is reused, build is not needed.

Build pipeline logic is implemented at [.github/workflows](/.github/workflows) folder.

#### Definition of done

The changes can be merged to main if:

1. Ticket task is done.
2. All the pipeline steps can be built.
3. The changes were tested by QA.

### Deploy to k8s

See [installation.md](/docs/public/installation.md)

## How to debug and troubleshoot

For general configuration troubleshooting, refer to [troubleshooting.md](/docs/public/troubleshooting.md)

Most common issues and respective most common place where to look for a problem:

* Problems with `helm install` command during deployment with errors in helm chart files: check helm chart.
* Problems with `helm install` command with it being stuck: check database configuration issues, check for jobs in k8s namespace. Most probably you need to check  [DBAAS configuration related issues](#dbaas-configuration-related-issues).
* Problems with status provisioner after successful `helm install` command: check problematic pods and containers and act accordingly
* Problems with airflow login with IDP integration: check [IDP Configuration related issues](#idp-configuration-related-issues)
* Problems with main airflow pods(including jobs) not being able to start: check error. If the error is related to logging, check [Logging Config Issues](#logging-config-issues)
* Problems with airflow pod restarts: Check log errors. Check [Performance issues](#performance-issues). If the error is related to gitSync container, check [GitSync container issues](#gitsync-container-issues)

### Performance issues

When investigating performance issues firstly it is necessary to ensure that PG/redis have enoug resources and connection slots available. This can be done using PG/redis or general monitoring.

Next thing to check is if airflow pods have enough resources - airflow is witten in Python and can also be resource heavy. It also can be done via monitoring.

Another possible thing to check is product/project DAGs. If they are written incorrectly, it can lead to excessive resource load, see https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html .

Also the issue can be on airflow side especially if it appeared after airflow upgrade, for example: https://github.com/apache/airflow/issues/33688 .

### DBAAS configuration related issues

For DBAAS integration airflow uses [custom secrets backend](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html#roll-your-own-secrets-backend).

For troubleshooting DBAAS/MAAS integration it is necessary to be familiar with [DBAAS preinstall job script](/docker/create_dbs_dbaas.py) (used to create DB via DBAAS before airflow installation) and with [qubership airflow secrets bakcend DBAAS package](/docker/dbaasintegrationpackage). 

**Note**: It is possible to enable more logging in the DBaaS integration package by setting the `DBAAS_INTEGRATION_LOG_LEVEL` environment variable to `DEBUG`. The `config.logging.logging_level` parameter must also be set to debug in this case.

Before investigating the problem, it is necessary to check if there were any changes done to dbaas integration/script on product side.

Next thing to check is DBAAS(and MAAS if it's used) logs. It is possible to search DBAAS logs by the namespace or service name. PG logs are also worth checking.

If the issue is only related to airflow connections(not main PG/airflow connections), it is also necessary to completely validate `config.secrets.backend_kwargs` - if it is specified correctly and if it is correctly passed to installer.

Also, if the problem only happens in preinstall job and it is not possible to read it's log because it is getting deleted too fast, it is possible to overwrite `.Values.customPreinstallJob.command` and `.Values.customPreinstallJob.args` installation parameters to make the job sleep for 10 minutes. After that it should be possible to access job pod terminal and run dbaas integration script from terminal - with this approach it is possible to see the logs.

If you are seeing SSL errors of different types, it is necessary to check TLS configuration: that certificates are correctly mounted into the pods, that paths to certificates are correctly specified and the services that airflow uses have correct certificates. It is also possible to disable certificate validations to check if the problem is really with certificate.


### Declarative DBaaS

By default, the secrets backend and the preinstall job request databases from the DBaaS REST API. With `dbaasDeclarative.enabled=true`, the chart renders `InternalDatabase` and `DatabaseSecretClaim` resources instead, and the `dbaas-operator` writes connection properties into Secrets. The Secrets are mounted under `/var/run/secrets/dbaas-declarative/`, and the backend reads each one from a known directory. See the [dbaas-operator documentation](https://github.com/Netcracker/qubership-dbaas/blob/main/docs/DBaaS%20Operator.md) for the CRs.

Both modes stay available in the same image:

* `dbaasDeclarative.enabled=false` (default): the backend uses the REST API only. The Secret volumes point to `dbaas-connection-params-main` and are not read.
* `dbaasDeclarative.enabled=true`: the backend sets `DBAAS_OPERATOR_ENABLED=true`, never calls the REST API for databases. Pods start only after the operator has created the Secrets, because the Secret volumes are required. The preinstall job skips database creation and the access policy call.

Things to know before enabling it:

* `dbaasDeclarative.operatorNamespace` is the namespace of the `dbaas-operator` that manages the resources. It defaults to `dbaas-operator` and is templated, so it can be set to an expression such as `{{ .Values.SOME_NAMESPACE }}`.
* The chart does not render a `DatabaseAccessPolicy`. Airflow pods read the Secrets and never call DBaaS, so they need no grants. Code in DAGs that calls the DBaaS REST API directly still needs a grant from the database owner.
* The backend reads the main databases from `/var/run/secrets/dbaas-declarative/postgresql` and `/var/run/secrets/dbaas-declarative/redis`, where the chart mounts their Secrets. It needs no database names, so `DBAAS_PG_MICROSERVICE_NAME` and `DBAAS_REDIS_MICROSERVICE_NAME` are not used. The microservice names come from `dbaasDeclarative.postgresql.microserviceName` and `dbaasDeclarative.redis.microserviceName`.
* The aggregator creates declarative databases with `backupDisabled=false`, and the owner is the classifier `microserviceName`. `DBAAS_PG_DB_OWNER`, `DBAAS_REDIS_DB_OWNER` and `DBAAS_*_BACKUP_DISABLED` have no effect.
* Classifier, type and secret name are immutable on the CRs. To change them, delete and recreate the CR.
* The chart renders a database and a claim for every `*_dbaas` entry of `qs_secrets_backend_params` with `type: postgresql`, so connections are defined once for both modes. The resources are named `<fullname>-<connection name>`, and the Secret is `<fullname>-dbaas-<connection name>`, where the connection name is the key without `_dbaas`, in lowercase, with `-` instead of `_`. Mount each Secret in `volumes` and `volumeMounts` at `/var/run/secrets/dbaas-declarative/<connection name>`. The backend reads exactly that directory. For a database that Airflow owns, `classifier.namespace` must be omitted or equal to the release namespace, because the `InternalDatabase` requires it. `dbOwner` and `backupDisabled` are ignored. `originService` is ignored too, except for connections in `existingConnections`, where it becomes the claim label. Only PostgreSQL connections are resolved, and MaaS (Kafka) still uses the REST API.
* To use a database owned by another service, possibly in another namespace, list it in `dbaasDeclarative.existingConnections`. Use `postgresql`, `redis`, or a connection name from `qs_secrets_backend_params`. For these entries the chart renders only the `DatabaseSecretClaim`. Set the owner namespace in `dbaasDeclarative.postgresql.namespace`, `dbaasDeclarative.redis.namespace`, or the connection's `classifier.namespace`. A cross-namespace claim requires that both namespaces are in the same composite structure registered in DBaaS, and that the owner grants `dbaasDeclarative.serviceName` access with a `DatabaseAccessPolicy`. The chart uses `serviceName` as the claim's `app.kubernetes.io/name` label (a connection's `originService` takes precedence), and the label must differ from `classifier.microserviceName`. Until the composite and the policy exist, the claim reports `NamespaceNotInComposite` or `AccessPolicyNotReady` and the pods wait for the Secret mount. Cross-namespace claims need a dbaas-operator version that supports them.
* Mount the Secrets of connections as required volumes, not `optional`. The backend reads them once and does not wait, so a pod must start only after the Secret exists. If a Secret never appears, the pod stays in `ContainerCreating` with a `FailedMount` event.
* Error code `AIRFLOW-8311` means that the Secret at the expected path is missing or incomplete. Check that the `DatabaseSecretClaim` exists, that its `status` is ready, and that its Secret is mounted at the path from the message. Error code `AIRFLOW-8312` means that the Secret at that path holds another database type, so check the mount.

### IDP Configuration related issues

By default, for IDP(Keycloak) integration airflow uses [webserver_config_keycloak.py](/chart/helm/airflow/qs_files/webserver_config_keycloak.py). In installation parameters it is specified like the following:

```yaml
webserver:
...
  webserverConfig: |-
    {{ .Files.Get "qs_files/webserver_config_keycloak.py" }}
...
```

Before investigating the problem it is necessary to verify that in installation parameters it is specified connection. It is also necessary to check if there are any changes made on uder side to `qs_files/webserver_config_keycloak.py`.

Next step is to validate IDP keycloak configuration: that client is correct, that client redirect uri parameter is correct, that there are users in keycloak and that these users in keycloak have correct roles. It is also necessary to check airflow environment variables and that they have correct values.

It is also necessary to try logging in to airflow and check URLs in your browser and if they correspond to idp integration configuration.

### Logging Config Issues

Custom logging config class supported by platform is located at [qs_platform_logging_config.py](/chart/helm/airflow/qs_files/qs_platform_logging_config.py). It is based on community logging config from https://github.com/apache/airflow/blob/main/airflow/config_templates/airflow_local_settings.py . Note, that handlers, specified in `airflow.task` logger are also used to fetch logs in airflow UI (see `class` of the secified handler).
Custom logging config class and related third-party classes usually are used to investigate/troubleshoot issues related to incorrect log format, incorrect number of logs, incorrect logging level.

When troubleshooting task logs in airflow webUI with celery executor, it is necessary to remember that without using S3 storage, logs in UI should be available only when workers are deployed as statefulset with persistence storage. If the workers are deployed differently, absence of airflow logs in UI is expected behavior.

### GitSync container issues

**TBD**

## Evergreen strategy

1) https://github.com/Netcracker/qubership-airflow/blob/main/docker/Dockerfile#L1 .
2) Update airflow version in https://github.com/Netcracker/qubership-airflow/blob/main/docker/requirements.txt (should be the same as in the image) . Check if other lines can be removed
3) Update [qs_platform_logging_config.py](/chart/helm/airflow/qs_files/qs_platform_logging_config.py) based on community logging config from https://github.com/apache/airflow/blob/main/airflow/config_templates/airflow_local_settings.py .
4) Check that airflow platform image and airflow test DAG image can still be built without issues.
5) Update airflow helm chart based on https://github.com/apache/airflow/tree/main/chart while keeping qubership changes.
6) Change the link in [generate_json_schema.py](/docker-transfer/generate_json_schema.py) to the commit the chart was updated to.
7) If necessary, update parameters at [generate_json_schema.py](/docker-transfer/generate_json_schema.py).
8) Update the chart-version in the pipeline .github/workflows/helm-charts-release.yaml when the chart is upgraded.
9) Update versions of statsd-exporter and git-sync in the chart\helm\airflow\release-images.yaml when the statsd-exporter and git-sync are upgraded.
10) Check that airflow can still be deployed.
11) Check that DBAAS/IDP integrations still work.
12) Check that test DAGs in test DAG image still work.
13) Update gitSync image based on community recommended image (`images.gitSync.tag` parameter in community helm chart).
14) Check that gitSync still works
15) Update community rclone image to the [latest released](https://github.com/rclone/rclone/releases): https://github.com/Netcracker/qubership-airflow/blob/main/rclone-image/Dockerfile .
16) Check that rclone still works
17) Update status provisioner image to the [latest released](https://github.com/Netcracker/qubership-deployment-status-provisioner/releases).
18) Update [integration-tests base image](https://github.com/Netcracker/qubership-airflow/blob/main/integration-tests/tests/docker/Dockerfile) based on the [latest released](https://github.com/Netcracker/qubership-docker-integration-tests/releases).
19) Update sitemanager base linux image to the latest released https://github.com/Netcracker/qubership-airflow/blob/main/site-manager/docker/Dockerfile#L1 and https://github.com/Netcracker/qubership-airflow/blob/main/site-manager/docker/Dockerfile#L23 .
20) Update go version in https://github.com/Netcracker/qubership-airflow/blob/main/site-manager/go.mod#L3 . It should be the same as in dockerfile.
21) Update [disaster recovery daemon version](https://github.com/Netcracker/qubership-airflow/blob/main/site-manager/go.mod#L8) to the [latest released](https://github.com/Netcracker/qubership-disaster-recovery-daemon/releases)
22) If there are specific Golang library vulnerabilities, address them in https://github.com/Netcracker/qubership-airflow/blob/main/site-manager/go.mod .
23) Let GoLand/PyCharm update go.mod/go.sum files of status provisioner based on your previous changes
24) Check that sitemanager still can be built and works
25) Check remaining vulnerabilities and address them.
26) Update the documentation with the new version (places for replacing can be found by the old airflow version).









