# Say what Nereus has

Register what a repository says it runs and publishes, Workloads and Packages, from its files in `catalog/`, and check that it holds together: the files are the truth, the catalog Reef holds a copy.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`: it brings the catalog Reef with its Nereid `catalog`, which writes each entry's status and changes nothing an entry names.
- The [tenancy tree](../access/tenancy.md) the entries name as owners.
- A checkout with a `catalog/` folder, such as Nereus's own.

## Steps

### 1. Register the repository's catalog

[`nereus catalog apply`](../../specs/cli/reefs/catalog.html#workload-apply) takes the folder, types first, then the entries. An owner that does not exist, or a registry a type does not take, refuses the whole folder; a second run prints `unchanged`.

```bash
nereus catalog apply \
  --from-file catalog/
```

``` { .text .output title="output" }
✓ catalog/workloadtypes/controller created
✓ catalog/workloadtypes/service created
✓ catalog/packagetypes/cli created
✓ catalog/packagetypes/image created
✓ catalog/workloads/flux created (owner: Project/nereids, type: controller)
✓ catalog/workloads/keycloak created (owner: Project/nereids, type: controller)
✓ catalog/workloads/openbao created (owner: Project/nereids, type: controller)
✓ catalog/workloads/triton created (owner: Project/triton, type: service)
✓ catalog/packages/nereus created (owner: Project/core, type: cli, registry: pypi)
✓ catalog/packages/openbao-image created (owner: Project/nereids, type: image, registry: oci)

Next steps:

  nereus catalog check
```

### 2. Write a new entry as a file

[`nereus catalog workload create`](../../specs/cli/reefs/catalog.html#workload-create) with `--dry-run --output yaml` prints the file to commit in `catalog/`, then apply. `--audience` is required: `none` says nobody talks to it. Without `--owner`, the owner set by [`nereus config set owner`](../../specs/cli/reefs/tenancy.html#config-owner) is used.

```bash
nereus catalog workload create edge-cloudflare \
  --type controller \
  --audience none \
  --ref branch=main \
  --dry-run \
  --output yaml
```

``` { .text .output title="output" }
apiVersion: catalog.getnereus.dev/v1alpha1
kind: Workload
metadata:
  name: edge-cloudflare
spec:
  owner:
    kind: Project
    name: nereids
  type: controller
  source:
    ref:
      branch: main
```

### 3. Check that it holds together

[`nereus catalog check`](../../specs/cli/reefs/catalog.html#check) fails with `✗` on a contradiction, such as an owner whose Project was deleted; a gap prints `!` with its issue and passes. A lookup that did not run is a gap, never a pass.

```bash
nereus catalog check
```

``` { .text .output title="output" }
✓ tenancy: 1 organization, 5 projects, every owner resolves
✓ types: every workload type and package type resolves, every registry allowed
! catalog/workloads/triton: audience people, agents, no edge reef (#470)
! catalog/workloads/triton: uses nats, no messaging reef (#576)
! catalog/packages/nereus: not found on pypi
0 contradictions, 3 gaps
```

`make catalog-check` runs it on the repository's files before a pull request, with a cluster that has the tenancy Reef.

## Check it worked

[`nereus catalog list`](../../specs/cli/reefs/catalog.html#workload-list) shows each Workload with what the catalog Nereid found, `-` until its first pass.

```bash
nereus catalog list
```

``` { .text .output title="output" }
WORKLOAD  OWNER            TYPE        AUDIENCE        STATUS
catalog   Project/nereids  controller  -               Ready
flux      Project/nereids  controller  -               NereidNotInstalled
keycloak  Project/nereids  controller  -               NereidNotInstalled
openbao   Project/nereids  controller  -               NereidNotInstalled
triton    Project/triton   service     agents, people  DeploymentNotFound
```

## Next

- [Follow the golden path](golden-path.md): a Workload deployed into an Environment of its own.

## Learn more

- [The catalog Reef](../../reference/reefs/catalog.md): Workloads, Packages, their types, every status and command.
- [ADR 0016](../../adr/0016-catalog-reef.md): the files in the repository are the truth, the cluster holds a copy.
