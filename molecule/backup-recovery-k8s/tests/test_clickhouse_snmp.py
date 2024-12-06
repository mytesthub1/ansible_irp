testinfra_hosts = ["ansible://clickhouse"]


def test_clickhouse_snmp_table_not_empty(host):
    output = host.check_output(
        'clickhouse-client -q "select count(*) from archive.snmp_location"'
    )
    assert int(output) >= 1
