# Know whose each thing is

Build the installation's tenancy tree, Organizations with Projects under them, so every Workload, Environment and database names who it belongs to.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md), in any profile: `nereus init` installs the tenancy Reef, its admission policy and the tree in `tenancy/`. The Reef has no Nereid.
- [Tenancy and access](../../concepts/tenancy-and-access.md) explains the tree and what an `owner` points at.

## Steps

### 1. Create an Organization

[`nereus tenancy organization create`](../../specs/cli/reefs/tenancy.html#organization-create) makes the top of a tree, its boundary.

```bash
nereus tenancy organization create example
```

``` { .text .output title="output" }
✓ tenancy/organizations/example created

Next steps:

  nereus tenancy organization list
```

### 2. Add a Project under it

[`nereus tenancy project create`](../../specs/cli/reefs/tenancy.html#project-create) needs a parent that exists; the line shows the full path. `--dry-run --output yaml` prints the object as `apply` takes it.

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

### 3. Nest a Project

A Project can sit under another [Project](../../specs/cli/reefs/tenancy.html#project-nested). A parent that does not exist is refused, and nothing is written.

```bash
nereus tenancy project create checkout --parent project/shop
```

``` { .text .output title="output" }
✓ tenancy/organizations/example/projects/shop/projects/checkout created

Next steps:

  nereus tenancy project list
```

### 4. Make a Project your default owner

[`nereus config set owner`](../../specs/cli/reefs/tenancy.html#config-owner) names the owner the next commands use when you give none.

```bash
nereus config set owner project/checkout
```

The kinds come from the installation, not the CLI: an installation whose `reefs/tenancy/` adds `Department` and `Squad` gets `nereus tenancy squad create` the same way. To keep the tree in files, [`nereus tenancy apply --from-file tenancy/`](../../specs/cli/reefs/tenancy.html#apply) writes parents before children.

## Check it worked

[`nereus tenancy project get`](../../specs/cli/reefs/tenancy.html#project-get) shows the full path and the boundary Organization.

```bash
nereus tenancy project get checkout
```

``` { .text .output title="output" }
Name:        checkout
Kind:        Project
Path:        tenancy/organizations/example/projects/shop/projects/checkout
Parent:      Project/shop
Boundary:    Organization/example
Repository:  -
```

## Clean up

!!! warning "Deletes everything under it"
    `--cascade` deletes every node under the Project, deepest first. Preview it with `--dry-run`.

```bash
nereus tenancy project delete shop --cascade
```

## Next

- [Authorize a team](authorization.md) on a Project of the tree.

## Learn more

- [The tenancy Reef](../../reference/reefs/tenancy.md): every command.
- [ADR 0015](../../adr/0015-tenancy.md): one tree of a fixed shape, with kinds from each installation.
