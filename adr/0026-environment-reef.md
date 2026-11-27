# 0026. The environment Reef: an Environment is only the request, and the kept cluster is nereus

!!! note "In short"
    The `environment` Reef has one kind, `Environment`, which is only the request; the cluster kept for it is `nereus`. Status: Proposed (2026-11-14).

**Status:** Proposed (2026-11-14)

## Context

The `Environment` kind and the `vcluster` Nereid exist (#620), installed by the `internal-developer-platform` profile (#827), and a release `Target` with an `environmentRef` delivers into that Environment's cluster through the `flux` Nereid (#828). No ADR records the Reef: what a person writes, what a Nereid writes, and how the release Reef finds where to deliver. ADR 0010 (Reefs at runtime) says only that the environment "knows the cluster and its credentials".

The kept k3d cluster, `k3d-nereus`, runs Triton and serves as production, but no Nereid knows it: #556 (two local k3d clusters at most) calls it production, and #159 and #160 (the always-on environment deployed from main) call it `live`. ADR 0017 (resource Reefs) is Accepted and settles how a request picks its Mandate; this Reef is its first user with two Nereids. #568 asked for the refinement, in the design session of 2026-10-30 on the catalog (#559), the tenancy (#21) and the resource Reefs (#560).

## Decision

**An `Environment` is only the request.** The Reef is `environment.getnereus.dev/v1alpha1`, with one cluster-scoped kind, `Environment`. One writer per field (ADR 0005):

| Field | Writer | What it holds |
|---|---|---|
| `spec.owner` | the person | who it is for, `{kind, name}` in the tenancy tree (ADR 0015) |
| `spec.region` | the person | optional, where it should run |
| `spec.expires` | the person | optional, a duration after which it goes away |
| `spec.mandate` | the person | optional, the Mandate to go through, by name |
| `status.nereid`, `status.mandate`, `status.phase` | the Nereid | who made it, through which Mandate, and its state |
| `status.expiresAt` | the Nereid | `creationTimestamp` plus `spec.expires` |
| `status.kubernetes.context`, `status.kubernetes.secretRef` | the Nereid | how to reach a Kubernetes environment: a context name and a reference to the Secret holding its kubeconfig |
| `status.kubernetes.namespaces` | the Nereid | where its Workloads' pods run in the cluster that hosts them, so the metrics Reef reads them there: a vcluster's host namespace; for `nereus`, the namespaces of the Targets that deliver into it (amended by the owner, 2026-11-26, #2305) |

`spec` names no technology (ADR 0002, the model): the person never names a cluster type, a provider or a Tool. A kept cluster, a vcluster, Cloud Run, Azure Container Apps or AWS Fargate are each a Nereid behind a Mandate, and each writes what it made in `status`. Credentials are never inline: `secretRef` points at a Kubernetes Secret today, and the secrets Reef (#529) takes the kubeconfig over when it exists, without changing the field.

**The Mandate is the one named, else the Reef's default** (ADR 0017's order, steps 3 and 4: no `match` key fits an environment's request today). The `vcluster` Nereid's Mandate is the Reef's default, so every environment a person asks for, a PR's included, is a vcluster unless it names another Mandate. The kept cluster is the only environment that names one: `nereus init` creates it with `--mandate local`. `match` gets no `expires` key: ADR 0017 compares values, and "has an expiry" is a presence test (owner, 2026-11-14). Each Nereid acts only on the Environments whose Mandate names it, so the `vcluster` and `k3d` Nereids share the Reef without touching each other's objects, as the `vcluster` Nereid already does.

**The kept k3d cluster is the Environment `nereus`**, the name of the k3d cluster itself (owner, 2026-11-23, #2150). The name is a disposable label like any other environment's, never `prod`: migrating data, restoring a backup, or swapping the cluster under a Workload changes the environment, not the Workload, all through the platform. It replaces `production` in #556 and `live` in #159 and #160 with one name.

**A `k3d` Nereid registers `nereus` (a stand-in).** It runs in the `local-nereids` image and knows only the cluster it runs in: it adopts that cluster for an Environment whose Mandate names it, writes `status.kubernetes`, refuses to make a second one, and never deletes the cluster; deleting `nereus` removes only the record. Only a Nereid writes its Reef's `status` (ADR 0002), so `nereus init` asks for `nereus` like a person would and does not write its `status`, and the release Reef reads `nereus` like any other environment (owner, 2026-11-14). It retires when a real environment Nereid makes clusters. #575 (the Reef's first slice) builds it.

**At `expires`, the Nereid that made the environment removes it**, writes `Expired` in `status.phase`, and leaves the `Environment` until `nereus environment delete`, so the history stays visible. The `vcluster` Nereid already does it; `nereus` takes no `expires`.

**The release Reef finds its target in the Environment's `status`.** A release Mandate's `match` on `environment` (ADR 0017) picks the Nereid that knows how to deliver there: `flux` for a Kubernetes environment, another Nereid for Cloud Run, with the same `nereus release create`. A `Target` with no `environmentRef` keeps meaning the cluster Nereus runs in, which is `nereus` on k3d; whether a `Target` may name a cluster directly stays ADR 0010's open question.

**Hostnames per environment belong to the edge Reef.** Internal hostnames `<workload>.<environment>.getnereus.dev` (`triton.nereus.getnereus.dev`) behind the public `<workload>.getnereus.dev` are #470's (the edge Reef), not this Reef's.

```text
# The admin, once (nereus init does it on k3d)
$ nereus mandate create vcluster \
    --reef environment \
    --nereid vcluster \
    --default
✓ core/mandates/vcluster created (reef: environment, nereid: vcluster, default)

$ nereus mandate create local \
    --reef environment \
    --nereid k3d
✓ core/mandates/local created (reef: environment, nereid: k3d)

# The kept cluster, registered by nereus init
$ nereus environment create nereus \
    --owner project/nereus \
    --mandate local
✓ environment/environments/nereus created (mandate: local, nereid: k3d)

# A PR environment: the default Mandate
$ nereus environment create pr-123 \
    --owner project/nereus \
    --expires 72h
✓ environment/environments/pr-123 created (mandate: vcluster, nereid: vcluster)

$ nereus environment list
ENVIRONMENT  OWNER           NEREID    STATUS  EXPIRES
nereus        Project/nereus  k3d       Ready   -
pr-123       Project/nereus  vcluster  Ready   2d

# A release into nereus: the release reef reads its status
$ nereus release create triton \
    --source triton \
    --target nereus
✓ release/releases/triton created (mandate: flux)
```

`nereus environment create` is `nereus environment environment create` (ADR 0013: a kind named after its Reef takes the Reef's verbs). The deck is `docs/specs/cli/reefs/environment.yaml`.

**Stand-ins:** the `k3d` Nereid, which knows only its own cluster, until a Nereid makes clusters; the kubeconfig in a Kubernetes Secret until the secrets Reef (#529) holds it; `owner` has nothing behind it until the authorization Reef (#897).

## Prior art

- Crossplane's claims and compositions: the person's claim names no provider; the composition the admin chose makes it and writes back its connection details, here the Mandate and the Nereid's `status`.
- Kubernetes `StorageClass`: a default class and a class named per request, the order ADR 0017 follows here.
- Argo CD's cluster secrets and Flux's `kubeConfig.secretRef`: a delivery target reached through a referenced kubeconfig, never inline.
- Preview environments removed at an expiry, as the `vcluster` Nereid already does (#620).

## Consequences

- One shape for every environment, whatever makes it: the release Reef, the delivery Reef (ADR 0020) and the catalog read `status`, never a technology.
- `nereus init` gets one more step: the `local` Mandate and the Environment `nereus`, through the `k3d` Nereid (#575).
- The Reef has two Nereids at once, which ADR 0017 allows; neither acts on the other's Environments.
- #159, #160 and #556 use the one name `nereus`.
- A new provider (Cloud Run, Fargate) is a Nereid and a Mandate, with no change to `spec` or to a person's command.

## Open questions

- Whether a `Target` may name a cluster directly (ADR 0010).
- What `status` a non-Kubernetes environment publishes (Cloud Run, Fargate): decided with its first Nereid.
- Whether `region` takes part in `match` (ADR 0017 lists only `engine`, `environment` and `owner`).

*Origin: the owner's decisions of 2026-10-30 in the design session on the catalog, tenancy and resource Reefs (#568), and of 2026-11-14 on its visual summary (the default Mandate and the stand-in for nereus). Raw data in Drive `dump-mental-prompts/opinions/2026-10-30/` and `#pontos/raw/2026-11-14/`.*
