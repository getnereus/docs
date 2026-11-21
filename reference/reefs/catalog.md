# The catalog reef

Every command that says what Nereus has: what runs, what is published, and whether it holds together.

## Commands

- [`nereus catalog apply`](../../specs/cli/reefs/catalog.html#workload-apply) One apply registers the repository
- [`nereus catalog workload create edge-cloudflare`](../../specs/cli/reefs/catalog.html#workload-create) create writes an entry from flags
- [`nereus catalog list`](../../specs/cli/reefs/catalog.html#workload-list) list searches by type
- [`nereus catalog delete openbao`](../../specs/cli/reefs/catalog.html#workload-delete) delete never touches what runs
- [`nereus catalog package create nereus`](../../specs/cli/reefs/catalog.html#package-apply) A Package says where it is published
- [`nereus catalog workload-type list`](../../specs/cli/reefs/catalog.html#workload-type-list) A type is a name plus answers
- [`nereus catalog check`](../../specs/cli/reefs/catalog.html#check) A contradiction fails, a gap points
- [`nereus catalog check`](../../specs/cli/reefs/catalog.html#check-contradiction) A contradiction fails the command

## Examples

### workload-apply

The files of catalog/ are the truth; Triton already exists and is imported the same way.

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

### workload-create

No --owner: the current owner is used and named in the output.

```bash
nereus catalog workload create edge-cloudflare \
  --type controller \
  --audience none \
  --repository https://github.com/getnereus/nereus \
  --ref branch=main \
  --path controllers/edge-cloudflare/ \
  --dry-run
```

``` { .text .output title="output" }
catalog/workloads/edge-cloudflare would be created (owner: Project/nereids, type: controller)
Nothing changed (--dry-run).
```

### workload-list

The catalog lists what it has, one row per Workload.

```bash
nereus catalog list \
  --type service
```

``` { .text .output title="output" }
WORKLOAD  OWNER           TYPE     AUDIENCE        STATUS
triton    Project/triton  service  agents, people  DeploymentNotFound
```

### workload-delete

The entry leaves the catalog; the Deployment, if any, stays.

```bash
nereus catalog delete openbao
```

``` { .text .output title="output" }
✓ catalog/workloads/openbao deleted
```

### package-apply

The same verbs, the kind in the path.

```bash
nereus catalog package create nereus \
  --owner project/core \
  --type cli \
  --registry pypi \
  --name nereus \
  --audience people \
  --audience programs \
  --ref branch=main \
  --path cli/ \
  --dry-run
```

``` { .text .output title="output" }
catalog/packages/nereus would be created (owner: Project/core, type: cli, registry: pypi)
Nothing changed (--dry-run).
```

### workload-type-list

The shapes of what runs, and what each one answers.

```bash
nereus catalog workload-type list
```

``` { .text .output title="output" }
TYPE         RUNS    TRIGGER         STATUS
controller   always  event           Ready
function     once    request, event  Ready
job          once    schedule        Ready
service      always  request         Ready
static-site  always  request         Ready
web-app      always  request         Ready
worker       always  event           Ready
```

### check

Nereus's own catalog today: no contradiction, and each gap with its issue.

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

### check-contradiction

An owner that does not exist, a registry the type does not allow, an audience missing.

```bash
nereus catalog check
```

``` { .text .output title="output" }
✗ catalog/workloads/api: owner Project/ghost does not exist
✗ catalog/packages/base-image: type image takes the registries oci, not pypi
✗ catalog/workloads/worker: audience is missing
3 contradictions, 0 gaps
```
