import psycopg2
import subprocess
import pytest
from datetime import datetime, timezone


@pytest.fixture(scope="module")
def hostvars(any_host):
    return any_host.ansible.get_variables()


@pytest.fixture(scope="module")
def last_optimization_time(hostvars, any_host):
    namespace = any_host.ansible("debug", "var=kubernetes_namespace")[
        "kubernetes_namespace"
    ]
    proc = subprocess.Popen(
        [
            "kubectl",
            "-n",
            namespace,
            "port-forward",
            "svc/postgres-cluster-r",
            "5432:5432",
        ],
        stdout=subprocess.PIPE,
    )
    # Waiting for port-forward
    for line in proc.stdout:
        if line.startswith(b"Forwarding from 127.0.0.1"):
            break

    database = hostvars["postgres_db_name"]
    user = hostvars["postgres_db_username"]
    password = any_host.ansible("debug", f"var=postgres_db_password")[
        "postgres_db_password"
    ]
    conn = psycopg2.connect(
        host="127.0.0.1", port=5432, database=database, user=user, password=password
    )
    cursor = conn.cursor()
    cursor.execute(
        "select to_timestamp(publication_ts) from capture.optimization_event order by publication_ts desc limit 1"
    )
    last_optimization_time = cursor.fetchone()[0]

    proc.terminate()

    return last_optimization_time


@pytest.mark.parametrize("age", [24 * 60 * 60])
def test_last_optimization_time(last_optimization_time, age):
    time_delta = datetime.now(timezone.utc) - last_optimization_time
    assert time_delta.total_seconds() < age
