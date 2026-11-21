# Connect an organisation

Connect an organisation of a source host to Nereus through the GitHub App an scm Mandate names: you write the organisation, and the `github` Nereid writes whether the App reaches it. A Connection holds no key and no token.

## Before you start

- The App's Mandate `github`, `Ready`, from [Prove a GitHub App installed](../access/github-app.md). For GitHub to deliver events, give that Mandate the App's webhook secret in `--param webhookSecret=<secret>`.

## Steps

### 1. Apply the scm reef and the github Nereid

The scm reef is opt-in, outside the `internal-developer-platform` profile. One `github` Nereid serves both the authentication and the scm reef.

```bash
nereus reef apply scm
```

``` { .text .output title="output" }
✓ core/reefs/scm created (scm.getnereus.dev/v1alpha1: connections)
```

[`nereus nereid apply`](../../specs/cli/reefs/scm.html#apply-github) names both reefs.

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

### 2. Bind the scm reef to the App

[`nereus mandate create`](../../specs/cli/core.html#mandate-create) binds the scm reef to the Nereid. Its name follows `<nereid>-<reef>`, and its param `identity` names the App's Mandate; a second App is a second scm Mandate.

```bash
nereus mandate create github-scm \
  --reef scm \
  --nereid github \
  --param identity=github \
  --default
```

``` { .text .output title="output" }
✓ core/mandates/github-scm created (reef: scm, nereid: github, default)
  clusterrole/controller-github configured (nereid github writes the status of mandate github-scm)

Next steps:

  nereus mandate list
```

### 3. Connect the organisations

[`nereus scm connection create`](../../specs/cli/reefs/scm.html#connection-create) names one organisation. The first Connection is the reef's default; `--mandate` picks another scm Mandate.

```bash
nereus scm connection create example \
  --org example
```

``` { .text .output title="output" }
✓ scm/connections/example created (mandate github-scm)

Next steps:

  nereus scm connection get example
```

Connect `labs`, `meta` and `some` the same way, with `--org example-labs`, `example-meta` and `example-some`. A second `--default` is refused: one in the reef.

```bash
nereus scm connection create other \
  --org example-other \
  --default
```

``` { .text .output title="output" }
✗ scm/connections/example is the reef's default already: one in the reef. Nothing was changed.
```

## Check it worked

[`nereus scm connection list`](../../specs/cli/reefs/scm.html#connection-list) shows what the App reaches on each organisation. There is no `verify`: the status is the check, from the first that fails: `NotInstalled`, `NotAllRepositories`, `MissingPermissions` (less than `metadata` and `contents` read), else `Ready`.

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

`nereus scm connection get` says what to do about a status.

```bash
nereus scm connection get labs
```

``` { .text .output title="output" }
Name:          labs
Org:           example-labs
Mandate:       github-scm
Nereid:        github
Default:       no
Status:        NotInstalled
Installation:  -
Repositories:  -
Permissions:   -
Message:       the App of mandate github is not installed on the organisation example-labs: install it at https://github.com/apps/example-nereus/installations/new
```

The App's webhook points at `POST /scm/webhook` on the github Nereid's Service, reached only inside the cluster for now: a delivery is accepted only when `X-Hub-Signature-256` checks with the App's `webhookSecret`.

## Clean up

[`nereus scm connection delete`](../../specs/cli/reefs/scm.html#connection-delete) removes the Connection; the App stays installed on the organisation, and its Mandate in the authentication reef.

```bash
nereus scm connection delete labs
```

``` { .text .output title="output" }
✓ scm/connections/labs deleted

Next steps:

  nereus scm connection list
```

## Next

- [Mirror a repository](scm-mirror.md) of a connected organisation into the cluster.

## Learn more

- [The scm reef](../../reference/reefs/scm.md): Connections and Mirrors, every command.
- [Reef, Nereid and Mandate](../../concepts/model.md): why a Mandate holds the App, never the Connection.
