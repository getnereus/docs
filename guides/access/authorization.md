# Authorize a team

Give a team a role on a node of the tenancy tree: every member gets it by joining and loses it by leaving, and the Nereus API asks the authorization Reef before every read and write.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`: it brings the teams Reef, the authorization Reef and its Nereid `openfga` with the default Mandate that turns the check on. Before that Mandate exists, only `nereus-admins` passes.
- A Project to own the team, from [Know whose each thing is](tenancy.md): `project/payments` below.
- [Tenancy and access](../../concepts/tenancy-and-access.md) tells a User, a Team, a Role and a Binding apart.

## Steps

### 1. Register the people

[`nereus user create`](../../specs/cli/reefs/authorization.html#user-create) records the e-mail the person's first sign-in is matched with. A login with no User may do nothing.

```bash
nereus user create ana --email ana@example.com
```

``` { .text .output title="output" }
✓ core/users/ana created
```

```bash
nereus user create bruno --email bruno@example.com
```

``` { .text .output title="output" }
✓ core/users/bruno created

Next steps:

  nereus teams create <team> --owner project/<project>
```

### 2. Make the team and name its tech lead

[`nereus teams create`](../../specs/cli/reefs/teams.html#team-create) makes the team under its Project; [`nereus teams member create`](../../specs/cli/reefs/teams.html#member-lead) adds a member, here with the position `tech-lead`.

```bash
nereus teams create payments --owner project/payments
```

``` { .text .output title="output" }
✓ teams/teams/payments created

Next steps:

  nereus teams member create <user> --team payments
```

```bash
nereus teams member create ana \
  --team payments \
  --position tech-lead
```

``` { .text .output title="output" }
✓ teams/teams/payments/members/ana created

Next steps:

  nereus teams get payments
```

### 3. Give the team a role

[`nereus authorization role list`](../../specs/cli/reefs/authorization.html#role-list) shows the roles: `administrator` is built in and cannot change; `viewer`, `developer` and `team-lead` are examples to edit. [`nereus authorization binding create`](../../specs/cli/reefs/authorization.html#binding-team) makes every member a developer of the Project.

```bash
nereus authorization binding create payments-developers \
  --role developer \
  --team payments \
  --owner project/payments
```

``` { .text .output title="output" }
✓ authorization/bindings/payments-developers created

Next steps:

  nereus authorization binding list --owner project/payments
```

### 4. Give one position a role

With [`--position`](../../specs/cli/reefs/authorization.html#binding-position), only the team's tech lead gets `team-lead`, which may create Environments.

```bash
nereus authorization binding create payments-leads \
  --role team-lead \
  --team payments \
  --position tech-lead \
  --owner project/payments
```

``` { .text .output title="output" }
✓ authorization/bindings/payments-leads created

Next steps:

  nereus authorization binding list --owner project/payments
```

## Check it worked

[`nereus authorization binding list`](../../specs/cli/reefs/authorization.html#binding-list) shows who holds what on the Project.

```bash
nereus authorization binding list --owner project/payments
```

``` { .text .output title="output" }
NAME                 SUBJECT                         ROLE       OWNER
mobile-leads         team/payments-mobile/tech-lead  team-lead  project/payments
payments-developers  team/payments                   developer  project/payments
payments-leads       team/payments/tech-lead         team-lead  project/payments
```

[`nereus authorization can-i`](../../specs/cli/reefs/authorization.html#can-i-yes) answers with the binding that allows it. With no `--user` it asks about you.

```bash
nereus authorization can-i create environment/environments \
  --owner project/payments \
  --user ana
```

``` { .text .output title="output" }
yes: authorization/bindings/payments-leads gives team-lead to team/payments/tech-lead at project/payments
```

Signed in as Bruno, creating an Environment there is refused, and nothing changes:

```bash
nereus environment create staging --owner project/payments
```

``` { .text .output title="output" }
✗ environment/environments/staging: bruno may not create environment/environments at project/payments. To see who may, run:
  nereus authorization binding list --owner project/payments
  Nothing was changed.
```

## Next

- [Know whose each thing is](tenancy.md): the tree a binding reaches down.

## Learn more

- [The authorization Reef](../../reference/reefs/authorization.md) and [the teams Reef](../../reference/reefs/teams.md): every command, presenting rights included.
- [ADR 0027](../../adr/0027-teams-roles-and-users.md): users, teams, roles and bindings.
