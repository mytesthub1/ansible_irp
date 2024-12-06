import pytest
import requests
import os

testinfra_hosts = ["ansible://aptly_repo_server"]


@pytest.fixture(scope="module")
def api_host(host):
    return host.ansible.get_variables()["ansible_host"]


@pytest.fixture(scope="module")
def api_port(host):
    return host.ansible.get_variables().get("aptly_api_port", 8080)


def test_aptly_api(api_host, api_port):
    api_user = os.environ.get("APTLY_API_USER")
    api_password = os.environ.get("APTLY_API_PASSWORD")
    if not (api_user or api_password):
        pytest.fail(
            "Enviroment variables APTLY_API_USER and APTLY_API_PASSWORD must be defined"
        )
    api_endpoint = f"http://{api_user}:{api_password}@{api_host}:{api_port}/api/version"
    req = requests.get(api_endpoint)
    assert req.status_code == 200


def test_aptly_api_noauth(api_host, api_port):
    api_endpoint = f"http://{api_host}:{api_port}/api/version"
    req = requests.get(api_endpoint)
    assert req.status_code == 401
