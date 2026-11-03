import importlib
import json
import sys
import types

import pytest


@pytest.fixture
def backend_module(monkeypatch, tmp_path):
    """Import the backend with Airflow stubbed out and the operator mode switched on."""
    for name, attr in (
        ("airflow.secrets.base_secrets", "BaseSecretsBackend"),
        ("airflow.secrets.local_filesystem", "LocalFilesystemBackend"),
    ):
        module = types.ModuleType(name)
        setattr(module, attr, type(attr, (), {"__init__": lambda self, **kwargs: None}))
        monkeypatch.setitem(sys.modules, name, module)
    for name in ("airflow", "airflow.secrets"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setenv("LOCAL_FILESYSTEM_BACKEND", "false")
    monkeypatch.setenv("DBAAS_OPERATOR_ENABLED", "true")
    monkeypatch.setenv("DBAAS_MOUNTED_SECRETS_DIR", str(tmp_path))
    sys.modules.pop("qsdbaasintegration.dbaas_secrets_backend", None)
    return importlib.import_module("qsdbaasintegration.dbaas_secrets_backend")


@pytest.fixture
def backend(backend_module):
    instance = object.__new__(backend_module.DBAASSecretsBackend)
    instance.namespace = "airflow-ns"
    instance.qs_secrets_backend_properties = {}
    return instance


def write_secret(root, directory, db_type, properties):
    secret_dir = root / directory
    secret_dir.mkdir()
    (secret_dir / "metadata.json").write_text(json.dumps({"type": db_type}))
    (secret_dir / "connectionProperties.json").write_text(json.dumps(properties))


class FakeRestResponse:
    status_code = 200
    content = json.dumps({"connectionProperties": {"host": "rest"}})


def fail_rest(**kwargs):
    raise AssertionError("REST API must not be called in operator mode")


def test_returns_properties_of_secret_in_directory(backend, tmp_path):
    write_secret(tmp_path, "postgresql", "postgresql", {"host": "pg"})
    write_secret(tmp_path, "redis", "redis", {"host": "redis"})
    assert backend.get_mounted_properties("postgresql", "postgresql") == {"host": "pg"}
    assert backend.get_mounted_properties("redis", "redis") == {"host": "redis"}


def test_type_is_compared_case_insensitively(backend, tmp_path):
    write_secret(tmp_path, "postgresql", "PostgreSQL", {"host": "pg"})
    assert backend.get_mounted_properties("postgresql", "postgresql") == {"host": "pg"}


def test_secret_of_another_type_is_rejected(backend, tmp_path, caplog):
    write_secret(tmp_path, "postgresql", "redis", {"host": "redis"})
    assert backend.get_mounted_properties("postgresql", "postgresql") is None
    assert "AIRFLOW-8312" in caplog.text


def test_missing_directory_returns_none(backend, caplog):
    assert backend.get_mounted_properties("postgresql", "postgresql") is None
    assert "AIRFLOW-8311" in caplog.text


def test_incomplete_secret_returns_none(backend, tmp_path):
    (tmp_path / "postgresql").mkdir()
    (tmp_path / "postgresql" / "metadata.json").write_text(
        json.dumps({"type": "postgresql"})
    )
    assert backend.get_mounted_properties("postgresql", "postgresql") is None


def test_malformed_secret_returns_none(backend, tmp_path):
    (tmp_path / "postgresql").mkdir()
    (tmp_path / "postgresql" / "metadata.json").write_text("not json")
    (tmp_path / "postgresql" / "connectionProperties.json").write_text("{}")
    assert backend.get_mounted_properties("postgresql", "postgresql") is None


def test_operator_mode_pg_and_redis_use_fixed_directories(backend, tmp_path):
    write_secret(tmp_path, "postgresql", "postgresql", {"host": "pg"})
    write_secret(tmp_path, "redis", "redis", {"host": "redis"})
    backend.requests_with_correct_auth = fail_rest
    assert backend.get_pg_database() == {"host": "pg"}
    assert backend.get_redis_database() == {"host": "redis"}


def test_operator_mode_connection_directory_comes_from_connection_id(backend, tmp_path):
    write_secret(tmp_path, "postgres-test-conn-1", "postgresql", {"host": "conn"})
    backend.requests_with_correct_auth = fail_rest
    dbaas_data = {"type": "postgresql", "classifier": {"microserviceName": "x"}}
    assert backend.get_conn_from_dbaas(dbaas_data, "Postgres_Test_Conn_1") == {
        "host": "conn"
    }


def test_operator_mode_non_postgresql_connection_is_not_looked_up(
    backend, backend_module, monkeypatch
):
    monkeypatch.setattr(backend_module, "dbaas_conn_namespace_from_config", "false")
    backend.requests_with_correct_auth = lambda **kwargs: FakeRestResponse()
    dbaas_data = {"type": "mongodb", "classifier": {"microserviceName": "x"}}
    assert backend.get_conn_from_dbaas(dbaas_data, "some_conn") == {"host": "rest"}


def test_legacy_mode_does_not_read_mounted_secrets(
    backend_module, backend, monkeypatch, tmp_path
):
    write_secret(tmp_path, "postgresql", "postgresql", {"host": "mounted"})
    write_secret(tmp_path, "redis", "redis", {"host": "mounted"})
    monkeypatch.setattr(backend_module, "dbaas_operator_enabled", False)
    backend.requests_with_correct_auth = lambda **kwargs: FakeRestResponse()
    assert backend.get_pg_database() == {"host": "rest"}
    assert backend.get_redis_database() == {"host": "rest"}
