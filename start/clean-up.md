# Clean up

Delete the Nereid, then the cluster and its local registry, so the machine is as it was before `init`.

## Run

Delete the Nereid: [`nereus nereid delete`](../specs/cli/core.html#nereid-delete)

```bash
nereus nereid delete reference-release
```

``` { .text .output title="output" }
✓ core/nereids/reference-release deleted
```

Delete the cluster, with everything `init` installed in it:

```bash
k3d cluster delete nereus
```

Delete the local registry `init` created next to it:

```bash
k3d registry delete k3d-nereus-registry.localhost
```

## What you get

- The `release` command group goes with the Nereid, and its Deployment, Service and identity with it; the Reef stays until the cluster goes.
- No cluster and no registry left.
- The settings stay in `~/.config/nereus/`: a next `nereus init --yes` creates a cluster that is the same installation, with the same id. Delete that folder to start from nothing.

## Next

Learn the words behind what you ran: [Reef, Nereid and Mandate](../concepts/model.md).
