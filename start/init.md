# Prepare the cluster

Create a local k3d cluster and install core on it, from the settings you wrote.

## Run

`init` needs Docker 20.10.5 or newer with its daemon running, k3d 5.0.0 or newer and Helm 4.0.0 or newer; it checks them first and stops before changing anything when one is missing, naming the version it needs.

Prepare the cluster without being asked to confirm: [`nereus init`](../specs/cli/core.html#init)

```bash
nereus init --yes
```

It prints the settings table, then one line per step with its time: the prerequisites, the local registry, the cluster, the kinds, the Nereus API and the installation. It ends with `cluster ready in context k3d-nereus` and names `nereus status` as the next step.

## What you get

- A k3d cluster `nereus`, its local registry on `localhost:5111`, and your kube context pointing at it.
- Core: the kinds of the [model](../concepts/model.md), the [Nereus API](../concepts/nereus-api.md) and the tenancy Reef; no Nereid yet.
- The installation's identity: its name and a random id, which the first `init` also writes into the settings file, so a cluster recreated from it is the same installation.
- `~/.config/nereus/values.yaml`: the values `init` passed to Helm, to run the same install by hand.
- The total time, measured against the SLO: 8 minutes on k3d.

## Next

[Look around](look-around.md) the new installation.
