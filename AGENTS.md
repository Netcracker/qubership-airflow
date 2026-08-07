# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## What This Repo Is

A Kubernetes deployment stack for Apache Airflow 3.3.0 with Qubership platform integrations. It contains Docker images, a Helm chart (forked from the official Apache Airflow chart), and supporting services. Nothing here runs locally — all testing and deployment targets Kubernetes.

## Linting

Linting runs via GitHub Actions (`super-linter.yaml`). The active validators are:

- **Python**: Black + Flake8 (`max-line-length = 120`). Black excludes `qs_platform_logging_config.py`.
- **JavaScript**: ESLint, Prettier, Standard
- **Go**: golangci-lint (config in `.github/linters/.golangci.yml`)
- **Bash**: shellcheck
- **JSCPD**: copy-paste detection
- **YAML/Markdown**: yaml-lint, markdown-lint
- **IaC**: Checkov (`.github/linters/.checkov.yaml`)

To run Black locally:
```sh
black --config .github/linters/.python-black docker/
```

To run Flake8 locally:
```sh
flake8 --config .github/linters/.flake8 docker/
```

## Building Docker Images

All images are built and pushed to `ghcr.io/netcracker/` via GitHub Actions (`basic-images.yml`, `advanced-images.yml`). To build locally:

```sh
# Main Airflow image
docker build -f docker/Dockerfile -t qubership-airflow .

# Site Manager (Go binary)
docker build -f site-manager/docker/Dockerfile -t qubership-airflow-sm site-manager/

# Integration tests
docker build -f integration-tests/tests/docker/Dockerfile -t qubership-airflow-integration-tests integration-tests/tests/
```

## Site Manager (Go)

The site-manager is a Go 1.26 binary in `site-manager/`. It manages Disaster Recovery mode-switching via the Kubernetes API.

```sh
cd site-manager && go build ./...
cd site-manager && go test ./...
```

## Architecture

### Main Docker Image (`docker/`)

Based on `apache/airflow:slim-3.3.0-python3.11`. Two custom Python packages are installed into it:

- `docker/dbaasintegrationpackage/` — Airflow secrets backend that resolves connections/configs from Qubership DBaaS (PostgreSQL, Redis) and MaaS (Kafka).
- `docker/keycloakrbacintegrationpackage/` — Keycloak RBAC/FAB integration for Airflow auth.

The main entrypoint is patched to replace the NSS wrapper function for UID-less Kubernetes deployments.

### DBaaS Secrets Backend (`docker/dbaasintegrationpackage/`)

`DBAASSecretsBackend` in `qsdbaasintegration/dbaas_secrets_backend.py` extends Airflow's `BaseSecretsBackend` (or `LocalFilesystemBackend` when `LOCAL_FILESYSTEM_BACKEND=true`). It resolves:

- `get_config()` — returns fernet key, JWT secret, API secret key, Keycloak client secret, PostgreSQL connection string, Redis connection string (Redis is also provisioned via DBaaS using the `/api/v3/dbaas/.../databases/get-by-classifier/redis` endpoint).
- `get_connection()` — resolves Airflow connections from DBaaS or MaaS based on `{conn_id}_dbaas` / `{conn_id}_maas` properties passed to the backend.

Credentials are read from mounted Kubernetes secrets at `/var/run/secrets/airflow/` (env fallback if missing). M2M auth uses a service account token at `/var/run/secrets/tokens/dbaas/token`.

### Helm Chart (`chart/helm/airflow/`)

A fork of the official Apache Airflow Helm chart (v1.22.0, appVersion 3.3.0). All Qubership modifications are annotated in template files, making it easy to diff against upstream. Two comment styles are used:
- YAML comment: `#---Qubership custom change: Change description---`
- Helm template comment: `{{- /* Qubership custom change: Change description--- */ -}}`

Key additions not in upstream:
- `templates/qspreinstallhooks/` — pre-install jobs (DB setup, TLS cert provisioning)
- `templates/qsmonitoring/` — Prometheus alerts and Grafana service monitors
- `templates/_qs_helpers.tpl` — Qubership-specific Helm helpers
- `qs_files/` — custom logging config (`qs_platform_logging_config.py`) and Keycloak FAB integration (`webserver_config_keycloak.py`)
- `monitoring/` — Grafana dashboard JSON (`airflow-overview.json`)
- `charts/airflow-site-manager/` — subchart for the DR site manager
- `charts/integrationTests/` — subchart for running integration tests

Key `values.yaml` changes from upstream defaults: internal PostgreSQL/Redis disabled (expects DBaaS), webserver ingress enabled, triggerer disabled, persistence off, DBaaS secrets backend configured.

Every change to the Helm chart must be verified locally with:
```sh
helm template qubership-airflow chart/helm/airflow
```

### Site Manager (`site-manager/`)

A Go daemon that implements the `qubership-disaster-recovery-daemon` interface to manage Airflow in DR (active/standby) mode. It uses `k8s.io/client-go` to manipulate deployments and watch cluster state.

### Integration Tests (`integration-tests/`)

Robot Framework test suite run as a Docker container. Tests cover DAG execution, monitoring, and provider connectivity. Triggered via the `integrationTests` Helm subchart after deployment.

### Supporting Images

- `docker-transfer/` — scratch-based image used to extract chart artifacts in CI pipelines.
- `rclone-image/` — Rclone-based alternative to GitSync for DAG synchronization.
- `tests_dags_image/` — Sample DAGs for smoke-testing Airflow providers.
