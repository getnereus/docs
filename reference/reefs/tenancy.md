# The tenancy Reef

Every command of the tenancy Reef: whose a thing is, as a tree of Organizations and Projects.

## Commands

- [`nereus reef apply tenancy`](../../specs/cli/reefs/tenancy.html#reef-apply) The tenancy Reef, with the kinds of this instance
- [`nereus status`](../../specs/cli/reefs/tenancy.html#status) No Nereid by design: the tenancy Reef is Ready with none
- [`nereus tenancy organization create example`](../../specs/cli/reefs/tenancy.html#organization-create) Another boundary: an Organization, the root of its tree
- [`nereus tenancy project create shop`](../../specs/cli/reefs/tenancy.html#project-create) A Project under the Organization, the path from the root
- [`nereus tenancy project create checkout`](../../specs/cli/reefs/tenancy.html#project-nested) A Project under another Project
- [`nereus tenancy project list`](../../specs/cli/reefs/tenancy.html#project-list) Each Project with its parent, the path only in get
- [`nereus tenancy project get checkout`](../../specs/cli/reefs/tenancy.html#project-get) One Project in full: its path and its boundary
- [`nereus tenancy apply`](../../specs/cli/reefs/tenancy.html#apply) Nereus's own tree, from files, parents before children
- [`nereus tenancy project delete shop`](../../specs/cli/reefs/tenancy.html#delete) A node with children waits for them
- [`nereus tenancy project delete shop`](../../specs/cli/reefs/tenancy.html#delete-cascade) A node and everything under it, deepest first
- [`nereus config set owner project/triton`](../../specs/cli/reefs/tenancy.html#config-owner) The current owner in the CLI's config, so --owner is optional

## Examples

### reef-apply

The CRDs of this instance, from its reefs/tenancy/.

```bash
nereus reef apply tenancy \
  --from-file reefs/tenancy/
```

``` { .text .output title="output" }
✓ core/reefs/tenancy created (tenancy.getnereus.dev/v1alpha1: organizations, projects)

Next steps:

  nereus tenancy organization create <organization>
```

### status

Right after a plain init: core, and the tenancy Reef every profile applies.

```bash
nereus status
```

``` { .text .output title="output" }
REEF     NEREID      VERSION  STATUS  AGE
core     nereus-api  0.1.0    Ready   2m
tenancy  -           -        Ready   2m
```

### organization-create

The kind with the boundary annotation takes no parent.

```bash
nereus tenancy organization create example
```

``` { .text .output title="output" }
✓ tenancy/organizations/example created

Next steps:

  nereus tenancy organization list
```

### project-create

A repository, under the Organization.

```bash
nereus tenancy project create shop \
  --parent organization/example \
  --repository https://github.com/example/shop
```

``` { .text .output title="output" }
✓ tenancy/organizations/example/projects/shop created

Next steps:

  nereus tenancy project list
```

### project-nested

A part of the shop, inside it.

```bash
nereus tenancy project create checkout \
  --parent project/shop
```

``` { .text .output title="output" }
✓ tenancy/organizations/example/projects/shop/projects/checkout created

Next steps:

  nereus tenancy project list
```

### project-list

One row per Project, in the tree's order.

```bash
nereus tenancy project list
```

``` { .text .output title="output" }
ORGANIZATION  PROJECT         REPOSITORY
example       shop            https://github.com/example/shop
example       shop/checkout   -
getnereus     nereus          https://github.com/getnereus/nereus
getnereus     nereus/core     -
getnereus     nereus/docs     -
getnereus     nereus/nereids  -
getnereus     nereus/triton   -
```

### project-get

The path climbs spec.parent to the root.

```bash
nereus tenancy project get checkout
```

``` { .text .output title="output" }
Name:        checkout
Kind:        Project
Path:        tenancy/organizations/example/projects/shop/projects/checkout
Parent:      project/shop
Boundary:    organization/example
Repository:  -
```

### apply

The Organization and the Projects of this repository, in tenancy/: init wrote them.

```bash
nereus tenancy apply \
  --from-file tenancy/
```

``` { .text .output title="output" }
tenancy/organizations/getnereus unchanged
tenancy/organizations/getnereus/projects/nereus unchanged
tenancy/organizations/getnereus/projects/nereus/projects/core unchanged
tenancy/organizations/getnereus/projects/nereus/projects/docs unchanged
tenancy/organizations/getnereus/projects/nereus/projects/nereids unchanged
tenancy/organizations/getnereus/projects/nereus/projects/triton unchanged

Next steps:

  nereus tenancy --help
```

### delete

A Project with a child is refused.

```bash
nereus tenancy project delete shop
```

``` { .text .output title="output" }
✗ tenancy/organizations/example/projects/shop has 1 child (checkout): delete it first, or it with it:
  nereus tenancy project delete shop --cascade --dry-run
  Nothing was changed.
```

### delete-cascade

First what it would delete.

```bash
nereus tenancy project delete shop \
  --cascade \
  --dry-run
```

``` { .text .output title="output" }
tenancy/organizations/example/projects/shop/projects/checkout deleted (dry run)
tenancy/organizations/example/projects/shop deleted (dry run)
```

### config-owner

The node the next commands are for.

```bash
nereus config set owner project/triton
```

``` { .text .output title="output" }
✓ config: owner = project/triton
```
