import pytest

from aptlycli import AptlyCli, APTLY_PARSER, AptlyError

testinfra_hosts = ["ansible://aptly_source_repo?force_ansible=True"]


@pytest.fixture(scope="module")
def hostvars(host):
    return host.ansible.get_variables()


@pytest.fixture(scope="module")
def inventory(host):
    return host.backend.ansible_runner.inventory


@pytest.fixture(scope="module")
def source_repo_url(host, inventory):
    inventory_hostname = host.backend.get_hostname()
    other_host_vars = inventory["_meta"]["hostvars"][inventory_hostname]
    address = f"http://{other_host_vars['ansible_host']}/"
    return address


@pytest.fixture(scope="module")
def distribution(host, inventory):
    inventory_hostname = host.backend.get_hostname()
    other_host_vars = inventory["_meta"]["hostvars"][inventory_hostname]
    return other_host_vars["debrepo_repo_dist"]


@pytest.fixture(scope="function")
def mirror_name():
    yield "exist_mirror"
    AptlyCli().delete_mirror("exist_mirror", drop_dep=True)


@pytest.fixture(scope="function")
def mirror(mirror_name, source_repo_url, distribution):
    AptlyCli().create_mirror(
        mirror_name,
        source_repo_url,
        distribution,
        ["main"],
        ignore_signatures=True,
    )
    return mirror_name


@pytest.fixture(scope="function")
def snapshot_name(mirror):
    AptlyCli().update_mirror(mirror, ignore_signatures=True)
    yield "snap"
    AptlyCli().delete_snapshot("snap")


@pytest.fixture(scope="function")
def snapshot(snapshot_name, mirror):
    AptlyCli().create_snapshot(snapshot_name, mirror, ignore_signatures=True)
    return snapshot_name


@pytest.fixture(scope="function")
def publish_prefix(snapshot, distribution):
    yield "publish_prefix"
    AptlyCli().delete_publish(distribution, "publish_prefix")


@pytest.fixture(scope="function")
def publish(publish_prefix, snapshot, distribution):
    AptlyCli().create_publish_snapshot(
        snapshot,
        prefix=publish_prefix,
        distribution=distribution,
        architectures=["i386", "amd64"],
        skip_signing=True,
    )
    return publish_prefix


@pytest.fixture(scope="function")
def repo_name():
    yield "repo_name"
    AptlyCli().drop_repo("repo_name", drop_dep=True)


@pytest.fixture(scope="function")
def repo(repo_name, distribution):
    AptlyCli().create_repo(repo_name, distribution=distribution)
    return repo_name


@pytest.fixture(scope="function")
def publish_repo_prefix(repo, distribution):
    yield "publish_repo_prefix"
    AptlyCli().delete_publish(distribution, "publish_repo_prefix")


def test_get_mirror_absent():
    assert AptlyCli().get_mirror("no_mirror") is None


def test_update_no_exist_mirror():
    assert AptlyCli().update_mirror("no_mirror") is None


def test_delete_no_exist_mirror():
    assert AptlyCli().delete_mirror("no_mirror") is None


def test_create_mirror(mirror_name, source_repo_url, distribution):
    mirror = AptlyCli().create_mirror(
        mirror_name,
        source_repo_url,
        distribution,
        ["main"],
        ignore_signatures=True,
    )
    assert mirror["Name"] == mirror_name
    assert mirror["Last update"] == "never"


def test_update_mirror(mirror):
    assert AptlyCli().update_mirror(mirror, ignore_signatures=True)["Name"] == mirror


def test_get_exist_mirror(mirror):
    assert AptlyCli().get_mirror(mirror)["Name"] == mirror


def test_get_mirror_release_info(mirror):
    assert AptlyCli().get_mirror_release_info(mirror)["Components"] == "main"


def test_get_no_exist_snapshot():
    assert AptlyCli().get_snapshot("no_snap") is None


def test_create_snapshot(snapshot_name, mirror):
    assert (
        AptlyCli().create_snapshot(snapshot_name, mirror, ignore_signatures=True)[
            "Name"
        ]
        == snapshot_name
    )


def test_delete_snapshot(snapshot):
    assert AptlyCli().delete_snapshot(snapshot)["Name"] == snapshot
    assert AptlyCli().get_snapshot(snapshot) is None


def test_rename_snapshot(snapshot):
    AptlyCli().rename_snapshot(snapshot, "new_snap")
    assert AptlyCli().get_snapshot("new_snap")


def test_get_no_exist_publish():
    assert AptlyCli().get_publish("no_publish") is None


def test_get_publish(publish, snapshot_name, distribution):
    publish = AptlyCli().get_publish(distribution, prefix=publish)
    assert "snapshot" in publish["main"]
    assert publish["main"]["snapshot"] == snapshot_name


def test_create_publish_snap(publish_prefix, snapshot, distribution):
    publish = AptlyCli().create_publish_snapshot(
        snapshot,
        prefix=publish_prefix,
        distribution=distribution,
        architectures=["i386", "amd64"],
        skip_signing=True,
    )
    assert publish["Prefix"] == publish_prefix
    assert AptlyCli().get_publish(distribution, prefix=publish_prefix)


def test_delete_no_snapshot():
    assert AptlyCli().delete_snapshot("snap") is None


def test_raise_delete_mirror_with_snap(snapshot):
    """Raise error when try do drop mirror with snapshots"""
    with pytest.raises(AptlyError) as excinfo:
        AptlyCli().delete_mirror("exist_mirror")
    assert "ERROR: won't delete mirror with snapshots" in str(excinfo)


def test_drop_mirror_with_deb(publish, mirror):
    assert AptlyCli().delete_mirror(mirror, drop_dep=True)["Name"] == mirror


def test_drop_publish_snapshot(publish, snapshot, mirror):
    assert AptlyCli().delete_snapshot(snapshot, drop_dep=True)["Name"] == snapshot


def test_switch_publish(publish, mirror, distribution):
    AptlyCli().create_snapshot("update_snap", mirror, ignore_signatures=True)
    publish = AptlyCli().switch_publish(
        distribution, "update_snap", prefix=publish, skip_signing=True
    )
    assert "snapshot" in publish["main"]
    assert publish["main"]["snapshot"] == "update_snap"


def test_get_no_exist_repo():
    assert AptlyCli().get_repo("no_repo") is None


def test_create_repo(repo_name):
    repo = AptlyCli().create_repo(
        repo_name,
    )
    assert repo["Name"] == repo_name


def test_drop_repo(repo):
    assert AptlyCli().drop_repo(repo) is None
    assert AptlyCli().get_repo(repo) is None


def test_create_publish_repo(repo, distribution, publish_repo_prefix):
    publish = AptlyCli().create_publish_repo(
        repo,
        distribution=distribution,
        prefix=publish_repo_prefix,
        architectures=["amd64"],
        skip_signing=True,
    )
    assert AptlyCli().get_publish(distribution, prefix=publish_repo_prefix)
