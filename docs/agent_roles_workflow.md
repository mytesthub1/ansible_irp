Workflow for agents
-------------------

Key properties:
* all agent roles does not have intricate knowledge of IRP internals
* As per statecalc v2 they query API for parameters. As per statecalc v2 that query gives IRP `station_name` and all `assigned_*` variables.
* Answer to that query may reject some of 'assigned' objects, in this case specific configuration is not made
* All roles support `mock_mode`, in which some stub reply is used from defaults. Mock reply serves two purposes: provide template for development of IRP APIs (what ansible expects to find in answer) and it provides a way to develop roles in absence of API server.

There are currently two reference implementations:
* irp-bgp-push (loop over `assigned_routers`)
* irp-snmp-collector (single agent on a single station with no assignations).
