# Write the settings

Choose the settings of your first installation and keep them in a file, before any cluster exists.

## Run

See what [`nereus init`](../specs/cli/core.html#init-dry-run) would use, and where each value comes from; `--dry-run` creates nothing:

```bash
nereus init --dry-run --create-cluster
```

``` { .text .output title="output" }
SETTING            VALUE   SOURCE
target             k3d     default
create_cluster     true    flag
name               nereus  default
ingress_port       8080    default
installation_name  nereus  cluster name
profile            core    default
```

The table comes first; the two `helm upgrade --install` lines after it make the same install by hand.

Write the same settings to a file with [`nereus init --generate-file`](../specs/cli/core.html#init-generate-file); it prints the table again and the path it wrote:

```bash
nereus init --generate-file --create-cluster
```

Read the file:

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
    create: true
    name: nereus
---
apiVersion: core.getnereus.dev/v1alpha1
kind: Installation
metadata:
  name: nereus
spec:
  alias: nereus
```

## What you get

- Two documents: the `InitConfig`, how this machine builds the platform, and the `Installation`, whose name never changes ([spec 0006](../specs/0006-installation-identity.md)).
- The profile `core`: core and the tenancy Reef, nothing more until you add it ([Runtime and profiles](../concepts/runtime-and-profiles.md)).
- A plain `nereus init` reads this file; a flag wins over it, and an unknown key is an error.
- Nothing created yet: no cluster, no registry.

## Next

[Prepare the cluster](init.md) from these settings.
