import subprocess
import re
import time

from datetime import timezone

# from dateutil.parser import parse

APTLY_PARSER = {
    "mirror": {
        "Name": lambda name: name,
        "Archive Root URL": lambda url: url,
        "Distribution": lambda dist: dist,
        "Components": lambda comp_list: list(comp_list.split(", ")),
        "Architectures": lambda arch: list(arch.split(", ")),
        "Download Sources": lambda flag: flag,
        "Download .udebs": lambda flag: flag,
        "Filter": lambda string: string,
        "Filter With Deps": lambda flag: flag,
        "Number of packages": lambda num: int(num),
        "Last update": lambda date: date,
    },
    "snapshot": {
        "Name": lambda name: name,
        "Created At": lambda date: date,
        "Description": lambda desc: desc,
        "Number of packages": lambda num: int(num),
    },
    "publish": {
        "Prefix": lambda prefix: prefix,
        "Distribution": lambda distr: distr,
        "Architectures": lambda arch: list(arch.split(" ")),
        "main": lambda source: {source.split(" ")[1][1:-1]: source.split(" ")[0]},
    },
    "repo": {
        "Name": lambda str: str,
        "Comment": lambda str: str,
        "Default Distribution": lambda str: str,
        "Default Component": lambda str: str,
        "Number of packages": lambda num: int(num),
    },
}


def to_commandline(cmd):
    return " ".join(cmd)


class AptlyError(Exception):
    pass


class AptlyCli:
    def __init__(self, run_command=None):
        from dateutil.parser import parse

        self.parse = parse
        if run_command:
            self.run_command = run_command
        else:
            self.run_command = self.exec

    def exec(self, cmd):
        res = subprocess.run(cmd, capture_output=True)
        return (res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8"))

    def output_parser(self, out, parser):
        parsed_dict = {}
        for line in out.split("\n"):
            if not line:  # stop parsing on the first empty line
                break
            if len(line.split(": ")) == 2:
                key, raw_val = map(str.strip, line.split(": "))
                try:
                    parsed_dict[key] = parser[key](raw_val)
                except KeyError:
                    raise AptlyError(f"Unknown key in aptly output: {key}")
        if not parsed_dict:
            return None
        return parsed_dict

    def release_info_parser(self, out):
        _, release_info = out.split("\nInformation from release file:\n")
        return dict(
            [l.split(": ", maxsplit=1) for l in filter(None, release_info.splitlines())]
        )

    def get_mirror(self, mirror_name):
        cmd = ["aptly", "mirror", "show", mirror_name]
        rc, out, err = self.run_command(cmd)
        start_time = time.time()
        while ("Status: In Update" in out) and (time.time() - start_time < 10):
            time.sleep(1)
            rc, out, err = self.run_command(cmd)
        return self.output_parser(out, APTLY_PARSER["mirror"])

    def get_mirror_release_info(self, mirror_name):
        cmd = ["aptly", "mirror", "show", mirror_name]
        rc, out, err = self.run_command(cmd)
        return self.release_info_parser(out)

    def get_repo(self, name):
        cmd = ["aptly", "repo", "show", name]
        rc, out, err = self.run_command(cmd)
        return self.output_parser(out, APTLY_PARSER["repo"])

    def is_fresh(self, desired_time_str, release_time_str):
        desired_datetime = self.parse(desired_time_str)
        release_datetime = self.parse(release_time_str)
        desired_datetime_tz = desired_datetime.replace(tzinfo=timezone.utc)
        delta = release_datetime - desired_datetime_tz
        if delta.total_seconds() < 0:
            return False
        return True

    def get_snapshot(self, snapshot_name):
        cmd = ["aptly", "snapshot", "show", snapshot_name]
        rc, out, err = self.run_command(cmd)
        return self.output_parser(out, APTLY_PARSER["snapshot"])

    def get_publish(self, distribution, prefix="."):
        cmd = ["aptly", "publish", "show", distribution, prefix]
        rc, out, err = self.run_command(cmd)
        return self.output_parser(out, APTLY_PARSER["publish"])

    def create_mirror(
        self,
        mirror_name,
        archive_url,
        distribution,
        components,
        architectures=None,
        filter=None,
        filter_with_deps=False,
        ignore_signatures=False,
    ):
        mirror = self.get_mirror(mirror_name)
        if not mirror:
            cmd = ["aptly", "mirror", "create"]
            if filter:
                cmd.append(f"-filter={filter}")
                if filter_with_deps:
                    cmd.append("-filter-with-deps")
            if ignore_signatures:
                cmd.append("-ignore-signatures")
            if architectures:
                arch = ",".join(architectures)
                cmd.append(f"-architectures={arch}")
            cmd += [
                mirror_name,
                archive_url,
                distribution,
            ]
            if components:
                cmd += [" ".join(components)]
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
        return self.get_mirror(mirror_name)

    def edit_mirror(
        self,
        mirror_name,
        archive_url=None,
        filter=None,
        filter_with_deps=False,
        architectures=None,
        ignore_signatures=False,
    ):
        mirror = self.get_mirror(mirror_name)
        if not mirror:
            raise AptlyError(f"Mirror {mirror_name} does not exist")
        cmd = ["aptly", "mirror", "edit"]
        if archive_url:
            cmd.append(f"-archive-url={archive_url}")
        if filter:
            cmd.append(f"-filter={filter}")
        if filter_with_deps:
            cmd.append("-filter-with-deps")
        if architectures:
            arch = ",".join(architectures)
            cmd.append(f"-architectures={arch}")
        if ignore_signatures:
            cmd.append("-ignore-signatures")
        cmd.append(mirror_name)
        rc, out, err = self.run_command(cmd)
        if rc != 0:
            raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
        return self.get_mirror(mirror_name)

    def delete_mirror(self, mirror_name, force=False, drop_dep=False):
        mirror = self.get_mirror(mirror_name)
        if not mirror:
            return None
        cmd = ["aptly", "mirror", "drop"]
        if force:
            cmd.append("-force")
        cmd.append(mirror_name)
        rc, out, err = self.run_command(cmd)
        if (
            rc == 1
            and f"Mirror `{mirror_name}` was used to create following snapshots" in out
        ):
            if drop_dep:
                for snapshot in self.mirror_dependencies(out, mirror_name):
                    self.delete_snapshot(snapshot, drop_dep=True)
                self.delete_mirror(mirror_name)
            else:
                raise AptlyError(err)
        elif rc != 0:
            raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
        return mirror

    def mirror_dependencies(self, output, mirror_name):
        # * [snapshot]: Snapshot from mirror [mirror_name]: http://10.74.196.179/ xenial
        parser = re.compile(r"\[(.*?)\]")
        for line in output.split("\n"):
            parse_res = parser.findall(line)
            if parse_res and parse_res[1] == mirror_name:
                yield parse_res[0]

    def update_mirror(self, mirror_name, ignore_signatures=False):
        mirror = self.get_mirror(mirror_name)
        if mirror:
            cmd = ["aptly", "mirror", "update"]
            if ignore_signatures:
                cmd.append("-ignore-signatures")
            cmd.append(mirror_name)
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
            return self.get_mirror(mirror_name)
        return None

    def create_snapshot(
        self,
        snapshot_name,
        src_name,
        ignore_signatures=False,
        update_mirror=True,
        from_src="mirror",
    ):
        if from_src == "mirror":
            if not self.get_mirror(src_name):
                raise AptlyError(f"Mirror {src_name} not exist")
        if from_src == "repo":
            if not self.get_repo(src_name):
                raise AptlyError(f"Repo {src_name} not exist")
        snap = self.get_snapshot(snapshot_name)
        if snap:
            return snap
        cmd = ["aptly", "snapshot", "create", snapshot_name, "from"]
        cmd.append(from_src)
        cmd.append(src_name)
        rc, out, err = self.run_command(cmd)
        if rc != 0:
            raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
        return self.get_snapshot(snapshot_name)

    def delete_snapshot(self, snapshot_name, force=False, drop_dep=False):
        snap = self.get_snapshot(snapshot_name)
        if snap:
            cmd = ["aptly", "snapshot", "drop"]
            if force:
                cmd.append("-force")
            cmd.append(snapshot_name)
            rc, out, err = self.run_command(cmd)
            if rc == 1 and f": [{snapshot_name}]" in out:
                if drop_dep:
                    disrtibution, prefix = self.snaphost_dependencies(out)
                    self.delete_publish(disrtibution, prefix)
                    self.delete_snapshot(snapshot_name)
                else:
                    raise AptlyError(err)
            elif rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
            return snap
        return None

    def rename_snapshot(self, old_name, new_name):
        snap = self.get_snapshot(old_name)
        if snap and self.get_snapshot(new_name) is None:
            cmd = ["aptly", "snapshot", "rename", old_name, new_name]
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
            return self.get_snapshot(new_name)
        elif self.get_snapshot(new_name):
            return None
        raise AptlyError()

    def snaphost_dependencies(self, output):
        disrtibution = ""
        prefix = ""
        for line in output.split("\n"):
            if "*" in line.split(" "):
                pref_dist = line.split(" ")[2].split("/")
                disrtibution = pref_dist.pop()
                prefix = "/".join(pref_dist)
        return disrtibution, prefix

    def create_publish_snapshot(
        self,
        snapshot_name,
        distribution=None,
        prefix=".",
        architectures=None,
        skip_signing=False,
    ):
        if not self.get_snapshot(snapshot_name):
            raise AptlyError(f"Snapshot {snapshot_name} not exist")
        publish = self.get_publish(distribution, prefix=prefix)
        if publish:
            return publish
        cmd = ["aptly", "publish", "snapshot"]
        if skip_signing:
            cmd.append("-skip-signing")
        if architectures:
            arch = ",".join(architectures)
            cmd.append(f"-architectures={arch}")
        if distribution:
            cmd.append(f"-distribution={distribution}")
        cmd += [snapshot_name, prefix]
        rc, out, err = self.run_command(cmd)
        if rc != 0:
            raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
        return self.get_publish(distribution, prefix=prefix)

    def switch_publish(
        self, distribution, new_snapshot, prefix=".", skip_signing=False
    ):
        if not self.get_snapshot(new_snapshot):
            raise AptlyError(f"Snapshot {new_snapshot} not exist")
        if self.get_publish(distribution, prefix=prefix):
            cmd = ["aptly", "publish", "switch"]
            if skip_signing:
                cmd.append("-skip-signing")
            cmd += [distribution, prefix, new_snapshot]
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
            return self.get_publish(distribution, prefix=prefix)
        else:
            raise AptlyError(f"Publish {prefix}/{distribution} not exist")

    def delete_publish(self, distribution, prefix="."):
        publish = self.get_publish(distribution, prefix=prefix)
        if publish:
            cmd = ["aptly", "publish", "drop", distribution, prefix]
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
            return publish
        return None

    def create_repo(self, name, component="main", distribution=None, comment=""):
        repo = self.get_repo(name)
        if not repo:
            cmd = [
                "aptly",
                "repo",
                "create",
                f"-component={component}",
                f"-comment={comment}",
            ]
            if distribution:
                cmd.append(f"-distribution={distribution}")
            cmd.append(name)
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
        return self.get_repo(name)

    def drop_repo(self, name, force=False, drop_dep=False):
        repo = self.get_repo(name)
        if repo:
            cmd = ["aptly", "repo", "drop"]
            if force:
                cmd.append("-force")
            cmd.append(name)
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(f"{err}\ncommand: {to_commandline(cmd)}")
        return None

    def create_publish_repo(
        self,
        repo_name,
        prefix=".",
        component="main",
        distribution=None,
        architectures=None,
        skip_signing=False,
    ):
        if not self.get_repo(repo_name):
            raise AptlyError(f"Repo {repo_name} not exist")
        publish = self.get_publish(distribution, prefix=prefix)
        if not publish:
            cmd = ["aptly", "publish", "repo"]
            if architectures:
                arch = ",".join(architectures)
                cmd.append(f"-architectures={arch}")
            if skip_signing:
                cmd.append("-skip-signing")
            cmd.append(f"-distribution={distribution}")
            cmd.append(f"-component={component}")
            cmd += [repo_name, prefix]
            rc, out, err = self.run_command(cmd)
            if rc != 0:
                raise AptlyError(err)
        return self.get_publish(distribution, prefix=prefix)
