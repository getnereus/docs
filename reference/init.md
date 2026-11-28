# What init does

What [`nereus init`](../specs/cli/core.html#init) does, step by step: the checks, the two Helm releases, the installation, the profile and the time. A first run is in [Prepare the cluster](../start/init.md).

## Prerequisites

`init` checks Docker (20.10.5 or newer, daemon running), k3d (5.0.0 or newer) and Helm (4.0.0 or newer) first. An older or missing one stops it before anything changes, naming the version it needs and where to get it.

Then it creates or reuses the local registry and the k3d cluster, and points the kube context at it. One registry serves every cluster `init` creates.

## Two Helm releases

From there `init` is two `helm upgrade --install`s and a wait ([#1055](https://github.com/getnereus/nereus/issues/1055)), each a release of the same name in `nereus-system`; `helm list --namespace nereus-system` shows both.

- **`kinds`**: the chart `nereus-reefs` installs the `Reef`, `Nereid`, `Mandate`, `ServiceLevelObjective` and `Installation` kinds and the `nereus-system` namespace.
- **`nereus`**: the chart `nereus` installs the Nereus API with the values from the settings.
- **`installation`**: reads back the [installation](installation.md) the chart created.

The kinds are templates, so every `helm upgrade` updates them; each is kept on `helm uninstall nereus-reefs`, with every object stored in it. [Install with Helm](../guides/operate/helm.md) installs the same charts without `init`.

## Core

The two charts also hold the profile core ([#1052](https://github.com/getnereus/nereus/issues/1052)): the tenancy Reef's kinds and admission policy, the `Reef` tenancy and Nereus's own tree, the Organization `getnereus` with its Project `nereus` and four Projects under it.

All of it is kept on `helm uninstall`, since a person's own Projects hang from the tree ([Know whose each thing is](../guides/access/tenancy.md)). On core alone, [`nereus status`](../specs/cli/core.html#status) lists `core` and `tenancy`, both `Ready`.

## The values file

`init` writes the values it passes to the chart `nereus` to `~/.config/nereus/values.yaml`, with the two `helm` commands that make the same install by hand in its header. `--dry-run` prints them and changes nothing.

``` { .text .output title="~/.config/nereus/values.yaml" }
image: localhost:5111/nereus-api:0.1.0-nereus-local
installation:
  name: nereus-local
  id: 1521c310-295d-49e9-a8ef-ed097f23fc46
  alias: nereus-local
profile: internal-developer-platform
thetis:
  image: localhost:5111/thetis-controller:0.1.0-nereus-local
  localRegistry: localhost:5111=k3d-nereus-registry.localhost:5000
nereids:
  registry: localhost:5111
  tag: 0.1.0-nereus-local
ingress:
  address: http://localhost:8080
```

## The images

The chart writes every Nereid's image into the `Profile`'s spec from `nereids`, and thetis installs them as written ([#1425](https://github.com/getnereus/nereus/issues/1425)). A checkout's `init` takes them from the local registry, where `docker push localhost:5111/...` puts them.

A CLI installed from a release installs the charts published at its own version, `oci://ghcr.io/getnereus/nereus/charts/nereus-reefs` and `.../nereus`, and the chart takes each image by digest from its `images.lock` ([#1785](https://github.com/getnereus/nereus/issues/1785)).

`NEREUS_NEREIDS_REGISTRY` or `NEREUS_NEREIDS_TAG` wins over both: a cluster that cannot reach the local registry takes every image from the registry `make promote NEREUS_PROMOTE_TARGET=registry.example.com/team/nereus` copied them to ([Publish on ghcr.io](../agent/publish.md)).

## Flux holds the releases

Once Flux `HelmRelease`s in `nereus-system` hold the releases `nereus-reefs` and `nereus`, Flux upgrades the charts with the `HelmRelease`'s values, and `init` leaves both alone:

``` { .text .output title="output" }
✓ kinds                     0.1s  release nereus-reefs held by HelmRelease nereus-reefs
✓ nereus                    0.0s  release nereus held by HelmRelease nereus
✓ installation              0.0s  kept nereus-local
✓ ready                     0.0s  the profile is HelmRelease nereus's
✓ public key                0.0s  the profile is HelmRelease nereus's
```

## The profile

`init` runs no step of the profile itself. The value `profile` makes the chart run [thetis](https://github.com/getnereus/nereus/tree/main/controllers/thetis), the installer Nereid, which installs the profile's Reefs, Nereids and Mandates in order ([The profiles](profiles.md)).

The step `ready` waits until each Nereid is Ready and prints how many and the slowest; each Nereid's time goes to the SLO report as a step of its own (`ready keycloak`).

The step `public key` prints the fingerprint of the secrets Reef's key.

## The time

Each step prints its time, and the total ends the run, even on failure (`✗`, then the error). On a terminal the lines are drawn live; elsewhere (CI, a script, a redirect, `NO_COLOR`) they print as each step ends ([#379](https://github.com/getnereus/nereus/issues/379)).

The total is measured against the target's SLO ([spec 0004](../specs/0004-init-time-slo.md)): green under 50%, yellow from 50%, orange from 75%, red past 100%. Missing it never stops `init`; `--check-slo` fails above it plus 10% ([Meet the time SLO](../guides/operate/slo.md)).

## Run it again

[`nereus init --yes`](../specs/cli/core.html#init) again reuses the registry and the cluster, upgrades both releases with the same values (revision 2), keeps the installation's identity, and finds every Nereid Ready at once, in seconds and `0% green`.

## The audit journal

Every `init` writes its entries to the installation's audit journal on this machine and prints its path: init started, each Reef and Nereid installed, init ended ([The audit journal](audit-journal.md)).
