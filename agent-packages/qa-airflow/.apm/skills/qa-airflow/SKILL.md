---
name: qa-airflow
description: Plan and verify testing of a Qubership Airflow change — pick the right Robot suite and tags, run the pytest secret-backend tests, reproduce the chart's config-variant behaviour (DBaaS declarative vs REST, Kerberos, SSL broker, triggerer, site-manager DR), and check the documented AIRFLOW-8xxx error codes and alert names. Triggers when the user asks how to test an Airflow change, which tags to run, or what must be verified before release. Do NOT run automatically.
---

## What this deployment is

`chart/helm/airflow` deploys Apache Airflow 3.4.0 (fork of the upstream chart 2.0.0) with
Qubership modifications. Image `apache/airflow:slim-3.4.0-python3.14` plus two installed
packages: a **DBaaS/MaaS secrets backend** and a **Keycloak RBAC** integration.
Default executor is `CeleryExecutor`; `triggerer.enabled` is **`false`** by default.

Anyone testing this must remember: **a passing suite is not the same as a tested feature.**
Several suites self-skip and still report success — see "Silent skips" below.

---

## Test suites that exist

| Suite | Path | Framework | Covers |
| --- | --- | --- | --- |
| Smoke | `integration-tests/tests/robot/tests/smoke/smoke.robot` | Robot | status API, PG DAG, Trino DAG, noop DAG |
| Connections | `integration-tests/tests/robot/tests/connections/` | Robot | connection wiring incl. `trino_test.robot` |
| HA | `integration-tests/tests/robot/tests/ha/ha.robot` | Robot | worker / scheduler / api pod kill |
| Image integrity | `integration-tests/tests/robot/tests/image_tests/image_tests.robot` | Robot | images vs ConfigMap `dd_images` |
| Alerts | `integration-tests/tests/robot/tests/monitoring/alerts.robot` | Robot | alert firing / inactivity |
| Secrets backend | `docker/dbaasintegrationpackage/tests/test_mounted_secrets.py` | pytest | mounted-secret resolution |

**There is no CI job that runs any of these.** CI runs super-linter and image builds only.
Treat "CI is green" as proof of linting, nothing more.

### Robot tags

Run through the `integrationTests` subchart (`integrationTests.enabled=true`,
`statusProvisioner.integrationTestsTimeout: 3000` when running the whole `airflow` tag).

```
airflow
├── smoke                 pg_connection_dag, trino_connection_dag
├── ha                    worker, scheduler, api
├── alert                 worker_degraded, worker_down, worker_down_firing,
│                         scheduler_down, api_down
└── airflow_images        airflow_images_worker, airflow_images_scheduler,
                          airflow_images_apiserver, airflow_images_tests,
                          airflow_images_statsd
```

### DAGs that must exist

`noop_dag`, `sleeping_dag`, `sleep_dag_with_retries`, `postgres_operator_test_dag`,
and `sql_trino_variable_catalog` **when Trino testing is enabled**. They live in
`tests_dags_image/dags/`. A missing DAG shows up as a suite failure, not a setup error.

### pytest

```
DBAAS_OPERATOR_ENABLED=true LOCAL_FILESYSTEM_BACKEND=false \
DBAAS_MOUNTED_SECRETS_DIR=<dir> python -m pytest docker/dbaasintegrationpackage/tests/
```

Runs without a cluster. This is the **only** test you can run on a laptop — use it for any
change to `dbaas_secrets_backend.py`.

---

## Silent skips — check these before claiming coverage

1. **Trino connection test** — the runner skips it entirely when Trino credentials are absent
   from the secret. "Trino passed" may mean "Trino never ran". Confirm the secret had
   `trino.host/port/user/password` and that `trino_default` connection existed.
2. **Alert suite** — `tags_exclusion.py` drops the whole `alert` tag when `PROMETHEUS_HOST`
   or `PROMETHEUS_PORT` is unset.
3. **Image tests** — skip when the `dd_images` ConfigMap key is empty.
4. **Monitoring** — `platformAirflowMonitoring`, `serviceMonitor.enabled`,
   `prometheusRule.enabled`, `serviceMonitorStatsd.enabled` all default to `false`. Alerts
   are inert unless explicitly enabled, so an alert test on a default install proves nothing.

---

## Configuration variants that must be exercised

Pick variants by what the change touches, not by convenience.

| Variant | Keys | Why it breaks |
| --- | --- | --- |
| DBaaS REST vs declarative | `dbaasDeclarative.enabled` | declarative **ignores** `DBAAS_*_DB_OWNER`, `*_BACKUP_DISABLED`, and inline `dbOwner`/`backupDisabled` |
| Secrets backend | `config.secrets.backend`, `qs_secrets_backend_params` | wrong param shape only fails at runtime |
| PostgreSQL driver | `data.metadataSecretName` value | `postgresql+psycopg://` for Airflow ≥ 3.4.0, `postgresql+psycopg2://` below — wrong prefix is a deploy-time failure |
| Executor | `executor`, `config.celery.worker_concurrency` | `KubernetesExecutor` skips Redis secret creation entirely |
| Triggerer | `triggerer.enabled` (default `false`) | Kafka DAGs need it; enabling it adds exposed ports |
| Kerberos | `kerberos.enabled`, `kerberos.principal` | placeholder principal `airflow@FOO.COM` must be replaced |
| Broker SSL | `data.brokerUrl` | Celery + SSL Redis without broker SSL config yields `AirflowTaskTimeout` with frozen worker logs |
| API workers | `config.api.workers` | 1 worker needs ≥ 300m/300Mi; 4 workers ≥ 800m/1500Mi, else `Child process [16] died` |
| Site manager (DR) | `airflow-site-manager.enabled` | standby = all components scaled to 0 and Redis purged |
| Read-only FS / arbitrary UID | NSS wrapper in image | pod relies on `/tmp` being writable |

### Upgrade-specific checks

- `data.brokerUrl` and `fernetKey` can **only** be set on `helm install`, not on upgrade.
  A regression test: install, then `helm upgrade` with a changed `data.brokerUrl` **must fail**.
- Changing `data.jwtSecret` on upgrade invalidates JWTs and can fail DAGs during the rollout —
  validate a rolling upgrade reproduces no outage, or that the documented procedure is followed.

---

## Chart validation gates

CI does **not** run them. Run manually on every chart change:

```
helm dependency update ./chart/helm/airflow
helm template <release> chart/helm/airflow
black --config .github/linters/.python-black docker/
flake8 --config .github/linters/.flake8 docker/
```

`templates/check-values.yaml` hard-fails `helm template` on invalid combinations — the most
useful negative tests, because each message is a contract:

- redis `passwordSecretName` without `data.brokerUrlSecretName` / `AIRFLOW__CELERY__BROKER_URL_CMD`
- both `redis.passwordSecretName` and `redis.password`
- Celery executor with `redis.enabled=false` and no broker url
- both `data.brokerUrlSecretName` and `data.brokerUrl`
- both `elasticsearch.enabled` and `opensearch.enabled`
- `airflowVersion` below 3.1.0

---

## Error codes and alerts to assert

DBaaS/MaaS errors `AIRFLOW-8300`–`AIRFLOW-8312`, `AIRFLOW-1930`, `AIRFLOW-1931` are emitted by
`create_dbs_dbaas.py` and `dbaas_secrets_backend.py`. High-value cases:

- `AIRFLOW-8308` — raised when `DBAAS_SSL_VERIFICATION_MAIN` is not `DISABLED`/`ENABLED`/`CERT_PATH:…`
- `AIRFLOW-8311` — declarative mode, Secret missing at `/var/run/secrets/dbaas-declarative/<conn>`
- `AIRFLOW-8312` — declarative mode, Secret for the wrong database type
- `AIRFLOW-8305` — Kafka auth mechanism not in `SASL_PLAINTEXT|PLAINTEXT|SSL|SASL_SSL`
- `AIRFLOW-8307` — Kafka credential type not `PLAIN|SCRAM`

Alert names asserted by `alerts.robot`: `WorkerStatefulsetIsDegraded`,
`ThereAreUnavailableWorkers`, `WorkerError`, `SchedulerError`, `APIerror`.
`AirflowDRState` exists but is **not** asserted by Robot.

---

## Failure modes that are not test failures

- `create_dbs_dbaas.py` **logs** errors and can exit 0 without creating the Secret. Always
  assert on Secret existence, never on the job exit code.
- `createdb.py` (legacy non-DBaaS path) string-interpolates SQL — fails on special characters
  in passwords.
- After credential rotation, scheduler/DAG-processor/triggerer self-heal via liveness probes,
  but **api-server and Celery workers do not** — a manual restart is required. Worker restart
  target differs: `deployment/<fullname>-worker` vs `statefulset/<fullname>-worker` depending
  on persistence.
- Split-brain in DR is not auto-handled; moving a site to standby is manual.
- `docs/public/performance.md` is written for Airflow **1.10.x** and is stale — do not use it
  as a benchmark source. Only its resource-accounting caveat still holds.

---

## Reviewing a change

1. Identify what changed: image, chart values, template, or Python package.
2. Map it to the table in "Configuration variants" and pick the smallest set that exercises it.
3. Name which suites must run and which tags, plus any silent skip that would invalidate the run.
4. Add a negative test for each `check-values.yaml` contract the change touches.
5. For secrets-backend changes, run the pytest suite and at least one live `AIRFLOW-83xx` case.
6. State explicitly what is **not** covered.
