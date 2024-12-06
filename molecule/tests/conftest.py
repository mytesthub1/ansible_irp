import testinfra


def pytest_generate_tests(metafunc):
    if "any_host" in metafunc.fixturenames:
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
        metafunc.parametrize("any_host", [host], ids=[str(host)], scope="session")
