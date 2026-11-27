# 0010. Reefs are added at runtime; commands are grouped by Reef

!!! note "In short"
    A Reef is added at runtime from its contract, and a Nereid is added on its own and looks after one or more Reefs. The `release` Reef has four kinds. Status: Proposed (2026-10-17, rewritten 2026-10-25).

**Status:** Proposed (2026-10-17, rewritten 2026-10-25)

## Context

ADR 0002 says the person asking names the Reef, never the Tool. Naming a command group after whoever fulfils it (`platform helm repo add`) would expose the Tool and would not survive a swap: Flux has no `helm repo`, and its sources may be Git repositories.

Helm, Flux and Argo CD all take something from a source and keep a version of it running in a cluster. Kubernetes keeps the same split for traffic: a `GatewayClass` exists in the cluster and names a `controllerName`; the person writing a `Gateway` never names the load balancer. Crossplane does it for infrastructure: a `CompositeResourceDefinition` is the contract, and Compositions fulfil it.

## Decision

**A Reef is added at runtime**, from its contract, and listed with the others:

```bash
nereus reef apply release --from-file ./reefs/release/
nereus reef list
```

**A Nereid is added on its own, top-level, and looks after one or more Reefs**; a Reef with no Nereid waits:

```bash
nereus nereid apply helm \
  --reef release \
  --image ghcr.io/getnereus/nereus/release-helm-controller:0.1.0
```

- Its commands are served under the Reef's group: `nereus release ...` (ADR 0004).
- Several Nereids may look after one Reef. Which one handles a request is chosen by a Mandate (ADR 0002), the Reef's default one when the request names none: `nereus mandate create ... --default`.

**The release Reef, `release.getnereus.dev/v1alpha1`, has four kinds** (#445), each named for one question, in the namespace Nereus runs in:

| Kind | Answers | Fields (`spec`) | Status (written by a Nereid) |
|---|---|---|---|
| `Repository` | where it comes from | `type` (`http`, `oci`, `git`), `url`, optional `secretRef` (a secret of the secrets Reef) | `ready`, `nereid`, `conditions` |
| `Source` | what | `repositoryRef`, `chart` (`name`, `version`); later `kustomize` or `manifests` instead of `chart`, in the same kind | `ready`, `resolvedVersion`, `nereid`, `conditions` |
| `Target` | where to | optional `environmentRef` (an environment of the environment Reef, which knows the cluster and its credentials), `namespace` | `ready`, `nereid`, `conditions` |
| `Release` | a Source running in a Target | optional `mandate` (the Reef's default when absent), `sourceRef`, `targetRef`, `values` | `phase` (`Pending`, `Progressing`, `Ready`, `Failed`), `version`, `nereid`, `mandate`, and a `Ready` condition in the Reef's reasons |

- **A Target with no environment is the cluster Nereus runs in**, until the environment Reef exists.
- **Who writes which status** (ADR 0005): a Release's, the Nereid of its Mandate; a Repository's, a Source's and a Target's, the Nereid of the Reef's default Mandate.
- **A Nereid keeps its Tool's objects next to the Reef's, on purpose:** the `flux` Nereid writes a Flux `HelmRepository` for each `Repository` and a Flux `HelmRelease` for each `Release` (its chart template from the `Source`), each owned by the Nereus object it comes from, and translates their `Ready` condition into the reasons the Reef declares (`Released` or `Indexed`, `Progressing`, `ReleaseFailed` or `IndexFailed`), keeping its status and message (#528); Flux's other conditions stay on Flux's objects. Swapping Flux for Argo CD or plain Helm changes the second object, never the first.

**A Reef has two levels of commands:**

- **Configuring** the Reef, done by a platform admin: where things come from (`repository`), what (`source`) and where they go (`target`).
- **Using** the Reef, done by a developer: its Instances (`release`), which name a source and a target that already exist.

The commands are `nereus <reef> <kind> <verb> <name>`, with long options and kubectl's verbs (ADR 0013). **A kind named after its Reef takes the Reef's own verbs:** `nereus release create` is `nereus release release create`, as `nereus environment create` will be `nereus environment environment create`.

```bash
# The admin, once: the Nereid and the reef's default Mandate
nereus nereid apply flux \
  --reef release

nereus mandate create flux \
  --reef release \
  --nereid flux \
  --default

# configure
nereus release repository create codecentric \
  --url https://codecentric.github.io/helm-charts \
  --type http

nereus release source create keycloak \
  --repository codecentric \
  --chart keycloakx \
  --version 7.0.1

nereus release target create dev-identity \
  --environment dev \
  --namespace identity

# use
nereus release create keycloak \
  --source keycloak \
  --target dev-identity \
  --values-file keycloak-values.yaml \
  --mandate flux

nereus release list
```

**Repositories are typed** (`http`, `oci`, `git`). A Nereid says in a Repository's status when it does not take its type: the `flux` Nereid takes `http` and `oci`, not `git` yet.

**GitOps is a way of making releases**, a Mandate of the `release` Reef in ADR 0002's terms, not a Reef of its own: a `gitops` Reef would leave plain Helm out.

**The contract of a Reef is a Kubernetes API**, the API group `<reef>.getnereus.dev/v1alpha1` (ADR 0009). Adding a Reef applies the CRDs of its contract (for `release`: its repositories, sources, targets and releases), so the platform's API is extended through Kubernetes itself: validation by OpenAPI schema, discovery, RBAC per resource, `kubectl` and watches come with it. Nereids reconcile those resources and write their `status`.

**Inspired by Crossplane, not built on it.** The model borrows the shape of a `CompositeResourceDefinition`, but the platform does not depend on Crossplane. Crossplane stays free to be what ADR 0002 makes of any other project: a Tool, used by a Nereid.

## Prior art

- **Gateway API's `GatewayClass`** ([gateway-api.sigs.k8s.io](https://gateway-api.sigs.k8s.io/reference/api-types/gatewayclass/)): the class names a `controllerName`, and the person writing a `Gateway` never names the load balancer.
- **Crossplane's composite resource definitions** ([docs.crossplane.io](https://docs.crossplane.io/latest/composition/composite-resource-definitions/)): a definition is the contract, and Compositions fulfil it; the contract of a Reef takes the shape, not the dependency.
- **Flux's source and helm controllers** ([fluxcd.io, HelmRepository](https://fluxcd.io/flux/components/source/helmrepositories/); [HelmRelease](https://fluxcd.io/flux/components/helm/helmreleases/)): where a chart comes from apart from what is released and where; the release Reef's `Repository`, `Source` and `Release` take the same split, and the `flux` Nereid writes those objects.
- **Custom resources and the operator pattern** ([Kubernetes, "Operator pattern"](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)): the API is extended at runtime with CRDs, and a controller reconciles them.

## Consequences

- Swapping Helm for Flux changes no command a person types: only which Nereid the Mandate names.
- Configuration and use are separate resources, so permissions split along the two levels without extra design (admins write repositories, sources and targets, developers write releases).
- Repositories, sources, targets and releases are Instances in the cluster instead of state in a Nereid's volume: a new Nereid inherits them.
- `reef`, `nereid` and `mandate` share one shape: the noun, the verb and the name as an argument, top-level (`nereus nereid apply helm`, `nereus reef apply release`).

## Open questions

- **How a contract is written and turned into commands.** To decide: how a Reef is packaged (`--from-file` today; an image or an OCI package next), how the CLI builds commands from its schema, and how a contract is versioned. Today the CLI builds the release Reef's commands from the contract it pins (#445), a stand-in for commands built from any Reef's schema.
- **How the Platform API sits in front of the Reefs.** `kubectl` reaches the CRDs of one cluster; the Platform API is the one door for every client (the CLI, a portal, an IDE, an agent), none of which should need a kubeconfig. It composes Reefs and owns what crosses them: authentication (ADR 0006), authorization by team, policy, cost, several clusters.
- **Actions that are not resources.** `source apply` and `release create` map to resources; `release rollback`, `sync` or `logs` are actions. Likely both mechanisms stay: commands built from the contract's schema for resources, and commands a Nereid publishes for actions (ADR 0004).
- **What a target is** beyond the cluster Nereus runs in: an environment of the environment Reef names the cluster and its credentials; whether a Target may also name a cluster directly is open.
- **Where the Reef's objects live:** today the namespace Nereus runs in; a namespace per organization and project comes with them.
- **Who upgrades the Tool** ([#449](https://github.com/getnereus/nereus/issues/449)): `nereus nereid apply flux` installs Flux before the Nereid, as the `openbao` Nereid runs OpenBao (owner, 2026-10-26): the source and helm controllers, from Flux's `install.yaml` pinned by version and digest. Who upgrades it, what the CLI does to a Flux it finds, and whether deleting the Nereid uninstalls it are open.

**The first Release the platform makes itself** (order 20261026-0840, step 2; [#597](https://github.com/getnereus/nereus/issues/597)): Keycloak. The `keycloak` Nereid writes it itself, by server-side apply through the Reef's default Mandate: a Repository `codecentric`, a Source `keycloak` (`keycloakx` 7.0.1), a Target `keycloak` (the namespace Nereus runs in) and a Release `keycloak` with the chart's values. While the release Reef has no default Mandate it writes nothing and reports `Ready=False` (`NoReleaseNereid`, naming `nereus nereid apply flux --reef release`); it reports `WaitingForRelease` until the Nereid of that Mandate reports the Release Ready, `ReleaseFailed` with the Release's own message when it fails, and only then applies its realm and publishes `status.oidc`, reaching Keycloak through the chart's Service. So the `keycloak` Nereid requires the `release` Reef, besides `secrets`. The Source, the Target and the Release are owned by the `core/nereids/keycloak` object, so deleting the Nereid lets Kubernetes' garbage collector delete them, and Flux uninstalls Keycloak; the shared Repository has no owner, and `nereus nereid delete keycloak` deletes it once no Source names it (owner, 2026-10-26).

**A Nereid that needs a Helm chart writes its own Release** (owner, 2026-10-30, [#597](https://github.com/getnereus/nereus/issues/597)), with the customisations it needs, through the chart's native options where possible (its values, `extraInitContainers`, `extraVolumes`); the CLI only installs the Nereid and never customises a chart. What a Nereid adds to its chart runs from its own image when it needs one (`NEREID_IMAGE`, pinned by digest), as the login theme of [#598](https://github.com/getnereus/nereus/issues/598) will.

*Rewritten 2026-10-25 from voice session; raw data in Drive #pontos/raw/2026-10-25. Rewritten again 2026-10-26 (order 20261026-1748, #445): the release Reef's four kinds (Repository, Source, Target, Release) and their fields, from the owner's walkthrough deck of 2026-10-26; `source` became `repository` and the chart moved from the release to the source; the syntax sugar of a kind named after its Reef. Amended 2026-10-26 (order 20261026-1843): the `flux` Nereid installs Flux itself. Amended again (order 20261026-0840, step 2): Keycloak is a Release of this Reef. Amended 2026-10-30 (#597): the `keycloak` Nereid writes that Release itself, and every Nereid that needs a chart writes its own.*
