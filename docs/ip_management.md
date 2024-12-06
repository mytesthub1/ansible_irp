There are two complicated IPs used in many places: monitoring_ip and api_external_ip.
They are defined at group_vars/all.yml and should be updated automatically.
This is done to reduce 'gather' stage for small pieces.

db.yaml should be run without --limit as it gather IPs to update pg_hba.conf for postgres
