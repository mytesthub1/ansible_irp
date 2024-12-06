Security Levels
===============

Goal: To minimize exposure of IRP to unrelated addresses.

Broad design:
* External firewall layer - hardware firewall, static rules imposed by third party (network department)
* Internal firewall layer - host-level firewall
* Application-level includes ALCs and password protection by applications itself or their proxing services

All levels restrict only ingress traffic. Egress traffic is not regulated.

# Terminology

* Installation: all hosts under this playbooks administration, including their IP aliases. It's separate for production and staging environments.
* Peers: Stand-alone specific hosts (routers, etc) outside of administrative domain of those playbooks. Examples: routers under 
* External mirrors: set of services, provided by third party for installation (mirrors, software catalogues, etc).
* World: Hosts with unknown (dynamic) IP addresses
* rttgod group: set of hosts within installation for performing ICMP probing ('quality check')


## External firewall layer
External layer imposes a very broad (loose) ingress restrictions:

Permissions:
* Replies to all egress TCP traffic from installation IPs
* All protocols to all installation IPs are permitted for:
  * installation IPs (host IP + aliases)
  * VPN IPs
  * Jenkins IPs (whole range for gov cloud)
  * Additional whitelisted hosts
* External peers with a specific port to all installation IPs (including aliases)
* The world reply to ICMP requests for rttgod group

Everything which is not permitted is denied


## Internal firewall layer

Internal firewall layer repeats external firewall layer configuration

## Application layer

ACL layer provides much fine-grained ingress control:
* posgres restrict access (by `pg_hba` means) access to hosts in the group `dbsettings` plus all hosts in `postgres_additional_ips` list.
* clickhouse restrict RW access to groups `feedback` and `rtt` and provide wordwide RO access
* IRP  http (api & web-interface) provide authorized (password) access world-wide, and permits
    limited unauthorized access to some API calles to specific hosts within installation
* agents permits access to monitoring and API to their http API
* monitoring permits world-wide authorized (password) access to monitoring interface
* grafana (with access to clickhouse and postgres) provides authorized (password) worldwide access
* Each host provides authorized (keys) SSH worldwide access
* netflow group accept netflow from unathorized limited list of IP addresses
