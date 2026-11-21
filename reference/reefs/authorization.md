# The authorization reef

Every command of the first slice: Users, teams, roles and bindings, and who may do what.

## Commands

- [`nereus reef apply authorization`](../../specs/cli/reefs/authorization.html#reef-apply) The authorization reef brings roles and bindings
- [`nereus profile apply internal-developer-platform`](../../specs/cli/reefs/authorization.html#nereid-apply) openfga answers who may do what
- [`nereus user create ana`](../../specs/cli/reefs/authorization.html#user-create) A person is one User, whatever the login
- [`nereus user list`](../../specs/cli/reefs/authorization.html#user-list) Every User, and how many identities each has
- [`nereus authorization role list`](../../specs/cli/reefs/authorization.html#role-list) One built-in role, three examples to edit
- [`nereus authorization role get team-lead`](../../specs/cli/reefs/authorization.html#role-get) A role is a list of rules: reef, kinds, verbs
- [`nereus authorization role create release-manager`](../../specs/cli/reefs/authorization.html#role-create) A new role takes the words the CLI already uses
- [`nereus authorization role delete administrator`](../../specs/cli/reefs/authorization.html#role-delete) The administrator role cannot be deleted
- [`nereus authorization binding create payments-developers`](../../specs/cli/reefs/authorization.html#binding-team) A binding gives a role to a team on a node
- [`nereus authorization binding create payments-leads`](../../specs/cli/reefs/authorization.html#binding-position) A position narrows the binding to the tech lead
- [`nereus authorization binding list`](../../specs/cli/reefs/authorization.html#binding-list) Every binding of a node, and who it reaches
- [`nereus authorization can-i create environment/environments`](../../specs/cli/reefs/authorization.html#can-i-yes) Ana asks, and the answer names the binding
- [`nereus authorization can-i create environment/environments`](../../specs/cli/reefs/authorization.html#can-i-no) Bruno may not, and the answer says why
- [`nereus can-i create build/builds`](../../specs/cli/reefs/authorization.html#can-i-shortcut) The shortcut asks the same question
- [`nereus authorization can-i drive presentations/sessions/platform-day`](../../specs/cli/reefs/authorization.html#can-i-drive) Presenting is a right: a Session's speakers drive it
- [`nereus authorization can-i assist presentations/sessions/platform-day`](../../specs/cli/reefs/authorization.html#can-i-assist) The staff assists a Session, and never drives it
- [`nereus environment create staging`](../../specs/cli/reefs/authorization.html#enforce-denied) Bruno's environment is refused, politely
- [`nereus environment create staging`](../../specs/cli/reefs/authorization.html#enforce-allowed) Ana's environment is created
- [`nereus teams member delete ana`](../../specs/cli/reefs/authorization.html#leave-team) [planned #1307] Leaving the team removes the access
- [`nereus environment list`](../../specs/cli/reefs/authorization.html#fail-closed) Without openfga, everything closes

## Examples

### reef-apply

The kinds of the reef.

```bash
nereus reef apply authorization
```

``` { .text .output title="output" }
✓ core/reefs/authorization created (authorization.getnereus.dev/v1alpha1: bindings, roles)

Next steps:

  nereus nereid apply openfga --reef authorization
```

### nereid-apply

The profile installs the Nereid and its default Mandate (an excerpt).

```bash
nereus profile apply internal-developer-platform
```

``` { .text .output title="output" }
✓ networkpolicy openfga                      0.0s  networkpolicies/openfga applied (only nereus-api and vmagent-nereus reach openfga)
✓ nereid openfga                            1m19s  core/nereids/openfga created, Ready
✓ mandate openfga                            7.0s  core/mandates/openfga created (reef: authorization, nereid: openfga, default)
```

### user-create

The tech lead.

```bash
nereus user create ana \
  --email ana@example.com
```

``` { .text .output title="output" }
✓ core/users/ana created
```

### user-list

The people of this instance.

```bash
nereus user list
```

``` { .text .output title="output" }
NAME   EMAIL              IDENTITIES  AGE
ana    ana@example.com    1           2m
bruno  bruno@example.com  0           1m
```

### role-list

The roles of this instance.

```bash
nereus authorization role list
```

``` { .text .output title="output" }
NAME           RULES                    BUILT IN
administrator  *:*:*                    yes
developer      *:*:list,get and 3 more  -
team-lead      *:*:list,get and 5 more  -
viewer         *:*:list,get             -
```

### role-get

What a team lead may do.

```bash
nereus authorization role get team-lead
```

``` { .text .output title="output" }
team-lead: 6 rules
REEF         KINDS         VERBS
*            *             list,get
build        builds        create,apply,delete
delivery     deliveries    create,apply,delete
environment  environments  create,delete
release      releases      create,apply,delete
teams        members       create,delete
```

### role-create

A role of this instance's own.

```bash
nereus authorization role create release-manager \
  --rule release:releases:create,apply,delete
```

``` { .text .output title="output" }
✓ authorization/roles/release-manager created

Next steps:

  nereus authorization binding create <name> --role release-manager --team <team> --owner project/<project>
```

### role-delete

No one locks the instance out.

```bash
nereus authorization role delete administrator
```

``` { .text .output title="output" }
✗ authorization/roles/administrator is built in: it cannot be changed or deleted. To see who holds it, run:
  nereus authorization binding list --role administrator
  Nothing was changed.
```

### binding-team

Everyone in the team is a developer of the Project.

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

### binding-position

Only who holds the position.

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

### binding-list

Who may do what on the Project.

```bash
nereus authorization binding list \
  --owner project/payments
```

``` { .text .output title="output" }
NAME                 SUBJECT                  ROLE       OWNER
payments-developers  team/payments            developer  project/payments
payments-leads       team/payments/tech-lead  team-lead  project/payments
```

### can-i-yes

Signed in as ana: with no --user, the question is about the caller.

```bash
nereus authorization can-i create environment/environments \
  --owner project/payments
```

``` { .text .output title="output" }
yes: authorization/bindings/payments-leads gives team-lead to team/payments/tech-lead at project/payments
```

### can-i-no

About someone else.

```bash
nereus authorization can-i create environment/environments \
  --owner project/payments \
  --user bruno
```

``` { .text .output title="output" }
no: no binding gives bruno create on environment/environments at project/payments

Next steps:

  nereus authorization binding list --owner project/payments
```

### can-i-shortcut

Signed in as bruno: a developer creates builds.

```bash
nereus can-i create build/builds \
  --owner project/payments
```

``` { .text .output title="output" }
yes: authorization/bindings/payments-developers gives developer to team/payments at project/payments
```

### can-i-drive

Ana is a speaker of platform-day.

```bash
nereus authorization can-i drive presentations/sessions/platform-day \
  --user ana
```

``` { .text .output title="output" }
yes: ana is a speaker of platform-day
```

### can-i-assist

Carla is on the staff team of platform-day.

```bash
nereus authorization can-i assist presentations/sessions/platform-day \
  --user carla
```

``` { .text .output title="output" }
yes: carla is on the staff of platform-day (team stage-2-staff)
```

### enforce-denied

Signed in as bruno.

```bash
nereus environment create staging \
  --owner project/payments
```

``` { .text .output title="output" }
✗ environment/environments/staging: bruno may not create environment/environments at project/payments. To see who may, run:
  nereus authorization binding list --owner project/payments
  Nothing was changed.
```

### enforce-allowed

Signed in as ana, the tech lead.

```bash
nereus environment create staging \
  --owner project/payments
```

``` { .text .output title="output" }
✓ environment/environments/staging created (mandate: vcluster, nereid: vcluster)

Next steps:

  nereus environment get staging --watch
```

### leave-team

Ana leaves the team.

```bash
nereus teams member delete ana \
  --team payments
```

``` { .text .output title="output" }
✓ teams/teams/payments/members/ana deleted
```

### fail-closed

A read while the Nereid does not answer.

```bash
nereus environment list
```

``` { .text .output title="output" }
✗ authorization does not answer (nereid: openfga): nothing is allowed until it is back. To see what is down, run:
  nereus doctor
  Nothing was changed.
```
