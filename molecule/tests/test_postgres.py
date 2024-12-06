import pytest
import json

testinfra_hosts = ["ansible://postgres"]


def test_postgres_service(host):
    postgres_service = host.service("postgresql")
    assert postgres_service.is_running
    assert postgres_service.is_enabled


def test_postgres_mandatory_data(host):
    db_name = host.ansible.get_variables()["postgres_db_name"]
    with host.sudo("postgres"):
        output = host.check_output(f'psql -d { db_name } -c "\\dn"  -t --csv')
        schemas = [schema.split(",")[0] for schema in output.splitlines()]
        assert "mandatory_data" in schemas
