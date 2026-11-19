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
* Mount the Secrets of connections as required volumes. A pod then starts only after the operator has created the Secret, and a Secret that never appears shows up as a `FailedMount` event on a pod in `ContainerCreating`. With `optional: true` the pod starts without the Secret, the backend does not wait for it, and tasks that use the connection fail with `AIRFLOW-8311` until the Secret is created.
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

The distribution follows the latest Apache Airflow release. One update is one pull request, as in `feat: Airflow340 update (#85)` for 3.4.0. The pull request covers the Airflow image, the forked community chart, the supporting images, and every file that carries a version.

Two rules hold for the whole procedure:

* The target Airflow version is the only input. The Python version, the chart version and the upstream commit are derived from it.
* Every Qubership change inside an upstream file carries a marker: `#---Qubership custom change: <description>---` in YAML and `{{- /* Qubership custom change: <description>--- */ -}}` in Helm templates. Unmarked content is treated as upstream content and is overwritten on the next sync.

### 1. Prepare the update

1. Pick the target release: the latest stable Apache Airflow version from [apache/airflow releases](https://github.com/apache/airflow/releases).
2. Pick the upstream chart commit. It must be a recent commit on the `apache/airflow` `main` branch whose `chart/Chart.yaml` declares `appVersion: <target>`. Release tags cannot be used: at tag `3.4.0` the chart still declares `appVersion: 3.3.2`, because the chart version is bumped after the release. Record the SHA; steps 10, 11, and 15 need it.
   * The 3.4.0 update used commit `1195d1b11ccd7178d09960a9ea47ab005983c540` (chart `2.0.0`, `appVersion: 3.4.0`).
   * With a local clone of `apache/airflow`: `git -C <airflow-clone> log -1 --format=%H origin/main` and `git -C <airflow-clone> show <SHA>:chart/Chart.yaml`.
3. Record the Python version from the official slim image tag, `apache/airflow:slim-<version>-python<X.Y>`. The same Python version appears in the test DAG image and in the documentation.
4. Create one branch and one pull request. Keep the chart sync as a commit of its own, separate from the version bumps, so that each concern can be reviewed on its own.

### 2. Airflow image and Python dependencies

5. Update the base image in [docker/Dockerfile](/docker/Dockerfile): `FROM apache/airflow:slim-<version>-python<X.Y>`.
6. Update [docker/requirements.txt](/docker/requirements.txt):
   * `apache-airflow[<extras>]==<version>` must be the same version as in the image tag.
   * Review every other line instead of blindly bumping it. Remove what is no longer needed, keep constraints that are still required (for example `celery<5.7` exists for provider compatibility), and bump provider pins that are coupled to the release (for example `apache-airflow-providers-keycloak`).
   * Keep the extra list complete: it is mirrored in [docs/public/installation.md](/docs/public/installation.md).
7. Review [tests_dags_image/requirements.txt](/tests_dags_image/requirements.txt) and [tests_dags_image/Dockerfile](/tests_dags_image/Dockerfile): the provider packages and the `pyspark` pin must still install on the new Python, and `SPARK_HOME` must point at the `python<X.Y>` directory of that Python.
8. Check the custom logging class [qs_platform_logging_config.py](/chart/helm/airflow/qs_files/qs_platform_logging_config.py) against the community logging config at [airflow_local_settings.py](https://github.com/apache/airflow/blob/main/airflow/config_templates/airflow_local_settings.py) and port whatever changed. The logging handlers are also what the UI uses to fetch task logs.
9. Verify that both images still build:

    ```sh
    docker build -f docker/Dockerfile -t qubership-airflow .
    docker build -f tests_dags_image/Dockerfile --build-arg base_img=qubership-airflow -t qubership-airflow-tests-dags-image .
    ```

### 3. Helm chart sync

10. Replace the upstream-owned part of `chart/helm/airflow` with the content of `chart/` at the recorded SHA.
    * Copied from upstream: `Chart.yaml`, `Chart.lock`, `.gitignore`, `.helmignore`, `values.yaml`, `files/pod-template-file.kubernetes-helm-yaml`, `files/statsd-mappings.yml`, and everything under `templates/`.
    * Not copied: upstream `docs/`, `tests/`, `kustomize-overlays/`, `newsfragments/`, `dockerfiles/`, `README.md`, `RELEASE_NOTES.rst`, `values.schema.json` (generated by `docker-transfer`, see step 15), and the bundled `charts/postgresql-*.tgz` (the internal PostgreSQL is not used).
    * Qubership-only files that must survive untouched: `templates/_qs_helpers.tpl`, `templates/qsdbaas/`, `templates/qsmonitoring/`, `templates/qspreinstallhooks/`, `templates/status-provisioner/`, `templates/api-server/api-server-httproute-qs-extras.yaml`, `qs_files/`, `monitoring/`, `charts/airflow-site-manager/`, `charts/integrationTests/`, `qubership_values.schema.json`, and `release-images.yaml`.
11. Re-apply the Qubership changes to the files that changed upstream, and delete local templates that upstream deleted: orphaned templates still render and are easy to miss. Expect structural changes between releases. 3.4.0 replaced the Kerberos init container with the sidecar and moved worker options under `workers.celery.*` and `workers.kubernetes.*`.
    * To confirm nothing is missing, compare the upstream template list with the local one. The only local-only entries must be the Qubership-only files from step 10:

      ```sh
      git -C <airflow-clone> ls-tree -r --name-only <SHA> chart/templates
      ```
12. In [values.yaml](/chart/helm/airflow/values.yaml), everything from `platformAirflowMonitoring:` to the end of the file is Qubership-owned and is kept as is. Set the values that follow the release:
    * `defaultAirflowTag` and `airflowVersion` to the target version.
    * Copy the image tags that come from upstream: `images.statsd.tag`, `images.redis.tag`, `images.pgbouncer.tag`, `images.pgbouncerExporter.tag`, `images.otelCollector.tag`.
    * `images.gitSync.tag`: use the newest community git-sync release. It may be newer than the chart default: 3.4.0 pinned `v4.8.0` while the chart default was `v4.4.2`.
    * `images.airflow.repository` and `images.flower.repository` stay `ghcr.io/netcracker/qubership-airflow` with `tag: main`.
    * `statusProvisioner.dockerImage` to the newest [qubership-deployment-status-provisioner release](https://github.com/Netcracker/qubership-deployment-status-provisioner/releases).
13. Update [Chart.yaml](/chart/helm/airflow/Chart.yaml):
    * `appVersion` to the target version.
    * `version` to the chart version of the recorded upstream commit (`1.22.0` became `2.0.0` in the 3.4.0 update).
    * Keep the `artifacthub.io/*` annotations as upstream ships them, including the stale `helm-chart/1.21.0` documentation link, which is upstream content and not a local defect.
    * Render the chart and make sure the command exits with code 0: `helm template qubership-airflow chart/helm/airflow > /dev/null`.
14. Update the release plumbing:
    * [.github/workflows/helm-charts-release.yaml](/.github/workflows/helm-charts-release.yaml): `chart-version` is the version the release action writes into `Chart.yaml`, so it must be the chart version with a `-dev` suffix (`2.0.0-dev`). The 3.4.0 update left it at `1.22.0-dev`.
    * [release-images.yaml](/chart/helm/airflow/release-images.yaml): `statsd-exporter` and `git-sync` must match `images.statsd.tag` and `images.gitSync.tag` from `values.yaml`. The Qubership-built images stay on `:main`.

### 4. Values schema generation

15. Update [generate_json_schema.py](/docker-transfer/generate_json_schema.py): the `url` must point at `chart/values.schema.json` of the same upstream commit as the chart sync.
16. Reconcile `values_params_to_keep` with the new upstream schema: a path that upstream removed makes the schema generation fail, so delete it or comment it out (as was done for `workers.celery.kerberosInitContainer.*`), and add newly added upstream parameters that Qubership exposes.
17. Every new Qubership-only value needs an entry in [qubership_values.schema.json](/chart/helm/airflow/qubership_values.schema.json), otherwise the generation fails the default-value validation.
18. Validate by building the transfer image, which runs the script at build time: `docker build -f docker-transfer/Dockerfile -t qubership-airflow-transfer .`. The generated `values.schema.json` is not stored in the repository; it exists only in that image.

### 5. Site manager and supporting images

19. Update [site-manager/docker/Dockerfile](/site-manager/docker/Dockerfile): the builder image `golang:<version>-alpine<release>` and the runtime `alpine:<release>`.
20. Update [site-manager/go.mod](/site-manager/go.mod): the `go` directive must be the same Go version as in the Dockerfile, `github.com/Netcracker/qubership-disaster-recovery-daemon` to the [latest release](https://github.com/Netcracker/qubership-disaster-recovery-daemon/releases), and the `k8s.io/*` modules to one consistent set. Then let the toolchain update the sums and check the result:

    ```sh
    cd site-manager && go mod tidy && go build ./... && go test ./...
    ```
21. Update [rclone-image/Dockerfile](/rclone-image/Dockerfile) to the [latest rclone release](https://github.com/rclone/rclone/releases) and re-check that `rclone-image/entrypoint.sh` still matches the rclone CLI it drives.
22. Update the base image in [integration-tests/tests/docker/Dockerfile](/integration-tests/tests/docker/Dockerfile) to the [latest qubership-docker-integration-tests release](https://github.com/Netcracker/qubership-docker-integration-tests/releases).
23. Scan the Go dependencies and address the reported vulnerabilities in `site-manager/go.mod`, or record why the remaining ones are acceptable.
24. The list of images CI builds lives in [.github/docker-build-config.json](/.github/docker-build-config.json) and [.github/workflows/advanced-images.yml](/.github/workflows/advanced-images.yml). Adding an image means adding it to both.

### 6. Documentation and agent-facing files

25. Search for the previous version and repeat until only intentional occurrences remain: `git grep -n "<old version>"`.
26. Update the documentation pages that carry Airflow doc links and the library list:
    * [installation.md](/docs/public/installation.md): base image and Python version, the library list copied from `docker/requirements.txt` including pinned providers, the Airflow documentation URLs, and the parameter descriptions affected by the chart changes.
    * [maintenance.md](/docs/public/maintenance.md), [monitoring.md](/docs/public/monitoring.md), and [airflow-site-manager.md](/docs/public/airflow-site-manager.md): Airflow documentation URLs.
27. Update [AGENTS.md](/AGENTS.md): the Airflow version, the base image tag and Python version, the Go version, and the chart version.
28. The troubleshooting skill references `agent-packages/troubleshoot-airflow/.apm/skills/troubleshoot-airflow/references/troubleshooting.md` and `references/monitoring.md` are generated from `docs/public/troubleshooting.md` and `docs/public/monitoring.md` by [sync-troubleshooting-skill.yml](/.github/workflows/sync-troubleshooting-skill.yml). Update the documentation source, and update the copies in the same pull request if the sync pull request has not landed yet.

### 7. Verification (definition of done)

29. All pipelines pass: basic images, advanced images (includes the test DAG image) and the super-linter. Lint locally where possible: `black --config .github/linters/.python-black docker/`, `flake8 --config .github/linters/.flake8 docker/`, and `golangci-lint` for `site-manager/`.
30. The chart renders and deploys: `helm template qubership-airflow chart/helm/airflow` succeeds and a test environment installs from the new chart.
31. The integrations still work: DBaaS in both REST and declarative mode, Keycloak IDP login, GitSync DAG delivery, rclone DAG delivery, the test DAGs from the test DAG image, site manager failover and switchover, and status provisioning.
32. The generated `values.schema.json` still accepts the documented installation parameters.
33. No unresolved vulnerabilities are left without a recorded reason.
