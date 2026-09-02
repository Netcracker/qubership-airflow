from datetime import datetime
import json
import logging
import time
import warnings
import urllib3

from airflow import DAG
from airflow.providers.common.sql.operators.sql import (
    SQLExecuteQueryOperator as BaseSQLExecuteQueryOperator,
    SQLValueCheckOperator as BaseSQLValueCheckOperator,
)
from airflow.providers.http.hooks.http import HttpHook

# Suppress InsecureRequestWarning logs across urllib3 and logging
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)


class TrinoHttpCursor:
    """Simulates a DB-API 2.0 cursor for SQLExecuteQueryOperator and SQLValueCheckOperator."""

    def __init__(self, data: list = None, columns: list = None):
        self._data = [tuple(row) if isinstance(row, list) else (row,) for row in (data or [])]
        self.description = [
            (col.get("name"), col.get("type"), None, None, None, None, None)
            for col in (columns or [])
        ]

    def fetchall(self):
        return self._data

    def fetchone(self):
        return self._data[0] if self._data else None

    def fetchmany(self, size=None):
        return self._data[:size] if size else self._data

    def close(self):
        pass


class TrinoHttpDbHook(HttpHook):
    """Executes Trino SQL via HTTP REST API adhering to DbApiHook interface."""

    def __init__(self, conn_id: str = "trino_default", **kwargs):
        super().__init__(method="POST", http_conn_id=conn_id, **kwargs)
        self.descriptions = []
        self.last_description = None

    def get_conn(self, headers=None):
        session = super().get_conn(headers)
        session.verify = False
        return session

    def get_first(self, sql: str, parameters=None):
        """Used by SQLValueCheckOperator and SQLCheckOperator."""
        res = self.run(sql, handler=lambda cur: cur.fetchone())
        return res

    def get_records(self, sql: str, parameters=None):
        """Used by standard SQL operators to retrieve all records."""
        return self.run(sql, handler=lambda cur: cur.fetchall())

    def run(self, sql: str, autocommit: bool = False, parameters=None, handler=None, **kwargs):
        conn = self.get_connection(self.http_conn_id)
        user = conn.login or "airflow"
        session = self.get_conn()

        schema_prefix = conn.schema or "https"
        port = f":{conn.port}" if conn.port else ""
        base_url = f"{schema_prefix}://{conn.host}{port}"

        headers = {
            "Content-Type": "text/plain",
            "X-Trino-User": user,
            "X-Trino-Catalog": "system",
            "X-Trino-Schema": "metadata",
        }

        # 1. Post statement
        response = session.post(
            f"{base_url}/v1/statement",
            data=sql.strip().encode("utf-8"),
            headers=headers,
            verify=False,
        )
        response.raise_for_status()
        data = response.json()

        # 2. Poll until complete and data is populated
        result_rows = []
        columns = []
        while "nextUri" in data:
            if "data" in data and data["data"]:
                result_rows.extend(data["data"])
            if "columns" in data and data["columns"]:
                columns = data["columns"]

            poll_resp = session.get(
                data["nextUri"],
                headers=headers,
                verify=False,
            )
            poll_resp.raise_for_status()
            data = poll_resp.json()
            time.sleep(0.3)

        # Collect final page of data/columns
        if "data" in data and data["data"]:
            result_rows.extend(data["data"])
        if "columns" in data and data["columns"]:
            columns = data["columns"]

        # 3. Check for errors
        if "error" in data:
            error_message = data["error"].get("message", "Unknown Trino error")
            raise RuntimeError(f"Trino Query Failed: {error_message}")

        # 4. Construct cursor
        cursor = TrinoHttpCursor(
            data=result_rows,
            columns=columns,
        )
        self.descriptions = [cursor.description]
        self.last_description = cursor.description

        if handler is not None:
            return handler(cursor)

        return cursor.fetchall()


class SQLExecuteQueryOperator(BaseSQLExecuteQueryOperator):
    def get_db_hook(self):
        return TrinoHttpDbHook(conn_id=self.conn_id)


class SQLValueCheckOperator(BaseSQLValueCheckOperator):
    def get_db_hook(self):
        return TrinoHttpDbHook(conn_id=self.conn_id)


def assert_row_contents(cursor):
    rows = cursor.fetchall()
    expected = [(1, "pipeline_started"), (2, "data_ingested"), (3, "pipeline_completed")]
    actual = [(r[0], r[1]) for r in rows]
    if actual != expected:
        raise ValueError(f"Data verification failed! Expected: {expected}, Got: {actual}")
    return rows


with DAG(
    dag_id="sql_trino_variable_catalog",
    start_date=datetime(2026, 8, 31),
    schedule=None,
    catchup=False,
) as dag:

    # 1. Clean up old catalog if present
    drop_existing_catalog = SQLExecuteQueryOperator(
        task_id="drop_existing_catalog",
        sql="DROP CATALOG IF EXISTS {{ var.json.trino_catalog_config.catalog_name }}",
        conn_id="trino_default",
    )

    # 2. Dynamically build CREATE CATALOG WITH (...) statement from Variable
    create_catalog = SQLExecuteQueryOperator(
        task_id="create_catalog",
        sql="""
        CREATE CATALOG {{ var.json.trino_catalog_config.catalog_name }} USING {{ var.json.trino_catalog_config.connector_type }}
        WITH (
            {%- for key, value in var.json.trino_catalog_config.catalog_properties.items() %}
            "{{ key }}" = '{{ value }}'{{ "," if not loop.last else "" }}
            {%- endfor %}
        )
        """,
        conn_id="trino_default",
    )

    # 3. Create Schema
    create_schema = SQLExecuteQueryOperator(
        task_id="create_schema",
        sql="CREATE SCHEMA IF NOT EXISTS {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}",
        conn_id="trino_default",
    )

    # 4. Drop table if left over from previous runs
    drop_table_initial = SQLExecuteQueryOperator(
        task_id="drop_table_initial",
        sql="DROP TABLE IF EXISTS {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}.{{ var.json.trino_catalog_config.table_name }}",
        conn_id="trino_default",
    )

    # 5. Create Fresh Table
    create_table = SQLExecuteQueryOperator(
        task_id="create_table",
        sql="""
        CREATE TABLE {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}.{{ var.json.trino_catalog_config.table_name }} (
            id BIGINT,
            event_name VARCHAR,
            created_at TIMESTAMP(6)
        )
        """,
        conn_id="trino_default",
    )

    # 6. Insert 3 fresh records
    insert_data = SQLExecuteQueryOperator(
        task_id="insert_data",
        sql="""
        INSERT INTO {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}.{{ var.json.trino_catalog_config.table_name }} (id, event_name, created_at)
        VALUES 
            (1, 'pipeline_started', current_timestamp),
            (2, 'data_ingested', current_timestamp),
            (3, 'pipeline_completed', current_timestamp)
        """,
        conn_id="trino_default",
    )

    # 7. Verify exact row count == 3
    verify_row_count = SQLValueCheckOperator(
        task_id="verify_row_count",
        sql="SELECT COUNT(*) FROM {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}.{{ var.json.trino_catalog_config.table_name }}",
        pass_value=3,
        conn_id="trino_default",
    )

    # 8. Verify actual row content
    verify_row_contents = SQLExecuteQueryOperator(
        task_id="verify_row_contents",
        sql="SELECT id, event_name FROM {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}.{{ var.json.trino_catalog_config.table_name }} ORDER BY id",
        handler=assert_row_contents,
        conn_id="trino_default",
    )

    # 9. Cleanup: Drop Table
    drop_table = SQLExecuteQueryOperator(
        task_id="drop_table",
        sql="DROP TABLE IF EXISTS {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}.{{ var.json.trino_catalog_config.table_name }}",
        conn_id="trino_default",
    )

    # 10. Cleanup: Drop Schema
    drop_schema = SQLExecuteQueryOperator(
        task_id="drop_schema",
        sql="DROP SCHEMA IF EXISTS {{ var.json.trino_catalog_config.catalog_name }}.{{ var.json.trino_catalog_config.schema_name }}",
        conn_id="trino_default",
    )

    # 11. Cleanup: Drop Catalog
    drop_catalog = SQLExecuteQueryOperator(
        task_id="drop_catalog",
        sql="DROP CATALOG IF EXISTS {{ var.json.trino_catalog_config.catalog_name }}",
        conn_id="trino_default",
    )

    (
        drop_existing_catalog
        >> create_catalog
        >> create_schema
        >> drop_table_initial
        >> create_table
        >> insert_data
        >> verify_row_count
        >> verify_row_contents
        >> drop_table
        >> drop_schema
        >> drop_catalog
    )