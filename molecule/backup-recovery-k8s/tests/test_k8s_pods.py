import testinfra
from kubernetes import client, config
import time
import pytest

testinfra_hosts = ["ansible://all"]


class Pod:
    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name


def kube_namespace(host):
    return host.ansible("debug", "var=kubernetes_namespace")["kubernetes_namespace"]


def get_pods(host):
    config.load_kube_config()
    namespace = kube_namespace(host)
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(namespace, watch=False)
    pods = []
    for pod in ret.items:
        pods.append(Pod(namespace, pod.metadata.name))
    return pods


def get_pod_status(pod):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces()
    for p in ret.items:
        if p.metadata.namespace == pod.namespace and p.metadata.name == pod.name:
            for container in p.status.container_statuses:
                if container.ready:
                    return True
    return False


def pytest_generate_tests(metafunc):
    if "pod" in metafunc.fixturenames:

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

        pods = get_pods(hosts[0])
        metafunc.parametrize("pod", pods, ids=[pod.name for pod in pods])


def delay_rerun(*args):
    time.sleep(1)
    return True


@pytest.mark.flaky(max_runs=60, rerun_filter=delay_rerun)
def test_pod_is_ready(pod):
    assert get_pod_status(pod)
