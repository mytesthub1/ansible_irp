import pytest
import subprocess


@pytest.fixture(scope="module")
def clickhouse_dbs(any_host):
    return any_host.ansible("debug", f"var=clickhouse_central_dbs")[
        "clickhouse_central_dbs"
    ]


@pytest.fixture(scope="module")
def k8s_namespace(any_host):
    return any_host.ansible("debug", f"var=kubernetes_namespace")[
        "kubernetes_namespace"
    ]


def test_clickhouse_tables(clickhouse_dbs, k8s_namespace):
    for db in clickhouse_dbs:
        output = subprocess.check_output(
            [
                "kubectl",
                "-n",
                k8s_namespace,
                "exec",
                "-t",
                "deploy/clickhouse",
                "--",
                "clickhouse-client",
                "-h",
                "127.0.0.1",
                "-d",
                db["name"],
                "-q",
                "show tables",
            ]
        )
        assert len(output.splitlines()) > 0
