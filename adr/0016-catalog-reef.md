# 0016. The catalog Reef: Workload and Package, three characteristics, configurable types

!!! note "In short"
    A `catalog` Reef holds two kinds split by lifecycle, `Workload` for what runs and `Package` for what is published, with three characteristics and configurable types. Status: Proposed (2026-10-30, rewritten 2026-11-03).

**Status:** Proposed (2026-10-30, rewritten 2026-11-03)

## Context

While the wasp-idp deck's "Developer Control Plane" part was ported as a Nereus deck (#541, the Developer Control Plane deck, PR #557), its golden-path slide showed `nereus catalog create hello-api --system greeter --template python-service`, a command with no counterpart in the CLI design (`docs/agent/cli.md`). The owner reacted to the model behind it, Backstage's: a `Component` (which the owner never knew the meaning of), under a `System`, under a `Domain`, with its `type` as a free string. The design session of 2026-10-29 and 2026-10-30 turned that reaction into three refinements: the catalog's kinds (#559, the catalog Reef: Workload, Package and their types), the tenancy model (#21, Organization and nested Projects, ADR 0015) and the resource Reefs (#560, the resource Reefs and how a Mandate picks their Nereid, ADR 0017).

The diagnosis that held through the session: Backstage classifies software for a portal, to look at; Nereus classifies it for a control plane, to act on. A type says what shape a thing has; a platform needs to know what it must do for the thing, and only that can be checked by a script. The owner's provocation, that classifying software by Backstage's words may be looking at the problem from an older time, was tested against the ways software is delivered in 2026 (micro-frontends, a BFF, edge sites, serverless functions, agents, MCP servers, inference endpoints, workers of a workflow engine, operators): every one of them is something that runs, something that is published, or both from one repository, and a type alone fits few of them without a qualifier.

The owner asked for the model to be proved on Nereus itself, dogfooding and inception, never on a generic example: the Nereids `openbao`, `keycloak` and `flux`, Triton, the CLI, the images, the docs site, the kept k3d cluster. The brief, the opinions and the research behind this ADR are private raw data on the owner's Drive.

## Decision

**A `catalog` Reef, `catalog.getnereus.dev/v1alpha1`, with two kinds split by lifecycle: `Workload` for what runs and `Package` for what is published.** There is no `Component`, no `System` (a leaf Project of the tenancy tree plays that part, ADR 0015) and no `API` or `Resource` kind: an API is a Workload with an audience, and a resource is an Instance of its own Reef (ADR 0017), which the catalog reads and never writes. A thing that runs and is published, such as the CLI's repository that is also a Package, is two entries.

**A Workload has three characteristics, each the answer to one question, as plain fields of `spec`:**

| Field | The question | Values |
|---|---|---|
| `runs` | does it stay up, or run until it completes? | `always`, `once` |
| `trigger` | what makes it work? | a list of `event` (something changed: the cluster, a queue, a file), `request` (someone asks), `schedule` |
| `audience` | who talks to it? | a list of `programs`, `people`, `agents`; `[]` means nobody |

The platform reads only these three. They are what the Reefs and `catalog check` act on, and they stay fixed: adding one is a change to this ADR. In OIDC an `aud` claim names who a token is for, another meaning of the word; the catalog's `audience` says who talks to a Workload.

**Types are configurable objects; the characteristics are not.** A `WorkloadType` is a name plus the answers it fills in for `runs` and `trigger`, as a StorageClass is a name plus the parameters its provisioner takes: the list of types changes with a file, never with an ADR, and the platform never reads a type's name. A Workload names its type and may override `runs` or `trigger` when the type does not fit. **`audience` is required on every Workload and never comes from a type:** both `service` Workloads of Nereus (Triton, for agents and people; the Keycloak server, for people, programs and agents) would override any default, so a default would be wrong more often than right, and "who is this for?" is the one question no type can answer.

The initial WorkloadTypes, in `catalog/workload-types/`:

| Type | What it is | `runs` | `trigger` |
|---|---|---|---|
| `controller` | watches the API and acts when something changes (every Nereid) | `always` | `event` |
| `service` | stays up and answers requests (an HTTP or gRPC API, a BFF) | `always` | `request` |
| `web-app` | an application that builds the page on each request, used by people | `always` | `request` |
| `static-site` | files, served as they are | `always` | `request` |
| `worker` | stays up consuming a queue or a topic, no port | `always` | `event` |
| `job` | runs to completion on a schedule | `once` | `schedule` |
| `function` | runs to completion on each call and scales to zero, as Knative Serving does | `once` | `request`, `event` |

`static-site` and `web-app` share the same answers: the name is for people and for search (`nereus catalog list --type static-site`), the characteristics are for the platform; `site` and `web` were dropped as names that do not explain themselves. A "files only" characteristic comes when the edge Reef (#470, publishing a Reef's endpoint at a hostname) needs it. `function` stays in the set with no function in Nereus yet: it costs one file. The docs site is a `static-site`; the portal, later, a `web-app`.

**A Nereid and the tool it runs are two entries.** The `keycloak` Nereid is a `controller` with `audience: []`: nobody talks to it; the CLI writes an object to the API and the Nereid acts. The Keycloak server is the tool the Nereid runs: people log in on it, the CLI exchanges tokens with it, the claude.ai connector authorizes agents through it. The server reaches the catalog as an Instance of the `authentication` Reef, which the catalog only reads; nobody writes a catalog file for it.

**A Package has a `type`, a `registry` and an `audience`.** `type` comes from configurable `PackageType`s (`cli`, `library`, `image`, `chart`, `reef`, `module`); the packaging format follows from the registry and is not a field. `registry` says where it is published, with the same values as ADR 0010's `Repository` types where they overlap (`git`, `oci`, `http`) plus `pypi`, `npm` and `maven`. A `PackageType` holds only `spec.registries`, the registries it allows, the minimum `catalog check` needs to refuse a registry the type does not take; more fields come when a real Package asks for them. A Reef that is only YAML files today is a Package with `type: reef` and `registry: git`: the same files are on GitHub for anyone, and when the Reef ships as an OCI package only `registry` and the name change. The owner's cut of what is published by consumer (`Package` for programs, `App` for people) fails on Nereus's first published thing, the CLI, which is both; `App` waits.

**`source` has `repository`, `ref` and `path`.** `ref` is structured as Flux's `GitRepository.spec.ref` (the owner's choice over one string): `branch`, `tag`, `semver`, `name` (a full Git reference, such as `refs/pull/420/head`) or `commit`, with Flux's precedence, `commit` over `name` over `semver` over `tag` over `branch`, and `commit` with `branch` meaning the commit must be on that branch. Workloads use `ref: {branch: main}`; a published Package names its tag or a semver range. The catalog Nereid writes the resolved commit in `status.source.commit`.

**Every entry names its owner in the tenancy tree** (ADR 0015) as `owner: {kind, name}`, never a namespace and never an apiVersion.

**A Workload says nothing about where it is delivered.** One Workload runs in several Environments, so a delivery's namespace and running image live in the `Delivery`'s `status` (ADR 0020, the delivery Reef). `runtime` is for what runs outside a Delivery, and `runtime.namespace` is allowed only with `runtime.kind: Deployment`, which cannot be found without it, as Triton today.

**A Workload may name its chart:** `spec.chart: {package: <name>}` references a `Package` of `type: chart`, with no new kind. With no `spec.chart`, the delivery Reef uses the curated chart `app-template`.

**The first entries are Nereus itself**, one file each in a `catalog/` folder at the repository's root:

```yaml
# catalog/workloads/triton.yaml: the room and the MCP door in one Pod, one entry until
# #508 (the bridge that splits Triton's room from the door)
apiVersion: catalog.getnereus.dev/v1alpha1
kind: Workload
metadata:
  name: triton
spec:
  owner: {kind: Project, name: triton}
  type: service                 # runs: always, trigger: [request]
  audience: [agents, people]    # always written here, never from the type
  source:
    repository: https://github.com/getnereus/nereus
    ref: {branch: main}
    path: controllers/triton/
  runtime:
    kind: Deployment
    namespace: triton
    name: triton
```

```yaml
# catalog/workloads/openbao.yaml: the controller of the secrets reef; nobody talks to it
apiVersion: catalog.getnereus.dev/v1alpha1
kind: Workload
metadata:
  name: openbao
spec:
  owner: {kind: Project, name: nereids}
  type: controller              # runs: always, trigger: [event]
  audience: []
  source:
    repository: https://github.com/getnereus/nereus
    ref: {branch: main}
    path: controllers/openbao/
  runtime:
    kind: Nereid
    name: openbao
```

```yaml
# catalog/packages/nereus.yaml: the CLI, installed by people and pulled by CI
apiVersion: catalog.getnereus.dev/v1alpha1
kind: Package
metadata:
  name: nereus
spec:
  owner: {kind: Project, name: core}
  type: cli
  registry: pypi
  name: nereus
  audience: [people, programs]
  source:
    repository: https://github.com/getnereus/nereus
    ref: {branch: main}         # no tag yet; a published version names its tag
    path: cli/
```

```yaml
# catalog/packages/openbao-image.yaml: the image of the openbao Nereid, one image per Nereid (#611)
apiVersion: catalog.getnereus.dev/v1alpha1
kind: Package
metadata:
  name: openbao-image
spec:
  owner: {kind: Project, name: nereids}
  type: image
  registry: oci
  name: localhost:5111/openbao-controller
  audience: [programs]
  source:
    repository: https://github.com/getnereus/nereus
    ref: {branch: main}
    path: controllers/openbao/
```

```yaml
# catalog/workload-types/service.yaml
apiVersion: catalog.getnereus.dev/v1alpha1
kind: WorkloadType
metadata:
  name: service
spec:
  runs: always
  trigger: [request]
```

```yaml
# catalog/package-types/cli.yaml
apiVersion: catalog.getnereus.dev/v1alpha1
kind: PackageType
metadata:
  name: cli
spec:
  registries: [pypi, npm, oci]
```

**The commands follow ADR 0013** (command conventions): `nereus catalog <kind> <verb> <name>`, kinds singular, `workload` the Reef's default kind; `apply` from files, `create` from flags, `list --type`, `get`, `delete`, and `check`. Output lines name the object by its full path with the owner and the type in a parenthesis:

```text
# Register what the repository says it has
$ nereus catalog apply --from-file catalog/
catalog/workloads/triton created (owner: Project/triton, type: service)
catalog/workloads/openbao created (owner: Project/nereids, type: controller)
catalog/packages/nereus created (owner: Project/core, type: cli, registry: pypi)
catalog/packages/openbao-image created (owner: Project/nereids, type: image, registry: oci)

Next steps:

  nereus catalog check

# Search by type
$ nereus catalog list --type static-site
WORKLOAD  OWNER         TYPE         AUDIENCE  DELIVERIES  STATUS
docs      Project/docs  static-site  people    0           Ready
```

**The catalog lists what it has, one row per Workload,** and `DELIVERIES` counts the Workload's Deliveries, read from the delivery Reef and never written. What was deployed, one row per Workload and Environment pair, is `nereus delivery list` (ADR 0020).

**`nereus catalog check` is deterministic:** it joins each entry to the tenancy tree, the types, the registries, and the Reefs and Mandates that fulfil it. It fails on a contradiction, when the file says something impossible (a registry the type does not allow, an `owner` that does not exist), and only points at a gap, when the catalog tells the truth and the platform cannot fulfil it yet, each gap with its issue, `!` instead of `✗`. On Nereus today it finds three gaps and no contradiction, and a PR passes with gaps:

```text
$ make catalog-check
✓ tenancy: 1 organization, 5 projects, every owner resolves
✓ types: every workload type and package type resolves, every registry allowed
! catalog/workloads/triton: audience people, agents, no edge reef (#470)
! catalog/workloads/triton: uses nats, no messaging reef (#576)
! catalog/packages/nereus: not found on pypi
0 contradictions, 3 gaps
```

`make catalog-check` joins the local checks before a PR that touches the catalog or the tenancy (`docs/agent/rules.md`), since CI is off.

**Registering an existing thing is `apply`; a template comes before the catalog.** The catalog entry is a file in the repository and the file is the truth, so Triton, which already exists, is imported with `nereus catalog apply --from-file catalog/`. A template writes files into a folder, new or existing, including the new `catalog/workloads/<name>.yaml`, and the same `apply` registers the new entry and leaves Triton `unchanged`. Creating the repository is #279 (the repository Reef). `--template` leaves the catalog's `create`. The golden-path slide of #541 (the Developer Control Plane deck) shows that order, the template first (the next Nereid of the backlog, `edge-cloudflare` of #470, in place of `hello-api`) and `catalog apply` second. `create` with flags stays for writing the file (`--dry-run --output yaml`).

**`Template` is a kind of the catalog,** and `nereus template` is a shortcut of `nereus catalog template` (ADR 0013); this replaces the owner's decision of 2026-10-30 that templates are a Reef of their own. The verb is `render`, with Copier: `create` makes the `Template` object and `apply` takes only files. There is no `type` field in the first slice, since Copier treats every template the same.

```text
# Write a template's files, then register what they say
$ nereus template render python-service \
    --path ./hello \
    --param name=hello
✓ catalog/templates/python-service rendered at ./hello

Next steps:

  nereus catalog apply --from-file ./hello/catalog/
```

**A current owner in the CLI's config (a proposal, owner's ask):** a command sets the current Project, and other repeated references, so `--owner` becomes optional when several resources are created for the same service or Project, as `kubectl config set-context --current --namespace` and `gcloud config set project` do; the flag wins over the config, and the output line names the owner used. The shape, `nereus config set owner project/triton`, goes into `docs/agent/cli.md` with the catalog's commands.

**The first slice, three pull requests (owner, 2026-11-03, #574):** the kinds, the commands and six entries, Workloads `triton`, `openbao`, `keycloak` and `flux`, Packages `nereus` and `openbao-image` (#902); `catalog check` and `make catalog-check` (#903); one `catalog` Nereid, in an image of its own as every Nereid since #611, writing `status`: a Workload's readiness, a Package's presence in its registry, the resolved commit of a `source` (#904).

## Prior art

- **Open Application Model, workload types** ([oam-dev/spec, 4.workload_types.md](https://raw.githubusercontent.com/oam-dev/spec/master/4.workload_types.md)): a workload type carries characteristics as labels, `replicable`, `daemonized` ("if the workload exits, this is considered a fault, and the system must fix it"), `exposed` ("have a service endpoint with a stable name for network traffic") and `podspecable`; the catalog's `runs` and `audience` are those two characteristics with the owner's words, and `trigger` is the project's own addition. In OAM a "trait" is an operational add-on, which is why the catalog says characteristics, as plain fields.
- **Backstage's system model** ([backstage.io, System model](https://backstage.io/docs/features/software-catalog/system-model)): "A component is a piece of software, for example a mobile feature, web site, backend service or data pipeline", with `API`, `Resource`, `System` and `Domain` around it; the catalog takes the idea of a repository-owned entity and replaces `Component` with the lifecycle split and the characteristics, `System` and `Domain` with the tenancy tree (ADR 0015), and `Resource` with the resource Reefs' own Instances (ADR 0017).
- **Copier** ([copier.readthedocs.io](https://copier.readthedocs.io/en/stable/)): "A library and CLI app for rendering project templates", whose goals include bringing existing projects up to date as a template changes; the engine behind `nereus template render`.
- **Kubernetes storage classes** ([StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)): "a way for administrators to describe the classes of storage they offer", a name plus a `provisioner` and `parameters`, created by administrators; a `WorkloadType` and a `PackageType` are configurable the same way, a name plus the answers it fills in, with the platform reading only the answers.
- **Knative Serving** ([knative.dev, Serving](https://knative.dev/docs/serving/)): revisions "automatically scaled up and down according to incoming traffic", down to zero; the `function` type takes that shape, `runs: once` on each `request` or `event`.
- **Flux's `GitRepository`** ([fluxcd.io, GitRepository](https://fluxcd.io/flux/components/source/gitrepositories/)): `spec.ref` with `branch`, `tag`, `semver`, `name` and `commit`, "with latter listed fields taking precedence over earlier ones"; `source.ref` takes the same fields and precedence.
- **kubectl's verbs and `kubectl config set-context`** ([Kubernetes, Managing Kubernetes objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/object-management/)): `apply` from files as the way to register what a repository declares (ADR 0013), and a current context that spares a repeated flag, the model of the current owner in the CLI's config.

The claim that types alone strain on Nereus's own entries (a Nereid is a `worker` only by elimination, the docs site needs "files only" on day one, Triton is both a service and the room's operator) is the project's own observation, from modelling the catalog on the repository and the live cluster.

## Consequences

- The platform acts on three answers it can check, never on a type's name: a new kind of software is a new `WorkloadType` file, not a change to the Reef, and `catalog check` stays deterministic.
- Every Workload says who talks to it; `catalog check` can join `audience` to the edge and authentication Reefs and say what is exposed with nothing publishing it, which is Triton today (#470).
- The catalog never writes a Nereid's tool: the Keycloak server, a database or a topic reach it as Instances of their Reefs; one writer per field holds (ADR 0005), the repository's file writes `spec`, the `catalog` Nereid writes `status`.
- The golden path is two commands of one Reef, a template that writes files and `catalog apply` that registers; the deck of #541 (the Developer Control Plane deck) and `docs/agent/cli.md` adopt the catalog's commands, kinds singular, `--owner` and the structured `ref`.
- `catalog check` becomes a local check before a PR, and its three gaps of today are the next work: #470 (publishing a Reef's endpoint at a hostname), #576 (the messaging Reef), publishing the CLI on PyPI.
- The proposal on the Drive used `spec.project`, `site`, `web` and a one-string `ref`; this ADR replaces them with `owner`, `static-site`, `web-app` and the structured `ref`.

## What the `catalog` Nereid writes

Decided by the owner on 2026-11-03 (#904, the catalog Nereid writes status); `controllers/catalog/README.md` has every reason.

- **A Workload's readiness:** `runtime.kind: Nereid` reads the `Ready` condition of the core Nereid object it names; `runtime.kind: Deployment` reads the Deployment's availability.
- **A Package's presence:** `pypi` and `oci` are looked up, any other registry is Unknown (`RegistryNotChecked`); a lookup with no answer never reads as found or as absent.
- **The resolved commit:** `status.source.commit`, with its own condition `SourceResolved`, apart from `Ready`, from `branch`, `tag`, `name` or `commit`; `semver` stays Unknown until its issue. No credential reaches the Nereid until the scm Reef (#927, the GitHub App connection), so a private repository answers `SourceUnreachable`.
- **`nereus catalog check`** reads a Package's presence from `status` when the Nereid has answered that very spec, and looks up PyPI itself otherwise, so `make catalog-check` needs no Nereid.

## Open questions

- **How a Workload lists the resources it needs** (a database, a topic, a cache): the owner's idea of a chart carrying the Kubernetes objects plus a Score application spec makes Score a candidate format for that list, to weigh when the first resource Reef is built (ADR 0017).
- **`App`** (what people install: mobile, desktop, a browser extension) waits until Nereus has one to prove it on; the CLI stays a `Package` for people and programs.
- **The current owner in the CLI's config:** its command's shape and where the value lives (the CLI's own config, never the person's kubeconfig).

*Origin: the owner's decisions of 2026-10-30 in a design session on the catalog (#559, the catalog Reef: Workload, Package and their types), tenancy (#21, Organization and nested Projects) and the resource Reefs (#560, the resource Reefs and how a Mandate picks their Nereid); raw data in Drive `#pontos/beach/opinions/2026-10-29/`, `#pontos/beach/opinions/2026-10-30/` (the brief, the opinions, the research and the YAML proposal) and `#pontos/raw/2026-10-29/`.*

*Rewritten 2026-11-03 from the owner's decisions of 2026-11-02 and 2026-11-03 (#835, the delivery model of the internal-developer-platform profile; #843, the delivery Reef's ADR): `runtime.namespace` and the running image, `spec.chart`, the `Template` kind and the `DELIVERIES` column; raw data in Drive `#pontos/raw/2026-11-02/` and `#pontos/raw/2026-11-03/`. Amended the same day (owner, #574): one image per Nereid, so `openbao-image` replaces the `local-nereids` image, which #611 had already retired.*
