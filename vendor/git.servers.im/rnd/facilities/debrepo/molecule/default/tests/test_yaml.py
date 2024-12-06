import pytest


def test_yaml_temp_publish():
    import yaml

    with open("temp_publish_info.yaml") as file:
        vars_list = yaml.safe_load(file)
    assert vars_list["temporary_publisher_dist"] == "xenial"
