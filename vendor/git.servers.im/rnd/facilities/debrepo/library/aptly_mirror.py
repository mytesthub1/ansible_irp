#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text

# Ansible magic for module AnsiballZ
from ansible.module_utils.aptlycli import AptlyCli, AptlyError

CHANGED = True
NOT_CHANGED = False


class AptlyMirror(AnsibleModule):
    def create(self):
        if self.data:
            edited_mirror = self.aptly.edit_mirror(
                mirror_name=self.params["name"],
                archive_url=self.params["archive_url"],
                filter=self.params["filter"],
                architectures=self.params["architectures"],
                filter_with_deps=self.params["filter_with_deps"],
                ignore_signatures=self.params["ignore_signatures"],
            )
            if edited_mirror == self.data:
                return NOT_CHANGED
            return CHANGED
        if not self.check_mode:
            self.aptly.create_mirror(
                mirror_name=self.params["name"],
                archive_url=self.params["archive_url"],
                distribution=self.params["distribution"],
                components=self.params["components"],
                architectures=self.params["architectures"],
                filter=self.params["filter"],
                filter_with_deps=self.params["filter_with_deps"],
                ignore_signatures=self.params["ignore_signatures"],
            )
        return CHANGED

    @property
    def release_date(self):
        release_info = self.aptly.get_mirror_release_info(self.name)
        return release_info["Date"]

    @property
    def data(self):
        if not self._data:
            mirror = self.aptly.get_mirror(self.name)
            self._data = mirror
        return self._data

    def is_update_needed(self, mirror_state):
        if self.data:  # Evaluetin only exist mirror
            if self.params["update_policy"] == "never":  # Never update mirror policy
                return False
            elif self.params["update_policy"] == "always":  # Update mirror always
                return True
            elif self.params["update_policy"] == "once":  # Update mirror once
                if mirror_state:
                    return True
                if self.data["Last update"] == "never":
                    return True
                return False
            elif self.params["update_policy"] == "deadline":
                return self.is_up_to_deadline(self.params["update_deadline"])
        return False

    def is_up_to_deadline(self, deadline):
        if self.aptly.is_fresh(
            deadline, self.data["Last update"]
        ) and self.aptly.is_fresh(deadline, self.release_date):
            return True
        return False

    def update(self):
        if not self.check_mode:
            mirror_data = self.aptly.update_mirror(
                self.params["name"],
                ignore_signatures=self.params["ignore_signatures"],
            )
            self._data = None
            if self.params["update_policy"] == "deadline":
                if not self.is_up_to_deadline(self.params["update_deadline"]):
                    self.fail_json(msg=to_text("Mirror older then deadline time!"))
        return CHANGED

    def delete(self):
        mirror = self.data
        if not mirror:
            self.exit_json(changed=False)
        else:
            if not self.check_mode:
                mirror = self.aptly.delete_mirror(
                    self.name,
                    force=self.params["force_drop"],
                    drop_dep=self.params["drop_dependencies"],
                )
                self._data = None
            self.exit_json(changed=True, mirror=mirror)

    def run(self):
        try:
            self.aptly = AptlyCli(self.run_command)
        except ModuleNotFoundError as e:
            self.fail_json(msg=str(e))
        self.name = self.params["name"]
        self._data = None
        if self.params["state"] == "present":
            mirror_state = self.create()
            if self.is_update_needed(mirror_state):
                self.update()
                self.exit_json(changed=True, mirror=self.data)
            self.exit_json(changed=mirror_state, mirror=self.data)
        elif self.params["state"] == "absent":
            self.delete()


def main():
    module = AptlyMirror(
        argument_spec={
            "name": {"required": True},
            "archive_url": {},
            "state": {"choices": ["present", "absent"], "default": "present"},
            "distribution": {},
            "ignore_signatures": {"type": "bool", "default": False},
            "force_drop": {"type": "bool", "default": False},
            "drop_dependencies": {"type": "bool", "default": False},
            "components": {"type": "list", "elements": "str"},
            "architectures": {"type": "list", "elements": "str"},
            "filter": {"type": "str"},
            "filter_with_deps": {"type": "bool", "default": False},
            "update_policy": {
                "choices": ["never", "once", "always", "deadline"],
                "default": "once",
            },
            "update_deadline": {},
        },
        supports_check_mode=True,
        required_if=[
            ["update_policy", "deadline", ["update_deadline"]],
            ["filter_with_deps", True, ["filter"]],
        ],
    )

    try:
        module.run()
    except AptlyError as e:
        module.fail_json(msg=to_text(e))


if __name__ == "__main__":
    main()
