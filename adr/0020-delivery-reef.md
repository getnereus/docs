# 0020. The delivery reef: a Delivery takes a Workload to an Environment

!!! note "In short"
    A `delivery` reef with one kind, `Delivery`, takes a Workload to an Environment; the Nereid, never the client, resolves an image tag to a digest. Status: Proposed (2026-11-03).

**Status:** Proposed (2026-11-03)

## Context

`make scene-golden-path` (PR #836) took a developer's image to a namespace with today's commands and listed what hurts: nothing says what runs (gap 8), changing a tag takes three steps (gap 9), and a re-pushed tag is not pulled (gap 10). #835 (the delivery model of the internal-developer-platform profile) refined the path from that list, and the owner settled it on 2026-11-02.

The catalog (ADR 0016) says what exists, the release reef (ADR 0010) runs a chart in a Target, the environment reef says where. Nothing joins them: one Workload runs in several Environments, and a developer should not write a `Repository`, a `Source`, a `Target` and a `Release` to run an image.

## Decision

**A `delivery` reef, `delivery.getnereus.dev/v1alpha1`, with one kind, `Delivery`, its default kind: one per Workload and Environment pair, cluster-scoped.** The pair lives in `spec`. `status` says what runs.

```yaml
apiVersion: delivery.getnereus.dev/v1alpha1
kind: Delivery
metadata:
  name: hello-dev
spec:                                   # written by the client: the CLI, or the portal through the API
  workload: hello
  environment: dev
  image: registry.example.com/hello:a1b2c3d
  requestedAt: "2026-11-03T14:00:00Z"
status:                                 # written by the Nereid
  resolved:
    requestedAt: "2026-11-03T14:00:00Z"
    image: localhost:5111/hello:0.1.0   # what this resolution read: a new deploy of another image resolves again
    digest: sha256:9f2c1e
    port: 8080                          # read once with the digest, so a retry reads no registry
  digest: sha256:9f2c1e                 # what is running
  previousDigest: sha256:77ab40         # the only history for now
  namespace: hello-dev
```

**The Nereid resolves a tag to a digest, never the client.** The CLI is today's client, and a portal will call the same API, so the rule sits behind them and works the same for both (owner, 2026-11-03). The Nereid uses the platform's registry credential, so a person needs only their own login, as #835 decided for publishing.

- **Each `deploy` is a new request:** the client writes `spec.requestedAt`, so a second deploy of the same tag changes `spec`, prints `configured` and reaches a re-pushed image.
- **One resolution per request:** the Nereid resolves only when `spec.requestedAt` differs from `status.resolved.requestedAt`. A tag that moves with no new `deploy` never changes what runs in silence.
- **A digest stays as it is:** an image given as `hello@sha256:...` is not resolved. The `Release` always carries the digest, so `imagePullPolicy: IfNotPresent` is no longer a trap.
- **What this costs:** `--dry-run` shows the tag, not the digest, and a tag that does not exist fails after `deploy` printed `created` or `configured`, with the reason in `status`. `--wait` brings that reason to the terminal.

**The Nereid writes the release reef's objects.** It writes a `Release` with the curated chart `app-template`, or the chart the Workload names in `spec.chart` (ADR 0016), and the `Source` and the `Target` that `Release` needs, so a developer configures nothing of the release reef. The namespace is the Delivery's name. The `keycloak` and `vcluster` Nereids already write their own `Release`. The `flux` Nereid still does the installing, with #828 (a Release reaches its Target's Environment) taking it into the Environment.

**The port comes from the image's `ExposedPorts`, overridden in the Workload,** with a clear error when both lack it. Secrets, databases and health checks go in the Workload; Score waits.

**One Nereid per platform it delivers to, with no new noun.** The kind `Target` and `init --target` already use the other word. The first Nereid is `kubernetes`: it delivers to a Kubernetes Environment through `Release`. A destination that is not Kubernetes is another Nereid, behind another Mandate, with the same `nereus workload deploy` and no `Release`.

**A Delivery's name is generated once and never changes:** `<workload>-<environment>`. When that name belongs to another pair (`hello` in `dev-x` and `hello-dev` in `x`), it takes a short suffix from the hash of the pair (`hello-dev-x-3f9a`); the same hash shortens a name that is too long. The limit is 53 characters, a Helm release's, since the Release takes the Delivery's name; the CRD checks it with CEL.

**How the CLI reads the argument:**

| Typed | Read as |
|---|---|
| `hello@dev` | the pair; `@` is sugar for `--environment` |
| `hello --environment dev` | the pair |
| `hello-dev` | the Delivery's name |
| `hello` | a Workload with a single Environment, except in `deploy` |

The Delivery's name is tried before the Workload. When both match different targets, or a Workload runs in several Environments, the error lists the candidates and picks none (ADR 0012).

**`deploy` never guesses:** it takes the unique name, `hello@dev` or `hello --environment dev`, and refuses a bare `hello` even with one Environment, so it cannot change target in silence when a second Environment appears.

**The commands follow ADR 0013.** `nereus workload deploy` creates or updates a `Delivery`, and `nereus delivery` has the five verbs. `nereus workload list` shows what the catalog has, and `nereus delivery list` shows what was deployed: the two are different questions (owner, 2026-11-03). The deck is `docs/specs/cli/reefs/delivery.yaml`.

```console
# Take a Workload to an Environment
$ nereus workload deploy hello@dev \
    --image registry.example.com/hello:a1b2c3d
✓ delivery/deliveries/hello-dev created

Next steps:

  nereus delivery get hello-dev

# What the catalog has
$ nereus workload list
WORKLOAD  OWNER          TYPE     AUDIENCE  DELIVERIES  STATUS
billing   Project/shop   service  programs  0           Ready
hello     Project/hello  service  people    2           Ready

# What was deployed
$ nereus delivery list \
    --workload hello
NAME         WORKLOAD  ENVIRONMENT  DIGEST         READY
hello-dev    hello     dev          sha256:9f2c1e  True
hello-stage  hello     stage        sha256:77ab40  True
```

**Stand-ins, for the issues that build them:** `workload deploy` and `nereus delivery` (#845) and `workload logs` (#846) reached the cluster with the kubeconfig until their group moved behind the Nereus API (ADR 0018): the first two through it since #1516, `workload logs` and `--follow` since #1517, streamed by the API from inside the Environment. The kubeconfig stays only while the instance offers no sign-in. This ADR creates none itself.

## Prior art

- **Kubernetes, images** ([kubernetes.io, Images](https://kubernetes.io/docs/concepts/containers/images/)): "Tags can be moved to point to different images, but digests are fixed", and with `IfNotPresent` "the image is pulled only if it is not already present locally"; the reason the `Release` carries the digest.
- **Flux's `HelmRelease`, triggering a reconcile** ([fluxcd.io, HelmReleases](https://fluxcd.io/flux/components/helm/helmreleases/)): the annotation `reconcile.fluxcd.io/requestedAt` queues a reconcile when its value differs from `.status.lastHandledReconcileAt`; `spec.requestedAt` and `status.resolved.requestedAt` take that shape. The same page describes `.spec.kubeConfig`, which "can apply and manage resources on a remote cluster", the way a `Release` reaches an Environment.
- **bjw-s `app-template`** ([bjw-s-labs, App Template](https://bjw-s-labs.github.io/helm-charts/docs/app-template/)): "a companion Helm chart that works alongside the Common Library to deploy any application in Kubernetes"; the curated chart, used since PR #836, instead of a chart of our own.
- **Kargo** ([docs.kargo.io, Core concepts](https://docs.kargo.io/user-guide/core-concepts/)): a Stage is "a promotion target" and Freight "references specific revisions of artifacts"; the Delivery plays the Stage's part for one Workload and holds one digest, with no pipeline. Update channels, if they come, should read Kargo first.

## Consequences

- One command takes an image to an Environment and one row says what runs: gaps 8, 9 and 10 of PR #836 close with #845.
- The catalog stays a reader (ADR 0016): `nereus workload list` only counts Deliveries, and the running image lives in the Delivery's `status`.
- A `Delivery` applied from a file with a tag resolves once, and applying the same file again prints `unchanged`. Moving to a re-pushed tag takes `nereus workload deploy` or a new `spec.requestedAt`.
- **Security (OWASP A10, server-side request forgery):** the Nereid contacts a registry a person named, with the platform's credential; #845 validates the reference and sends that credential only to the registry it belongs to. Authorization is by `owner` for now, then the authorization reef.

## Open questions

- **Rollback:** `status.previousDigest` is the only record; no command uses it yet.
- **History of a Delivery:** whether more than one previous digest is kept, and where.
- **Update channels:** an idea, not designed.
- **Which registries a Delivery may name:** a list per Organization or Project is a candidate for when the authorization reef exists.

*Origin: the owner's decisions of 2026-11-02 in the review of #835 (the delivery model of the internal-developer-platform profile), and of 2026-11-03 in the design of #843 (this ADR): `nereus delivery list` apart from `nereus workload list`, the Nereid `kubernetes` and what it writes, and the Nereid resolving the digest. Raw data in Drive `#pontos/raw/2026-11-02/` and `#pontos/raw/2026-11-03/`.*
