from PlatformLibrary import PlatformLibrary
import requests
import json
import logging
import base64
import os
import re
from pathlib import Path

pl_lib = PlatformLibrary(managed_by_operator="true")


def get_operator_pg_connection_properties(secrets):
    """
    Return PG connection properties from a Secret written by the dbaas-operator.

    Used with declarative DBaaS, where the REST API must not be called for the Airflow database.
    Returns None if no such Secret exists.
    """
    for secret in secrets.items:
        data = secret.data or {}
        if "metadata.json" not in data or "connectionProperties.json" not in data:
            continue
        metadata = json.loads(base64.b64decode(data["metadata.json"]))
        if (
            metadata.get("type") == "postgresql"
            and metadata.get("classifier", {}).get("isServiceDb") == "true"
        ):
            properties = json.loads(base64.b64decode(data["connectionProperties.json"]))
            return (
                properties["host"],
                properties["username"],
                properties["password"],
                properties.get("name") or properties["dbName"],
            )
    return None


def get_pg_connection_properties(
    namespace, dbaas_secret="dbaas-connection-params-main", pg_secret="airflow-metadata"
):
    secrets = pl_lib.get_secrets(namespace)
    operator_properties = get_operator_pg_connection_properties(secrets)
    if operator_properties:
        return operator_properties
    for secret in secrets.items:
        if dbaas_secret == secret.metadata.name:
            dbaas_host = base64.b64decode(secret.data.get("DBAAS_HOST")).decode()
            headers = {"Content-Type": "application/json"}
            m2m_enabled = os.getenv("DBAAS_M2M_ENABLED", "").lower() not in (
                "",
                "false",
                "no",
            )
            if m2m_enabled:
                token = Path("/var/run/secrets/tokens/dbaas/token").read_text()
                headers["Authorization"] = f"Bearer {token}"
                auth = None
            else:
                try:
                    with open("/var/run/secrets/airflowtests/dbaas-user", "r") as file:
                        dbaas_user = file.read()
                except FileNotFoundError:
                    dbaas_user = base64.b64decode(
                        secret.data.get("DBAAS_USER")
                    ).decode()
                try:
                    with open(
                        "/var/run/secrets/airflowtests/dbaas-password", "r"
                    ) as file:
                        dbaas_password = file.read()
                except FileNotFoundError:
                    dbaas_password = base64.b64decode(
                        secret.data.get("DBAAS_PASSWORD")
                    ).decode()
                auth = (dbaas_user, dbaas_password)

            dbaas_pg_db_owner = base64.b64decode(
                secret.data.get("DBAAS_PG_DB_OWNER")
            ).decode()
            dbaas_pg_backup_disabled = base64.b64decode(
                secret.data.get("DBAAS_PG_BACKUP_DISABLED")
            ).decode()
            dbaas_pg_microservice_name = base64.b64decode(
                secret.data.get("DBAAS_PG_MICROSERVICE_NAME")
            ).decode()
            data = {
                "backupDisabled": dbaas_pg_backup_disabled,
                "type": "postgresql",
                "dbOwner": dbaas_pg_db_owner,
                "originService": dbaas_pg_microservice_name,
                "classifier": {
                    "namespace": namespace,
                    "scope": "service",
                    "microserviceName": dbaas_pg_microservice_name,
                    "isServiceDb": "true",
                },
            }
            response = requests.put(
                f"{dbaas_host}/api/v3/dbaas/{namespace}/databases",
                headers=headers,
                data=json.dumps(data),
                auth=auth,
            )
            if response.status_code == 201 or response.status_code == 200:
                connectionProperties = json.loads(response.content)[
                    "connectionProperties"
                ]
                return (
                    connectionProperties["host"],
                    connectionProperties["username"],
                    connectionProperties["password"],
                    connectionProperties["name"],
                )
            else:
                logging.error(
                    "[error_code=AIRFLOW-8301] Could not get DBAAS PG database. Response code: %s",
                    response.status_code,
                )
        elif pg_secret == secret.metadata.name:
            pg_connection = base64.b64decode(secret.data.get("connection")).decode()
            pattern = re.compile(
                r"([^:]+)://([^:]+):([^@]+)@([^:/]+):(\d+)/([^?]+)\?(\w+=[^&]+&?)*"
            )
            match = pattern.match(pg_connection)
            if match:
                conn = match.groups()
                pg_host = conn[3]
                pg_user = conn[1]
                pg_password = conn[2]
                pg_database = conn[5]
            else:
                logging.error(
                    "PG connection from secret does not match the expected pattern."
                )
            return pg_host, pg_user, pg_password, pg_database


def identify_dags_manager(name, namespace):
    deployment = pl_lib.get_deployment_entity(name, namespace)
    for container in deployment.spec.template.spec.containers:
        if container.name == "git-sync":
            for mount in container.volume_mounts:
                if mount.name == "rclone-config":
                    return "rclone"
            return "gitsync"
    return None
