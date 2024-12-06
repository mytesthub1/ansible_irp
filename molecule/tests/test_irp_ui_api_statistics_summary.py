import pytest
import requests
from urllib3.exceptions import InsecureRequestWarning


@pytest.fixture(scope="module")
def hostvars(any_host):
    return any_host.ansible.get_variables()


@pytest.fixture(scope="module")
def api_host(any_host):
    return any_host.ansible("debug", f"var=irp_api_host")["irp_api_host"]


@pytest.fixture(scope="module")
def auth_token(api_host, hostvars):
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    req = requests.post(
        f"{api_host}/api/login",
        json={
            "email": hostvars["irp_api_user"],
            "password": hostvars["irp_api_password"],
        },
        verify=False,
    )
    req.raise_for_status()
    return req.json()["token"]


@pytest.mark.parametrize("summary_key", ["routers", "carriers", "locations"])
def test_irp_rest_config_summary(api_host, auth_token, summary_key):
    api_endpoint = f"{api_host}/api/application/statistics/summary"
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    req = requests.get(
        api_endpoint, headers={"Authorization": f"Bearer {auth_token}"}, verify=False
    )
    summary = req.json()
    assert summary[summary_key] > 0
