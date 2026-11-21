# The settings file

The file `~/.config/nereus/init.yaml` holds the settings of [`nereus init`](../specs/cli/core.html#init): written once with `--generate-file`, read by every plain `nereus init`.

A setting comes from its flag, else from the file, else from its default, in that order. An unknown key is an error.

## The file

Two YAML documents, written by `nereus init --generate-file`: an `InitConfig`, how to build the platform from this machine, and the `Installation`, as it goes to the cluster.

The first `init` writes the installation's `id` into the file, so a cluster recreated from it is the same installation.

```bash
cat ~/.config/nereus/init.yaml
```

``` { .text .output title="output" }
apiVersion: core.getnereus.dev/v1alpha1
kind: InitConfig
spec:
  profile: core
  ingressPort: 8080
  undercloud:
    create: false
    name: nereus
---
apiVersion: core.getnereus.dev/v1alpha1
kind: Installation
metadata:
  name: nereus
spec:
  alias: nereus
```

## InitConfig

Every key lives under `spec` of the `InitConfig` document.

| Key | Flag | Default |
|---|---|---|
| `profile` | `--profile` | `core` |
| `ingressPort` | `--ingress-port` | `8080` |
| `cloud` | `--target` | absent (`k3d`) |
| `undercloud.create` | `--create-cluster` | `false` |
| `undercloud.name` | `--name` | `nereus` |

`profile` is what `init` installs after core: `core` (nothing more), `internal-developer-platform` or `secrets` ([ADR 0014](../adr/0014-profiles.md), the profiles). A cloud target takes no profile yet.

`ingressPort` is the host port of the cluster's ingress gateway, from 1 to 65535, mapped on the loopback only to port 80 of the load balancer of a cluster `init` creates.

`cloud` names the Nereid of the cloud reef whose cloud the cluster bootstraps. It is absent for a local `k3d` cluster, and it cannot be `k3d`.

`undercloud.create` creates the cluster, or reuses it when it exists. `undercloud.name` is the name of the cluster to create.

## Installation

The second document names the installation, after the cluster unless `--installation-name` says otherwise ([spec 0006](../specs/0006-installation-identity.md)).

| Key | Meaning | Written by |
|---|---|---|
| `metadata.name` | The installation's name | `--installation-name` |
| `spec.alias` | The installation's alias | `init`, from the name |
| `spec.id` | The installation's UUID | the first `init` |
| `spec.naming.overrides` | Names that differ from the default | the author |

## Next

[Initialise the platform](../start/init.md) reads this file; the [Glossary](glossary.md) holds the words.
