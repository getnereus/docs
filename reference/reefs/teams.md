# The teams reef

Every command of the first slice: teams on the tenancy tree, their members and positions.

## Commands

- [`nereus reef apply teams`](../../specs/cli/reefs/teams.html#reef-apply) The teams reef brings teams and members
- [`nereus teams create payments`](../../specs/cli/reefs/teams.html#team-create) A team sits on a node of the tenancy tree
- [`nereus teams create billing`](../../specs/cli/reefs/teams.html#team-missing-owner) A team whose owner does not exist is refused
- [`nereus teams member create ana`](../../specs/cli/reefs/teams.html#member-lead) Ana joins as the tech lead: a position
- [`nereus teams member create bruno`](../../specs/cli/reefs/teams.html#member-developer) Bruno joins with no position
- [`nereus teams get payments`](../../specs/cli/reefs/teams.html#team-get) The team shows its members and positions
- [`nereus teams list`](../../specs/cli/reefs/teams.html#team-list) Every team, its owner and how many members
- [`nereus teams delete payments`](../../specs/cli/reefs/teams.html#team-delete-refused) A team with members is not deleted
- [`nereus teams member delete bruno`](../../specs/cli/reefs/teams.html#member-delete) Bruno leaves the team
- [`nereus teams apply`](../../specs/cli/reefs/teams.html#team-apply) A file of teams and members, applied again with no change

## Examples

### reef-apply

The kinds of the reef, with no Nereid.

```bash
nereus reef apply teams
```

``` { .text .output title="output" }
✓ core/reefs/teams created (teams.getnereus.dev/v1alpha1: members, teams)

Next steps:

  nereus teams --help
```

### team-create

The team of the payments Project.

```bash
nereus teams create payments \
  --project payments
```

``` { .text .output title="output" }
✓ teams/teams/payments created

Next steps:

  nereus teams member create <user> --team payments
```

### team-missing-owner

No Project billing yet.

```bash
nereus teams create billing \
  --project billing
```

``` { .text .output title="output" }
✗ teams/teams/billing: its owner project/billing does not exist: see 'nereus tenancy project list'
```

### member-lead

A member with a position.

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

### member-developer

A member like most.

```bash
nereus teams member create bruno \
  --team payments
```

``` { .text .output title="output" }
✓ teams/teams/payments/members/bruno created

Next steps:

  nereus teams get payments
```

### team-get

Who is in the team.

```bash
nereus teams get payments
```

``` { .text .output title="output" }
payments: 2 members, owner project/payments
MEMBER  POSITION   USER
ana     tech-lead  core/users/ana
bruno   -          core/users/bruno

Next steps:

  nereus authorization binding create <name> --role <role> --team payments --project payments
```

### team-list

The teams of the platform.

```bash
nereus teams list
```

``` { .text .output title="output" }
NAME      ORGANIZATION  PROJECT   MEMBERS  AGE
payments  example       payments  2        5m
```

### team-delete-refused

Two members still in it.

```bash
nereus teams delete payments
```

``` { .text .output title="output" }
✗ teams/teams/payments has 2 members (ana, bruno): delete them first:
  nereus teams member delete ana --team payments
  Nothing was changed.
```

### member-delete

The team keeps its other members.

```bash
nereus teams member delete bruno \
  --team payments
```

``` { .text .output title="output" }
✓ teams/teams/payments/members/bruno deleted

Next steps:

  nereus teams get payments
```

### team-apply

Teams first, then their members.

```bash
nereus teams apply \
  --from-file payments.yaml
```

``` { .text .output title="output" }
✓ teams/teams/payments created
✓ teams/teams/payments/members/ana created
✓ teams/teams/payments/members/bruno created

Next steps:

  nereus teams list
```
