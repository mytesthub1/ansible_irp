#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

# Ansible magic for module AnsiballZ
from ansible.module_utils.aptlycli import AptlyCli

INVALID_CHARACTERS = ["/"]


class AptlyPublishSnapshot(AnsibleModule):
    def publish(self):
        publish = self.aptly.get_publish(
            self.params["distribution"], prefix=self.params["prefix"]
        )
        if not publish:
            distribution = self.params["distribution"]
            if any(ext in distribution for ext in INVALID_CHARACTERS):
                for char in INVALID_CHARACTERS:
                    distribution = distribution.replace(char, "")
                self.warn(
                    f"Distribution has invalid character and was changed to {distribution}"
                )
            if not self.check_mode:
                publish = self.aptly.create_publish_snapshot(
                    self.params["snapshot_name"],
                    distribution=distribution,
                    prefix=self.params["prefix"],
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

    def snapshot_switch(self):
        publish = self.aptly.get_publish(
            self.params["distribution"], prefix=self.params["prefix"]
        )
        if publish is None:
            self.publish()
        elif "snapshot" in publish["main"] and publish:
            if publish["main"]["snapshot"] == self.params["snapshot_name"]:
                self.exit_json(changed=False, publish=publish)
            else:
                if not self.check_mode:
                    publish = self.aptly.switch_publish(
                        self.params["distribution"],
                        self.params["snapshot_name"],
                        prefix=self.params["prefix"],
                        skip_signing=self.params["skip_signing"],
                    )
                self.exit_json(changed=True, publish=publish)
        else:
            self.fail_json(msg=to_text("The publish made not from snapshot"))

    def run(self):
        self.aptly = AptlyCli(self.run_command)
        if not self.params["prefix"]:
            self.fail_json(msg=to_text("Prefix cannot be empty"))
        if self.params["state"] == "present":
            self.publish()
        elif self.params["state"] == "absent":
            self.drop()
        elif self.params["state"] == "switched":
            self.snapshot_switch()
        else:
            self.fail_json(
                msg=to_text("Unknown state: %s" % repr(self.params["state"]))
            )


def main():
    module = AptlyPublishSnapshot(
        argument_spec={
            "distribution": {"required": True},
            "snapshot_name": {},
            "state": {
                "choices": ["present", "absent", "switched"],
                "default": "present",
            },
            "skip_signing": {"type": "bool", "default": False},
            "prefix": {"required": True},
            "architectures": {"type": "list", "elements": "str"},
        },
        supports_check_mode=True,
        required_if=[("state", ("present", "switched"), "snapshot_name", True)],
    )

    module.run()


if __name__ == "__main__":
    main()
