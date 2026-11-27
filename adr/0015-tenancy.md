# 0015. Tenancy: a tenancy Reef whose kinds come from each instance, with one fixed shape

!!! note "In short"
    Tenancy is a Reef whose kinds come from each instance, with one fixed shape: every kind is a tree node with an optional parent, and one kind is the boundary. Status: Proposed (2026-10-30, rewritten 2026-11-12, amended 2026-11-15).

**Status:** Proposed (2026-10-30, rewritten 2026-11-12, amended 2026-11-15)

## Context

Nereus is born multi-tenant (#21, Organization and nested Projects): the tenancy model is part of the product, not something added later. On 2026-10-29 the owner settled its levels: an **Organization** is the top level of separation, the boundary of people, permissions and isolation; a **Project** always sits under an Organization, and a Project may sit under another Project. Nested Projects take the place of Backstage's Domain and subdomain, and a leaf Project plays the part of Backstage's System, so there is no `System` kind.

The catalog Reef (#559, the catalog Reef: Workload, Package and their types) and the resource Reefs (#560, the resource Reefs and how a Mandate picks their Nereid) both need to say whose a thing is, and that question could not be answered until two others were: whether a Project is a Kubernetes namespace, and where the tenancy kinds live.

**A namespace does not fit.** A namespace exists once per cluster and does not nest. A Project nests (`nereus` holds `triton`), and the same Project runs in several environments: the Triton of `nereus` (the kept k3d cluster) and the Triton of a `pr-<n>` vcluster are one Project in two namespaces, on two clusters. Hierarchical namespaces would give the nesting but not the second cluster, and the project that provided them is archived.

**The kinds differ from one instance to another.** This instance of Nereus is organised as Organizations and Projects. A company with its own structure (departments and squads, say) may run its own instance of Nereus with its own tenancy kinds; what the platform must not do is force one vocabulary on every company, nor let the catalog break when the vocabulary changes. A Reef is a contract, an API group with its kinds (ADR 0002, ADR 0010), and ADR 0011 says an Instance's fields are common to every Nereid of the Reef. If the kinds were free, the catalog would have to reference any kind (`{apiVersion, kind, name}`), and `catalog check` would no longer know what a parent or a boundary is: the fixed thing has to be the shape of a kind, not its name.

## Decision

**Tenancy is a Reef, `tenancy.getnereus.dev/v1alpha1`, and its kinds come from each instance.** The group is fixed; its CRDs are applied from the instance's `reefs/tenancy/` as any Reef is (ADR 0010). This instance applies `Organization` and `Project`; another instance may apply its own kinds, and its catalog still works, because the contract is the shape of every kind of the group, not the kind names:

- **Every kind of the group is a node** with an optional `spec.parent: {kind, name}`; a node with no parent is a root. The kind of a parent is one of the group's own kinds.
- **One CRD of the group carries the annotation `tenancy.getnereus.dev/boundary: "true"`:** the kind that isolates (people, billing, isolation), as `core.getnereus.dev/default-kind` marks a Reef's default kind (ADR 0013, command conventions). Here it is `Organization`.
- **Whatever points to the tree names `owner: {kind, name}` inside the group,** never an apiVersion: the catalog's Workloads and Packages, an Environment of the environment Reef, a Mandate's `match`. The field replaces the `spec.project` of the first proposal.
- **`catalog check` climbs `spec.parent` to the root** without knowing the kinds: it resolves every `owner`, refuses a cycle or a parent that does not exist, and finds the boundary by the annotation.

On this instance:

```yaml
# reefs/tenancy/: the kinds of this instance, applied with nereus reef apply
# tenancy/organizations/getnereus.yaml: the boundary
apiVersion: tenancy.getnereus.dev/v1alpha1
kind: Organization
metadata:
  name: getnereus

# tenancy/projects/nereus.yaml: the monorepo, under the Organization
apiVersion: tenancy.getnereus.dev/v1alpha1
kind: Project
metadata:
  name: nereus
spec:
  parent: {kind: Organization, name: getnereus}
  repository: https://github.com/getnereus/nereus

# tenancy/projects/triton.yaml: a Project under another Project
apiVersion: tenancy.getnereus.dev/v1alpha1
kind: Project
metadata:
  name: triton
spec:
  parent: {kind: Project, name: nereus}

# catalog/workloads/triton.yaml: the catalog points to the tree by kind and name
apiVersion: catalog.getnereus.dev/v1alpha1
kind: Workload
metadata:
  name: triton
spec:
  owner: {kind: Project, name: triton}
```

Another instance, with its own kinds (a placeholder company, `acme.example.com`), keeps the same shape and the same catalog field:

```yaml
# that instance's reefs/tenancy/ applies Department (boundary) and Squad
apiVersion: tenancy.getnereus.dev/v1alpha1
kind: Squad
metadata:
  name: payments
spec:
  parent: {kind: Department, name: platform-engineering}

# its catalog, the same field
spec:
  owner: {kind: Squad, name: payments}
```

**The commands** follow ADR 0013: `nereus tenancy <kind> <verb> <name>`, built from the Reef's schema, as the release Reef's are; the output names the object by its full path, parents before children; `nereus reef apply` lists the kinds the Reef created (owner, 2026-10-30).

```text
# Apply the tenancy reef of this instance
$ nereus reef apply tenancy --from-file reefs/tenancy/
core/reefs/tenancy created (tenancy.getnereus.dev/v1alpha1: organizations, projects)

# The boundary
$ nereus tenancy organization create getnereus
tenancy/organizations/getnereus created

# A Project under the Organization
$ nereus tenancy project create nereus \
    --parent organization/getnereus \
    --repository https://github.com/getnereus/nereus
tenancy/organizations/getnereus/projects/nereus created

# A Project under another Project
$ nereus tenancy project create triton \
    --parent project/nereus
tenancy/organizations/getnereus/projects/nereus/projects/triton created

Next steps:

  nereus catalog apply --from-file catalog/
```

**A Project is not a namespace.** A Project is an object of the platform, cluster-scoped, with its parent in `spec`; the namespace is only where a Project runs, one per environment (`triton` on `nereus`, the kept k3d cluster, `triton` again on the `pr-<n>` vcluster). The API projects who may act on a Project into the namespaces where it runs; it has to stand in front of the Reefs in any case (ADR 0010, open question on the Platform API).

**The permissions are relations, in the authorization Reef.** The tenancy Reef holds the tree; who may do what on it is the authorization Reef's job, with its `openfga` Nereid (ADR 0027), permission flowing down the tree and never up. **One OpenFGA type, `node`, serves every tenancy kind** (owner, 2026-11-15, spec 0011, decision 11): the kinds come from each instance, and the model is fixed, versioned with the Nereid, so it cannot name them. A node's id is its kind in lowercase, a slash and its name (`node:project/triton`), and its `parent` is another node or, for a root, the one `instance`. A new tenancy kind on another instance changes no model, only tuples.

```text
type node
  relations
    define parent: [instance, node]
    define granted: [grant#subject with rule_matches]
    define can: granted or can from parent
```

The first sketch of this ADR had one OpenFGA type per tenancy kind, with an instance writing its own model over its own kinds; it was dropped because a model fixed with the Nereid could not follow each instance's kinds.

**The boundary kind carries `domains` and `requireMandate`** (owner, 2026-11-10, #1311). Both are optional fields of the kind annotated `boundary`, whatever its name; here, `Organization`. The authentication Reef reads them (ADR 0006): a login by e-mail finds the Organization by the address's domain, and the Organization's Mandate by `match` (ADR 0017).

```yaml
apiVersion: tenancy.getnereus.dev/v1alpha1
kind: Organization
metadata:
  name: acme
spec:
  domains: [example.com]
  requireMandate: true
```

- **`domains`:** the e-mail domains of the Organization. A domain counts only once verified: the Organization's admin publishes a DNS TXT record the API gives, and the API checks it. Until then the domain is `Unverified` in `status` and takes no part in the login's discovery or in `requireMandate`.
- **`requireMandate: true`:** an e-mail of the verified domains enters only with a token of the Mandate that matches the Organization. The API refuses the field while no authentication Mandate matches the Organization, so nobody is locked out.
- **A team is a `match` on Projects.** The tenancy has Organization and Project, no Team kind: a Mandate for "one or more teams" matches their Projects, until the tenancy gets teams.

**The first version has no tenancy Nereid:** the API keeps the tree, as it keeps the `core` kinds. A Nereid comes when the tree is synced from or to another system (Keycloak groups, a human-resources system); OpenFGA's tuples are written from the tree by the authorization Reef's `openfga` Nereid (ADR 0027). That work is what makes tenancy a Reef rather than two more kinds in `core`: `core` is the mechanism (Reef, Nereid, Mandate) and never has a Nereid.

**Sharing across Projects or Organizations goes by publishing or by access, never by a permission climbing the tree.** A Project runs its own copy from a published `Package` (a chart in an OCI registry, installed through the release Reef, as Keycloak is today), or talks to the running thing through its `audience` (Triton, for agents and people of any Project); the registry decides who pulls.

## Prior art

- **GitLab groups and subgroups** ([docs.gitlab.com](https://docs.gitlab.com/user/group/subgroups/)): one kind of node nests "up to 20 levels" (five or fewer recommended), and a member's permissions are "inherited from the group into all subgroups"; the Project that nests and the permission flowing down take that shape.
- **Google Cloud's resource hierarchy** ([docs.cloud.google.com](https://docs.cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy)): an organization at the root, folders that "can contain projects and other folders", and "IAM roles granted on a folder resource are inherited by all project and folder resources in that folder"; the Organization as boundary and the nested node come from here too.
- **Gateway API's `ParentReference`** ([`shared_types.go`](https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/main/apis/v1/shared_types.go)): "identifies an API object (usually a Gateway) that can be considered a parent of this resource (usually a route)", with `group`, `kind` and `name`, used by every route kind; `owner: {kind, name}` is that reference with the group fixed.
- **Kubernetes namespaces** ([kubernetes.io](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)): "Namespaces cannot be nested inside one another and each Kubernetes resource can only be in one namespace"; the reason a Project is not a namespace.
- **Hierarchical Namespace Controller** ([github.com/kubernetes-sigs/hierarchical-namespaces](https://github.com/kubernetes-sigs/hierarchical-namespaces)): "hierarchical policies and delegated creation to Kubernetes namespaces"; the alternative weighed and dropped, nesting inside one cluster only, with the repository archived in April 2025.
- **OpenFGA and Google's Zanzibar** ([openfga.dev](https://openfga.dev/docs/concepts)): an authorization model "combines one or more type definitions", each listing its relations, and a relationship tuple is "a user, relation, and object"; its model syntax "closely follows the original syntax in the" Zanzibar paper. The relations over the tree are written in that model.
- **GitHub's verified domains** ([Verifying or approving a domain for your organization](https://docs.github.com/en/organizations/managing-organization-settings/verifying-or-approving-a-domain-for-your-organization)): the owner of an organization proves a domain by following "the instructions under 'Add a DNS TXT record' to create a DNS TXT record with your domain hosting service"; the way an Organization's `domains` are verified.
- **Backstage's Domain, System and Component** are the model the owner reacted to (#21): nested Projects replace Domain and subdomain, and a leaf Project plays System's part; the project's own observation.

## Consequences

- `spec.project` becomes `owner: {kind, name}` in everything that points to the tree: the catalog's Workloads and Packages (#559), an Environment, a resource Instance and a Mandate's `match` (#560). The CLI gets a current owner in its config so `--owner` is optional when several things are created for the same Project (owner's ask, #559).
- A new Reef that needs to say whose a thing is reuses the field and the climb to the root; none of them learns a kind name.
- Each instance owns its `reefs/tenancy/`; the kinds of this instance (`Organization`, `Project`) are the reference ones, shipped with `nereus init`, and the first entries are Nereus itself: Organization `getnereus`, Project `nereus`, and `core`, `nereids`, `triton` and `docs` under it.
- Permissions are not free from Kubernetes RBAC: the API projects them into the namespaces where a Project runs, and the authorization Reef holds the relations.
- The output of `nereus reef apply` grows a list of the kinds it created, for every Reef.
- The boundary kind's shape grows two optional fields, `domains` and `requireMandate`; #1314 (the API accepts several issuers) builds `requireMandate`, and #1315 (identifier-first login) builds `domains` and their verification, deciding the TXT record's name and the `status` fields.

## Open questions

- **A depth limit:** a limit (four levels, for example) until a case asks for more, as #21 (Organization and nested Projects) suggested; not decided.
- **How permissions are projected** from a Project into the namespaces where it runs, per environment, and what the API does when a Project runs on a cluster it does not own.
- **The tenancy Nereid:** when the tree is synced with Keycloak groups or a human-resources system, which side is the source, and what `status` it writes on each node. OpenFGA's tuples are settled (ADR 0027): the tree is the source, and the authorization Reef's `openfga` Nereid reads it, so tenancy still needs no Nereid of its own for them.
- **The Organization of `nereus init`:** where the first Organization and Project come from on a fresh cluster (#21's "what the first slice becomes").
- **Two Organizations that claim one domain.** Recommendation for #1315: the first to verify it holds it, and the second is refused.

*Origin: the owner's decisions of 2026-10-29 (the levels, #21) and 2026-10-30 (a Project is not a namespace; a tenancy Reef with kinds per instance and one fixed shape), in a design session with a second opinion and research by subagents; raw data in Drive `#pontos/beach/opinions/2026-10-30/` (the session brief, the proposal as YAML, the opinions and research) and `#pontos/raw/2026-10-30/`.*

*Rewritten 2026-11-12 from the owner's decisions of 2026-11-10 (#1311: an Organization's `domains` and `requireMandate`, teams as a `match` on Projects) and of 2026-11-12 (a domain is verified by a DNS TXT record); raw data in Drive `#pontos/raw/2026-11-10/` and `#pontos/raw/2026-11-12/`.*

*Amended 2026-11-15 from the owner's decisions refining #897 into spec 0011 (decision 11: one OpenFGA type, `node`, for every tenancy kind; ADR 0027); raw data in Drive `#pontos/raw/2026-11-15/`.*
