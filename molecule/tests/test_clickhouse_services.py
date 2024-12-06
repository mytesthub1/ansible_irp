import pytest

testinfra_hosts = ["ansible://clickhouse"]


def test_irp_rest_service(host):
    irp_rest_service = host.service("clickhouse-server")
    assert irp_rest_service.is_running
    assert irp_rest_service.is_enabled
