import pytest
import requests
from urllib3.exceptions import InsecureRequestWarning


@pytest.fixture(scope="module")
def frontend_fqdn(any_host):
    return any_host.ansible("debug", f"var=frontend_fqdn")["frontend_fqdn"]


def test_irp_ui_api_fqdn_https(frontend_fqdn):

    api_endpoint = f"https://{ frontend_fqdn }/api/heartbeat"
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    req = requests.get(api_endpoint, verify=False)
    assert req.status_code == 200
