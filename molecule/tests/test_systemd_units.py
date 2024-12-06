testinfra_hosts = ["ansible://all"]


def test_failed_systemd_units(host):
    assert (
        host.check_output(
            "systemctl list-units --state=failed --no-legend --no-pager"
        )
        == ""
    )
