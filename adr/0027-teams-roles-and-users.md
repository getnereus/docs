# 0027. Teams, roles and Users: a role is bound to a team, a position or a User on a node of the tenancy tree, and the Nereus API asks before it acts

!!! note "In short"
    A role is bound to a team, a position or a User on a node of the tenancy tree, and the Nereus API asks before it acts. Access roles, teams and Users are kept apart. Status: Accepted (2026-11-16).

**Status:** Accepted (2026-11-16)

## Context

Today the Nereus API admits one group of people, the Keycloak group `nereus-admins`, and refuses everyone else: there is no way to say that a person may list Environments in one Project and create them in another. #897 (refine the authorization Reef: an `openfga` Nereid answers who may do what) chose the tool; #1306 (decide how teams, roles and Users relate) asked for the model it serves, before the `teams`, `hiring` and `university` Reefs are designed (#1307, #1308, #1309).

Three earlier decisions frame it. ADR 0006 (authentication) makes the person a `User` of core, not an identity provider's `sub`, and says teams and authorization are the platform's job, outside the identity provider. ADR 0015 (tenancy) gives the tree, Organizations and nested Projects, whose kinds come from each instance, and sketches the permissions as OpenFGA relations over it. ADR 0013 (command conventions) gives the verbs a rule can name.

The owner's concern (2026-11-10, #1306): a person who signs in and belongs to groups that grant access overlaps with the `teams` Reef, a set of people who may or may not have a User. Keeping two lists, groups for access and teams for work, means keeping them in sync forever.

The first slice that builds this model is spec 0011 (the first slice of teams and authorization, the journey #1644); its decisions 1 to 19 are recorded here.

## Decision

**Three concepts, kept apart** (owner, 2026-11-10, #1306):

| Concept | Answers | Lives in |
|---|---|---|
| Access role | what may this person do on the platform? | the `authorization` Reef: `Role` and `Binding`, on the tenancy tree |
| Team | who does this person work with, in which position? | the `teams` Reef: `Team` and `Member` |
| A person's skills and courses | what does this person know? | the `teams` Reef's `Member`, read later by `hiring` and `university` |

"Profile" stays ADR 0014's word (the set of Reefs, Nereids and Mandates an instance installs); access is a **role**, and skills never go on core's `User`, since core is only the engine.

**`Team`, not `Group`** (owner, 2026-11-10). `Team` and `Member` live in the `teams` Reef, `Role` and `Binding` in the `authorization` Reef, `User` in core. There is **one list of members, and access derives from it:** a binding names a team, so joining the team grants its access and leaving removes it. An identity provider's groups are an output, never the source: a Nereid may later write Keycloak groups from the teams.

**A person is one `User` with several identities** (ADR 0006). The subject of every check is `user:<User name>`, never a `sub` or an e-mail, so the owner's Google, Microsoft and other accounts give the same access. **A token whose identity is linked to no `User` has no permission:** having a login is not having permission. An external candidate shows the split: they sign in, become a `User` and may apply to an opening, but belong to no team and hold no role.

**A member points to a `User` when the person has one** (owner, 2026-11-10), and the kind foresees members with none (an open position, a contractor, an agent). In the first slice a `Member` names a User and `spec.kind` takes only `person`; `agent` joins later with agents as subjects (`docs/agent/ai-and-teams.md`).

**A binding names a team, a position in a team, or, as the exception, one User.** The position is a free, lowercase name on the `Member` (`tech-lead`): when the person in the position changes, the access follows without touching a binding. #1307's `Position` kind (skills, level, places) takes the same name later, and neither the binding nor the tuples change.

**A team sits on one node of the tenancy tree** (`spec.owner: {kind, name}`, required, any node: an Organization or a Project), and **teams do not nest**: the tree already gives the hierarchy, and access flows down it.

**Roles are registered, never a fixed list** (owner, 2026-11-10). A `Role` is an object made of rules, and a rule is `<reef>:<kinds>:<verbs>`, each part a comma list or `*`, in the words the CLI already uses: the Reef as the CLI names it (`environment`, `core`), the kinds as the plurals of the routes (`environments`), the verbs of ADR 0013 plus `can-i`. It is Kubernetes RBAC's `apiGroups`, `resources` and `verbs` in Nereus's words.

```console
# A role from flags
$ nereus authorization role create release-manager \
    --rule release:releases:create,apply,delete
authorization/roles/release-manager created

# The developer role to a whole team, at a Project
$ nereus authorization binding create payments-developers \
    --role developer \
    --team payments \
    --owner project/payments
authorization/bindings/payments-developers created

# The team-lead role to whoever holds a position in the team
$ nereus authorization binding create payments-leads \
    --role team-lead \
    --team payments \
    --position tech-lead \
    --owner project/payments
authorization/bindings/payments-leads created

# The exception: one User, on the whole instance
$ nereus authorization binding create ana-admin \
    --role administrator \
    --user ana
authorization/bindings/ana-admin created
```

**Where a role and a binding hold** (#1306's first question). Both take an optional `spec.owner: {kind, name}`: a role with none serves the whole instance, and one with an owner serves that node and the nodes under it, as Kubernetes' `ClusterRole` and `Role`; a binding with none holds on the whole instance. A binding refuses a role whose owner is neither its own node nor an ancestor of it, and a role, team or User that does not exist.

**The roles** (#1306's fourth and fifth questions). `administrator` is built in: every verb on every kind of every Reef, present and future (`*:*:*`, so a Reef installed later is covered), never changed or deleted, so nobody locks the instance out by narrowing it. It is applied with the `authorization` Reef, not by `nereus init` as #1306 first said: core checks nothing until that Reef is installed, so the role arrives with the Reef that reads it. `viewer` (`*:*:list,get`), `developer` and `team-lead` are editable examples a person applies from the Reef's samples.

**Managing members is a rule like any other** (`teams:members:create,delete`), carried by a role: who may create a role, a binding or a member is itself a rule (#1306). **A position that a binding names is assigned only by who may create bindings at that binding's node**, so whoever manages members cannot give themselves more access than they hold.

**The objects are the source of truth; the `openfga` Nereid writes the tuples.** `Role`, `Binding`, `Team`, `Member`, `User` and the tenancy nodes are objects the Nereus API keeps, as it keeps tenancy; neither Reef has a Nereid for its objects, and neither `Role` nor `Binding` names OpenFGA (the API never names a Nereid). The `authorization` Reef's Nereid, `openfga`, reads the objects, computes the tuples and writes only the difference; deleting OpenFGA's store loses nothing, since one pass writes it again.

**One fixed OpenFGA model, versioned with the Nereid and tested with `fga model test`.** A new role becomes tuples, never a new model. **One OpenFGA type, `node`, serves every tenancy kind:** the kinds come from each instance (ADR 0015), and a fixed model cannot name them, so a node's id is its kind in lowercase, a slash and its name (`node:project/payments`), under one `instance:nereus`. A rule becomes a grant whose condition matches the request's Reef, kind and verb, so `*` covers what does not exist yet:

```text
type node
  relations
    define parent: [instance, node]
    define granted: [grant#subject with rule_matches]
    define can: granted or can from parent
```

The question is always one check, `user:<name>` `can` on the object's node (or on `instance:nereus` when it has no owner), with the context `{reef, kind, verb}`. The whole model, its tuples and its tests are in spec 0011, "The model".

**OpenFGA runs from its official Helm chart through the release Reef, with Postgres through the `Database` kind**, as the `keycloak` Nereid does: open source first, nothing new to invent.

**The Nereus API asks before every read and write**, through the `authorization` Reef's default Mandate, never OpenFGA by name: `POST /v1/check` to the Mandate's Nereid with `{user, verb, reef, kinds, node}`, answering `{allowed, bindings}`. A list keeps only the objects whose owner allows `list`. The routes that are always open (`/healthz`, `/v1/me`, `/v1/status`, `/v1/doctor`, `/.well-known/nereus-configuration`) are never asked. The check covers Environments and the tenancy tree too, which reach the platform through the Nereus API since #1638 and #1639.

**Fail closed: with the Nereid down, every read and write is refused**, except `whoami`, `status` and `doctor`. An outage must never become a way to read.

**`nereus-admins` is the emergency exit.** A token in that Keycloak group passes when the normal check does not (refused, no User, or the Nereid down), the API logs it, and `nereus doctor` warns that the exit was used. An instance with no default Mandate of the `authorization` Reef keeps today's rule unchanged: only `nereus-admins`.

**The instance's root** (owner, 2026-11-10). The first administrator is the instance's root, as AWS's root user or Linux's `root`: `nereus init` creates it, bound to `administrator`, ends with the step to create a personal administrator, and the root is kept for recovery, its sign-ins audited, MFA required, `nereus doctor` warning when it signs in. It is not in the first slice: until it is built, the `nereus-admins` exit plays its part.

**Commands use singular kinds** (`nereus authorization role create`, `nereus authorization binding list`), as ADR 0013 and the built decks do; #1306's sketch used plurals. `--owner` takes `<kind>/<name>` in lowercase, as `nereus environment` does. The commands of the slice: `nereus user`, `nereus teams` (the default kind `Team`) and `nereus teams member`, `nereus authorization role` (the default kind `Role`) and `nereus authorization binding`, each with ADR 0013's five verbs.

**`can-i` is a new verb**, `nereus authorization can-i <verb> <reef>/<kinds>`, with the shortcut `nereus can-i`. It asks the question the Nereus API asks, and the answer names the binding that grants it; exit code 0 for yes and 1 for no. With no `--user` it answers for the caller; asking about another User is itself a permission (`authorization:can-i:get` at that node). ADR 0013 lists it.

```console
# May bruno create Environments in the Project payments?
$ nereus authorization can-i create environment/environments \
    --owner project/payments \
    --user bruno
no: no binding gives bruno create on environment/environments at project/payments
```

### Stand-ins of the first slice

| Stand-in | Why | Replaced by |
|---|---|---|
| **The first identity is linked by the token's verified e-mail.** An administrator creates the User with its e-mail; the first sign-in of a token with `email_verified: true` and that e-mail links `{issuer, sub}`. A second identity is not linked at all. | ADR 0006 links a new `sub` only after an e-mail code, which needs a notification Reef that does not exist. The stand-in trusts the `email_verified` claim of the instance's own issuer, also when that issuer brokered another identity provider. | ADR 0006's e-mail code through a notification Reef, and `nereus user identity` commands for a second identity. |
| **The User's id is the object's name** (`core/users/ana`). | ADR 0006 has the platform generate the id; the first slice keeps the name, which the CLI and the bindings already use. | A generated id, with the name kept as a field. |
| **`nereus-admins` stands in for the instance's root.** | The exit exists already and does not depend on OpenFGA. | The root User of `nereus init`, with MFA and audited sign-ins (#1306). |

## Prior art

- **GitHub teams** ([About teams](https://docs.github.com/en/organizations/organizing-members-into-teams/about-teams)): "Teams are groups of organization members that reflect your company or group's structure", and "Organization owners and team maintainers can give teams admin, read, or write access to organization repositories". A team as both the org chart and the subject of a permission is the shape taken here. GitHub's "Child teams inherit the parent's access permissions" is the nesting left out: the tenancy tree already nests.
- **Backstage's `Group` and `User`** ([Descriptor format of catalog entities](https://backstage.io/docs/features/software-catalog/descriptor-format/)): "A group describes an organizational entity, such as for example a team, a business unit, or a loose collection of people", and "A user describes a person, such as an employee, a contractor, or similar", whose `spec.memberOf` is "The list of groups that the user is a direct member of". `Team` and `Member` keep the person apart from the team as Backstage does, with the membership on its own object so a position can sit on it.
- **Kubernetes RBAC** ([Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)): "A Role always sets permissions within a particular namespace" and "ClusterRole, by contrast, is a non-namespaced resource"; "Permissions are purely additive (there are no "deny" rules)"; "A role binding grants the permissions defined in a role to a user or set of users. It holds a list of _subjects_ (users, groups, or service accounts), and a reference to the role being granted." The rule of Reef, kinds and verbs, the optional owner of a role and the binding are taken from it. Its "You can only create/update a role binding if you already have all the permissions contained in the referenced role ... _or_ if you have been authorized to perform the `bind` verb" is the later answer to escalation through bindings; the first slice guards only positions (decision 8 of spec 0011).
- **AWS's root user** ([Root user best practices for your AWS account](https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html)): "We strongly recommend you don't access the AWS account root user unless you have a task that requires root user credentials", "Instead of accessing the root user, create an administrative user for everyday tasks", "it's crucial to add MFA for the root user", and "monitor, alert, and report the sign in and use of root user credentials". The instance's root, its personal administrator, its MFA and `nereus doctor`'s warning follow it.
- **OpenFGA's modelling of roles** ([Roles and Permissions](https://openfga.dev/docs/modeling/roles-and-permissions), [Custom Roles](https://openfga.dev/docs/modeling/custom-roles), [Conditions](https://openfga.dev/docs/modeling/conditions)): "Roles are relations that are directly assigned to users" and "Permissions are relations that users get through other relations"; custom roles fit when "It is not known beforehand (at the time of Authorization Model creation) what the application roles are", so "we represent them in a new type instead of as relations on that same type"; and "Conditions allow you to model more complex authorization modeling scenarios involving attributes". Registered roles become tuples on a `grant` type, never relations of the model, and the condition `rule_matches` carries the Reef, kind and verb.

## Consequences

- The `teams` and `authorization` Reefs gain their first kinds (`Team`, `Member`; `Role`, `Binding`), and core gains `User`; the `openfga` Nereid is the `authorization` Reef's first. Spec 0011 builds them, task by task, under #1644.
- Every route of the Nereus API declares its Reef, its kinds and how to find the owner of the object it names; a route with no declaration refuses to register, so a new route cannot forget the check.
- Nothing changes on an instance that has not installed the `authorization` Reef with a default Mandate: `nereus-admins` stays the only door, as today.
- The `Team` of the `teams` Reef is not a tenancy node: a Mandate's `match` still names Projects (ADR 0006, ADR 0015), and quotas can attach to a team later.
- ADR 0006 records the two stand-ins of the first identity and the User's id; ADR 0013 lists `can-i`; ADR 0015's sketch of one OpenFGA type per tenancy kind becomes one `node` type.
- OWASP A01 (broken access control) is what the slice answers: every read and write is checked, it fails closed, and who may create a role, a binding or a member is itself a rule. OWASP A07 (identification and authentication failures) is the stand-in's risk: the first identity trusts `email_verified`, and the root's MFA and audit wait for the root User.
- #1307 (the `Position` kind), #1308 (the `hiring` Reef) and #1309 (the `university` Reef) build on `Member`, without changing a binding.

## Open questions

- **Whether the root can be disabled** once a personal administrator exists, as AWS removes the root credentials of member accounts. Recommendation for the root's issue: yes, with the recovery path written down first.
- **Escalation through bindings:** today whoever may create bindings at a node may grant any role there. Recommendation: only what they hold themselves, or an explicit `bind`, as Kubernetes RBAC does.
- **Bindings projected into Kubernetes RBAC,** so `kubectl` is refused too, the layer below the Nereus API (ADR 0015, "the API projects them into the namespaces where a Project runs").
- **Agents as subjects:** `Member.spec.kind: agent`, a token by OAuth 2.0 Token Exchange (RFC 8693) with the `act` claim, and a permission that is the intersection of the person's and the agent's.

*Origin: the owner's decisions of 2026-11-10 on #1306 (three concepts, teams as the one list, registered roles, the built-in `administrator`, the instance's root) and of 2026-11-15 refining #897 into spec 0011 (decisions 1 to 19, the stand-ins of the first identity); raw data in Drive `#pontos/raw/2026-11-10/` and `#pontos/raw/2026-11-15/`.*
