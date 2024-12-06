#! /usr/bin/env python3
import sys
from datetime import datetime
import requests
import json
import time
from typing import List, Optional
import argparse
import dateutil.parser


class ClickhouseBackupApi:
    CREATE_TIMEOUT = 60

    host: str

    def __init__(self, host: str) -> None:
        self.host = host

    def request(self, method: str, endpoint="", command="") -> requests.Response:
        if command:
            req_data = f'{{"command": "{command}"}}'
            endpoint = "backup/actions"
        else:
            req_data = {}
        try:
            req = requests.request(
                method, f"http://{self.host}/{endpoint}", data=req_data
            )
        except (
            requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
        ) as e:
            print("Request error: {}".format(e), file=sys.stderr)
            quit(1)
        req.raise_for_status()
        return req

    def get_backups(self) -> list:
        req = self.request("GET", "backup/list")
        records = req.content.splitlines()
        backups = []
        for record in records:
            backups.append(json.loads(record))
        return backups

    def wait_for_status(self, command: str, timeout: int) -> str:
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            status = self.get_command_status(command)
            if status == "in progress":
                time.sleep(1)
            else:
                break
        return status

    def get_status(self) -> list:
        req = self.request("GET", "backup/actions")
        status = []
        for line in req.content.splitlines():
            status.append(json.loads(line))
        return status

    def get_command_status(self, command: str) -> str:
        statuses = self.get_status()
        filtered_jobs = filter(lambda job: job["command"] == command, statuses)
        return next(filtered_jobs)["status"]

    def create_backup(self, backup_name: str) -> str:
        command = f"create {backup_name}"
        self.request("POST", command=command)
        return self.wait_for_status(command, self.CREATE_TIMEOUT)

    def upload_full_backup(self, backup_name: str) -> str:
        req = self.request("POST", command=f"upload {backup_name}")
        print(req.json())
        return req.json()["status"]

    def upload_increment_backup(
        self, backup_name: str, latest_remote_backup: str
    ) -> str:
        req = self.request(
            "POST",
            command=f"upload --diff-from-remote {latest_remote_backup} {backup_name}",
        )
        print(req.json())
        return req.json()["status"]


class ClickhouseBackup:
    api: ClickhouseBackupApi

    def __init__(self, api: ClickhouseBackupApi) -> None:
        self.api = api

    def create_backup(self, backup_name: str) -> str:
        return self.api.create_backup(backup_name)

    def get_latest_remote_backup(self) -> Optional[str]:
        sorted_backups = sorted(
            self.api.get_backups(), key=lambda k: k["created"], reverse=True
        )
        for backup in sorted_backups:
            if backup["location"] == "remote":
                return backup["name"]
        return None

    def get_latest_full_remote_backup(self) -> Optional[str]:
        sorted_backups = sorted(
            self.api.get_backups(), key=lambda k: k["created"], reverse=True
        )
        for backup in sorted_backups:
            if backup["location"] == "remote" and not backup["required"]:
                print(backup)
                # print(f"{backup['name']} {dateutil.parser.parse(backup['created'])}")
                return backup
        return None

    def check_running_uploads(self) -> bool:
        jobs_status = self.api.get_status()
        for job in jobs_status:
            if job["command"].startswith("upload") and job["status"] == "in progress":
                return True
        return False

    def check_running_create(self) -> bool:
        jobs_status = self.api.get_status()
        for job in jobs_status:
            if job["command"].startswith("create") and job["status"] == "in progress":
                return True
        return False

    def wait_for_create(self, backup_name):
        counter = 600
        while self.check_running_create() and counter > 0:
            time.sleep(1)
            counter -= 1
        jobs_status = self.api.get_status()
        for job in jobs_status:
            if job["command"].startswith(f"create {backup_name}"):
                return job["status"]

    def upload_backup(
        self, backup_name: str, force_full: bool, full_period_days: int
    ) -> str:
        make_full = force_full
        latest_remote_backup = self.get_latest_remote_backup()
        if not latest_remote_backup:
            make_full = True
        latest_full_remote_backup = self.get_latest_full_remote_backup()
        if latest_full_remote_backup:
            if (
                datetime.now()
                - dateutil.parser.parse(latest_full_remote_backup["created"])
            ).days > full_period_days:
                make_full = True
        else:
            make_full = True
        if make_full:
            return self.api.upload_full_backup(backup_name)
        else:
            return self.api.upload_increment_backup(backup_name, latest_remote_backup)


def print_help():
    print("Usage: clickhouse-backup-trigger.py host:port backup_prefix")


def main():
    detetime_now = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="Clickhouse server ip:port")
    parser.add_argument("backup_prefix", help="Backup name prefix")
    parser.add_argument("full_period_days", type=int, help="Make full backup in n days")
    parser.add_argument(
        "--force-full", help="Force to make full backup now", action="store_true"
    )
    args = parser.parse_args()
    host = args.host
    backup_name = f"{args.backup_prefix}_{detetime_now}"
    api = ClickhouseBackupApi(host)
    clickhouse_backup = ClickhouseBackup(api)
    if clickhouse_backup.check_running_uploads():
        print("Previous backup upload job is still active", file=sys.stderr)
        quit(0)
    clickhouse_backup.create_backup(backup_name)
    status = clickhouse_backup.wait_for_create(backup_name)
    if status != "success":
        print(f"Backup create error, status: {status}", file=sys.stderr)
        quit(2)
    status = clickhouse_backup.upload_backup(
        backup_name, args.force_full, args.full_period_days
    )
    if status != "acknowledged":
        print(f"Backup upload error, status: {status}", file=sys.stderr)
        quit(2)


if __name__ == "__main__":
    main()
