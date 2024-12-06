testinfra_hosts = ["ansible://aptly_server"]


def test_mirror_has_package(host):
    with host.sudo():
        cmd = host.check_output("aptly mirror show -with-packages repo1-xenial")
    assert "megapackage_1.1_all" in cmd


def test_mirror_has_not_filtering_package(host):
    with host.sudo():
        cmd = host.check_output("aptly mirror show -with-packages repo1-xenial")
    assert "megapackage_1.0_all" not in cmd
