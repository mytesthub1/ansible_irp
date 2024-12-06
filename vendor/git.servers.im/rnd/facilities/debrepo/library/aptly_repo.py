#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

# Ansible magic for module AnsiballZ
from ansible.module_utils.aptlycli import AptlyCli


class AptlyRepo(AnsibleModule):
    def create(self):
        repo = self.aptly.get_repo(self.name)
        if not repo:
            if not self.check_mode:
                repo = self.aptly.create_repo(
                    self.name,
                    component=self.params["component"],
                    distribution=self.params["distribution"],
                    comment=self.params["comment"],
                )
            self.exit_json(changed=True, repo=repo)
        self.exit_json(changed=False, repo=repo)

    def drop(self):
        repo = self.aptly.get_repo(self.name)
        if repo:
            if not self.check_mode:
                self.drop_repo(
                    self.name,
                    force=self.params["force_drop"],
                    drop_dep=self.params["drop_dependencies"],
                )
            self.exit_json(changed=True, repo=repo)
        self.exit_json(changed=False)

    def run(self):
        try:
            self.aptly = AptlyCli(self.run_command)
        except ModuleNotFoundError as e:
            self.fail_json(msg=str(e))
        self.name = self.params["name"]
        if self.params["state"] == "present":
            self.create()
        else:
            self.drop()


def main():
    module = AptlyRepo(
        argument_spec={
            "name": {"required": True},
            "state": {"choices": ["present", "absent"], "default": "present"},
            "comment": {"type": "str"},
            "component": {"type": "str", "default": "main"},
            "distribution": {"type": "str"},
            "force_drop": {"type": "bool", "default": False},
            "drop_dependencies": {"type": "bool", "default": False},
        },
        supports_check_mode=True,
    )

    module.run()


if __name__ == "__main__":
    main()
