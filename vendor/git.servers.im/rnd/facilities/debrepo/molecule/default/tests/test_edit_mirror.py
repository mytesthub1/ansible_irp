testinfra_hosts = ["ansible://aptly_server"]


def test_mirror_has_no_packages(host):
    with host.sudo():
        cmd = host.check_output("aptly mirror show -with-packages repo1-xenial")
    assert "megapackage_1.1_all" not in cmd


def test_snapshot_has_package(host):
    from datetime import date

    current_date = date.today().isoformat()
    with host.sudo():
        cmd = host.check_output(
            f"aptly snapshot show -with-packages snapshot-repo1-xenial-{current_date}"
        )
    assert "megapackage_1.0_all" in cmd
