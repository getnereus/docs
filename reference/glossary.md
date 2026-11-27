# Glossary

The project's words and acronyms, one line each. A new term enters in the pull request that introduces it; a borrowed term links its source (#332).

## The project

| Term | Meaning |
|---|---|
| Nereus | The project: a composable API platform, with an API and a CLI: Reefs add the APIs, Nereids look after them, installed at runtime. An Internal Developer Platform is one profile of it. Organisation `getnereus`, domains `getnereus.dev` (development) and `getnereus.app` (production). After [Nereus](https://en.wikipedia.org/wiki/Nereus), the old man of the sea. |
| Nereus API | `nereus-api`, the platform's own HTTP API in the cluster (`api/`, #607): `GET /v1/me` answers who a token names, after checking it against the default authentication Mandate; `GET /v1/status`, what `nereus status --output json` prints (#739). |

## The model

Words of ADR 0002 (Conceptual model) and ADR 0011 (Reefs, Nereids and Mandates; `nereus reef`, `nereus nereid`, `nereus mandate`), used exactly.

| Term | Meaning |
|---|---|
| Reef | A capability of the platform (`auth`, `secrets`, `release`), an API group. Added with `nereus reef apply`; a `Reef` object of `core.getnereus.dev/v1alpha1`; its own kinds live in `<reef>.getnereus.dev/v1alpha1` (ADR 0009). Legacy: Interface. |
| Nereid | What looks after a Reef (`keycloak`, `auth0`, `reference-release`): a controller installed in the platform with `nereus nereid apply`; a `Nereid` object of `core.getnereus.dev/v1alpha1`. Legacy: Implementation. |
| Mandate | Binds one Reef to one Nereid and may make it the default; `nereus mandate create`, after Gateway API's [`GatewayClass`](https://gateway-api.sigs.k8s.io/reference/api-types/gatewayclass/). A `Mandate` object of `core.getnereus.dev/v1alpha1` (`azure` binds the `cloud` Reef to the `azure` Nereid). Legacy: Class. |
| Profile | A named list of Reefs, Nereids and Mandates applied on top of core (`core`, `internal-developer-platform`, `reference`, `secrets`); `nereus init --profile`, `nereus profile apply` (ADR 0014). |
| thetis | The installer Nereid: run by the chart `nereus` when a profile is set, it installs the profile's Reefs, Nereids and Mandates in order. |
| Instance | One occurrence of a Reef: a login for a team, a database for an app in an environment. |
| Repository (release Reef) | Where a chart comes from: a Helm repository (`http`), an OCI registry (`oci`) or Git (`git`), with an optional secret of the secrets Reef; a kind of `release.getnereus.dev/v1alpha1` (ADR 0010). `flux` writes it as a Flux [`HelmRepository`](https://fluxcd.io/flux/components/source/helmrepositories/). |
| Source (release Reef) | What is released: a chart of a Repository at a version (later Kustomize or plain manifests); a kind of `release.getnereus.dev/v1alpha1` (ADR 0010). |
| Target (release Reef) | Where a release goes: a namespace of an environment (`environmentRef`) or, with none, of the cluster Nereus runs in; a kind of `release.getnereus.dev/v1alpha1` (ADR 0010). |
| Connection (scm Reef) | One organisation of a source host, reached through the App its scm Mandate names (`--param identity=<authentication mandate>`); its status says whether the App is installed there, on every repository, with the permissions it needs (ADR 0024, #1281). `nereus scm connection create`. |
| Registry (registry Reef) | A registry of images that runs in the cluster, a kind of `registry.getnereus.dev/v1alpha1` (ADR 0021). Not the Nereid registry (#22), the public site listing Nereids. |
| Release (release Reef) | A Source running in a Target, with its values, made by the Nereid of its Mandate; a kind of `release.getnereus.dev/v1alpha1` (ADR 0010). `flux` writes it as a Flux [`HelmRelease`](https://fluxcd.io/flux/components/helm/helmreleases/). `nereus release <verb>` is `nereus release release <verb>`: a kind named after its Reef takes the Reef's verbs. |
| Controller | The mechanism: each Nereid runs as a [Kubernetes controller](https://kubernetes.io/docs/concepts/architecture/controller/) that reconciles and writes `status`. Used in ADRs, code and repository names, not in commands. |
| Tool | What a Nereid works with: the `helm` binary, the Auth0 Management API. |
| Vendor | An attribute: whose thing it is (Auth0, AWS, local). |
| Concept | Former word for Reef (then Interface), before ADR 0011. |
| Default Mandate | The one a Reef's commands go to when several Nereids look after it (#72); formerly the active Implementation. |
| Good Citizen | The rules every Nereid must follow, checked by the platform (spec 0003). |
| Conformance | Whether a Nereid honours its Reef's contract: labels at add, the contract call at start, a suite before the catalog (spec 0003). |

## The platform

| Term | Meaning |
|---|---|
| `nereus` | The CLI binary (formerly `nereus`). |
| Control Plane | The owner's name for the Nereus API as Nereids see it: what they talk to through events, subscribing to and sending to topics set when their Nereid is added (#254). |
| Triton | The switchboard operator of the agents (`controllers/triton`): lists who is connected, keeps the rooms where a team's agents talk as peers (a JetStream stream per room, #1417), and carries the owner's orders to an agent. After [Triton](https://en.wikipedia.org/wiki/Triton_(mythology)), herald of the sea. |
| Nereus API | The one door every client goes through (CLI, portal, agent), installed by the chart `nereus` (ADR 0018, the Nereus API as the one door). Formerly Platform API. |
| Progress lines | What `nereus init` prints of its steps: one line each, with a mark, detail and time; drawn live on a terminal, the running one spinning (#88, #379). A cloud target sums them in three lines at the end, and its plan turns each numbered line into a `✓` and its time as it runs. |
| Scene | The end-to-end script of the current slice (`test/scene`), run on a throwaway k3d cluster, locally and in CI. |
| Platform orchestrator | The centrepiece of an IDP in [internaldeveloperplatform.org](https://internaldeveloperplatform.org/platform-orchestrators/)'s words: published contracts between developers and platform teams; compared in [Platform orchestrators](../research/platform-orchestrators.md). |
| Promise | [Kratix's contract](https://docs.kratix.io/main/reference/promises/intro): an API (a CRD) and the workflows that fulfil it, in one object. |
| Recipe Pack | [Radius's implementation](https://docs.radapp.io/concepts/recipe-packs/) of its Resource Types, one Bicep or Terraform recipe per type, chosen by the Environment. |
| Score | A [workload specification](https://score.dev/) (`score.yaml`), a candidate for the app declaration the Nereus API composes. |
| Session | A live collaboration: people join with a code, contribute together, and every screen updates live (#217, #223). |
| Slice | A thin end-to-end piece that ends with something a person can run from the CLI; one spec each (`docs/specs/`). |
| Undercloud, overcloud | The local k3d cluster that seeds the platform, `<installation>-undercloud` (`tailwind-undercloud`) when `nereus init --target <name>` bootstraps a cloud (`nereus` otherwise), and the cloud cluster it moves into, AKS (#61, #263, spec 0005). |
| Cluster role | `undercloud` or `overcloud`: the label `core.getnereus.dev/cluster-role` of the nereus namespace, written by `init` and kept apart from the installation's identity so the pivot never carries it (#263). |
| Pivot | The move of the platform from the undercloud to the overcloud, as in Cluster API's [`clusterctl move`](https://cluster-api.sigs.k8s.io/clusterctl/commands/move) (#61). |
| Inception | The platform building, running, measuring and telling its own construction (#24): its services run on itself, its metrics and agent records come through its own tools (#137), and it learns from how its owner suggests (#138). A lens: how could each practice become a native capability. |
| Lean Inception | The workshop ([Paulo Caroli's method](https://martinfowler.com/articles/lean-inception/)) that shaped the MVP (#79, `docs/inception.md`). |
| One writer per field | ADR 0005: the API (or the CLI) writes `spec`, the Nereid writes `status`, after Kubernetes' [spec and status](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md#spec-and-status). |
| Pinned version | The version of a Reef's kinds a CLI ships and `nereus reef apply` applies (`cloud` 0.1.0, in `cli/src/nereus/interfaces/`); `apply --path` or `--image` apply another (#264). |
| Reef package | An OCI artifact whose layers are a Reef's CRDs as YAML (`application/yaml`), which `nereus reef apply --image` reads (#264). |
| Pinned by digest | An image recorded as `<repository>@sha256:...`, the digest of the manifest its labels were read from, not a tag that can be pushed again (#126, spec 0003 rule 3). |
| `cloud` Reef | The connection to a cloud: an account, optionally the organization above it, and the identity the platform presents; `azure` is its first Nereid (spec 0005). |
| Workload identity | A pod trades the token its cluster signs for its service account at the cloud for a token of an identity, then calls the cloud as that identity; the platform projects that token into every Nereid that requires `cloud` (spec 0005, #310). |
| Workload identity federation | A cloud trusts tokens a cluster signs for one service account and trades them for its own, so the platform keeps no secret (spec 0005; [Microsoft Entra](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation)). |
| Discovery document | `/.well-known/openid-configuration`: names the issuer and where its JWKS is. |
| Bootstrap plan | The plan the `cloud` Nereid makes when the undercloud's issuer is not published: the resource group, issuer storage and container, the person's grant on it, the issuer documents, then the first identity (spec 0005, #263). |
| Names plan | The read-only plan the `cloud` Nereid publishes before the bootstrap plan, checking every name at once; `init` runs it with no question, and a `404` is an answer, not a failure (spec 0005, #263). |
| Service principal | What roles are granted to in Entra ID; a managed identity has one, as an app registration does. |
| App registration | An application's definition in Entra ID; spec 0005 needs none for now. |
| Access entry | What a Reef needs from the cloud, its identity and optionally a role on a scope, kept in the `Cloud` Instance's `spec.access` once a person approves it (spec 0005). |
| Location | Where an installation's resources are created, in the cloud's words (`northeurope`, `eu-west-1`): the `Cloud` Instance's `spec.location`, from `--param location=<region>` or the Tool's default (`az config set defaults.location=<region>`) (#319). |
| Requester tags | The tags every cloud resource the platform creates carries: installation, who asked, request id, Instance and the purpose the contract fixes; for attribution, never authorisation (spec 0005, #155). |
| Installation | One running platform, named once (`tailwind`): the name never changes, names its `Installation` object and is part of every name the platform creates; an id (random UUID v4) never changes either; an alias that listings show may. Undercloud and overcloud are one installation across the pivot (#154, #251). |
| Installation alias | What listings show of an installation, free text (`Tailwind Prod`) changed by `nereus config installation set --alias`; no resource name changes (spec 0006). |
| Invitation | A link and QR code that let one person into a Nereus, a kind of the `authentication` Reef (`nereus authentication invitation create`, alias `nereus invitation create`); the link and the access expire separately (`--invitation-expires`, `--access-expires`), and accepting creates a core `User` ([spec 0007](../specs/0007-invitation.md)). |
| Naming override | A name a person gives instead of a generated one that is taken (`issuer.storage`, `state.storage`, `secrets.vault`), kept in `spec.naming.overrides` of the installation and validated against the resource's rules (spec 0005, spec 0006). |
| Plan | The cloud requests a `cloud` Nereid publishes in its Instance's `status.plans[]` for the CLI to run with the person's login, each a method, an `https` URL and a JSON body, shown and approved first; untrusted input, checked against the request protocol's limits (`cli/src/nereus/plans.py`, spec 0005). |
| Stalled | The condition a Nereid sets `True` when it refuses an Instance as it is and plans nothing until its spec changes, with a reason, a message, the `observedGeneration` and, when known, the refusal's `cause`, `check` and `fix` (ADR 0012); `nereus nereid apply` stops on it and prints why, one line per field, after Kubernetes' [kstatus](https://github.com/kubernetes-sigs/cli-utils/blob/master/pkg/kstatus/README.md) (spec 0005, #318, #327). |
| Request id | `r-` and a lowercase [ULID](https://github.com/ulid/spec) (`r-01jaqb…`), sortable by time: the CLI writes one for each access entry and on every object it writes (`<API_GROUP>/request`); the entry's plan carries it and `spec.approved` records it once the plan ran; listings show its first 6 characters after `r-` (spec 0005, #307). |
| Naming function | The one place that turns the naming table of spec 0005, the installation's name and id, and its overrides into full names (`tailwind-platform`, `tailwind-cloud-provisioner`, `tailwind-undercloud-azure`, `issuers<id16>`); automation receives the full name, never composes one (`cli/src/nereus/naming.py`, #307). |
| Cloud resource identification | The attributes every cloud resource the platform creates carries: installation id and name, requester id and name, request id; names only when a compliance policy allows (#155). |
| Request protocol | How a Nereid reaches a cloud before it has an identity: it publishes a plan, and once approved the CLI runs it on the person's machine with their own short-lived login, from a Tool entry fixed in the CLI (`az` first); the token never leaves the machine. Limits: `https`, the Tool's hosts (issuer storage only for the issuer's documents), no header but `Content-Type`, bodies up to 64 KiB, at most 50 requests, substitutions only from an earlier answer into a string value (#82, #264, spec 0005). |
| Managed identity (user-assigned) | An Azure identity created as a resource, with no secret to keep; one per Reef and per installation, `<installation>-<reef>-<role>` (`tailwind-secrets-reader`), the same across the pivot (#82, spec 0005). |
| Federated credential | A trust on a cloud identity: tokens from one OIDC issuer, for one subject (a Kubernetes service account) and audience, are exchanged for the identity's access, with no secret stored (#82, #93). |
| OIDC issuer | The URL whose discovery document and JWKS let a cloud verify a cluster's service-account tokens; a k3d undercloud publishes its own on a public storage container, AKS has one built in (#82). |

## Access

Words of ADR 0027 (teams, roles and Users).

| Term | Meaning |
|---|---|
| User | A person, one core `User` whatever the login; a login with no User has no permission. |
| Team | A group of people who work together; a `Team` of the `teams` Reef. Joining it grants its access, leaving removes it. |
| Member | One person in a Team, pointing to their User; a `Member` of the `teams` Reef. |
| Position | A free, lowercase name on a Member (`tech-lead`); a Binding that names it follows whoever holds it. |
| Role | A list of rules, `<reef>:<kinds>:<verbs>`; a `Role` of the `authorization` Reef. |
| Binding | Gives a Role to a Team, a Position or, as the exception, one User, on one node of the tenancy tree; access flows down the tree. |

## Ways of working

| Term | Meaning |
|---|---|
| Board, queue | Project v2 #1 of `getnereus`: its order is the plan; `scripts/board/queue` reads and changes it. |
| Claim | `queue claim <issue>`: assigns the issue and sets `In Progress` in one step. |
| Handoff comment | The last step, the next step and the open decision, left on the issue before stopping. |
| Walking skeleton | Ship a thin end-to-end slice first, then widen it ([Alistair Cockburn](https://wiki.c2.com/?WalkingSkeleton)). |
| Osmotic communication | Everyone works in one room and overhears the others, so information flows unsent; Triton's room on NATS does the same for agents. Alistair Cockburn's term in *Crystal Clear* ([the book](https://en.wikipedia.org/wiki/Alistair_Cockburn)). |
| Dogfooding | [Eat your own dog food](https://en.wikipedia.org/wiki/Eating_your_own_dog_food): the project builds itself with the platform, first user of each capability (`vision.md`). |
| Conventional Commits | The commit message format every commit follows: `<type>(<scope>)!: <description>` ([conventionalcommits.org](https://www.conventionalcommits.org/en/v1.0.0/)), checked by Commitizen through `scripts/check-commit-message`. |
| Commitizen, `cz` | The tool that checks the commit format and computes the version from the commits (`cz.yaml`, which reads the version from the tags `v<x.y.z>`, #186; bumps and releases in #55). |
| Copier | The open-source project template tool ([copier.readthedocs.io](https://copier.readthedocs.io/), MIT) behind `templates/nereid`: `scripts/nereid/new` renders a new Nereid with it, and `copier update` brings a later change of the template as a diff (#752). |
| Cycle time | From claimed to closed ([The Kanban Guide](https://kanbanguides.org/)). |
| Lead time | From created to closed. |
| Work item age | How long an `In Progress` issue has been open ([The Kanban Guide](https://kanbanguides.org/)). |
| #NoEstimates | No sizing: forecasts from what was delivered (#95). |
| Fitness function | An automated check that a quality of the architecture holds, from [*Building Evolutionary Architectures*](https://evolutionaryarchitecture.com/) (Ford, Parsons, Kua) (#50): `init --check-slo` in the scene fails CI when `init` misses its SLO by more than the tolerance (#141); the swap step fails it when swapping a Nereid changes a command (#124). |
| Installation | One platform with its own identity: a name and an id that never change and an alias that may, in the `Installation` object the first `nereus init` creates; undercloud and overcloud are one installation (spec 0006). |
| SLO (service level objective) | A target a quality must meet ([Google SRE book](https://sre.google/sre-book/service-level-objectives/)); the first is the time `nereus init` may take: 8 minutes on k3d, 20 on a cloud, in the `ServiceLevelObjective` object with defaults in code (spec 0004, provisional). |
| Band | The colour of `init`'s clock by the share of its time objective used: green, yellow from 50%, orange from 75%, red past 100% (spec 0004). |
| Tolerance | The share over the time objective (10%) past which the fitness function fails (spec 0004). |
| `proposed-by-agent` | Label of an issue an agent proposed, kept as its origin; waits for the owner's triage. |
| `triage/accepted` | The owner accepted a proposal (after Kubernetes' [triage labels](https://www.kubernetes.dev/docs/guide/issue-triage/)); a dropped one closes as `not planned`. When to do it is the board's order. |
| Illusion of certainty | An AI answer taken as settled when it is a guess; the AI should help teams learn faster, not create this illusion (Paulo Caroli, [*Times importam mais do que nunca*](https://caroli.org/livro/times-importam-mais-do-que-nunca/), `agent/ai-and-teams.md`). |
| Illusion of efficacy | Speed and output without direction, mistaken for progress (Paulo Caroli, [*Times importam mais do que nunca*](https://caroli.org/livro/times-importam-mais-do-que-nunca/), `agent/ai-and-teams.md`). |
| First reasonable idea | The trap of settling on the first idea that looks good enough; before a recommendation, the agent asks for alternatives, assumptions, unintended consequences, ignored signals and how it would fail (Paulo Caroli, [*Times importam mais do que nunca*](https://caroli.org/livro/times-importam-mais-do-que-nunca/), `agent/ai-and-teams.md`). |
| Learn faster together | The edge of a team that uses AI: not more output, but faster shared learning (Paulo Caroli, [*Times importam mais do que nunca*](https://caroli.org/livro/times-importam-mais-do-que-nunca/), `agent/ai-and-teams.md`). |

## Acronyms

| Acronym | Meaning |
|---|---|
| ACR, ECR, GHCR | Azure Container Registry, Amazon Elastic Container Registry, GitHub Container Registry. |
| ADR | Architecture Decision Record (`docs/adr/`, [Nygard format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)). |
| ARM | Azure Resource Manager: the API every Azure resource and role assignment goes through. |
| AKS | Azure Kubernetes Service. |
| C901 | The cyclomatic-complexity rule of `ruff` ([McCabe](https://en.wikipedia.org/wiki/Cyclomatic_complexity)); the limit here is 10 per function. |
| CEL | Common Expression Language: the validation rules inside a CRD (`self == oldSelf`). |
| CI | Continuous integration: `.github/workflows/ci.yaml` on every pull request. |
| CLI | Command-line interface. |
| CRD | CustomResourceDefinition: a kind added to the Kubernetes API (`cli/src/nereus/crds/`). |
| DCO | Developer Certificate of Origin: a sign-off on each commit (#19). |
| DORA | DevOps Research and Assessment ([dora.dev](https://dora.dev/)): its delivery metrics (deployment frequency, lead time, change failure rate, time to restore). |
| IAM | Identity and Access Management: who may do what in AWS and GCP. |
| IDP | Internal Developer Platform. |
| JWKS | JSON Web Key Set: the public keys an OIDC issuer publishes, so a token it signed can be verified. |
| k3d, k3s | k3s, a small Kubernetes distribution, run in Docker by k3d; the local cluster. |
| MVP | Minimum viable product: the waves in [What it offers](what-is-built.md). |
| OCI | Open Container Initiative: the image format and the Distribution API the CLI reads labels through. |
| OAM | Open Application Model: the application model [KubeVela](https://kubevela.io/docs/) is built on. |
| OIDC | OpenID Connect (ADR 0006, authentication). |
| OLM | Operator Lifecycle Manager ([olm.operatorframework.io](https://olm.operatorframework.io/)): a precedent for what an operator owns and requires. |
| PKCE | Proof Key for Code Exchange ([RFC 7636](https://www.rfc-editor.org/rfc/rfc7636)): protects the OAuth flow of a public client such as the CLI. |
| PR | Pull request. |
| RBAC | Role-based access control: roles granted on a scope, in Kubernetes and in Azure. |
| RGD | ResourceGraphDefinition: [kro's blueprint](https://kro.run/docs/overview) for a custom API, turned into a CRD. |
| SIEM | Security information and event management: where a security team searches logs. |
| SSE | Server-sent events: a server keeps an HTTP response open and pushes events down it, how every session screen updates live (#223). |
| STRIDE | Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege: the six threats a threat model asks about for each part ([Microsoft, "STRIDE model"](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)); the method proposed for #125. |
| STS | Security Token Service: where AWS and GCP trade a federated token for their own. |
| WIP | Work in progress. |
| XRD | CompositeResourceDefinition: [Crossplane's contract](https://docs.crossplane.io/latest/composition/composite-resource-definitions/), a precedent for Reefs. |
