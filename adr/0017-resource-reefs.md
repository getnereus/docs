# 0017. Resource Reefs: a small contract kind per family, the provider in the Mandate, and a Mandate's match

!!! note "In short"
    Five resource Reefs, each a small contract kind per family, with the provider chosen in the Mandate and a Mandate selected by its `match`. Status: Accepted (2026-11-14, by the owner; proposed 2026-10-30, rewritten 2026-11-12).

**Status:** Accepted (2026-11-14, by the owner; proposed 2026-10-30, rewritten 2026-11-12)

## Context

A platform provisions resources for the things that run on it: a database, a queue or a topic, a cache, a bucket, a hostname. The clouds offer each of them in their own way (a Postgres on RDS has `multiAz`, a topic on NATS has JetStream), and the owner, in the design session of #560 (the resource Reefs and how a Mandate picks their Nereid), leaned towards one kind per engine or per provider offering, so that nothing of a provider is lost.

ADR 0011 (Reefs, Nereids and Mandates) says the opposite: an Instance's fields are generic, common to every Nereid of the Reef, and what one Nereid needs and the others lack becomes a common field of the Reef, never a Nereid-specific kind. A kind per engine would amend it, and would change the command a person types on every swap of provider, against ADR 0002 (the person asking names the Reef, never the Tool).

The research asked for by the owner (on the owner's Drive, private) shows what teams do with Crossplane, the project closest to this problem: a generic kind bound to provider classes was tried and dropped in 2020 as the lowest common denominator, and teams now build two layers, a small contract kind on top (an engine, a size) and typed, provider-specific objects one layer down, picked by a selector or a class. It also shows how the platforms pick an implementation (Humanitec by the most specific criteria, StorageClass and IngressClass by a default, Score by the first match), and that a cache's contract is small and distinct from a database's.

The order comes from the dogfooding: Nereus itself runs Triton on NATS with no Reef (#483, Triton as the messaging Reef) and publishes Triton through a tunnel made by hand (#470, publishing a Reef's endpoint at a hostname: an edge Reef with a cloudflare Nereid). No Workload of the catalog (#559, the catalog Reef) asks for a database yet.

## Decision

**Five resource Reefs, in the order the dogfooding asks.** Each is a Reef in ADR 0002's sense: an API group `<reef>.getnereus.dev/v1alpha1`, fulfilled by Nereids, bound by Mandates.

| Order | Reef | Kinds | Why now |
|---|---|---|---|
| 1 | `messaging` | `Queue`, `Topic` | Triton uses NATS with no Reef (#483) |
| 2 | `edge` | hostname, certificate, DNS | Triton behind a tunnel made by hand (#470) |
| 3 | `database` | `Database` | when a Workload of the catalog asks |
| 4 | `cache` | `Cache` | when a Workload of the catalog asks |
| 5 | `storage` | `Bucket` | when a Workload of the catalog asks |

DNS lives in `edge`. The other families of the research (data lake, streams, AI services, about 35 in all) enter one by one when `catalog check` (#559) points at the gap, each as its own Reef or kind, never decided in advance.

**A small contract kind per family, with `engine`.** The kind carries `owner: {kind, name}` (the node of the tenancy tree it belongs to, #21, Organization and nested Projects), `engine` and the fields every engine understands. What only one provider has goes in the Mandate's `params`, written once by the admin; what a person chooses per request and every engine understands becomes a common field of the kind, as ADR 0011 asks. ADR 0011 stays as it is: the person writes the contract, the Mandate holds the provider.

```yaml
# The person asks (Instance): the small contract
apiVersion: messaging.getnereus.dev/v1alpha1
kind: Topic
metadata:
  name: triton-orders
spec:
  owner: {kind: Project, name: triton}
  engine: nats

# The admin decides once (Mandate): the provider's part
apiVersion: core.getnereus.dev/v1alpha1
kind: Mandate
metadata:
  name: messaging-nats
spec:
  reef: messaging
  nereid: nats
  match: {engine: nats}
  params: {jetstream: "true", replicas: "3"}
```

**`spec.match` on the Mandate picks the Nereid; the most specific wins.** The rule:

- A `match` holds when every key it names equals the request. A key the match does not name is not looked at.
- **`owner` holds down the tree** (owner, 2026-11-10, #1311): a match on a node of the tenancy tree (ADR 0015) holds for that node and for every node under it, so a Mandate matching an Organization covers its Projects.
- Among the Mandates whose match holds, the one whose match contains every other matching one wins (the most specific, by containment). On `owner`, the nearest node wins: a Project's own Mandate before its Organization's.
- The empty match is the Reef's default (`spec.default: true` and no `match` mean the same).
- `--mandate` on the request forces one Mandate, as today.
- The keys are `engine`, `environment` and `owner`; `kind` only in a Reef with several resource kinds (`messaging`, with `Queue` and `Topic`).
- `nereus mandate create` refuses a match identical to an existing one, and a partial overlap (two matches that can both hold on one request and neither contains the other), with an error that follows ADR 0012 (error messages) and gives the fix to copy. A tie is refused when the Mandate is made, never when a resource is asked. Two matches that differ only in `owner`, one node above the other in the tree, are not an overlap: the nearest wins.
- The output line of a request names the Mandate resolved and its Nereid.

**The selection rule is the same for every Reef** (owner, 2026-11-10, #1311). A Reef may have several Nereids at once, and a request picks its Mandate in this order:

1. **Only the Nereids that serve the request take part.** A Nereid serves a request when it publishes what the request needs: the kind, for a request of a kind; `status.oidc`, for a login (ADR 0006).
2. **The Mandate whose `match` holds,** the most specific one, by the rule above.
3. **Else the Reef's default.**
4. **Else the only one,** when a single Mandate is left.

`--mandate` skips the order. A request that reaches the end with no Mandate, or with several, fails with the Mandates that exist and the `--match` that would catch it (ADR 0012).

```text
# The authentication reef with three Mandates:
#   corporate   keycloak  the default
#   acme-auth0  auth0     match: owner=organization/acme
#   github      github    no match, not the default; mints tokens only

# A login of a Project under acme:  acme-auth0 (step 2, the Organization's match covers its Projects)
# A login of anyone else:           corporate  (step 3; github publishes no status.oidc and is out at step 1)
# A Token:                          github     (step 4; the only Nereid that mints tokens, without being the default)
```

```yaml
# The reef's default: what nereus init makes on k3d
apiVersion: core.getnereus.dev/v1alpha1
kind: Mandate
metadata:
  name: cloudnative-pg
spec:
  reef: database
  nereid: cloudnative-pg
  default: true

# Postgres on nereus, the kept cluster, goes to RDS: the most specific match wins
apiVersion: core.getnereus.dev/v1alpha1
kind: Mandate
metadata:
  name: database-postgres-nereus
spec:
  reef: database
  nereid: aws-rds
  match:
    engine: postgres
    environment: nereus
  params:
    accountId: "123456789012"
    region: us-east-1
    multiAz: "true"
```

```text
# Triton's topic, through the messaging reef's Mandate for NATS
$ nereus messaging topic create triton-orders \
    --owner project/triton \
    --engine nats
messaging/topics/triton-orders created (mandate: messaging-nats, nereid: nats)

# The same request in two environments: nereus resolves the specific Mandate, pr-123 the default
$ nereus database create orders \
    --owner project/triton \
    --engine postgres \
    --environment nereus
database/databases/orders created (mandate: database-postgres-nereus, nereid: aws-rds)

$ nereus database create orders \
    --owner project/triton \
    --engine postgres \
    --environment pr-123
database/databases/orders created (mandate: cloudnative-pg, nereid: cloudnative-pg)

# A partial overlap is refused when the Mandate is made
$ nereus mandate create database-postgres-eu \
    --reef database \
    --nereid aws-rds \
    --match engine=postgres \
    --match region=eu
✗ core/mandates/database-postgres-eu overlaps database-postgres-nereus (engine=postgres) and neither contains the other. To fix it, run:
  # name the environment too, so one match contains the other
  nereus mandate create database-postgres-eu --reef database --nereid aws-rds --match engine=postgres --match environment=nereus --match region=eu
  Nothing was changed.
```

**The same `match` picks who delivers into an environment.** An `Environment` (the environment Reef) is only the request, with no technology in its `spec`, and its name is a disposable label (`nereus` for the kept k3d cluster today, the name of the k3d cluster itself; never `prod`, owner 2026-10-30 and 2026-11-23), so that migrating data, restoring a backup or swapping the cluster under a Workload changes the environment, not the Workload; the Nereid of its Mandate materializes it (a kept cluster, a vcluster, a managed container service) and writes what it made in `status`. A Mandate of the release Reef with a `match` on the environment picks the Nereid that knows how to deliver there, so `nereus release create` is the same command whatever the environment is made of.

**A `cache` Reef of its own, Valkey by default.** The in-memory contract is small (get and set with a time to live; the data may be lost) and differs from a database's, so a cache is not a `Database` with another engine. Valkey, Redis and Memcached are engines and params of the `Cache` kind; the Reef's default Nereid runs Valkey. A durable, no-eviction Redis is a key-value database (`database`, `engine: redis`); CDN and HTTP caches belong to the edge Reef.

```yaml
apiVersion: cache.getnereus.dev/v1alpha1
kind: Cache
metadata:
  name: sessions
spec:
  owner: {kind: Project, name: triton}
  engine: valkey
```

## Prior art

- **Kubernetes StorageClass** ([Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)): "When a PVC does not specify a `storageClassName`, the default StorageClass is used", and its `parameters` are provider-specific, read by the provisioner alone; the Mandate's empty match as the default and its `params` as the provider's part take the same split. Kubernetes keeps the newest of several defaults "to allow for seamless migration"; this ADR refuses the second one instead.
- **Kubernetes IngressClass** ([Ingress, "Default IngressClass"](https://kubernetes.io/docs/concepts/services-networking/ingress/#default-ingress-class)): "If you have more than one IngressClass marked as the default for your cluster, the admission controller prevents creating new Ingress objects that don't have an `ingressClassName` specified"; the refusal of an identical or overlapping match at `mandate create` moves that refusal to the moment the class is made.
- **Humanitec resource definitions** ([Resource Definitions](https://developer.humanitec.com/platform-orchestrator/docs/platform-orchestrator/resources/resource-definitions/)): matching criteria on environment type, application, environment, resource id and class, each with a weight, and "when selecting with Matching Criteria, the most specific one is selected"; the most-specific rule is taken, by containment instead of weights, so that a tie cannot happen.
- **Crossplane composite resources** ([Composite Resources](https://docs.crossplane.io/latest/composition/composite-resources/); [Compositions](https://docs.crossplane.io/latest/composition/compositions/)): a composite resource names its Composition with `compositionRef` or selects one by labels with `compositionSelector`, and a Composition is "a template for creating multiple Kubernetes resources as a single composite resource"; the two layers (a contract kind over provider-specific objects) are the shape this ADR takes, with the Mandate in the place of the Composition. That Crossplane dropped its generic kinds in 2020 and that teams build two layers is the project's own reading of the research on the Drive.
- **Score resources** ([Score specification reference](https://docs.score.dev/docs/score-specification/score-spec-reference/)): a workload declares a resource by `type`, an optional `class` and `params`, and "it is up to the Score implementation to resolve the resource by name, type, or any other meta information available"; the contract kind with `engine` plays the part of `type` and `class`, and the Mandate the part of the implementation's resolution.

## Consequences

- A person asks for a `Topic`, a `Database` or a `Cache` by its engine and never names a Tool or a provider; swapping NATS for Kafka, or CloudNativePG for RDS, changes a Mandate, not a command or a file of the person.
- Every provider-only setting is written once, in a Mandate's `params`, by the admin; a setting a person needs per request becomes a common field of the kind, which is the way out of the lowest common denominator ADR 0011 already names.
- The choice of Nereid is deterministic and refused early: with the overlap rule enforced at `mandate create`, every request resolves to one Mandate or to none, and a request with no Mandate fails with the Mandates that exist and the `--match` that would catch it (ADR 0012).
- A Reef takes several Nereids at once: the refusal "one Nereid per Reef" of `nereus nereid apply` goes away (#1313), and the authentication Reef is the first to use it (ADR 0006).
- `nereus mandate create` grows `--match <key>=<value>` (repeatable) next to `--param`, and `nereus mandate list` shows the match of each Mandate; `nereus status` keeps one row per Reef and Nereid pair (ADR 0011).
- The messaging and edge Reefs come first, so the two stand-ins of Nereus itself (NATS with no Reef, the tunnel by hand) are retired by a feature of the platform, as #269 asks.
- Each Reef's commands follow ADR 0013 (command conventions): `nereus <reef> <kind> <verb> <name>`, kinds singular in commands, a default kind per Reef (`nereus database create` is `nereus database database create`), full-path output lines, `--dry-run` everywhere.

## Open questions

- **How a Workload lists the resources it needs.** The catalog's `Workload` (#559) has no list of resources yet; the owner's idea of a chart carrying the Kubernetes objects plus a Score application spec makes Score's `resources` a candidate format, to weigh when the first resource Reef is built.
- **How a Workload gets the credentials of a resource.** The first opinion proposed a binding through the secrets Reef in the Service Binding layout (the Nereid writes the connection as a secret the Workload mounts); not decided.
- **The edge Reef's kinds.** #470 names the hostname and the cloudflare Nereid; whether a certificate and a DNS record are kinds of their own or fields of the hostname is decided there.

*Origin: the owner's decisions of 2026-10-30, in the design session on the catalog, tenancy and resource Reefs (#21, #559, #560); the brief, the opinions and the three research files (`research-crossplane.md`, `research-resource-families.md`, `research-mandate-matching.md`) in Drive `#pontos/beach/opinions/2026-10-29/` and `2026-10-30/` (private); the raw log under `#pontos/raw/2026-10-29/`.*

*Rewritten 2026-11-12 from the owner's decisions of 2026-11-10 (#1311: the selection rule for every Reef, and a match on `owner` holding down the tree); raw data in Drive `#pontos/raw/2026-11-10/`.*
