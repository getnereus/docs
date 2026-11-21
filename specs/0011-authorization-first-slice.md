# 0011. The first slice of teams and authorization

**Status:** Proposed (2026-11-15)

From #897 (Refine the authorization reef: an openfga Nereid answers who may do what), refined with the owner on 2026-11-15. The journey is #1644 (the first slice of teams and authorization); each task below is one of its sub-issues.

This file is the plan an agent carries out end to end, without asking design questions. Read it whole before the first task. When this file and the repository disagree, the repository wins: record the difference in the progress log and go on.

## The answer

Users and teams are registered. A role is bound to a team, or to a position in it, on a node of the tenancy tree. The Nereus API asks before every read and write. A member with a privileged position may do what the other members may not.

```console
$ nereus authorization can-i create environment/environments \
    --owner project/payments \
    --user bruno
no: no binding gives bruno create on environment/environments at project/payments

$ nereus environment create staging \
    --owner project/payments
✗ environment/environments/staging: bruno may not create environment/environments at project/payments. To see who may, run:
  nereus authorization binding list --owner project/payments
  Nothing was changed.
```

## Decisions

Each taken with the owner on 2026-11-15 unless another date is given.

1. **Team, not Group** (#1306, owner 2026-11-10): `Team` and `Member` live in the `teams` reef, `Role` and `Binding` in the `authorization` reef, `User` in core. Reason: access derives from team membership, so there is no second list of groups to keep in sync; an identity provider's groups are an output, never the source.
2. **A person is one `User` of Nereus with several identities** (ADR 0006: the person is a `User` of core, not a `sub`). The subject of every check is `user:<User name>`, never an identity provider's `sub` or an e-mail. Reason: the owner's Google, Microsoft and other accounts must give the same access.
3. **A token whose identity is linked to no `User` has no permission.** Reason: having a login is not having permission (#1306).
4. **The first identity is linked by the token's verified e-mail; a second identity is out of this slice.** An administrator creates the User with its e-mail; the first sign-in of a token with `email_verified: true` and that e-mail links `{issuer, sub}`. Reason: ADR 0006 asks for an e-mail code to link a new `sub`, which needs a notification reef that does not exist. This is a stand-in: it trusts the `email_verified` claim of the instance's own issuer, also when that issuer brokered another identity provider. ADR 0006 also says the platform generates the User's id; in this slice the id is the object's name. Task 2 records both as stand-ins and amends ADR 0006.
5. **A binding names a team, a position in a team, or (the exception) one User.** The position is a free name on the `Member` in this slice. Reason: when the person in the position changes, the access follows without touching a binding; #1307's `Position` kind (skills, level, places) takes the same name later, and the binding and the tuples do not change.
6. **Teams do not nest.** Reason: the tenancy tree (Organization, Project, nested Projects) already gives the hierarchy, and access flows down it.
7. **Managing members is a rule like any other** (`teams:members:create,delete`), carried by a role. Reason: #1306, "who may create a role or a binding is itself a rule".
8. **A position that a binding names is assigned only by who may create bindings at that binding's node.** Reason: whoever manages members must not give themselves more access than they hold.
9. **The objects are the source of truth; the `openfga` Nereid writes the tuples.** Reason: declarative and auditable; deleting OpenFGA loses nothing.
10. **One fixed OpenFGA model, versioned with the Nereid and tested with `fga model test`.** A new role becomes tuples, never a new model. Reason: deterministic first.
11. **One OpenFGA type, `node`, serves every tenancy kind.** This differs from ADR 0015's sketch ("one OpenFGA type per tenancy kind"): the tenancy kinds come from each instance, and a fixed model cannot name them. Task 2 records it in the ADR.
12. **OpenFGA runs from its official Helm chart through the release reef, with Postgres through the `Database` kind**, as the `keycloak` Nereid does. Reason: open source first, and nothing new to invent.
13. **The slice refuses Environments and the tenancy tree too.** `nereus environment` and `nereus tenancy` reach the platform through the Nereus API since #1638 and #1639 (both under #1320, the CLI never knows the cluster).
14. **OpenFGA down: every read and write is refused**, except `whoami`, `status` and `doctor`. Reason: fail closed; an outage must never become a way to read.
15. **`nereus-admins` is the emergency exit.** A token in that Keycloak group passes when the normal check does not, and `nereus doctor` warns when the exit was used. Before the `authorization` reef has a default Mandate, today's rule holds unchanged (only `nereus-admins`). Reason: the exit exists already and does not depend on OpenFGA; #1306's root User with MFA replaces it later.
16. **Agents as subjects are out of this slice.** `Member.spec.kind` takes only `person` now; `agent` joins later.
17. **Roles:** `administrator` is built in (every verb on every kind of every reef, present and future; never changed or deleted). `viewer`, `developer` and `team-lead` are editable examples.
18. **Commands use singular kinds** (`nereus authorization role create`), as ADR 0013 (command conventions) and the built decks do; #1306's sketch used plurals. `--owner` takes `<kind>/<name>` in lowercase, as `nereus environment` does.
19. **`can-i` is a new verb**, under `nereus authorization can-i`, with the shortcut `nereus can-i`. With no `--user` it answers for the caller; asking about another User is itself a permission. Task 2 amends ADR 0013.
20. **The pillar "No single control point" joins `docs/vision.md`** in this slice (owner, 2026-11-15, from *Thinking in Platforms*, Kaspar von Grünberg and Luca Galante, 2026).
21. **The agent merges alone during this journey** (the envelope of #1644): one task, one PR, merged by rebase once `make checks` and the scene the task names pass. A design decision or a bug the plan does not cover is settled with a Fable agent and recorded in the progress log.
22. **No password users on `k3d-nereus`** (the refiner's call, the conservative one): the two signed-in people of the final scene exist only on the throwaway cluster of the scene. On `k3d-nereus` the proof is `can-i --user`. Reason: the kept cluster's Keycloak must not gain accounts with a password an agent chose.

## The CLI

The source of truth for the commands is the deck `docs/specs/cli/reefs/authorization.yaml` (26 slides, 22 of them a command, every one `planned`), approved by the owner on 2026-11-15. Build each command to print what its slide shows: **where this file and the deck differ on a command's output, the deck wins.** The commands, in the order of the story:

| Command | Reef | Task |
|---|---|---|
| `nereus reef apply authorization`, `nereus reef apply teams` | core | 4, 5 |
| `nereus nereid apply openfga --reef authorization` | core | 6 |
| `nereus user create\|apply\|list\|get\|delete` | core | 3 |
| `nereus teams create\|apply\|list\|get\|delete` (default kind `Team`) | teams | 4 |
| `nereus teams member create\|apply\|list\|get\|delete` | teams | 4 |
| `nereus authorization role create\|apply\|list\|get\|delete` | authorization | 5 |
| `nereus authorization binding create\|apply\|list\|get\|delete` | authorization | 5 |
| `nereus authorization can-i <verb> <reef>/<kinds>`, `nereus can-i` | authorization | 8 |

Every command follows ADR 0013: long options, `--dry-run` on every change, `--examples`, output lines ending in `created`, `configured`, `unchanged` or `deleted` with the full path (`teams/teams/payments/members/ana created`), and a `Next steps:` block with a blank line before and after and the commands indented two spaces. A refusal follows ADR 0012 (error messages).

The options the deck fixes:

```console
$ nereus user create ana \
    --email ana@example.com

$ nereus teams create payments \
    --owner project/payments

$ nereus teams member create ana \
    --team payments \
    --position tech-lead

$ nereus authorization role create release-manager \
    --rule release:releases:create,apply,delete

$ nereus authorization binding create payments-leads \
    --role team-lead \
    --team payments \
    --position tech-lead \
    --owner project/payments

$ nereus authorization binding create ana-admin \
    --role administrator \
    --user ana
```

A rule is `<reef>:<kinds>:<verbs>`, each part a comma list or `*`. The reef is the name the CLI uses (`environment`, `core`); the kinds are the plurals of the routes (`environments`); the verbs are ADR 0013's (`create`, `apply`, `list`, `get`, `delete`, `deploy`, `render`, `logs`, `publish`) plus `can-i`.

## The kinds

The fields a builder may not change; the rest (status, printer columns, validation details) is the builder's.

**`User`**, `core.getnereus.dev/v1alpha1`, cluster scoped. `spec.email` (required), `spec.displayName` (optional). The linked identities are a list of `{issuer, sub}`, written only by the Nereus API; follow ADR 0006 (its example near "The person is a `User` of core") and ADR 0005 (one writer per field) for where the list sits. The object's name is the User's id in this slice.

**`Team`**, `teams.getnereus.dev/v1alpha1`, cluster scoped, the reef's default kind. `spec.owner: {kind, name}` (required, a node of the tenancy tree), `spec.description`.

**`Member`**, `teams.getnereus.dev/v1alpha1`, cluster scoped. `spec.team` (required), `spec.user` (a User's name; the CLI defaults it to the member's name), `spec.kind` (`person`, the only value now), `spec.position` (optional, a free name, lowercase). A member is unique in its team; the builder chooses how the object's name carries both (the path printed is `teams/teams/<team>/members/<name>`).

**`Role`**, `authorization.getnereus.dev/v1alpha1`, cluster scoped, the reef's default kind. `spec.rules: [{reef, kinds: [], verbs: []}]`, `spec.owner: {kind, name}` (optional: with none the role serves the whole instance). A built-in role carries an annotation and refuses `apply` and `delete`.

**`Binding`**, `authorization.getnereus.dev/v1alpha1`, cluster scoped. `spec.role` (required), exactly one subject: `spec.team` with an optional `spec.position`, or `spec.user`; `spec.owner: {kind, name}` (optional: with none the binding holds on the whole instance). A binding refuses a role, team or User that does not exist, and a role whose `owner` is neither its own node nor an ancestor of it.

Neither reef has a Nereid of its own for the objects (the API keeps them, as with tenancy); the `authorization` reef's Nereid, `openfga`, only answers the question. Neither `Role` nor `Binding` names OpenFGA.

## The model

`controllers/openfga/model.fga`, as it is here. It passes `fga model test` (9 of 9 checks) with the store file below.

```text
model
  schema 1.1

type user

type team
  relations
    define member: [user]

type position
  relations
    define holder: [user]

type grant
  relations
    define subject: [user, team#member, position#holder]

type instance
  relations
    define granted: [grant#subject with rule_matches]
    define can: granted

type node
  relations
    define parent: [instance, node]
    define granted: [grant#subject with rule_matches]
    define can: granted or can from parent

condition rule_matches(reef: string, kind: string, verb: string, rule_reef: string, rule_kind: string, rule_verb: string) {
  (rule_reef == "*" || rule_reef == reef) && (rule_kind == "*" || rule_kind == kind) && (rule_verb == "*" || rule_verb == verb)
}
```

The question is always one check: `user:<name>` `can` on `node:<kind>/<name>` (or on `instance:nereus` when the object has no owner), with the context `{reef, kind, verb}`.

The tuples the Nereid writes, from the objects:

| From | Tuple |
|---|---|
| a tenancy node with no parent | `instance:nereus` `parent` `node:organization/example` |
| a tenancy node with a parent | `node:organization/example` `parent` `node:project/payments` |
| a `Member` with a User | `user:ana` `member` `team:payments` |
| a `Member` with a position | `user:ana` `holder` `position:payments/tech-lead` |
| a `Binding` to a team, per rule triple | `team:payments#member` `subject` `grant:<binding>/<triple>` |
| a `Binding` to a position, per rule triple | `position:payments/tech-lead#holder` `subject` `grant:<binding>/<triple>` |
| a `Binding` to a User, per rule triple | `user:ana` `subject` `grant:<binding>/<triple>` |
| the same binding, per rule triple | `grant:<binding>/<triple>#subject` `granted` `node:project/payments`, with the condition `rule_matches` and the context `{rule_reef, rule_kind, rule_verb}` |

A role's rules expand to one triple per reef, kind and verb (`environment:environments:create,delete` is two triples). The grant's id comes from the binding's name and the triple, never from an index, so the same objects always give the same tuples. A node's id is its kind in lowercase, a slash and its name.

The store file of the tests, `controllers/openfga/model.fga.yaml` (the builder may add cases, never remove one):

```yaml
name: nereus authorization
model_file: ./model.fga
tuples:
  - {user: "instance:nereus", relation: parent, object: "node:organization/example"}
  - {user: "node:organization/example", relation: parent, object: "node:project/payments"}
  - {user: "node:project/payments", relation: parent, object: "node:project/payments-mobile"}
  - {user: "node:organization/example", relation: parent, object: "node:project/billing"}
  - {user: "user:ana", relation: member, object: "team:payments"}
  - {user: "user:bruno", relation: member, object: "team:payments"}
  - {user: "user:ana", relation: holder, object: "position:payments/tech-lead"}
  - {user: "user:root", relation: subject, object: "grant:root-admin/0"}
  - user: "grant:root-admin/0#subject"
    relation: granted
    object: "instance:nereus"
    condition: {name: rule_matches, context: {rule_reef: "*", rule_kind: "*", rule_verb: "*"}}
  - {user: "team:payments#member", relation: subject, object: "grant:payments-developers/0"}
  - user: "grant:payments-developers/0#subject"
    relation: granted
    object: "node:project/payments"
    condition: {name: rule_matches, context: {rule_reef: "*", rule_kind: "*", rule_verb: "list"}}
  - {user: "team:payments#member", relation: subject, object: "grant:payments-developers/1"}
  - user: "grant:payments-developers/1#subject"
    relation: granted
    object: "node:project/payments"
    condition: {name: rule_matches, context: {rule_reef: "*", rule_kind: "*", rule_verb: "get"}}
  - {user: "position:payments/tech-lead#holder", relation: subject, object: "grant:payments-leads/0"}
  - user: "grant:payments-leads/0#subject"
    relation: granted
    object: "node:project/payments"
    condition: {name: rule_matches, context: {rule_reef: "environment", rule_kind: "environments", rule_verb: "create"}}
tests:
  - name: the slice
    check:
      - {user: "user:ana", object: "node:project/payments", context: {reef: environment, kind: environments, verb: create}, assertions: {can: true}}
      - {user: "user:bruno", object: "node:project/payments", context: {reef: environment, kind: environments, verb: create}, assertions: {can: false}}
      - {user: "user:bruno", object: "node:project/payments", context: {reef: environment, kind: environments, verb: list}, assertions: {can: true}}
      - {user: "user:ana", object: "node:project/payments-mobile", context: {reef: environment, kind: environments, verb: create}, assertions: {can: true}}
      - {user: "user:ana", object: "node:project/billing", context: {reef: environment, kind: environments, verb: create}, assertions: {can: false}}
      - {user: "user:ana", object: "node:organization/example", context: {reef: environment, kind: environments, verb: create}, assertions: {can: false}}
      - {user: "user:ana", object: "node:project/payments", context: {reef: delivery, kind: deliveries, verb: create}, assertions: {can: false}}
      - {user: "user:root", object: "node:project/billing", context: {reef: anything, kind: future, verb: delete}, assertions: {can: true}}
      - {user: "user:carla", object: "node:project/payments", context: {reef: environment, kind: environments, verb: list}, assertions: {can: false}}
```

The command that proves it (the image is pinned by digest in the make target of task 6):

```bash
docker run \
  --rm \
  --volume "${PWD}/controllers/openfga":/w:ro \
  openfga/cli model test \
  --tests /w/model.fga.yaml
```

## How the Nereus API decides

One function, in a new `api/authorization.py`. `admitted()` (`api/server.py`) cannot hold it: it sees only the request and the verifier, before the body is read, and knows neither the route's reef and kinds nor the stored object. So the route wrappers (`service_route`, `streamed_route`, `cluster_route`, `object_route`) gain a declaration per registration: the reef, the kinds (plural) and a function that gives the owner of the object the request names (from the body on a `PUT`, from the stored object on a `GET` or `DELETE`). The wrapper asks before `act` runs, and filters the `items` of a list after it. Every registration in every `api/*_routes.py` gets its declaration; a route with none refuses to register, so a new route cannot forget it. `/v2` (`api/registry_proxy.py`, the registry), `/v1/screens` and `/v1/ideas/notes` are checked on the instance, as `registry`, `screens` and `ideas` with the kinds their paths name.

In order:

1. **Open routes** (`/healthz`, `/v1/me`, `/v1/status`, `/v1/doctor`, `/.well-known/nereus-configuration`) are never asked.
2. **No default Mandate of the `authorization` reef:** today's rule, unchanged (`nereus-admins` only). The slice changes nothing on an instance that has not installed the reef.
3. **The User:** the token's `{issuer, sub}` is looked up in the Users' identities; with none, a User whose `spec.email` equals the token's e-mail, only when the token says `email_verified: true`, gets the identity linked now (`api/auth.py` does not read `email_verified` today, and `Principal` has no issuer: add both, the issuer from the verifier).
4. **The check:** the Nereus API asks the reef's default Mandate's Nereid, never OpenFGA by name. It finds the service the way `api/ideas_notes.py` finds doris (`mandate_of()`, which names the `ideas` reef today and takes the reef as an argument from now on, picks the reef's default Mandate; `address()` builds the service's address from its `spec.nereid`). The contract is `POST /v1/check` with `{user, verb, reef, kinds, node}` (`kinds` is the plural, as `environments`; `node` is `{kind, name}` with the Kind as the objects write it, as `Project`, or `null` for the instance; `spec.owner` and a tenancy node's `spec.parent` carry the Kind the same way, and only the Nereid lowercases it for a `node:` id), answering `{allowed, bindings}` (the names of the bindings that grant it, for `can-i`'s "yes"). A timeout of two seconds, a refused connection or any answer but 200 counts as "down".
5. **Allowed:** go on, and log the person as today (`who(principal)`).
6. **Not allowed, no User, or down, and the token is in `nereus-admins`:** go on through the emergency exit, log it, and count it for `nereus doctor`. An administrator who has their own User and a binding to `administrator` never uses the exit; task 11 creates both first.
7. **Otherwise refuse:** 403 when the answer was no or the token has no User, 503 when the Nereid is down, each with ADR 0012's fields (`cause`, `fix`), so the CLI prints the next steps.

Which node a request is checked on:

| Request | Node |
|---|---|
| `PUT` of an object with `spec.owner` | the owner in the body; when it changes an existing object's owner, both the old and the new |
| `GET` and `DELETE` of one object | the stored object's `spec.owner` |
| a list | every object is kept or dropped by a check on its own owner (one check per distinct owner, not per object) |
| an object with no `spec.owner` (core kinds, an instance-wide `Role` or `Binding`, a `User`) | the instance |
| a tenancy kind | the node itself; creating a node under a parent is checked on the parent |
| a `Team` | its `spec.owner`; a `Member` is checked on its team's owner |

The verb comes from the request: a list is `list`, `GET` of one object `get`, `PUT` with `mustNotExist` is `create`, another `PUT` `apply`, `DELETE` `delete`; a route that is none of these (a publish, a log stream) names its own ADR 0013 verb.

## Tasks

Each task is one sub-issue of #1644, one worktree, one PR. "Proves it" is the command whose passing output goes in the PR. Every task also runs `make checks` once before its PR and commits the record (`chore(checks): record make checks (#<id>)`), as every merged change does.

### Task 1 (#1653): the pillar "No single control point"

- **Touches:** `docs/vision.md` (the list of pillars and its `###` section), the README's "The pillars" section.
- **Depends on:** nothing.
- **Does:** adds the pillar: control (identity, authorization, quota, policy) is enforced in layers (the cloud, Kubernetes, the Environment, the Nereus API), so one layer failing or misconfigured does not collapse the platform. The section says what holds today (the Nereus API's check and the emergency exit of this slice) and what does not yet (Kubernetes RBAC from the bindings, cloud policy), and credits the book.
- **Done when:** the pillar count and both lists agree.
- **Proves it:** `make docs-lint`.

### Task 2 (#1654): the ADR of teams, roles and Users, and the amendments

- **Touches:** a new ADR in `docs/adr/` (the next number), ADR 0006, ADR 0013, ADR 0015, `mkdocs.yml`.
- **Depends on:** nothing. It can run beside every other task.
- **Does:** writes the ADR #1306 asks for, `Proposed`, by the checklist of `docs/agent/adr.md`, with `## Prior art` (GitHub teams, Backstage's `Group` and `User`, Kubernetes RBAC, AWS's root user, OpenFGA's modelling of roles, each opened and quoted). It records decisions 1 to 19 above, #1306's decisions of 2026-11-10, and the stand-ins of decision 4. It amends ADR 0006 with those stand-ins (the first identity by verified e-mail, the User's name as its id), ADR 0013 with the verb `can-i`, and ADR 0015 with decision 11 (one `node` type). It comments on #1306 that the commands are singular.
- **Done when:** the ADR is in the index and the docs build.
- **Proves it:** `make docs-lint` and the docs build of `make checks`. Accepting the ADR is the owner's.

### Task 3 (#1645): the `User` kind of core, and the person behind a token

- **Touches:** `cli/src/nereus/crds/` (the new CRD), `make chart` (the templates of `cli/src/nereus/charts/nereus-reefs`), `cli/tests/test_crds.py`, the API's RBAC (`cli/src/nereus/charts/nereus/templates/api.yaml`, pinned by `cli/tests/test_chart.py`), a new `api/user_routes.py` and `cli/src/nereus/user_service.py`, a new `cli/src/nereus/commands/user.py`, `api/auth.py` (`Principal`), `/v1/me` (`api/server.py`), `nereus whoami` (`cli/src/nereus/commands/login.py`).
- **Copy from:** `api/mandate_routes.py`, `cli/src/nereus/mandate_service.py`, `cli/src/nereus/commands/mandate.py` and their tests (a core kind served at `/v1/core/...`).
- **Depends on:** nothing.
- **Does:** the kind; `/v1/core/users[/{name}]` (admins only for now, like every route until task 7); the commands; a function that gives the User of a `Principal` (by identity, else by verified e-mail, linking it), used by `/v1/me`, which now also answers `user`; `nereus whoami` prints the User's name, or says the person has no User yet with the next step.
- **Done when:** a User is created, listed and deleted through the API; a token whose e-mail is not verified links nothing; a second User with the same e-mail is refused.
- **Proves it:** the unit tests of `api/` and `cli/tests/` for the routes, the commands and the lookup. The end-to-end proof is task 11's scene: the reference profile of `make scene-core` has no sign-in, so the API takes no write there.

### Task 4 (#1646): the `teams` reef

- **Touches:** a new `reefs/teams/` (the CRDs, an admission policy, `samples/`), the symlink `cli/src/nereus/interfaces/teams`, `cli/src/nereus/cli.py` (where a reef's group is registered), a new `api/teams_routes.py`, `cli/src/nereus/teams_service.py`, `cli/src/nereus/commands/teams.py`, the API's RBAC and its pin, the reference profile, a new `test/scene-core-teams`, a new deck `docs/specs/cli/reefs/teams.yaml` (the team slides move there from the authorization deck, `status: built`), `docs/specs/cli/index.yaml`.
- **Copy from:** the commit `2597436a` (the usage reef, 43 files: route module, command, deck, samples, scene, `test_boundaries`, `test_profiles`), and `reefs/tenancy/admission.yaml` for the admission policy.
- **Depends on:** nothing to start (a `Member` names a User by name; the check that the User exists joins when task 3 is on `main`).
- **Does:** `Team` and `Member` as in "The kinds"; the routes `/v1/teams/teams[/{name}]` and `/v1/teams/members[/{name}]`; the commands; refusals: a team whose owner does not exist, a member of a team that does not exist, a team deleted while it has members or a binding names it.
- **Done when:** the deck's team commands print what their slides show.
- **Proves it:** the unit tests (each command both ways, as `cli/tests/test_mandate_through_api.py`), and `make scene-core` with the new `scene-core-teams`, which applies the objects with `kubectl` as `scene-core-usage` does (the reference profile has no sign-in, so the API takes no write there): the CRDs install, the admission policy refuses a team with no owner, the objects are stored. The commands end to end are task 11's.

### Task 5 (#1647): the `authorization` reef's kinds

- **Touches:** a new `reefs/authorization/` (the CRDs, the built-in `administrator`, an admission policy, `samples/` with `viewer`, `developer` and `team-lead`), the symlink under `cli/src/nereus/interfaces/`, `cli/src/nereus/cli.py`, a new `api/authorization_routes.py`, `cli/src/nereus/authorization_service.py`, `cli/src/nereus/commands/authorization.py`, the API's RBAC and its pin, a new `test/scene-core-authorization`, the deck `docs/specs/cli/reefs/authorization.yaml` (role and binding slides to `built`).
- **Copy from:** the same as task 4.
- **Depends on:** nothing to start (a binding's check that its team exists joins when task 4 is on `main`). Tasks 3, 4 and 5 touch the same registration lines (`cli.py`, the API's RBAC, `create_app` in `api/server.py`): the second and third to merge rebase and keep both sides.
- **Does:** `Role` and `Binding` as in "The kinds"; the routes `/v1/authorization/roles[/{name}]` and `/v1/authorization/bindings[/{name}]`; the commands with `--rule`; `administrator` applied with the reef and refused on `apply` and `delete`; a role refused on delete while a binding names it. The example roles: `viewer` is `*:*:list,get`; `developer` is `viewer` plus `create,apply,delete` on the kinds of build, delivery and release; `team-lead` is `developer` plus `environment:environments:create,delete` and `teams:members:create,delete`. A profile cannot apply sample objects today, so the samples are applied by `nereus authorization role apply --path` and the reef's `Next steps:` says so.
- **Done when:** the deck's role and binding commands print what their slides show.
- **Proves it:** the unit tests, and `make scene-core` with `scene-core-authorization`, driven with `kubectl` as in task 4.

### Task 6 (#1648): the `openfga` Nereid

- **Touches:** a new `controllers/openfga/` made with `scripts/nereid/new` (`docs/guides/build/new-nereid.md`), `Makefile` (`NEREIDS`, a target `authorization-model-test`), `cli/src/nereus/local_nereids.py` (`TOOLS`, its RBAC), `cli/tests/test_boundaries.py` (`BY_INIT`), the README's table of Nereids.
- **Copy from:** `controllers/keycloak/` (`keycloak.py`: `release_objects` and `ensure_release` for the chart through the release reef, `database_object` and `ensure_database` for Postgres, the connection read from the Secret `<name>-database`; `server.py`: the loop and `ready()`), and doris for a Nereid that serves HTTP to the Nereus API.
- **Depends on:** the fields of "The kinds" only; it is built against fixtures, beside tasks 3, 4 and 5.
- **Does:** installs OpenFGA (the chart `openfga/openfga`, its version pinned, the Postgres of the `Database` kind, migrations as the chart runs them); creates the store and writes `model.fga` when its content changed, keeping the store and model ids in its status; each pass reads the tenancy nodes, Teams, Members, Roles and Bindings, computes the tuples of "The model", reads the store's tuples and writes only the difference; serves `POST /v1/check` (the contract of "How the Nereus API decides") and `/healthz`; reports Ready only when OpenFGA answers and the tuples are in step.
- **Done when:** the objects of the model's store file, as fixture objects, give exactly the store file's tuples, and the nine answers of its tests through `POST /v1/check` against an OpenFGA the test starts in Docker (`openfga/openfga run`, in memory; skipped where Docker is absent, so `make checks` stays as it is). The proof on a cluster, with flux and cloudnative-pg, is task 11's scene.
- **Proves it:** `make authorization-model-test`; the Nereid's unit tests (the tuples computed from fixture objects, the difference, the check). `make contract` and `make scene-idp` run only on the owner's word and are not delegated to this journey: do not run them.

### Task 7 (#1649): the Nereus API asks before acting

- **Touches:** a new `api/authorization.py`, `api/server.py` (`admitted()`, `service_route`, `cluster_route`, `object_route`, `streamed_route`), `api/registry_proxy.py` (its own group check), every registration in every `api/*_routes.py` (its declaration), `cli/src/nereus/commands/doctor.py` (a `WARN` state, which does not exist today, and the check of the emergency exit).
- **Depends on:** tasks 3, 4, 5 and 6 on `main`, and #1638 and #1639.
- **Does:** "How the Nereus API decides", whole. The refusal's text is the deck's. `nereus doctor` gains `WARN` and one line: how many times the emergency exit was used since the API started. A `WARN` never fails `doctor`: its exit code stays 0.
- **Done when** (in the unit tests, with a fake check service; end to end in task 11): with the reef installed, a User with the `developer` role at a Project lists there and is refused a create; a User with no binding is refused everything but the open routes; with the Nereid stopped, everyone but `nereus-admins` gets 503 and the same message every time; with no Mandate of the reef, every existing test passes unchanged.
- **Proves it:** the unit tests of `api/authorization.py` with a fake check service (allowed, refused, down, no User, admin through the exit, no Mandate, the list filter with two owners, a registration with no declaration refused), and `make scene-core` unchanged (no Mandate of the reef there).

### Task 8 (#1650): `can-i`

- **Touches:** `api/authorization_routes.py` (`POST /v1/authorization/can-i`), `cli/src/nereus/commands/authorization.py`, the top-level shortcut in `cli/src/nereus/cli.py`, the deck's slides to `built`.
- **Depends on:** task 7.
- **Does:** `nereus authorization can-i <verb> <reef>/<kinds> [--owner <kind>/<name>] [--user <name>]`: the deck's lines (`yes: authorization/bindings/<binding> gives <role> to <subject> at <node>`, or `no: no binding gives <user> <verb> on <reef>/<kinds> at <node>`); exit code 0 for yes and 1 for no. Asking with `--user` needs `authorization:can-i:get` at that node. The shortcut `nereus can-i` is the same command.
- **Done when:** the deck's three `can-i` slides print what they show.
- **Proves it:** the unit tests, and the step in the final scene.

### Task 9 (#1651): only who may bind assigns a position a binding names

- **Touches:** `cli/src/nereus/teams_service.py`, its tests.
- **Depends on:** task 7.
- **Does:** creating or changing a `Member` with a `spec.position` that some Binding names is allowed only to who may `authorization:bindings:create` at that binding's node (decision 8); the refusal names the binding and says who can do it.
- **Done when:** a User with only `teams:members:create,delete` adds a member with no position, and is refused giving themselves `tech-lead`.
- **Proves it:** the unit tests, and the step in the final scene.

### Task 10 (#1655): the profile, the walkthrough and the docs

- **Touches:** `cli/src/nereus/charts/nereus/profiles/internal-developer-platform.yaml` (the `teams` reef, the `authorization` reef with `{name: openfga}` and its default Mandate), ADR 0014's note that these "do not exist yet", a new `docs/guides/access/authorization.md`, `docs/features.md` (the rows that waited for #897, and the stand-ins table), `mkdocs.yml`, the decks' remaining statuses.
- **Depends on:** tasks 4, 5, 6 and 7.
- **Does:** the profile installs the two reefs and the Nereid; the walkthrough is the deck's story with real output; `docs/features.md` says what is built.
- **Done when:** the profile lists the two reefs, the Nereid and the default Mandate, and its tests pass; a fresh instance of the profile ending with the `authorization` reef Ready is seen in task 11.
- **Proves it:** the profile's unit tests (`cli/tests/test_profiles.py`), the docs build, and task 11's `make scene`. `make scene-idp` is not delegated to this journey: leave it, named in the PR, for the owner's word.

### Task 11 (#1652): the final scene, and the slice on `k3d-nereus`

- **Touches:** `test/scene` (a new step file it sources), a helper that creates two local people in the scene's Keycloak through its admin API (the Secret `keycloak-admin`), with a verified e-mail at `example.com`, and signs each in with `test/oidc-flow`.
- **Depends on:** every task above.
- **Does:** the scene below, on the throwaway cluster of `make scene`; then `scripts/registry/release publish`, `scripts/deploy/live --allow-kept-cluster`, the two reefs and the Nereid applied on `k3d-nereus`, and the proof of decision 22 there. On both clusters the first step is the administrator's own access: the signed-in administrator creates their own User (the e-mail `nereus whoami` shows) and a binding of `administrator` to it, through the emergency exit, once.
- **Done when:** the scene passes, and on `k3d-nereus` `nereus doctor` ends with exit code 0 (a `WARN` of the emergency exit is expected after the first step) and `nereus authorization can-i ... --user bruno` answers `no` while `--user ana` answers `yes`.
- **Proves it:** `make scene`, and the commands' output on `k3d-nereus` pasted in #1644.

## The final scene

On the scene's cluster, signed in as the scene's administrator unless a step says otherwise:

1. `nereus user create ana` and `bruno`; a team `payments` owned by `project/payments`; `ana` a member with the position `tech-lead`, `bruno` a member with none.
2. Bindings: `developer` to the team, `team-lead` to the position, both at `project/payments`.
3. `can-i create environment/environments --owner project/payments --user ana` says yes and names the binding; `--user bruno` says no.
4. As bruno: `nereus environment list` answers; `nereus environment create` is refused with its next steps and exit code 1; nothing was created.
5. As ana: the same `create --dry-run` is accepted.
6. As bruno: adding a member with no position is refused (bruno is not a team lead); as ana, it is accepted; as ana, giving herself or anyone the position `tech-lead` on a second team whose binding she may not create is refused (task 9).
7. `nereus teams member delete ana --team payments`; `can-i` for ana now says no, and as ana the `create --dry-run` is refused (leaving the team removes the access).
8. A person with a login and no User is refused everything but `nereus whoami`, which says so.
9. The `openfga` Nereid scaled to zero: as bruno, a list is refused with the "down" message; as the administrator it answers, and `nereus doctor` shows the `WARN` of the emergency exit. Scaled back, bruno's list answers again.
10. OpenFGA's database deleted and the Nereid restarted: after one pass, step 3's answers are the same (the objects are the source of truth).

## Carrying it out

**Who:** one Opus agent orchestrates and owns the journey (it comments "Owner session: <name>" on #1644), with **up to five subagents at a time and about eleven subagent runs in all**. Opus for tasks 2 to 9 and 11; Sonnet for tasks 1 and 10. A Fable agent is called only for a design decision or a bug the plan does not cover (decision 21); its answer and the reason go in the progress log.

**Waves:**

| Wave | Tasks, in parallel | Ends with |
|---|---|---|
| A | 3, 4, 5, 6, and one subagent for 1 then 2 (merge order: 3, 4, 5, then 6) | milestone 1: the kinds and the Nereid on `main`; nothing is enforced, so nothing changes for anyone |
| B | 7, with 10's docs drafted beside it | the API asks |
| C | 8, 9, 10 | milestone 2: the slice is whole |
| D | 11, by the orchestrator | milestone 3: the scene passes and `k3d-nereus` runs it |

A release and a deploy to `k3d-nereus` happen at milestones 1, 2 and 3, never between.

**Quota-safe order.** Every task merges alone and leaves `main` green and usable: tasks 3 to 6 add kinds and a Nereid nothing uses yet; task 7 changes nothing while the reef has no Mandate; the profile gains the reef only in task 10. When the quota ends, a new session resumes from the state, never from memory: `gh issue view 1644` (the sub-issues open and closed, and the comments), the progress log below, `gh pr list`, `git worktree list`. A task with a worktree and no merged PR is resumed in that worktree.

**The rules every subagent gets** (the same block in every brief, plus its task's section):

- Read `CLAUDE.md`, `docs/agent/rules.md` and `docs/agent/worktrees.md` first. Work only in the task's worktree (`scripts/worktree/new <type> <issue>-<slug>`); the main clone is read and pulled only.
- Its own scratch directory for commit messages and notes, never a shared one.
- Tests first. Targeted tests while working; `make checks` once at the end; never two scenes at the same time on this machine (the orchestrator says when a subagent may run `make scene-core`; `make scene` and `make scene-idp` are run by the orchestrator).
- Conventional Commits, one per topic, with `git -C <worktree> add --all` then `git -C <worktree> commit --file <message file>` as plain separate commands.
- Public by design: no e-mail, personal or company name, internal domain, account id or token; examples use `example.com`.
- Never `speak`. Never message another session. Never push or merge: the orchestrator does both.
- Report in a few lines: the commits, each check run and its result, what was left out and why. Never file contents.

**The orchestrator, per task:** brief the subagent; when it reports, read the diff, rebase onto `main`, run what the task's "Proves it" names, open the PR saying what ran, merge by rebase, close the sub-issue, add its line to the progress log, remove the worktree. A check failing three times in a row on the same task stops that task: the log says what was tried, and the orchestrator goes on to a task that does not depend on it.

**Limits, with no exception:**

- Nothing destructive on the host: no `sudo`, no `docker system prune`, no deleting of a k3d cluster other than the scenes' own throwaway ones, no `rm` outside a worktree or a scratch directory, nothing written to the owner's home but what `make` already writes.
- No cloud resource: no cloud provider's CLI is run at all.
- `k3d-nereus` is reached only through `scripts/registry/release publish`, `scripts/deploy/live --allow-kept-cluster` and the `nereus` CLI. It may go down and come up as often as needed. While another session is alive on the repository (`claude-peers`), an `[ask]` comes first (`docs/agent/peers.md`).
- The release publishes to the project's own registry on ghcr.io. A new package (the `openfga` Nereid's image) is private until a click makes it public (#1338, `docs/agent/publish.md`). The owner pre-authorized that click for this journey (2026-11-15): the agent makes it in the owner's browser (the Chrome tools), for the packages this plan creates and for nothing else on that page, and records it in the progress log. When the browser is not reachable, install the Nereid on `k3d-nereus` from the local registry (`docs/guides/operate/kept-cluster-update.md`, "without publishing": the image at `localhost:5111`, then `nereus nereid apply openfga --image ...`), and leave the click as the one item waiting for the owner.

## Out of scope

Each with the better solution it leads to.

- **A second identity on the same User:** ADR 0006's e-mail code through a notification reef; `nereus user identity` commands.
- **The instance's root User** (#1306): created by `nereus init`, MFA required, its sign-ins audited; it replaces the `nereus-admins` emergency exit.
- **Agents as subjects:** `Member.spec.kind: agent`, a token by OAuth 2.0 Token Exchange (RFC 8693) with the `act` claim, and a permission that is the intersection of the person's and the agent's scope; the audit trail records both.
- **Quotas:** Kubernetes `ResourceQuota` object counts first, then a `quota` reef (Quota, Budget) on the same tenancy nodes; a `Team` is already a place a quota can attach.
- **Bindings projected into Kubernetes RBAC:** the layer below the Nereus API of the pillar "No single control point" (ADR 0015: "the API projects them into the namespaces where a Project runs"), so `kubectl` is refused too.
- **The `Position` kind** (#1307): skills, level and places; the position's name on a `Member` becomes a reference to it.
- **Groups mirrored to or from an identity provider:** a Nereid writes Keycloak groups from the teams (#1306: an output, never the source).
- **No escalation on bindings:** today whoever may create bindings at a node may grant any role there; later, only what they hold themselves, as Kubernetes RBAC's `escalate` and `bind`.
- **The model test in `make checks`:** `make authorization-model-test` needs Docker, which `make checks` does not use today.
- **`nereus environment kubeconfig`** still reads the kubeconfig (#1638); serving a virtual cluster's credentials through the API is its own decision.

## Progress log

One line per task when its PR merges, and one per decision the plan did not cover. Newest last.

| When | Task | What | By |
|---|---|---|---|
| 2026-11-15 | plan | The plan, the deck and the model's tests (9 of 9) written; #1638 and #1639 put `environment` and `tenancy` behind the Nereus API | the refining session |
| 2026-11-15 | 1 (#1653) | The pillar "No single control point" in `docs/vision.md` and the README; the deck `more-than-an-idp` counts twenty-three (PR #1661) | alimede |
| 2026-11-15 | 3 (#1645) | The `User` kind of core, `/v1/core/users`, `nereus user`, the User behind a token (by `{issuer, sub}`, else once by verified e-mail), `/v1/me` and `nereus whoami` answer it | alimede |
| 2026-11-15 | orchestration | A subagent's commit in a worktree may be refused by `guard-main` when its session's cwd is the main clone; the orchestrator then commits for it. On a rebase, the `docs/checks/` conflict takes the task's side and the README is re-rendered from `main`'s with `scripts/checks/checks render`, never taken whole from the task's side | alimede |
| 2026-11-15 | 3 (#1645) | A security review found a race in linking an identity: `put_cluster` takes an `expected_version`, and `user_of` and `put_user` write with a compare-and-swap (PR #1663) | alimede |
| 2026-11-15 | 2 (#1654) | ADR 0027 (teams, roles and Users), `Proposed`; ADR 0006, 0013 and 0015 amended; #1306 told the commands are singular (PR #1664). `administrator` comes with the `authorization` reef, not with `nereus init` as #1306 said | alimede |
| 2026-11-15 | 4 (#1646) | The `teams` reef: `Team`, `Member` (its User must exist), `/v1/teams/...`, `nereus teams`, the deck `teams.yaml`, `scene-core-teams` (passed). No profile can install a reef with no Nereid: the scene applies it with `nereus reef apply teams` | alimede |
| 2026-11-15 | 5 (#1647) | The `authorization` reef's kinds: `Role`, `Binding` (its role, team or User must exist; the role's owner reaches the binding's node, on create and on apply), the built-in `administrator` applied with the reef (not by `nereus init`), the examples `viewer`, `developer`, `team-lead`, `nereus authorization role\|binding`, `scene-core-authorization` (passed). A security review: only the reef marks a role built in (`built-in-name` policy). A User is not deleted while a binding names it | alimede |
| 2026-11-15 | 5 (#1647) | Two defects only a scene caught: thetis's image did not COPY `reefs/authorization` (now `cli/tests/test_dockerfile_reefs.py` checks every image that builds the CLI); and Kubernetes' CEL type checker refuses a map literal mixing a string and a list, which cel-python accepts. Gap: `make checks` does not compile CEL as the API server does | alimede |
| 2026-11-15 | 6 (#1648) | The `openfga` Nereid: chart 0.4.1 through the release reef, Postgres through `Database`, the store and model written, the tuples computed from the objects and only the difference written, `POST /v1/check`; `make authorization-model-test` (9 of 9); the fixtures guarded against the real CRDs. Repository over plan: grant ids are `grant:<binding>/<reef>.<kind>.<verb>` with `*` written `_` (OpenFGA refuses `:` and `*` there); the store and model ids live in the Mandate's status (`authorization`); migrations run in an init container; `nereid apply openfga` does not make the default Mandate (`--default` is its next step, the switch of decision 15) | alimede |
| 2026-11-15 | milestone 1 | The kinds and the Nereid on `main`; nothing is enforced yet | alimede |
| 2026-11-15 | milestone 1 | Released v0.1.11 (3 images built, 24 reused) and deployed to `k3d-nereus` (smoke test and `nereus doctor` pass). The click that makes `openfga-controller` public on ghcr.io was refused by Claude Code's permission classifier in the owner's browser: it waits for the owner, and `make promote CHECK=1` fails on that one package until then | alimede |
| 2026-11-16 | 7 (#1649) | The Nereus API asks the `authorization` reef's default Mandate's Nereid before acting: `api/authorization.py`, a declaration on every route (an undeclared one refuses to register), the emergency exit counted, `nereus doctor`'s `WARN`. A security review found two defects before the PR, both fixed with tests: a PUT's verb now comes from the field its action reads (a query `create` was gated as a create on the parent while overwriting a node), and a stored owner that cannot be read fails closed (only a 404 means none). Left out: the deck's doctor line for openfga not answering | alimede |
| 2026-11-16 | 10 (#1655) | The `internal-developer-platform` profile installs `teams` and `authorization` with `openfga` and its default Mandate `openfga`; a reef no Nereid serves gets a lane of its own, which `openfga` waits for (`READS` in `profiles.py`); the walkthrough `docs/guides/access/authorization.md` carries the deck's output until task 11 replaces it; `docs/features.md` and ADR 0014's note updated. The deck's `nereid-apply` and `fail-closed` slides stay `planned`: what tasks 6 and 7 print differs from them, and task 11's real output settles them. `make scene-idp` not run (the owner's word) | alimede |
| 2026-11-16 | 9 (#1651) | Only who may `authorization:bindings:create` at a binding's node gives a member a position that binding names. Repository over plan: the check lives in the Nereus API (a route declares extra checks, `position_checks` in `api/teams_routes.py`), not in `teams_service.py`, since only the API knows the asker. Asked on a create and on an apply that changes the position or its User; taking a position away is not checked (it reduces access) | alimede |
| 2026-11-16 | 7 (#1649) | A security review of the merged code: a listing whose answer has no `items` was answered unfiltered; it now fails closed with `500 Unfilterable` (PR #1671) | alimede |
| 2026-11-16 | 8 (#1650) | `nereus authorization can-i` and the shortcut `nereus can-i`, through `POST /v1/authorization/can-i` (one `yes:` line per granting binding, exit code 1 for no). A check that cannot run is a refusal, never a no: 409 `NoDefaultMandate` with no default Mandate of the reef, 503 when the Nereid is down. A security review: a question about yourself never tells whether a node exists (a missing node answers a plain no), and with `--user` nothing is looked up before the `authorization:can-i:get` gate passes. Left out: `--team` | alimede |
| 2026-11-16 | milestone 2 | The slice is whole on `main`: the API asks, `can-i`, positions guarded, the profile installs both reefs | alimede |
| 2026-11-16 | milestone 2 | Released v0.1.12 and deployed to `k3d-nereus` at `cdd1fc1` (smoke test and `nereus doctor` pass) | alimede |
| 2026-11-16 | 11 (#1652) | The final scene of teams and authorization (`test/scene-authorization`, steps 1 to 10 of the plan) and the walkthrough's real output. It caught four defects, each one local fix with a test, none for Fable: the chart's pods carried `app.kubernetes.io/name=openfga`, which the Nereid's own Service and NetworkPolicy select (`nameOverride`); a profile applied the `authorization` reef without its built-in `administrator` (`authorization_service.built_ins` on both paths); `nereus database delete` waited for a name its owner created again (`wait_gone` compares the uid); and `nereus-mcp` moves the issuer, so the scene signs in again. The API now logs why it refused a token. Task 10 had left the scene's counts at 13 Nereids | alimede |
| 2026-11-16 | milestone 3 | Released v0.1.13 (`main` d83f6706, PR #1739) and deployed to `k3d-nereus`; the `openfga` Nereid moved to it with `nereus nereid apply openfga --image ...`, and its server's Deployment was recreated once for the new selector. The administrator has its own User and the binding `owner-admin`; `can-i --user` answers yes for the tech lead and no for the other member | alimede |
| 2026-11-16 | decision 15 | The doctor's `emergency-exit` warned until the API restarted, also after the fix: four of nine uses came within the openfga Nereid's 5-second sync after `owner-admin` was created. It now names the last use and by whom, and warns only while that use is less than a day old (the owner's choice, not a Fable call) | nemertes |
| 2026-11-16 | journey | Closed: the final scene passed, the slice runs on `k3d-nereus`, ADR 0027 is `Accepted` and `openfga-controller` is public on ghcr.io. A stale CLI commands cache after a restart hid `nereus authorization` until `nereus reef list` (#982) | nemertes |
