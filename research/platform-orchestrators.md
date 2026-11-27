# Platform orchestrators

*Historical page (2026-10-19): it uses the model's words of that time (Interface, Implementation, `platform`); today's are Reef, Nereid and `nereus` ([The CLI design](../agent/cli.md)).*

Are we reinventing the wheel? "Native first, build last" ([vision](../vision.md)) asks, before building more of Nereus, whether an existing tool already does what it proposes. The page [Platform Orchestrators](https://internaldeveloperplatform.org/platform-orchestrators/) of internaldeveloperplatform.org calls the orchestrator the centrepiece of an Internal Developer Platform and, after Thoughtworks, describes these tools as offering published contracts between developers and platform teams, with variations self-served through configuration. That is close to what Nereus proposes, so this page compares the four orchestrators it lists (Humanitec, Kratix, KusionStack, Massdriver) and the open-source tools closest to the model (Crossplane, Radius, KubeVela, kro, and Score as a workload specification), as asked in #363 (evaluate the platform orchestrators). Every fact below comes from a page opened on 2026-10-19 and linked in [Learn more](#learn-more); what could not be verified is said so. Repository figures (licence, stars, last push, last release) were read from the GitHub API on that day.

## What Nereus proposes

The rows every tool is measured against, with where each is decided:

| # | Our proposal | Where it is decided |
|---|---|---|
| 1 | Interface, Instance, Class, Implementation, Tool; the API never names an Implementation | ADR 0002, ADR 0011 |
| 2 | The platform starts empty; capabilities are Implementations installed at runtime | ADR 0003, ADR 0010 |
| 3 | Each installed Implementation adds its own commands to the CLI | ADR 0004, ADR 0013 |
| 4 | One writer per field: the API writes `spec`, the Controller writes `status` | ADR 0005 |
| 5 | Swapping an Implementation (Keycloak for Auth0) keeps the same commands and API | ADR 0002, [Inception](../project/inception.md) |
| 6 | Cloud access as plans the person approves, no secret stored | [spec 0005](../specs/0005-cloud-reef.md) |
| 7 | CLI first, the portal after, `platform-mcp` for agents | `CLAUDE.md` |

## The comparison

| Tool | Licence and governance | Activity (2026-10-19) | Closest to our | Could Nereus be built on it? |
|---|---|---|---|---|
| Humanitec Platform Orchestrator | Commercial, "a SaaS solution operated by Humanitec", with a self-hosted option; Score and resource definitions are its open-source building blocks | No public repository of the Orchestrator to read; two documentation sets (v1 and a newer one) are live | Resource Type ≈ Interface, Resource Definition with a Driver ≈ Implementation, matching criteria ≈ Class | No: closed, hosted, and it would own the API |
| Kratix | Apache-2.0, created and hosted by Syntasso; Syntasso Kratix Enterprise adds support and a Backstage integration | 780 stars; pushed and released on 2026-10-19 | Promise = Interface and Implementation in one object | Partly, at the cost of fusing Interface and Implementation and of a GitOps state store |
| KusionStack (Kusion) | Apache-2.0, CNCF Sandbox (accepted 2024-09-12) | 1,323 stars; last push 2026-10-15; last release v0.15.0 on 2025-06-30; its docs call it an early project | Module ≈ Implementation, AppConfiguration ≈ an app declaration | No: client-side, application-centric, slow releases |
| Massdriver | Commercial; Business plan at $999/month for 15 seats, self-hosted only in Enterprise; its CLI `mass` is Apache-2.0 | `mass`: 112 stars, release 2.4.1 on 2026-10-14; the platform's own code is not in the public repositories seen | Bundle with typed connections ≈ Implementation with a contract | No: closed and paid |
| Crossplane | Apache-2.0, CNCF Graduated (2025-10-28) | 12,180 stars; release v2.4.2 on 2026-09-22 | XRD = Interface, Composition ≈ Implementation | Possible for the contract, rejected by ADR 0010; best as a Tool behind an Implementation |
| Radius | Apache-2.0, CNCF Sandbox (accepted 2024-04-16) | 1,667 stars; release v0.61.1 on 2026-09-30 | Resource Type = Interface, Recipe Pack = Implementation, Environment selects it | Possible for the contract; Recipes are templates, not Controllers with commands |
| KubeVela | Apache-2.0, CNCF Incubating (2023-02-27) | 7,915 stars; release v1.11.0 on 2026-07-20 | X-Definitions and addons ≈ Interfaces added at runtime | No: its centre is the Application (OAM), not a capability |
| kro | Apache-2.0, a subproject of Kubernetes SIG Cloud Provider; API at `v1alpha1` | 3,077 stars; release v0.9.4 on 2026-09-04 | ResourceGraphDefinition = an Interface and its composition | No as a base; a good Tool for an Implementation that composes Kubernetes resources |
| Score | Apache-2.0, CNCF Sandbox | `score-spec/spec`: 8,092 stars, 0.4.1 on 2026-05-25; `score-compose` 0.48.0 and `score-k8s` 0.21.0 on 2026-10-17 | A workload specification, the "app declaration" of the [vision](../vision.md) | Not a platform; a candidate input format for the Platform API |

How each covers the rows above, from the pages opened (✓ covers, ◐ covers in part, — not found in the pages opened). In row 4, ✓ marks a tool whose API is made of Kubernetes custom resources, so it inherits the `spec` and `status` convention ADR 0005 takes; none of the pages opened states a writer rule of its own.

| Tool | 1 Model | 2 Starts empty | 3 CLI grows | 4 One writer | 5 Swap | 6 Approved plans | 7 CLI, portal, MCP |
|---|---|---|---|---|---|---|---|
| Humanitec | ◐ | — | — | — | ✓ | — | ◐ |
| Kratix | ◐ | ✓ | — | ✓ | ◐ | — | ◐ |
| KusionStack | ◐ | — | — | — | ◐ | — | ◐ |
| Massdriver | ◐ | — | — | — | ◐ | — | ◐ |
| Crossplane | ✓ | ✓ | — | ✓ | ✓ | — | — |
| Radius | ✓ | ◐ | — | ◐ | ✓ | — | ◐ |
| KubeVela | ◐ | ✓ | — | ✓ | ◐ | — | ◐ |
| kro | ◐ | ✓ | — | ✓ | — | — | — |
| Score | — | — | — | — | ◐ | — | ◐ |

No tool covers rows 3 and 6: an installed capability that adds its own commands to the CLI as data (ADR 0004), and cloud access the person approves as a plan run with their own short-lived login, with nothing stored (spec 0005). Those two, with the strict split of Interface and Implementation that lets a whole running Controller be swapped, are what Nereus adds.

## Humanitec

**What it is.** The [product page](https://humanitec.com/products/platform-orchestrator) calls the Platform Orchestrator a "graph-based backend for your IDP" that unifies infrastructure management "for humans and AI agents", reached through a portal, a CLI, Terraform, Score and an API ("One API for every agent, developer, and pipeline"). The [documentation's overview](https://developer.humanitec.com/platform-orchestrator/docs/introduction/overview) says "The Platform Orchestrator is a SaaS solution operated by Humanitec"; the product page also offers a self-hosted option. It does not say the Orchestrator itself is open source; it lists Score and Resource Definitions as "OSS building blocks".

**How it maps.** A developer describes a workload once ([Dynamic Configuration Management](https://developer.humanitec.com/platform-orchestrator/docs/concepts/dynamic-configuration-management/)), and the platform builds its configuration per environment. A [Resource Definition](https://developer.humanitec.com/platform-orchestrator/docs/platform-orchestrator/resources/resource-definitions/) "defines how and when a Resource should be provisioned": a Resource Type (our Interface), a Driver (Terraform, Template, or a custom one, our Implementation) and matching criteria by environment type, application, environment, resource id or Resource Class (our Class, resolved from the scope as ADR 0002 asks). Swapping the Driver behind a Resource Type keeps what the developer wrote: row 5 is covered. Its [MCP knowledge server](https://developer.humanitec.com/platform-orchestrator/docs/platform-orchestrator/mcp-knowledge-server/) answers questions about the product and "cannot see data in your Orchestrator organization".

**What it lacks for us.** The Orchestrator owns the API and the model; an Implementation does not add commands to its CLI; the pages opened describe no plan the person approves with their own cloud login. Its activity could not be measured: there is no public repository of the Orchestrator.

**Built on it?** No. Adopting it would make a closed, hosted product the centre of an Apache-2.0 platform (ADR 0007, public by design), and its open parts (Score, Resource Definitions) are useful without it.

## Kratix

**What it is.** "Created by Syntasso, Kratix is an open-source platform framework", Apache-2.0 ([repository](https://github.com/syntasso/kratix)). Its [documentation](https://docs.kratix.io/) calls the Promise its core: a contract between the platform and application teams that bundles self-service APIs, embedded workflows and fleet management; Syntasso Kratix Enterprise adds support and a Backstage integration.

**How it maps.** A [Promise](https://docs.kratix.io/main/reference/promises/intro) has an API ("Promise APIs are Kubernetes Custom Resource Definitions (CRDs) under the hood", namespace-scoped only), dependencies installed on every matching Destination, `configure` and `delete` workflows (chains of containers) at Promise and at resource level, and destination selectors. A Promise is installed at runtime, so the platform grows one capability at a time (row 2), and the workflows write the result, keeping requests and their fulfilment apart (row 4). A [Destination](https://docs.kratix.io/main/reference/destinations/intro) is "the representation of a system that Kratix can write documents to": Kratix writes into a Git or bucket State Store, and a GitOps tool on the target cluster, "such as Flux or ArgoCD", applies them.

**What it lacks for us.** The Promise fuses our Interface and our Implementation: the API and the workflows that fulfil it ship together, so swapping Keycloak for Auth0 means editing or replacing the Promise, not installing a second Implementation into the same Interface and switching (row 5 only in part). Promises add no commands to a CLI; the pages opened describe no approved cloud plans.

**Built on it?** Partly possible: each Interface a Promise whose workflow calls the active Implementation. It would add a GitOps state store to every installation and a second, Syntasso-led framework under ours, for little the CRDs of ADR 0010 do not already give.

## KusionStack

**What it is.** Kusion is "an intent-driven Platform Orchestrator, which sits at the core of an Internal Developer Platform" ([repository](https://github.com/KusionStack/kusion), Apache-2.0), a [CNCF Sandbox project](https://www.cncf.io/projects/kusionstack/) since 2024-09-12. Its [documentation](https://www.kusionstack.io/docs/) says it is still early and iterating quickly; the docs shown are for v0.14, and the last release on GitHub is v0.15.0 of 2025-06-30.

**How it maps.** Developers write one AppConfiguration, "without needing to supply environment-specific values"; platform engineers build Modules that "abstract the complexity of underlying infrastructure tooling" and Workspaces per landing zone. The [documentation](https://www.kusionstack.io/docs/) calls it a "Pure client-side solution"; since v0.14 a Kusion Server offers the same as the CLI with a Developer Portal and REST APIs. [Projects](https://www.kusionstack.io/docs/concepts/project/overview) are folders with a `project.yaml`, usually kept in Git.

**What it lacks for us.** The centre is the application, not a capability with its own lifecycle; Modules are not running Controllers and add no commands; the pages opened describe no swap of an active Module across running Instances, nor approved cloud plans.

**Built on it?** No. Its slow release pace and application-first model make it a reference for the app declaration, not a base.

## Massdriver

**What it is.** "An internal developer platform that turns infrastructure-as-code into reusable, self-service components" ([documentation](https://docs.massdriver.cloud/)). Its [pricing page](https://www.massdriver.cloud/pricing) lists a Business plan at $999/month billed annually for 15 seats and an Enterprise plan with custom pricing and self-hosted support. Of its [public repositories](https://github.com/massdriver-cloud), the CLI [`mass`](https://github.com/massdriver-cloud/mass) is Apache-2.0; none of the repositories seen is the platform itself.

**How it maps.** A [bundle](https://docs.massdriver.cloud/concepts/bundles) is "a reusable, versioned definition of cloud infrastructure or application components": IaC (Terraform, OpenTofu, Helm, Bicep), its inputs (parameters and connections), its outputs, and policies. Typed contracts make sure "You can't connect a PostgreSQL database to a component expecting a Redis connection". The platform is "API-first", and developers wire bundles on a visual canvas.

**What it lacks for us.** Closed and paid; the portal comes first, not the CLI; a bundle is a template run by a pipeline, not a Controller that keeps running and serves commands; the pages opened describe no approved cloud plans.

**Built on it?** No.

## Crossplane

**What it is.** "Crossplane is a control plane framework for platform engineering" ([what's Crossplane](https://docs.crossplane.io/latest/whats-crossplane/)), Apache-2.0, [CNCF Graduated](https://www.cncf.io/projects/crossplane/) since 2025-10-28, the most mature tool here (v2.4.2, [repository](https://github.com/crossplane/crossplane)).

**How it maps.** A [composite resource definition](https://docs.crossplane.io/latest/composition/composite-resource-definitions/) "define[s] the schema for a custom API" (our Interface; namespaced by default in v2), and Compositions, pipelines of functions in YAML, KCL, Python or Go, fulfil it without writing a controller. "If more than one Composition references the same XRD, the composite resource must select which Composition to use"; an XRD sets a `defaultCompositionRef` or an `enforcedCompositionRef`: the swap of row 5, done in the cluster. Managed resources reach external systems, and the package manager installs providers, functions and shared configurations at runtime (row 2). ADR 0010 already took the shape of an XRD for an Interface.

**What it lacks for us.** A Composition renders resources; it is not a long-running Implementation (Keycloak, a `helm` Controller) that also serves commands. Crossplane has no CLI that grows with what is installed, no portal and no MCP of its own in the pages opened, and no plan the person approves with their own login: it acts with the credentials its providers hold.

**Built on it?** Possible: every Interface an XRD, every Implementation a Composition. ADR 0010 (Interfaces are objects added at runtime) rejected it because Crossplane would then be the platform and one of its Implementations at once, and an Implementation that is a running Controller (row 3, the commands) does not fit a Composition. This research finds no reason to reverse that: Crossplane is the strongest Tool for a `database` or `cloud` Implementation, not the base.

## Radius

**What it is.** An application platform with a `rad` CLI, "the primary means of interacting with Radius for both developers and platform engineers" ([concepts](https://docs.radapp.io/concepts/)), Apache-2.0, a [CNCF Sandbox project](https://www.cncf.io/projects/radius/) since 2024-04-16 (v0.61.1, [repository](https://github.com/radius-project/radius)). Its dashboard is built on Backstage.

**How it maps.** It is the closest match to our split. [Resource Types](https://docs.radapp.io/concepts/resource-types/) are defined by platform engineers as the contract between developers and the platform, each with an OpenAPI schema, "cloud provider agnostic". [Recipe Packs](https://docs.radapp.io/concepts/recipe-packs/) supply the implementation: "While a Resource Type defines the interface used to request a resource, a Recipe Pack defines the implementation", one Bicep or Terraform recipe per type, and "An Environment lists the Recipe Packs it uses". "Changing the Recipe Pack changes how resources are deployed without changing the applications that use them" is our row 5. Read-only properties (`host`, `port`) are "set by the recipe after the resource has been deployed", close to our `status`.

**What it lacks for us.** A Recipe is a Bicep or Terraform template run at deploy time, not a running Controller; installing a Recipe Pack adds no commands to `rad`; the pages opened describe no approved cloud plans; and it is pre-1.0. Its centre is the application, with the Environment selecting the implementation, where ours is the capability, with an active Implementation per Interface.

**Built on it?** Possible for the contract (an Interface as a Resource Type, an Implementation as a Recipe Pack), but it would leave out what makes an Implementation here: a Controller with its own lifecycle and commands. Worth following, and worth a conversation with its maintainers on the vocabulary.

## KubeVela

**What it is.** An application delivery platform built on the Open Application Model ([documentation](https://kubevela.io/docs/)), Apache-2.0, [CNCF Incubating](https://www.cncf.io/projects/kubevela/) since 2023-02-27 (v1.11.0, [repository](https://github.com/kubevela/kubevela)), with native multi-cluster delivery.

**How it maps.** An Application bundles Components, Traits, Policies and Workflow steps ([core concepts](https://kubevela.io/docs/getting-started/core-concept/)); each is backed by "programmable configurations called Definitions" that the platform team maintains, written in CUE, and "A package of OAM Definitions and Kubernetes CRD Controller is called an Addon": capabilities installed at runtime (row 2).

**What it lacks for us.** Everything is shaped around delivering one application; a capability like authentication or a cloud connection is not a first-class contract with swappable Implementations; addons add no CLI commands of their own in the pages opened; no approved cloud plans.

**Built on it?** No: it would make the application model the centre, where ours is the capability.

## kro

**What it is.** "Kube Resource Orchestrator (kro) is a subproject of Kubernetes SIG Cloud Provider" ([repository](https://github.com/kubernetes-sigs/kro), Apache-2.0), whose API "is currently at `v1alpha1`" and may break.

**How it maps.** A [ResourceGraphDefinition](https://kro.run/docs/overview) "is the blueprint for a custom API": kro "turns that definition into a CRD, watches for instances of that API", and infers the order of the resources it creates from CEL expressions ("You never declare resource order"). It is the lightest way to give an Interface a CRD whose Instances become several Kubernetes resources.

**What it lacks for us.** One RGD is one fixed composition: there is no second Implementation of the same API to switch to, no CLI, no portal.

**Built on it?** No as a base. A good Tool for an Implementation whose job is to compose Kubernetes resources (ACK, ASO, Config Connector, or plain Deployments), as an alternative to writing that Controller by hand.

## Score

**What it is.** "Score is a developer-centric and platform-agnostic workload specification" ([score.dev](https://score.dev/)), Apache-2.0, a CNCF Sandbox project, with reference implementations [`score-compose`](https://github.com/score-spec/score-compose) and [`score-k8s`](https://github.com/score-spec/score-k8s) ([specification](https://github.com/score-spec/spec)); Humanitec builds on it.

**How it maps.** One `score.yaml` says what a workload needs; an implementation turns it into Docker Compose or Kubernetes configuration per environment. It is not a platform; it is the shape of the "app declaration" the [vision](../vision.md) says the Platform API will compose into several Instances.

**Built on it?** Not a base, but a candidate input: the Platform API could read a `score.yaml` and turn each resource it requests into an Instance of an Interface, instead of inventing its own app file.

## Recommendation

**Build as now; do not adopt or build on any orchestrator as the base; use them as Tools behind Implementations, and consider Score for the app declaration.**

- **The model is not new, and that is good news.** Crossplane (XRD and Compositions), Radius (Resource Types and Recipe Packs) and Humanitec (Resource Types, Drivers and matching criteria) all split a contract from what fulfils it and let the fulfilment change without touching the request. Rows 1, 2, 4 and 5 are well-trodden; ADR 0002 and ADR 0010 already credit the same precedents. The docs should say so plainly, citing these tools, rather than present the split as an invention.
- **What no tool does is what Nereus is for.** None lets an installed capability add its own commands to the CLI (ADR 0004), none treats an Implementation as a whole running Controller swappable inside one Interface (ADR 0011), and none asks the person to approve the cloud plan and runs it with their own short-lived login (spec 0005). Building on Crossplane, Radius or Kratix would keep the contract and lose these, and would put a second framework, with its own vocabulary and release pace, under ours.
- **Adopting is ruled out by licence or maturity.** Humanitec and Massdriver are closed and paid, against ADR 0007 (public by design, Apache-2.0). KusionStack's releases have slowed, Radius is pre-1.0, kro is `v1alpha1`.
- **Native first still applies inside Implementations.** An Implementation that provisions cloud resources should use Crossplane or kro as its Tool rather than call cloud APIs by hand; a `database` Interface could have a Crossplane Implementation and a Radius-style Terraform one side by side. That is ADR 0010's position, and this research confirms it.
- **One idea worth taking.** Score is an open, CNCF workload specification for exactly the app declaration the Platform API will compose. Before designing our own app file, the owner may want a `Proposal` issue to evaluate Score as that input.

Nothing is adopted without the owner (#332, credit what we use). If the owner chooses to build on or adopt a tool, that decision becomes an ADR; otherwise this page is the record.

## Learn more

- internaldeveloperplatform.org, [Platform Orchestrators](https://internaldeveloperplatform.org/platform-orchestrators/): the definition and the four listed tools.
- Humanitec: [Platform Orchestrator product page](https://humanitec.com/products/platform-orchestrator); documentation [overview](https://developer.humanitec.com/platform-orchestrator/docs/introduction/overview), [Dynamic Configuration Management](https://developer.humanitec.com/platform-orchestrator/docs/concepts/dynamic-configuration-management/), [Resource Definitions](https://developer.humanitec.com/platform-orchestrator/docs/platform-orchestrator/resources/resource-definitions/), [MCP knowledge server](https://developer.humanitec.com/platform-orchestrator/docs/platform-orchestrator/mcp-knowledge-server/).
- Kratix: [documentation](https://docs.kratix.io/), [Promises](https://docs.kratix.io/main/reference/promises/intro), [Destinations](https://docs.kratix.io/main/reference/destinations/intro), [repository](https://github.com/syntasso/kratix).
- KusionStack: [documentation](https://www.kusionstack.io/docs/), [Projects](https://www.kusionstack.io/docs/concepts/project/overview), [repository](https://github.com/KusionStack/kusion), [CNCF project page](https://www.cncf.io/projects/kusionstack/).
- Massdriver: [documentation](https://docs.massdriver.cloud/), [bundles](https://docs.massdriver.cloud/concepts/bundles), [pricing](https://www.massdriver.cloud/pricing), [GitHub organisation](https://github.com/massdriver-cloud), [`mass` CLI](https://github.com/massdriver-cloud/mass).
- Crossplane: [what's Crossplane](https://docs.crossplane.io/latest/whats-crossplane/), [composite resource definitions](https://docs.crossplane.io/latest/composition/composite-resource-definitions/), [repository](https://github.com/crossplane/crossplane), [CNCF project page](https://www.cncf.io/projects/crossplane/).
- Radius: [concepts](https://docs.radapp.io/concepts/), [Resource Types](https://docs.radapp.io/concepts/resource-types/), [Recipe Packs](https://docs.radapp.io/concepts/recipe-packs/), [repository](https://github.com/radius-project/radius), [CNCF project page](https://www.cncf.io/projects/radius/).
- KubeVela: [documentation](https://kubevela.io/docs/), [core concepts](https://kubevela.io/docs/getting-started/core-concept/), [repository](https://github.com/kubevela/kubevela), [CNCF project page](https://www.cncf.io/projects/kubevela/).
- kro: [overview](https://kro.run/docs/overview), [repository](https://github.com/kubernetes-sigs/kro).
- Score: [score.dev](https://score.dev/), [specification](https://github.com/score-spec/spec), [`score-compose`](https://github.com/score-spec/score-compose), [`score-k8s`](https://github.com/score-spec/score-k8s).
