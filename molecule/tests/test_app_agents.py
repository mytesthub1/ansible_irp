import testinfra
import requests
import pytest
import time
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


def get_api_host(host):
    return host.ansible("debug", f"var=irp_api_host")["irp_api_host"]


def login(hostvars, api_host):
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


def get_agents_status(host):
    hostvars = host.ansible.get_variables()
    api_host = get_api_host(host)
    api_endpoint = f"{api_host}/api/agent/health"
    token = login(hostvars, api_host)

    req = requests.get(
        api_endpoint, headers={"Authorization": f"Bearer {token}"}, verify=False
    )
    agents = req.json()
    return agents


def pytest_generate_tests(metafunc):
    if "agent" in metafunc.fixturenames:

        # copypaste from pytest_generate_tests from testinfra plugin
        host = list(
            testinfra.get_hosts(
                ["ansible://all"],
                connection=metafunc.config.option.connection,
                ssh_config=metafunc.config.option.ssh_config,
                ssh_identity_file=metafunc.config.option.ssh_identity_file,
                sudo=metafunc.config.option.sudo,
                sudo_user=metafunc.config.option.sudo_user,
                ansible_inventory=metafunc.config.option.ansible_inventory,
                force_ansible=metafunc.config.option.force_ansible,
            )
        )[0]

        agents = get_agents_status(host)
        metafunc.parametrize("agent", list(agents.keys()), ids=list(agents.keys()))


def delay_rerun(*args):
    time.sleep(5)
    return True


@pytest.mark.flaky(max_runs=24, rerun_filter=delay_rerun)
def test_agents_status(agent, any_host):
    agents_status = get_agents_status(any_host)
    assert agents_status[agent] == "Up"
