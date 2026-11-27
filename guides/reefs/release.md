# Release a chart

Release a Helm chart into a namespace, with its values and its secrets, through the Nereid that its [Mandate](../../concepts/model.md) picks: Flux here, swappable for another tool.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`: it brings the release Reef with the Nereid `flux` as its default, and the secrets Reef.
- A secret `google-oauth` from [Keep a secret](secrets.md), in a vault that allows the target's namespace.
- A file `keycloak-values.yaml` with the chart's values.

## Steps

### 1. Point at the chart repository

A [`Repository`](../../specs/cli/reefs/release.html#repository-create) says where charts come from: `http` for a Helm repository, `oci` for a registry.

```bash
nereus release repository create codecentric \
  --url https://codecentric.github.io/helm-charts \
  --type http
```

``` { .text .output title="output" }
✓ release/repositories/codecentric created
NAME         TYPE  URL                                        READY
codecentric  http  https://codecentric.github.io/helm-charts  True

Next steps:

  nereus release source create <name> --repository codecentric --chart <chart> --version <version>
```

### 2. Pick the chart and its version

A [`Source`](../../specs/cli/reefs/release.html#source-create) is one chart at one version.

```bash
nereus release source create keycloak \
  --repository codecentric \
  --chart keycloakx \
  --version 7.0.1
```

``` { .text .output title="output" }
✓ release/sources/keycloak created
NAME      REPOSITORY   CHART      VERSION  DIGEST  READY
keycloak  codecentric  keycloakx  7.0.1    -       True

Next steps:

  nereus release target create <name> --namespace <namespace>
```

### 3. Say where it goes

A [`Target`](../../specs/cli/reefs/release.html#target-create) is a namespace, made when missing. `--environment` picks an environment of the environment Reef; without it, the target is in the cluster Nereus runs in.

```bash
nereus release target create dev-identity \
  --environment dev \
  --namespace identity
```

``` { .text .output title="output" }
✓ release/targets/dev-identity created
NAME          ENVIRONMENT  NAMESPACE  READY
dev-identity  dev          identity   True

Next steps:

  nereus release create <name> --source <source> --target dev-identity
```

### 4. Release it with its values and secrets

[`nereus release create`](../../specs/cli/reefs/release.html#release-create-secrets) puts the source in the target. `--secret` makes a Kubernetes Secret with every key of a secret in the target's namespace; `--secret-value <path>=<secret>/<key>` puts one key into one values field. The CLI refuses a vault that does not allow the namespace before writing anything.

```bash
nereus release create keycloak \
  --source keycloak \
  --target dev-identity \
  --values-file keycloak-values.yaml \
  --mandate flux \
  --secret google-oauth \
  --secret-value nereus.googleClientId=google-oauth/GOOGLE_CLIENT_ID
```

``` { .text .output title="output" }
✓ release/releases/keycloak created (nereid: flux)
  binding secrets/vaults/default/secrets/google-oauth/secretbindings/identity/keycloak
  binding secrets/vaults/default/secrets/google-oauth/secretbindings/nereus-system/keycloak-values-google-oauth

Next steps:

  nereus release get keycloak --watch
```

## Check it worked

[`nereus release get --watch`](../../specs/cli/reefs/release.html#release-create-secrets) follows the release: the secret bindings first, then the chart, until it is `Ready`.

```bash
nereus release get keycloak \
  --watch
```

``` { .text .output title="output" }
NAME      SOURCE    TARGET        VERSION  NEREID             STATUS
keycloak  keycloak  dev-identity  7.0.1    flux    Pending
2026-10-30T07:53:21Z  ✓ binding      2 Secrets ready: identity/keycloak, nereus-system/keycloak-values-google-oauth.
2026-10-30T07:53:21Z  ✓ helmrelease  Wrote the Flux HelmRelease keycloak.
keycloak  keycloak  dev-identity  7.0.1    flux    Progressing
keycloak  keycloak  dev-identity  7.0.1    flux    Ready
```

A release that fails shows `Failed` once Flux stops retrying; a refused namespace or a failed binding shows `BindingFailed`.

## Next

- [Run a registry](registry.md) to publish your own chart with [`nereus release source publish`](../../specs/cli/reefs/release.html#source-publish).
- [Follow the golden path](golden-path.md): your own image, deployed through a ready-made chart into an Environment of its own.

## Learn more

- [The release Reef](../../reference/reefs/release.md): repositories, sources, targets and releases, every command.
- [Runtime and profiles](../../concepts/runtime-and-profiles.md): why the Mandate, not the Reef, picks Flux.
