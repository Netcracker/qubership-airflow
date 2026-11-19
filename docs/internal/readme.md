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
* https://github.com/apache/airflow/blob/main/airflow-core/src/airflow/config_templates/airflow_local_settings.py - airflow default logging config

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

Custom logging config class supported by platform is located at [qs_platform_logging_config.py](/chart/helm/airflow/qs_files/qs_platform_logging_config.py). It is based on community logging config from https://github.com/apache/airflow/blob/main/airflow-core/src/airflow/config_templates/airflow_local_settings.py . Note, that handlers, specified in `airflow.task` logger are also used to fetch logs in airflow UI (see `class` of the secified handler).
Custom logging config class and related third-party classes usually are used to investigate/troubleshoot issues related to incorrect log format, incorrect number of logs, incorrect logging level.

When troubleshooting task logs in airflow webUI with celery executor, it is necessary to remember that without using S3 storage, logs in UI should be available only when workers are deployed as statefulset with persistence storage. If the workers are deployed differently, absence of airflow logs in UI is expected behavior.

### GitSync container issues

**TBD**

## Evergreen strategy

The distribution follows the latest Apache Airflow release. One update is one pull request, as in `feat: Airflow340 update (#85)` for 3.4.0. The pull request covers the Airflow image, the forked community chart, the supporting images, and every file that carries a version.

Three rules hold for the whole procedure:

* The target Airflow version is the only input. The Python version, the chart version, and the upstream commit follow from it.
* A Qubership change inside an upstream file is marked so that the next sync can tell it apart from upstream content. Three styles exist: `#---Qubership custom change: <description>---` in YAML, `{{- /* Qubership custom change: <description>--- */ -}}` in Helm templates, and `# Qubership override: <value> (upstream default: <value>)` for a changed default.
* Markers are not a complete inventory. Many overrides in `chart/helm/airflow/values.yaml` predate them and carry none, so the diff against the chart you are updating from is the source of truth for what is local. The "Prepare the update" section explains how to build that diff.

Steps are numbered from 1 in each section. Cite them as `<section>.<step>`, for example `3.2` for the second step of the Helm chart sync, and use the same form when reporting progress or resuming after an interruption. Adding a step renumbers only its own section.

### 1. Prepare the update

1. Pick the target release: the latest stable Apache Airflow version from [apache/airflow releases](https://github.com/apache/airflow/releases).
2. Pick the upstream chart commit. It must be a recent commit on the `apache/airflow` `main` branch whose `chart/Chart.yaml` declares `appVersion: <target>`. Release tags do not work: at tag `3.4.0` the chart still declares `appVersion: 3.3.2`, because the chart version is bumped after the release. Record the SHA; the chart sync and the values schema use it.
   * The 3.4.0 update used commit `1195d1b11ccd7178d09960a9ea47ab005983c540` (chart `2.0.0`, `appVersion: 3.4.0`).
   * With a local clone of `apache/airflow`: `git -C <airflow-clone> log -1 --format=%H origin/main`, then `git -C <airflow-clone> show <SHA>:chart/Chart.yaml`.
3. Record the commit the current chart was synced from. It is pinned in [generate_json_schema.py](/docker-transfer/generate_json_schema.py), and earlier ones are in `git log -p -- docker-transfer/generate_json_schema.py`.
4. Diff the local chart against the upstream chart at that commit, for example `git diff --no-index <upstream-chart-dir> chart/helm/airflow`. That diff lists every Qubership delta, marked or not, before anything is overwritten.
5. Record the Python version from the official slim image tag, `apache/airflow:slim-<version>-python<X.Y>`. The same Python version appears in the test DAG image and in the documentation.
6. Create one branch and one pull request. Keep the chart sync in a commit of its own, separate from the version bumps, so that each concern can be reviewed on its own.

### 2. Airflow image and Python dependencies

1. Update the base image in [docker/Dockerfile](/docker/Dockerfile): `FROM apache/airflow:slim-<version>-python<X.Y>`.
2. Update [docker/requirements.txt](/docker/requirements.txt):
   * `apache-airflow[<extras>]==<version>` must be the same version as in the image tag.
   * Review every other line instead of bumping it blindly. Remove what is no longer needed, keep constraints that are still required (`celery<5.7` exists for provider compatibility), and bump the provider pins that are coupled to the release (`apache-airflow-providers-keycloak`).
3. Mirror [docker/requirements.txt](/docker/requirements.txt) into [docs/public/installation.md](/docs/public/installation.md) verbatim, extras and pins included. The two drift apart quickly; the requirements file wins.
4. Review [tests_dags_image/requirements.txt](/tests_dags_image/requirements.txt) and [tests_dags_image/Dockerfile](/tests_dags_image/Dockerfile): the provider packages and the `pyspark` pin must still install on the new Python, and `SPARK_HOME` must point at the `python<X.Y>` directory.
   * The apt packages in that Dockerfile depend on the base distribution. The 3.4.0 base is Debian 13, where `libxmlsec1-openssl` resolves to `libxmlsec1t64-openssl`, and hardened versions (`+dhi`) sort above the point-release rebuilds apt tries to install, so a package that pins its runtime dependency exactly can make the transaction unresolvable.
   * When the layer stops resolving, build the image as in step 6 and prefer dropping the optional `-dev` package over forcing a downgrade. The follow-up to the 3.4.0 update dropped `libxmlsec1-dev` for that reason: nothing in the image needs xmlsec on Python 3.14, and the package pulled `libgnutls28-dev` and `nettle-dev`, which no longer resolved against the hardened `libnettle8t64` and `libhogweed6t64` in the base image.
5. Check the custom logging class [qs_platform_logging_config.py](/chart/helm/airflow/qs_files/qs_platform_logging_config.py) against the community logging config at [airflow_local_settings.py](https://github.com/apache/airflow/blob/main/airflow-core/src/airflow/config_templates/airflow_local_settings.py) and port whatever changed. The logging handlers are also what the UI uses to fetch task logs.
6. Verify that both images still build. The context is the repository root, because both Dockerfiles copy repository paths:

   ```sh
   docker build -f docker/Dockerfile -t qubership-airflow .
   docker build -f tests_dags_image/Dockerfile \
     --build-arg base_img=qubership-airflow \
     -t qubership-airflow-tests-dags-image .
   ```

### 3. Helm chart sync

1. Replace the upstream-owned part of `chart/helm/airflow` with the content of `chart/` at the recorded SHA.
   * Copied from upstream: `Chart.yaml`, `Chart.lock`, `.gitignore`, `.helmignore`, `files/pod-template-file.kubernetes-helm-yaml`, `files/statsd-mappings.yml`, and everything under `templates/`.
   * Merged instead of overwritten: `values.yaml`. Start from the upstream file and re-apply the local deltas from the "Prepare the update" diff; the values steps below list where they sit.
   * Not copied: upstream `docs/`, `tests/`, `kustomize-overlays/`, `newsfragments/`, `dockerfiles/`, `README.md`, `RELEASE_NOTES.rst`, `values.schema.json` (generated by `docker-transfer`), and `charts/postgresql-*.tgz` (the internal PostgreSQL is not used).
   * Qubership-only files that must survive untouched: `templates/_qs_helpers.tpl`, `templates/qsdbaas/`, `templates/qsmonitoring/`, `templates/qspreinstallhooks/`, `templates/status-provisioner/`, `templates/api-server/api-server-httproute-qs-extras.yaml`, `qs_files/`, `monitoring/`, `charts/airflow-site-manager/`, `charts/integrationTests/`, `qubership_values.schema.json`, and `release-images.yaml`.
2. Re-apply the Qubership changes to the files that changed upstream, and delete local templates that upstream deleted: orphaned templates still render and are easy to miss. Expect structural changes between releases. 3.4.0 replaced the Kerberos init container with the sidecar and moved worker options under `workers.celery.*` and `workers.kubernetes.*`.
   * To confirm nothing is missing, compare the upstream template list with the local one. The only local-only entries must be the Qubership-only files listed above:

     ```sh
     git -C <airflow-clone> ls-tree -r --name-only <SHA> chart/templates
     ```
3. Update [values.yaml](/chart/helm/airflow/values.yaml). Two kinds of local change survive the sync:
   * The Qubership block: everything from `platformAirflowMonitoring:` to the end of the file is Qubership-owned and copied as is.
   * The in-body overrides in the upstream part: image repositories and tags, security context defaults, `dags.gitSync.rcloneImage`, the redirect route block, and similar. Most carry no marker, so take them from the "Prepare the update" diff.
4. Then set the values that follow the release:
   * `defaultAirflowTag` and `airflowVersion` to the target version.
   * Copy the image tags that come from upstream: `images.statsd.tag`, `images.redis.tag`, `images.pgbouncer.tag`, `images.pgbouncerExporter.tag`, `images.otelCollector.tag`.
   * `images.gitSync.tag`: use the newest community git-sync release. It may be newer than the chart default: 3.4.0 pinned `v4.8.0` while the chart default was `v4.4.2`.
   * `images.airflow.repository` and `images.flower.repository` stay `ghcr.io/netcracker/qubership-airflow` with `tag: main`.
   * `statusProvisioner.dockerImage` to the newest [qubership-deployment-status-provisioner release](https://github.com/Netcracker/qubership-deployment-status-provisioner/releases).
5. Update [Chart.yaml](/chart/helm/airflow/Chart.yaml):
   * `appVersion` to the target version.
   * `version` to the chart version of the recorded upstream commit (`1.22.0` became `2.0.0` in the 3.4.0 update).
   * Keep the `artifacthub.io/*` annotations as upstream ships them, including the stale `helm-chart/1.21.0` documentation link. That link is upstream content, not a local defect.
   * Render the chart and check the exit code: `helm template qubership-airflow chart/helm/airflow > /dev/null`.
6. Update the release plumbing:
   * [.github/workflows/helm-charts-release.yaml](/.github/workflows/helm-charts-release.yaml): set `chart-version` to the `version` from `Chart.yaml` with a `-dev` suffix, so chart `2.0.0` takes `2.0.0-dev`. That is how the value tracked the chart before. The action writes this value into `Chart.yaml` at release time, and the convention is documented nowhere in the repository, so state the assumption in the pull request description instead of pausing to ask for a decision.
   * [release-images.yaml](/chart/helm/airflow/release-images.yaml): `statsd-exporter` and `git-sync` must match `images.statsd.tag` and `images.gitSync.tag` from `values.yaml`. The Qubership-built images stay on `:main`.

### 4. Values schema generation

1. Update [generate_json_schema.py](/docker-transfer/generate_json_schema.py): the `url` must point at `chart/values.schema.json` of the same upstream commit as the chart sync.
2. Reconcile `values_params_to_keep` with the new upstream schema. A path that upstream removed makes the schema generation fail, so delete it or comment it out, as was done for `workers.celery.kerberosInitContainer.*`. Add the upstream parameters that Qubership now exposes.
3. Every new Qubership-only value needs an entry in [qubership_values.schema.json](/chart/helm/airflow/qubership_values.schema.json), otherwise the generation fails the default-value validation.
4. Validate by building the transfer image: `docker build -f docker-transfer/Dockerfile -t qubership-airflow-transfer .`. It first copies the tags from `release-images.yaml` into `values.yaml` and the two subchart value files, then runs the schema script. A mismatch therefore shows up as changed tags after the build. The generated `values.schema.json` is not stored in the repository; it exists only in that image.

### 5. Site manager and supporting images

1. Update [site-manager/docker/Dockerfile](/site-manager/docker/Dockerfile): the builder image `golang:<version>-alpine<release>` and the runtime `alpine:<release>`.
2. Update [site-manager/go.mod](/site-manager/go.mod): the `go` directive must match the Go version in the Dockerfile, `github.com/Netcracker/qubership-disaster-recovery-daemon` goes to the [latest release](https://github.com/Netcracker/qubership-disaster-recovery-daemon/releases), and the `k8s.io/*` modules move as one consistent set. Then update the sums and check the result:

   ```sh
   cd site-manager && go mod tidy && go build ./... && go test ./...
   ```
3. Update [rclone-image/Dockerfile](/rclone-image/Dockerfile) to the [latest rclone release](https://github.com/rclone/rclone/releases) and re-check that `rclone-image/entrypoint.sh` still matches the rclone CLI it drives.
4. Update the base image in [integration-tests/tests/docker/Dockerfile](/integration-tests/tests/docker/Dockerfile) to the [latest qubership-docker-integration-tests release](https://github.com/Netcracker/qubership-docker-integration-tests/releases).
5. Scan the Go dependencies and address the reported vulnerabilities in `site-manager/go.mod`, or record why the remaining ones are acceptable.
6. Know which file owns which image before adding or renaming one. A Qubership-built image touches six places:
   * [.github/workflows/basic-images.yml](/.github/workflows/basic-images.yml): the build matrix, which builds `qubership-airflow`, `-transfer`, `-rclone`, `-sm`, and `-integration-tests`.
   * [.github/docker-build-config.json](/.github/docker-build-config.json): the same five entries, read by the release workflow.
   * [chart/helm/airflow/release-images.yaml](/chart/helm/airflow/release-images.yaml): the image reference with its tag. `docker-transfer/sync_util.py` copies that tag into the values entry below while the transfer image builds.
   * The values entry that the tag is written to: `images.<name>` in `chart/helm/airflow/values.yaml`, `image` in `charts/airflow-site-manager/values.yaml`, or `image` in `charts/integrationTests/values.yaml`. Without one, the sync has nothing to update.
   * [.github/helm-charts-release-config.yaml](/.github/helm-charts-release-config.yaml): the image reference with its release version, which rewrites that tag at release time.
   * [.github/workflows/clean.yml](/.github/workflows/clean.yml): the GHCR cleanup matrix, which deletes package versions when a branch or tag is deleted. A missing entry leaves stale package versions behind; it does not break a build.
   `qubership-airflow-tests-dags-image` is the exception. It is built in [.github/workflows/advanced-images.yml](/.github/workflows/advanced-images.yml) on top of `qubership-airflow`, ships in no chart, and appears only there and in `clean.yml`.

### 6. Documentation and agent-facing files

1. Search for the previous version and repeat until only intentional occurrences remain: `git grep -n "<old version>"`.
2. Update the documentation pages that carry Airflow doc links and library data:
   * [installation.md](/docs/public/installation.md): base image and Python version, the library list (mirror of `docker/requirements.txt`), the Airflow documentation URLs, and the parameter descriptions affected by the chart changes.
   * [maintenance.md](/docs/public/maintenance.md), [monitoring.md](/docs/public/monitoring.md), and [airflow-site-manager.md](/docs/public/airflow-site-manager.md): Airflow documentation URLs.
3. Update [AGENTS.md](/AGENTS.md): the Airflow version, the base image tag and Python version, the Go version, and the chart version.
4. The troubleshooting skill references `agent-packages/troubleshoot-airflow/.apm/skills/troubleshoot-airflow/references/troubleshooting.md` and `references/monitoring.md` are generated from `docs/public/troubleshooting.md` and `docs/public/monitoring.md` by [sync-troubleshooting-skill.yml](/.github/workflows/sync-troubleshooting-skill.yml). Update the documentation source and, if the sync pull request has not landed yet, the copies in the same pull request.

### 7. Verification (definition of done)

1. All pipelines pass: basic images, advanced images (includes the test DAG image), and the super-linter. Lint locally where possible: `black --config .github/linters/.python-black docker/`, `flake8 --config .github/linters/.flake8 docker/`, and `golangci-lint` for `site-manager/`.
2. The chart renders and deploys: `helm template qubership-airflow chart/helm/airflow` succeeds, and a test environment installs from the new chart.
3. The integrations still work: DBaaS in both REST and declarative mode, Keycloak IDP login, GitSync DAG delivery, rclone DAG delivery, the test DAGs from the test DAG image, site manager failover and switchover, and status provisioning.
4. The generated `values.schema.json` still accepts the documented installation parameters.
5. No unresolved vulnerabilities are left without a recorded reason.
