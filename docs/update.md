Updates in this article means updates of packages of IRP and rttgod.

Normally all updates should be done through jenkins. For complicated cases manual run may be needed.

Simple update procedure:

```
ansible-playbook -i production irp-update.yaml --tags irp_update
```
(`--tags` is important!)

Key knobs to tune:
1) `--limit`: [rtt, snmp, app] - group scope
2) `--skip-tags`: [snmp, rtt, netflow, registration, etc]

Note: do not use --tags netflow, or --tags rtt (and other components as this will not only update
packages but also will perform all other configuration tasks for components).

The single inclusive  (mandatory) tag here is `irp_update`, all other tags should be used only in
`--skip-tags` context.

Examples
--------
```
ansible-playbook -i production/ irp-update.yaml --limit rtt --skip-tags netflow --tags irp_update
```

Update software rtt hosts, but do not update netflow-related components
