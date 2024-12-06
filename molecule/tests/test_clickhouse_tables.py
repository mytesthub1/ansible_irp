import pytest

testinfra_hosts = ["ansible://clickhouse"]


@pytest.fixture(scope="module")
def clickhouse_dbs(host):
    return host.ansible("debug", f"var=clickhouse_central_dbs")[
        "clickhouse_central_dbs"
    ]


def test_clickhouse_tables(host, clickhouse_dbs):
    for db in clickhouse_dbs:
        if db["host"] == host.ansible.get_variables()["inventory_hostname"]:
            output = host.check_output(
                f'clickhouse-client -h 127.0.0.1 -d {db["name"]} -q "show tables"'
            )
            assert len(output) >= 1
