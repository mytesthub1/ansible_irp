#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

# Ansible magic for module AnsiballZ
from ansible.module_utils.aptlycli import AptlyCli


class AptlyPublishRepo(AnsibleModule):
    def publish(self):
        publish = self.aptly.get_publish(
            self.params["distribution"], prefix=self.params["prefix"]
        )
        if not publish:
            if not self.check_mode:
                publish = self.aptly.create_publish_repo(
                    self.params["repo_name"],
                    prefix=self.params["prefix"],
                    distribution=self.params["distribution"],
                    component=self.params["component"],
                    architectures=self.params["architectures"],
                    skip_signing=self.params["skip_signing"],
                )
            self.exit_json(changed=True, publish=publish)
        self.exit_json(changed=False, publish=publish)

    def drop(self):
        publish = self.aptly.get_publish(
            self.params["distribution"], prefix=self.params["prefix"]
        )
        if not publish:
            self.exit_json(changed=False)
        else:
            if not self.check_mode:
                publish = publish = self.aptly.delete_publish(
                    self.params["distribution"], self.params["prefix"]
                )
            self.exit_json(changed=True, publish=publish)

    def run(self):
        self.aptly = AptlyCli(self.run_command)
        if self.params["state"] == "present":
            self.publish()
        elif self.params["state"] == "absent":
            self.drop()


def main():
    module = AptlyPublishRepo(
        argument_spec={
            "prefix": {"type": "str", "default": "."},
            "repo_name": {},
            "distribution": {"required": True},
            "component": {"default": "main"},
            "state": {
                "choices": ["present", "absent"],
                "default": "present",
            },
            "skip_signing": {"type": "bool", "default": False},
            "architectures": {"type": "list", "elements": "str"},
        },
        supports_check_mode=True,
        required_if=[
            ("state", "present", ["repo_name"], True),
            ("state", "absent", ["distribution"]),
        ],
    )

    module.run()


if __name__ == "__main__":
    main()
