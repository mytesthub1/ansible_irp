testinfra_hosts = ["ansible://app", "ansible://stations"]


def test_irp_journal_non_empty(host):
    assert host.check_output("journalctl --namespace irp --no-pager -n 1 -o json")
