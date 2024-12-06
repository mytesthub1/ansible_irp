#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

# Ansible magic for module AnsiballZ
from ansible.module_utils.aptlycli import AptlyCli, AptlyError


class AptlySnapshot(AnsibleModule):
    def create(self):
        snapshot = self.aptly.get_snapshot(self.params["name"])
        if not snapshot:
            if not self.check_mode:
                snapshot = self.aptly.create_snapshot(
                    self.params["name"],
                    self.params["src"],
                    ignore_signatures=self.params["ignore_signatures"],
                    from_src=self.params["from_src"],
                )
            self.exit_json(changed=True, snapshot=snapshot)
        if self.params["newer_than"]:
            if self.params["from_src"] == "repo":
                self.fail_json(
                    msg=to_text(
                        "aptly_snapshot does not support `newer_than` for local repo"
                    )
                )
            mirror_update_date = self.aptly.get_mirror(self.params["src"])[
                "Last update"
            ]
            snapshot_created_date = snapshot["Created At"]
            if not self.aptly.is_fresh(snapshot_created_date, mirror_update_date):
                if not self.check_mode:
                    self.update()
                    self.exit_json(changed=True, snapshot=snapshot)
        self.exit_json(changed=False, snapshot=snapshot)

    def update(self):
        snapshot = self.aptly.get_snapshot(self.params["name"])
        if not snapshot:
            if not self.check_mode:
                self.create()
            self.exit_json(changed=True, snapshot=snapshot)
        else:
            if not self.check_mode:
                try:
                    self.aptly.delete_snapshot(
                        self.params["name"], drop_dep=self.params["drop_dependencies"]
                    )
                    self.create()
                except AptlyError as e:
                    self.fail_json(msg=to_text(e))
            self.exit_json(changed=True, snapshot=snapshot)

    def delete(self):
        snapshot = self.aptly.get_snapshot(self.params["name"])
        if not snapshot:
            self.exit_json(changed=False)
        else:
            if not self.check_mode:
                snapshot = self.aptly.delete_snapshot(self.params["name"])
            self.exit_json(changed=True, snapshot=snapshot)

    def run(self):
        self.aptly = AptlyCli(self.run_command)
        if self.params["state"] == "present":
            self.create()
        elif self.params["state"] == "absent":
            self.delete()
        elif self.params["state"] == "updated":
            self.update()
        else:
            self.fail_json(
                msg=to_text("Unknown state: %s" % repr(self.params["state"]))
            )


def main():
    module = AptlySnapshot(
        argument_spec={
            "name": {"required": True},
            "state": {
                "choices": ["present", "absent", "updated"],
                "default": "present",
            },
            "from_src": {
                "choices": ["mirror", "repo"],
                "default": "mirror",
            },
            "src": {},
            "ignore_signatures": {"type": "bool", "default": False},
            "newer_than": {},
            "drop_dependencies": {"type": "bool", "default": False},
        },
        supports_check_mode=True,
        required_if=[["state", "present", ["src"]]],
    )

    try:
        module.run()
    except AptlyError as e:
        module.fail_json(msg=to_text(e))


if __name__ == "__main__":
    main()
