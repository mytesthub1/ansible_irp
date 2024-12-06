# aptly
## General
Management debian repositories

## Playbook usage examples
```shell script
ansible-playbook -i my_inventory.yaml aptly.yaml
```

## Inventory examples
```yaml
---

```

# Usage
## install aptly
```shell script
ANSIBLE_INVENTORY=$ANSIBLE_INVENTORY,aptly_server_inventory.yaml ansible-playbook install.yaml
```
For extract aptly public key add `gpg_public_report_path` variable to ansible host.
`gpg_public_report_path` - has to contain path and file name.

## create mirror
```shell script
ANSIBLE_INVENTORY=$ANSIBLE_INVENTORY,aptly_server_inventory.yaml ansible-playbook create_mirror.yaml
```

## mirror update and create temporary publish
```shell script
ANSIBLE_INVENTORY=$ANSIBLE_INVENTORY,aptly_server_inventory.yaml ansible-playbook temporary_publish.yaml
```

## switch temp snapshot to main publish
```shell script
ANSIBLE_INVENTORY=$ANSIBLE_INVENTORY,aptly_server_inventory.yaml ansible-playbook switch_temp_snapshot.yaml
```
