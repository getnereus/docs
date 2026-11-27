# Connect a GitHub App

Connect a GitHub App as a Mandate of the authentication Reef's Nereid `github`: its status proves where the App is installed and what it may do, and consumers ask it for one-hour tokens, never for its key.

## Before you start

- A cluster with the secrets Reef and its vault `default`, from [Keep a secret](../reefs/secrets.md).
- An App you already have: its id, and its private key (a `.pem` file). With no App yet, [`nereus authentication app-register`](../../specs/cli/reefs/authentication.html#app-register) creates one in the browser, and only the Nereid ever holds its key; skip to step 4.
- [Reef, Nereid and Mandate](../../concepts/model.md): the App is a Mandate, its id and key its params.

## Steps

### 1. Keep the App's private key as a secret

[`nereus secrets create`](../../specs/cli/reefs/secrets.html#create) encrypts it on your machine before it leaves it.

```bash
GITHUB_APP_KEY="$(cat app.pem)" nereus secrets create github-app-key --from-env GITHUB_APP_KEY
```

``` { .text .output title="output" }
✓ secrets/vaults/default/secrets/github-app-key created (key SHA256:l0jt+UOKUmA72jydN0DSpTzFJIdO6wP/xUvdAKryBe4)
Stored encrypted; a Kubernetes Secret is made only when a binding asks for it (#532).
```

### 2. Apply the Nereid

The Nereid is opt-in, outside every profile. [`nereus nereid apply`](../../specs/cli/core.html#nereid-apply) gives it one namespace, `nereus-system-github`, the only one where it reads Secrets.

```bash
nereus nereid apply github --reef authentication
```

``` { .text .output title="output" }
✓ core/nereids/github created, Ready, pinned to sha256:021dd70640d0: see 'nereus authentication --help'
  namespaces/nereus-system-github applied (the github Nereid's Role there, where vault default delivers the App keys)

Next steps:

  nereus mandate create github --reef authentication --nereid github --param appId=<id> --param privateKey=<secret> --param allow=<namespace>:<repository>:<permission>=<level> --default
```

### 3. Create the App's Mandate

[`nereus mandate create`](../../specs/cli/core.html#mandate-create) names the App, its key's secret and who may ask a token. Each `allow` is `<namespace>:<repository or *>:<permission>=<level>`; with none, no token is ever made.

```bash
nereus mandate create github \
  --reef authentication \
  --nereid github \
  --param appId=123456 \
  --param privateKey=github-app-key \
  --param allow=nereus-system:*:contents=read \
  --param allow=example:example/app:metadata=read \
  --default
```

``` { .text .output title="output" }
✓ core/mandates/github created (reef: authentication, nereid: github, default)
  clusterrole/controller-github configured (nereid github writes the status of mandate github)
```

### 4. Lend a repository for an hour

[`nereus authentication token create`](../../specs/cli/reefs/authentication.html#token-create) asks the Mandate for a token of one repository. The Nereid writes it to the Secret `token-<name>` of the Token's namespace; no command prints it.

```bash
nereus authentication token create catalog \
  --repository example/app \
  --permission contents=read
```

``` { .text .output title="output" }
✓ authentication/tokens/catalog created (expires in 1h, mandate github)

Next steps:

  nereus authentication token get catalog
```

A namespace the Mandate does not allow gets no token, and the line names the `allow` to add.

## Check it worked

[`nereus mandate get`](../../specs/cli/core.html#mandate-get) shows the App as GitHub answered, and the allowlist as the Nereid read it.

```bash
nereus mandate get github
```

``` { .text .output title="output" }
Name:           github
Reef:           authentication
Nereid:         github
Default:        true
Params:         allow=nereus-system:*:contents=read;example:example/app:metadata=read, appId=123456, privateKey=github-app-key
Status:         Ready
App:            example-nereus
Installations:  example (all repositories)
Permissions:    contents=read, metadata=read
Age:            10s
Allowed:
  NAMESPACE      REPOSITORY   PERMISSIONS
  nereus-system  *            contents=read
  example        example/app  metadata=read
```

Another status names what is wrong: `NotInstalled` with the URL to install the App, `InvalidCredentials` for a key of no App, `MissingParam` for a secret that does not exist.

## Clean up

```bash
nereus authentication token delete catalog
```

``` { .text .output title="output" }
✓ authentication/tokens/catalog deleted

Next steps:

  nereus authentication token list
```

## Next

- [Connect a repository host](../reefs/scm-connection.md) that builds and mirrors through the App.

## Learn more

- [The authentication Reef](../../reference/reefs/authentication.md): `app-register`, tokens and every command.
- [ADR 0006](../../adr/0006-authentication-reef.md): the platform's identity towards an outside system is a Mandate.
