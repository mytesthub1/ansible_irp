How to start
============
#### OpenStack credentials
To use automatic creation of test bench with Molecule, you need credentials
for Openstack. Use portal or os dashboard.

If you never run virtual machines in Portal, you may need to create one
manually (you can delete it afterwards) to force portal to create
all required networks.

Put `OS_*` credentials  into `rnd/user_scripts/your_local_username`.

See `rnd/user_scripts/example` for more information.

Run `source rnd/activate` before staring work and `source rnd/deactivate`
after you done. (Deactivate should run in the same shell as activate).

#### Molecule
Each molecule scenario has it own's `group_var` in `molecule/<scenario_name>/group_vars` directory. Tweak it if it's needed.

##### Examples
1. Run tests for the all scenarios:
    ```
    molecule test --all
    ``` 
2. Choose specific scenario:
    ```
    molecule test -s disable_motd_news
    ``` 
3. Do not destroy VMs:
    ```
    molecule test -s disable_motd_news --destroy never
    molecule login -s disable_motd_news -h <instance_name>
    ``` 

### Adding a new feature
If you want to add a new playbook to the project, please start with creation new molecule scenario (a new directory in `molecule/`).
This will give you the ability to run your playbook on a dynamic created environment:
```
molecule converge -s <new_scenario>
molecule destroy -s <scenario>
``` 

You can see all existing scenarios: `molecule matrix test`.

### Code placement
* If several of your scenarios have the same tests, move pytest/testinfra code to `tests/` (in the root of the project)
  and use symlinks of the required files in the molecule scenario test dirs
* Actual playbook (to test) should be called from `converge.yaml`
* Tests should be symlinked from `tests/` to `molecule/<scenario>/tests`
* Scenario description is in `molecule/<scenario>/molecule.yaml`

### Disabling concurrent pipelines
To limit CI with only one running pipeline at the same time set `CI_CONCURRENT_PIPELINES` variable to `false`.
  
### Getting access to CI VMs after failed job
To keep CI from cleaning up VMs, set `keep_vm` variable value equal the scenario name, whose VMs should not be removed 
before running pipelines (CI/CD->Pipelines->Run Pipeline).
To gain the access you need to use ssh key from the pipeline artifacts: 
`Artifacts\molecule_cache\molecule\generic\<scenario_name>\ssh_key`.

Please note, you need to cleanup those VMs by yourself.
