# Kamaji or vCluster for the environment reef

**Keep vCluster as the Nereid of today's Environments; register Kamaji as the candidate Nereid for an Environment, or a cluster, with nodes of its own.** The owner asked on 2026-11-07 whether [Kamaji](https://kamaji.clastix.io/) should replace vCluster. Facts come from Kamaji's [README](https://github.com/clastix/kamaji/blob/master/README.md) and [versioning page](https://github.com/clastix/kamaji/blob/master/docs/content/reference/versioning.md), opened on GitHub that day; `kamaji.clastix.io` was not reachable from the session.

## What each one gives

| Question | vCluster (the `vcluster` Nereid) | Kamaji |
|---|---|---|
| What it makes | A virtual cluster: control plane in a pod, tenant pods synced into a host namespace | A hosted control plane: `kube-apiserver`, scheduler and controller manager in pods (`TenantControlPlane`), state in a `Datastore` |
| Where the tenant's pods run | On the host cluster's own nodes | On worker nodes that join the control plane (kubeadm, Konnectivity); Kamaji does not create them, Cluster API does |
| What an Environment needs | A Helm release in `env-vcluster-<name>`: one chart, no machine | A control plane plus at least one node: a VM or a machine per Environment |
| Datastore | Embedded, in an `emptyDir` today | etcd, or MySQL, PostgreSQL or NATS through kine, one store shared by many control planes |
| Cluster API | | A [control plane provider](https://github.com/clastix/cluster-api-control-plane-provider-kamaji) |
| Licence and releases | Apache-2.0; the chart 0.37.5 pinned by SHA-256 | Apache-2.0; monthly `-edge` releases only; stable, semantically versioned artifacts only by subscription to CLASTIX since July 2024 |

## Why not swap

- **The use case is an Environment per agent on one k3d cluster** (#620, #568). vCluster runs it with no new machine; Kamaji would need a node per Environment, a VM or a kubeadm container, for the same result, with more to delete at expiry.
- **The scenes stay small:** `make scene-environment` makes two vclusters at once on the throwaway cluster; with Kamaji each would also need node containers of its own beside the throwaway cluster.
- **Releases:** only edge versions are open; Nereus pins what it installs, and pinning an edge release means following one every month.

## Where Kamaji fits

- **An Environment with its own nodes**, isolated at the node level: a second Nereid of the environment reef, chosen by Mandate, without changing the reef (ADR 0002).
- **Bootstrapping from a local seed** (#61): the clusters the platform creates in a cloud, with Cluster API, could get their control planes from Kamaji, many on one management cluster and one shared datastore (CloudNativePG, already a Nereid).

## Learn more

- [Kamaji README](https://github.com/clastix/kamaji/blob/master/README.md) and [releases and versions](https://github.com/clastix/kamaji/blob/master/docs/content/reference/versioning.md) (CLASTIX).
- [The vcluster Nereid](../reference/what-is-built.md) (#620, #633).
