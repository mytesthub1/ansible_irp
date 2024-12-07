import pytest

from aptlycli import AptlyCli, APTLY_PARSER, AptlyError


def test_exec_output_is_str():
    rc, out, err = AptlyCli().exec(["aptly", "mirror", "show", "foo"])
    assert type(out) is str


def test_mirror_output_parser():
    output = (
        "Name: exist_mirror\n"
        "Archive Root URL: http://mirror.servers.com/apt.servers.com/\n"
        "Distribution: ceph-octopus\n"
        "Components: main\n"
        "Architectures: amd64\n"
        "Download Sources: no\n"
        "Download .udebs: no\n"
        "Last update: never\n\n"
        "Information from release file:\n"
        "Architectures: amd64\n"
        "Codename: ceph-octopus\n"
        "Components: main\n"
        "Date: Mon, 25 Jan 2021 10:16:20 UTC\n"
        "Description:  Generated by aptly\n\n"
        "Label: . ceph-octopus\n"
        "Origin: ceph.com\n"
        "Suite: ceph-octopus\n"
    )
    assert type(AptlyCli().output_parser(output, APTLY_PARSER["mirror"])) is dict
    assert (
        AptlyCli().output_parser(output, APTLY_PARSER["mirror"])["Name"]
        == "exist_mirror"
    )
    assert (
        type(AptlyCli().output_parser(output, APTLY_PARSER["mirror"])["Components"])
        is list
    )
    assert (
        type(AptlyCli().output_parser(output, APTLY_PARSER["mirror"])["Architectures"])
        is list
    )


def test_release_info_parser():
    output = (
        "Name: exist_mirror\n"
        "Archive Root URL: http://mirror.servers.com/apt.servers.com/\n"
        "Distribution: ceph-octopus\n"
        "Components: main\n"
        "Architectures: amd64\n"
        "Download Sources: no\n"
        "Download .udebs: no\n"
        "Last update: never\n\n"
        "\n"
        "Information from release file:\n"
        "Architectures: amd64 arm64 armhf\n"
        "Codename: stable\n"
        "Components: main\n"
        "Date: Wed, 30 Jan 2019 16:56:52 UTC\n"
        "Description:  Generated by aptly\n"
        "\n"
        "Label: grafana stable\n"
        "Origin: grafana stable\n"
        "Suite: stable\n"
    )
    assert (
        AptlyCli().release_info_parser(output)["Date"]
        == "Wed, 30 Jan 2019 16:56:52 UTC"
    )


def test_mirror_dependencies():
    output = (
        "Mirror `mirror_repo2` was used to create following snapshots:\n"
        " * [mirror_init_repo2_snapshot]: Snapshot from mirror [mirror_repo2]: http://10.74.196.179/ xenial\n"
        " * [mirror_update_repo2_snapshot]: Snapshot from mirror [mirror_repo2]: http://10.74.196.179/ xenial\n"
    )
    assert list(AptlyCli().mirror_dependencies(output, "mirror_repo2")) == [
        "mirror_init_repo2_snapshot",
        "mirror_update_repo2_snapshot",
    ]


def test_snapshot_dependencies():
    output = (
        "Snapshot `mirror_init_repo1_snapshot` is published currently:\n"
        " * repo1/xenial (origin: . xenial) [amd64] publishes {main: [mirror_init_repo1_snapshot]: Snapshot from mirror [mirror_repo1]: http://10.74.196.189/ xenial}"
    )
    assert AptlyCli().snaphost_dependencies(output) == ("xenial", "repo1")


def test_is_fresh():
    desired_time_str = "2021-01-01"
    release_time_str = "Mon, 25 Jan 2021 10:16:20 UTC"
    assert AptlyCli().is_fresh(desired_time_str, release_time_str)


def test_snapshot_parser():
    output = (
        "Name: snapshot\n"
        "Created At: 2021-03-26 17:31:04 EET\n"
        "Description: Snapshot from mirror [test_mirror]: http://10.74.196.155/ xenial\n"
        "Number of packages: 1\n"
        "Sources:\n"
        "  test_mirror [repo]\n"
    )
    assert (
        AptlyCli().output_parser(output, APTLY_PARSER["snapshot"])["Created At"]
        == "2021-03-26 17:31:04 EET"
    )


def test_repo_parser():
    output = (
        "Name: stable\n"
        "Comment: Stable packages for project Foo\n"
        "Default Distribution: wheezy\n"
        "Default Component: main\n"
        "Number of packages: 10\n"
    )
    assert (
        AptlyCli().output_parser(output, APTLY_PARSER["repo"])["Default Component"]
        == "main"
    )
