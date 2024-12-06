import testinfra
from kubernetes import client, config

testinfra_hosts = ["ansible://all"]


def kube_namespace(host):
    return host.ansible("debug", f"var=kubernetes_namespace")["kubernetes_namespace"]


def get_containers_statuses(host):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(kube_namespace(host), watch=False)
    containers_statuses = {}
    for pod in ret.items:
        for container in pod.status.container_statuses:
            containers_statuses[container.name] = container
    return containers_statuses


def pytest_generate_tests(metafunc):
    if "container_status" in metafunc.fixturenames:

        # copypaste from pytest_generate_tests from testinfra plugin
        hosts = testinfra.get_hosts(
            testinfra_hosts,
            connection=metafunc.config.option.connection,
            ssh_config=metafunc.config.option.ssh_config,
            ssh_identity_file=metafunc.config.option.ssh_identity_file,
            sudo=metafunc.config.option.sudo,
            sudo_user=metafunc.config.option.sudo_user,
            ansible_inventory=metafunc.config.option.ansible_inventory,
            force_ansible=metafunc.config.option.force_ansible,
        )

        containers = get_containers_statuses(hosts[0])
        metafunc.parametrize(
            "container_status", list(containers.values()), ids=list(containers.keys())
        )


def test_container_started(container_status):
    assert container_status.started == True


def test_container_ready(container_status):
    assert container_status.ready == True
