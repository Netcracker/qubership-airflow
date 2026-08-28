---
name: troubleshoot-airflow
description: Diagnose and resolve failures in a Qubership Airflow Helm deployment — DAGs/tasks stuck or failed, scheduler/api-server/worker pod restarts, Celery/Redis broker errors, missing task logs, IDP/Keycloak redirect_uri protocol mismatches, api-server startup-resource issues, DBaaS/MaaS secrets-backend errors (including AIRFLOW-8300–8310, AIRFLOW-1930/1931 log codes), or a Disaster-Recovery mode-switch (site-manager) failure. Falls back to a general checklist, framed for the user to check, when nothing matches.
---

## Reading the reference file

1. Grep issue headers with line numbers: `grep -n "^## " references/troubleshooting.md`. This is level-anchored —
   only issue titles and the Error Codes section use `##`; nothing else in the file does.
2. Match the symptom against the jump table below (or the raw headers if the table is stale) to pick a section.
3. Read only that section: offset at its line number, limit through the next `##` header's line number. Never load
   the whole file for one lookup.
4. If the symptom is a log line containing `[error_code=AIRFLOW-XXXX]`, jump straight to the Error Codes table and
   match the code. If the code isn't in the table, grep the codebase for it directly —
   `grep -rn "AIRFLOW-XXXX" docker/` — before concluding it's undocumented; the table has known gaps (see the note
   above it) and the code's log-call site usually explains the trigger condition well enough on its own.

## Symptom → reference section

| Symptom | Header in references/troubleshooting.md |
|---|---|
| A DAG run shows Failed state | Airflow DAG has Failed State |
| Tasks sit in `queued` and never start | Tasks are Stuck in Queued State |
| All new DAG runs stay in `running`; UI banner "The scheduler does not appear to be running." | DAGs are Stuck in Running State |
| `component=api-server` pod restarts repeatedly, no other symptom | API server Pod Restarts Multiple Times |
| Some other Airflow pod restarts repeatedly / won't start, no more specific row fits | Airflow Pods Restart Multiple Times |
| CeleryExecutor: worker log stalls right after gunicorn/celery startup banner, task never runs | Task does not Execute and Worker Logs are Stuck in Celery Executor |
| Worker log shows `Cannot connect to redis://...: Connection reset by peer` | Task does not Execute and Worker Logs Contain Redis Connection Error |
| Task fails; `*** Could not read served logs: Request URL is missing an 'http://' or 'https://' protocol` | Task Fails with Error and no Logs Available While the Logs for Other Successful Tasks are Visible |
| Keycloak/IDP login error `Invalid parameter: redirect_uri`, scheme is `http` where `https` is expected | Wrong Protocol Resolution in redirect_uri in IDP Integration |
| Logs for earlier task tries missing in UI; only the latest try's logs show | Airflow Logs are not Available for Some Attempts in Tasks with Multiple Tries |
| api-server container killed during startup: `Waiting for child process` / `Child process died` | Airflow API Server Startup Failed due to Insufficient Resources |
| Preinstall job fails and its pod is gone (logs unreadable) before anyone can inspect it | Preinstall Job Fails and Logs are Unavailable |
| Log/exception contains `[error_code=AIRFLOW-XXXX]` | Error Codes |

Start every diagnosis by getting the exact error text or log line and the affected component (`api-server`,
`scheduler`, `worker`, `triggerer`, `dag-processor`) — several rows above match on a specific log string, not a
general description. Check context/attachments for already-provided logs before asking for them.

If the symptom plausibly matches more than one row (e.g. "pod restarts" alone matches two different rows for two
different reasons), ask which one applies rather than guessing.

## Guardrails

- Don't recommend `kubectl scale` on Airflow Deployments/StatefulSets (`tier=airflow`) in a namespace managed by
  `airflow-site-manager` outside of an actual DR switchover. The next switchover call
  (`site-manager/pkg/disasterrecovery/airflow/manager.go`) drives every `component=<name>` Deployment/StatefulSet to
  the replica count in its configured `componentToReplicaMap`, so a manual scale gets silently overwritten on the
  next mode change and can desync from what the DR daemon believes is running.
- Don't recommend deleting pods labeled `component=worker,kubernetes_executor=True` as a generic "stuck task" fix.
  Under KubernetesExecutor these are per-task ephemeral pods; site-manager only deletes them during a STANDBY/DISABLED
  switchover. Deleting one manually mid-run kills that task's execution, not a stuck queue.
- The DBaaS/MaaS secrets backend (`DBAASSecretsBackend`) reads each credential from a mounted file under
  `/var/run/secrets/airflow/<ENV_NAME>` first and only falls back to the `<ENV_NAME>` environment variable if the
  file is missing. If a user updates a secret's env var (or `extraEnvFrom`) and redeploys but a volume-mounted secret
  with the same key still exists, the stale mounted value wins silently — check for a leftover volume mount before
  assuming the new value didn't take effect.
- `config.secrets.backend_kwargs` (built from `qs_secrets_backend_params` via `toJson`) is replaced wholesale on
  every Helm upgrade, not merged. A recommended change that adds one `<conn_id>_dbaas` / `<conn_id>_maas` entry must
  preserve every existing entry in `qs_secrets_backend_params`, or previously working connections silently lose their
  DBaaS/MaaS resolution.
- `DBAASSecretsBackend.get_variable()` only returns a value when `LOCAL_FILESYSTEM_BACKEND` is enabled — Airflow
  Variables are never resolved from DBaaS/MaaS. If a user reports an empty/`None` Variable while using the DBaaS
  secrets backend, that's expected behavior, not a bug to chase.
- Only Postgres connections are resolvable via `<conn_id>_dbaas` (see `get_conn_value` — it only branches on
  `type == "postgresql"`); Kafka goes through `<conn_id>_maas` instead. There's no DBaaS-backed path for other
  connection types.
- Every Helm chart change recommended here must be verified with `helm template qubership-airflow chart/helm/airflow`
  before telling the user to redeploy — this is a hard repo rule (see AGENTS.md), not optional for troubleshooting
  suggestions specifically.
- The preinstall job's `activeDeadlineSeconds` is hardcoded to `600` in
  `chart/helm/airflow/templates/qspreinstallhooks/custom-preinstall-job.yaml` (both the Job and pod-template level)
  and isn't exposed through `values.yaml`. When recommending the "sleep instead of running the DB-creation script"
  workaround (see "Preinstall Job Fails and Logs are Unavailable"), don't suggest a sleep duration at or above 600
  seconds — Kubernetes kills the job at the 600-second mark regardless of what the container is running, cutting the
  debugging window short.

## Config value conventions

- DBaaS auth defaults to basic auth (`DBAAS_M2M_ENABLED: 'false'`), requiring `DBAAS_USER`/`DBAAS_PASSWORD` in the
  `dbaas-connection-params-main` secret. MaaS defaults the *other* way — `MAAS_M2M_ENABLED: 'true'` — using the
  `maas-m2m-token` service-account token instead. This asymmetry is a common source of "why does DBaaS need a
  password but MaaS doesn't" confusion; don't assume both flags default the same way.
- M2M service-account tokens are mounted at `/var/run/secrets/tokens/dbaas/token` and
  `/var/run/secrets/tokens/maas/token` respectively — only relevant when the corresponding `*_M2M_ENABLED` is `true`.
- Fernet key / API secret key / JWT secret / Keycloak client secret are read from `/var/run/secrets/airflow-keys/`
  (fixed filenames: `fernet-key`, `api-secret-key`, `jwt-secret`, `client-secret`), separate from the
  `/var/run/secrets/airflow/` folder used for every other DBaaS/MaaS credential.
- `DBAAS_INTEGRATION_LOG_LEVEL=DEBUG` enables verbose logging in the secrets backend, but only takes effect together
  with `config.logging.logging_level: debug` — setting just one of the two leaves the other component quiet.
- There's no single Airflow-side `airflow.cfg` umbrella override; all provider-specific values live under `config.*`
  in `values.yaml` (rendered into `airflow.cfg` via the standard upstream chart mechanism) — check for a dedicated
  `config.<section>.<key>` before suggesting an env-var override.

## Cluster/deployment conventions

- Pod/Deployment/StatefulSet label `component=<name>` identifies each piece: `api-server`, `scheduler`, `worker`,
  `triggerer`, `dag-processor`, `flower`, `statsd`, `redis`, `pgbouncer`, `otel-collector`. All of them additionally
  carry `tier=airflow`.
- The `worker` component only exists when `executor` is Celery-based — `site-manager` explicitly skips checking it
  when not deployed (`isComponentDeployed("component", "worker")`), and KubernetesExecutor task pods carry the extra
  label `kubernetes_executor=True` on top of `component=worker`.
- There is no continuously-reconciling operator in this stack (unlike an operator-managed database) — the Helm chart
  renders once per `helm upgrade`/`helm template` invocation, and `airflow-site-manager` only acts on an explicit DR
  mode-change request. Config drift between releases isn't self-healing the way it would be under a reconciling
  operator; a stuck bad state generally needs a redeploy, not a wait.
- Check DR health/state via the site-manager `/healthz` endpoint (`HealthAirflow` in
  `site-manager/pkg/disasterrecovery/airflow/manager.go`) rather than inferring it purely from pod counts — it
  already encodes the same `up`/`degraded`/`down` logic used during switchover.
