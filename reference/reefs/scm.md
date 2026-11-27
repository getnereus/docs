# The scm Reef

Every command that lets Nereus reach a source host as an application, never as a person.

## Commands

- [`nereus nereid apply github`](../../specs/cli/reefs/scm.html#apply-github) One github Nereid serves both Reefs, opt-in
- [`nereus scm connection create example`](../../specs/cli/reefs/scm.html#connection-create) A Connection names an organisation, and nothing secret
- [`nereus scm connection list`](../../specs/cli/reefs/scm.html#connection-list) list says what each App reaches, and what is missing
- [`nereus scm connection delete labs`](../../specs/cli/reefs/scm.html#connection-delete) delete removes the Connection, never the App
- [`nereus nereid apply forgejo`](../../specs/cli/reefs/scm.html#mirror-apply) The forgejo Nereid runs Forgejo in the cluster, in the profile
- [`nereus scm mirror create nereus`](../../specs/cli/reefs/scm.html#mirror-create) A Mirror copies a repository into the cluster
- [`nereus scm mirror list`](../../specs/cli/reefs/scm.html#mirror-list) list shows the commit each copy holds

## Examples

### apply-github

Apply the github Nereid to both Reefs.

```bash
nereus nereid apply github \
  --reef authentication \
  --reef scm
```

``` { .text .output title="output" }
✓ core/nereids/github created, Ready, pinned to sha256:1e74cbc6a968: see 'nereus authentication --help'
  namespaces/nereus-system-github applied (the github Nereid's Role there, where vault default delivers the App keys)

Next steps:

  nereus mandate create github --reef authentication --nereid github --param appId=<id> --param privateKey=<secret> --param allow=<namespace>:<repository>:<permission>=<level> --default
  nereus mandate create github-scm --reef scm --nereid github --param identity=github --default
```

### connection-create

The organisation, through the Reef's default Mandate.

```bash
nereus scm connection create example \
  --org example
```

``` { .text .output title="output" }
✓ scm/connections/example created (mandate github-scm)

Next steps:

  nereus scm connection get example
```

### connection-list

Every Connection, with its status.

```bash
nereus scm connection list
```

``` { .text .output title="output" }
CONNECTION  ORG           MANDATE     STATUS              DEFAULT
example     example       github-scm  Ready               yes
labs        example-labs  github-scm  NotInstalled        no
meta        example-meta  github-scm  MissingPermissions  no
some        example-some  github-scm  NotAllRepositories  no
```

### connection-delete

Remove the Connection.

```bash
nereus scm connection delete labs
```

``` { .text .output title="output" }
✓ scm/connections/labs deleted

Next steps:

  nereus scm connection list
```

### mirror-apply

Apply the forgejo Nereid to the scm Reef; it needs the release and secrets Reefs.

```bash
nereus nereid apply forgejo \
  --reef scm
```

``` { .text .output title="output" }
✓ core/nereids/forgejo created, Ready: see 'nereus scm --help'
  core/mandates/forgejo created (reef: scm, nereid: forgejo)

Next steps:

  nereus scm mirror create <name> --from https://github.com/<owner>/<repository>
```

### mirror-create

Copy a public repository, pulled every 10 minutes.

```bash
nereus scm mirror create nereus \
  --from https://github.com/getnereus/nereus \
  --interval 10m
```

``` { .text .output title="output" }
✓ scm/mirrors/nereus created (mandate forgejo)

Next steps:

  nereus scm mirror get nereus
```

### mirror-list

Every Mirror, the commit it holds and its status.

```bash
nereus scm mirror list
```

``` { .text .output title="output" }
MIRROR   FROM                                       MANDATE  LAST SYNC             COMMIT   STATUS
nereus   https://github.com/getnereus/nereus        forgejo  2026-11-10T12:00:00Z  68d7a0d  Ready
outside  https://example.com/example/outside        forgejo  -                     -        SourceUnreachable
```
