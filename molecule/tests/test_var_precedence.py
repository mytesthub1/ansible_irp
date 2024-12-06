testinfra_hosts = ["ansible://all"]


def test_var_precendence(host):
    test_var_for_override = host.ansible.get_variables()["test_var_for_override"]
    assert test_var_for_override == "defined_in_inventory_file"
