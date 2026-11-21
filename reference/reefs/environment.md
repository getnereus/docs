# The environment reef

Every command of the environment reef: an environment per agent, made by a Nereid, gone at its expiry.

## Commands

- [`nereus reef apply environment`](../../specs/cli/reefs/environment.html#setup) The environment reef, the vcluster Nereid and its default Mandate
- [`nereus environment create a`](../../specs/cli/reefs/environment.html#create) An environment of its own, for an hour
- [`nereus mandate create heavy`](../../specs/cli/reefs/environment.html#size) A bigger environment, for Nereus itself
- [`nereus environment list`](../../specs/cli/reefs/environment.html#list) Two agents, two environments, and the time each one has left
- [`nereus environment kubeconfig a > a.kubeconfig`](../../specs/cli/reefs/environment.html#kubeconfig) Its kubeconfig, read with your own credentials
- [`nereus environment delete a`](../../specs/cli/reefs/environment.html#delete) Deleting it removes the vcluster, then its namespace
- [`nereus environment create c`](../../specs/cli/reefs/environment.html#expires) At its expiry, its Nereid removes it by itself
- [`nereus environment create naxos`](../../specs/cli/reefs/environment.html#naxos) The kept cluster is the environment naxos, made through its own Mandate

## Examples

### setup

The vcluster Nereid requires the release reef: it asks it for the vcluster chart.

```bash
nereus reef apply environment
```

``` { .text .output title="output" }
✓ core/reefs/environment 0.1.0 created (environment.getnereus.dev/v1alpha1: environments)

Next steps:

  nereus environment --help
  nereus nereid apply <nereid> --reef environment
```

### create

Who it is for, and for how long.

```bash
nereus environment create a \
  --owner project/nereus \
  --expires 1h
```

``` { .text .output title="output" }
✓ environment/environments/a created (mandate: vcluster, nereid: vcluster)

Next steps:

  nereus environment get a --watch
  nereus environment kubeconfig a
```

### size

A Mandate whose Environments are of size platform.

```bash
nereus mandate create heavy \
  --reef environment \
  --nereid vcluster \
  --param size=platform
```

``` { .text .output title="output" }
✓ core/mandates/heavy created (reef: environment, nereid: vcluster)

Next steps:

  nereus mandate list
```

### list

Its Nereid, its state, and when it goes.

```bash
nereus environment list
```

``` { .text .output title="output" }
ENVIRONMENT  OWNER           NEREID    STATUS  SIZE   EXPIRES
a            Project/nereus  vcluster  Ready   small  58m
b            Project/nereus  vcluster  Ready   small  58m
```

### kubeconfig

```bash
kubectl get namespaces \
  --kubeconfig a.kubeconfig
```

``` { .text .output title="output" }
NAME              STATUS   AGE
default           Active   42s
kube-node-lease   Active   42s
kube-public       Active   42s
kube-system       Active   42s
```

### delete

Waits until its Nereid removed what it made.

```bash
nereus environment delete a
```

``` { .text .output title="output" }
2026-10-30T19:40:35Z  … release    Deleting release/releases/env-a: Flux uninstalls the vcluster chart.
2026-10-30T19:40:36Z  · namespace  Deleting the namespace env-vcluster-a.
2026-10-30T19:40:56Z  ✓ release    release/releases/env-a deleted.
2026-10-30T19:40:56Z  … namespace  Deleting the namespace env-vcluster-a.
✓ environment/environments/a deleted

Next steps:

  nereus environment list
```

### expires

An environment for one minute.

```bash
nereus environment create c \
  --owner project/nereus \
  --expires 1m
```

``` { .text .output title="output" }
✓ environment/environments/c created (mandate: vcluster, nereid: vcluster)

Next steps:

  nereus environment get c --watch
  nereus environment kubeconfig c
```

### naxos

The CLI's first setup registers the kept k3d cluster; vcluster stays the default.

```bash
nereus environment create naxos \
  --owner project/nereus \
  --mandate local
```

``` { .text .output title="output" }
✓ environment/environments/naxos created (mandate: local, nereid: k3d)

Next steps:

  nereus environment get naxos --watch
```
