# The release Reef

Every command of the release Reef: where a chart comes from, what it is, where it goes and the release itself.

## Commands

- [`nereus reef apply release`](../../specs/cli/reefs/release.html#apply-reef) One command applies the release Reef, with its four kinds
- [`nereus nereid apply reference-release`](../../specs/cli/reefs/release.html#apply-reference) The reference-release Nereid answers every kind with no tool, through the reference Mandate
- [`nereus nereid apply flux`](../../specs/cli/reefs/release.html#apply-flux) The flux Nereid installs Flux and becomes the default through its Mandate
- [`nereus release repository create codecentric`](../../specs/cli/reefs/release.html#repository-create) A repository says where the charts come from
- [`nereus release repository create codecentric`](../../specs/cli/reefs/release.html#repository-apply) Apply takes a file, and applying what already holds changes nothing
- [`nereus release repository list`](../../specs/cli/reefs/release.html#repository-list) The list shows every repository and whether it is ready
- [`nereus release repository get codecentric`](../../specs/cli/reefs/release.html#repository-get) One repository, by its name
- [`nereus release repository delete codecentric`](../../specs/cli/reefs/release.html#repository-delete) A repository goes once no source names it
- [`nereus release source create keycloak`](../../specs/cli/reefs/release.html#source-create) A source is one chart of a repository, at one version
- [`nereus release source create keycloak`](../../specs/cli/reefs/release.html#source-apply) A new version is one file away
- [`nereus release source list`](../../specs/cli/reefs/release.html#source-list) The list shows every source with its chart and version
- [`nereus release source get keycloak`](../../specs/cli/reefs/release.html#source-get) One source, by its name
- [`nereus release repository create ghcr`](../../specs/cli/reefs/release.html#source-publish) Publishing goes through the platform, with its credential, never yours
- [`nereus release source delete keycloak`](../../specs/cli/reefs/release.html#source-delete) A source in use is refused, with what to delete first
- [`nereus release target create dev-identity`](../../specs/cli/reefs/release.html#target-create) A target is a namespace, of an environment or of the cluster Nereus runs in
- [`nereus release target create dev-identity`](../../specs/cli/reefs/release.html#target-apply) Applying the same target again changes nothing
- [`nereus release target list`](../../specs/cli/reefs/release.html#target-list) The list shows every target with its environment and namespace
- [`nereus release target get dev-identity`](../../specs/cli/reefs/release.html#target-get) One target, by its name
- [`nereus release target delete dev-identity`](../../specs/cli/reefs/release.html#target-delete) A target goes once no release names it
- [`nereus release create keycloak-reference`](../../specs/cli/reefs/release.html#release-create) A release runs a source in a target, through the Reef's default Mandate
- [`nereus release create keycloak`](../../specs/cli/reefs/release.html#release-create-values) Values and a Mandate of your choice, with Flux installing the chart
- [`nereus release create keycloak`](../../specs/cli/reefs/release.html#release-create-secrets) A release asks for its secrets by name, and its values never pass through Nereus
- [`nereus release create keycloak-reference`](../../specs/cli/reefs/release.html#release-apply) One folder holds the whole release, and the second apply changes nothing
- [`nereus release list`](../../specs/cli/reefs/release.html#release-list) The list shows every release, its version and the Nereid behind it
- [`nereus release get keycloak-reference`](../../specs/cli/reefs/release.html#release-get) One release, by its name
- [`nereus release delete keycloak-reference`](../../specs/cli/reefs/release.html#release-delete) Deleting a release uninstalls its chart
- [`kubectl apply`](../../specs/cli/reefs/release.html#ingress-crds) The Gateway API CRDs come first, applied by hand for now
- [`nereus release repository create istio`](../../specs/cli/reefs/release.html#ingress-repository) Istio's charts come from its own Helm repository
- [`nereus release source create istio-base`](../../specs/cli/reefs/release.html#ingress-sources) Three charts at one pinned version: base and istiod first
- [`nereus release source create istio-gateway`](../../specs/cli/reefs/release.html#ingress-sources-gateway) Three charts at one pinned version: then the gateway, into istio-system
- [`nereus release create istio-base`](../../specs/cli/reefs/release.html#ingress-istio-base) Each chart starts once the previous one is Ready: base first
- [`nereus release create istiod`](../../specs/cli/reefs/release.html#ingress-istiod) Then istiod, the control plane
- [`nereus release create istio-gateway`](../../specs/cli/reefs/release.html#ingress-istio-gateway) Last, the ingress gateway, with no values of its own
- [`kubectl apply`](../../specs/cli/reefs/release.html#ingress-curl) A Gateway opens Envoy's listener, and with no route it answers 404

## Examples

### apply-reef

Apply the release Reef.

```bash
nereus reef apply release
```

``` { .text .output title="output" }
✓ core/reefs/release 0.1.0 created (release.getnereus.dev/v1alpha1: releases, repositories, sources, targets)

Next steps:

  nereus release --help
  nereus nereid apply <nereid> --reef release
```

### apply-reference

Apply the reference Nereid to the release Reef.

```bash
nereus nereid apply reference-release \
  --reef release \
  --image localhost:5111/reference-release-controller:0.1.0
```

``` { .text .output title="output" }
✓ core/nereids/reference-release created, Ready, pinned to sha256:b3c32d74194e: see 'nereus release --help'

Next steps:

  nereus nereid list
```

### apply-flux

Apply the flux Nereid to the release Reef.

```bash
nereus nereid apply flux \
  --reef release
```

``` { .text .output title="output" }
✓ core/nereids/flux created, Ready, pinned to sha256:e8731e3fb833: see 'nereus release --help'
  flux/v2.9.6 created (source-controller, helm-controller in namespace flux-system)

Next steps:

  nereus mandate create flux --reef release --nereid flux --default
```

### repository-create

A Helm repository over http.

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

### repository-apply

Apply the file.

```bash
nereus release repository apply \
  --from-file codecentric.yaml
```

``` { .text .output title="output" }
release/repositories/codecentric unchanged

Next steps:

  nereus release repository list
```

### repository-list

Every repository.

```bash
nereus release repository list
```

``` { .text .output title="output" }
NAME         TYPE  URL                                        READY
codecentric  http  https://codecentric.github.io/helm-charts  True
```

### repository-get

One repository.

```bash
nereus release repository get codecentric
```

``` { .text .output title="output" }
NAME         TYPE  URL                                        READY
codecentric  http  https://codecentric.github.io/helm-charts  True
```

### repository-delete

Delete the repository.

```bash
nereus release repository delete codecentric
```

``` { .text .output title="output" }
✓ release/repositories/codecentric deleted

Next steps:

  nereus release repository list
```

### source-create

The keycloakx chart at 7.0.1.

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

### source-apply

Apply the file.

```bash
nereus release source apply \
  --from-file keycloak.yaml
```

``` { .text .output title="output" }
✓ release/sources/keycloak configured

Next steps:

  nereus release source list
```

### source-list

Every source.

```bash
nereus release source list
```

``` { .text .output title="output" }
NAME      REPOSITORY   CHART      VERSION  DIGEST  READY
keycloak  codecentric  keycloakx  7.0.2    -       True
```

### source-get

One source.

```bash
nereus release source get keycloak
```

``` { .text .output title="output" }
NAME      REPOSITORY   CHART      VERSION  DIGEST  READY
keycloak  codecentric  keycloakx  7.0.2    -       True
```

### source-publish

An OCI repository whose push credential is a secret of the platform.

```bash
nereus release repository create ghcr \
  --type oci \
  --url oci://ghcr.io/getnereus/charts \
  --secret ghcr-push
```

``` { .text .output title="output" }
✓ release/repositories/ghcr created
NAME  TYPE  URL                              READY
ghcr  oci   oci://ghcr.io/getnereus/charts   True

Next steps:

  nereus release source create <name> --repository ghcr --chart <chart> --version <version>
```

### source-delete

A release still uses it.

```bash
nereus release source delete keycloak
```

``` { .text .output title="output" }
✗ source keycloak is used by release keycloak-reference.
  Delete it first: nereus release delete keycloak-reference
```

### target-create

The identity namespace of the dev environment.

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

### target-apply

Apply the file.

```bash
nereus release target apply \
  --from-file dev-identity.yaml
```

``` { .text .output title="output" }
release/targets/dev-identity unchanged

Next steps:

  nereus release target list
```

### target-list

Every target.

```bash
nereus release target list
```

``` { .text .output title="output" }
NAME          ENVIRONMENT  NAMESPACE  READY
dev-identity  dev          identity   True
```

### target-get

One target.

```bash
nereus release target get dev-identity
```

``` { .text .output title="output" }
NAME          ENVIRONMENT  NAMESPACE  READY
dev-identity  dev          identity   True
```

### target-delete

Delete the target.

```bash
nereus release target delete dev-identity
```

``` { .text .output title="output" }
✓ release/targets/dev-identity deleted

Next steps:

  nereus release target list
```

### release-create

Run keycloak in dev-identity.

```bash
nereus release create keycloak-reference \
  --source keycloak \
  --target dev-identity
```

``` { .text .output title="output" }
✓ release/releases/keycloak-reference created (nereid: reference-release)

Next steps:

  nereus release get keycloak-reference --watch
```

### release-create-values

Keycloak with its values, through the flux Mandate.

```bash
nereus release create keycloak \
  --source keycloak \
  --target dev-identity \
  --values-file keycloak-values.yaml \
  --mandate flux
```

``` { .text .output title="output" }
✓ release/releases/keycloak created (nereid: flux)

Next steps:

  nereus release get keycloak --watch
```

### release-create-secrets

Keycloak with a Secret in its namespace and one key in its values.

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

### release-apply

Apply the folder: every kind of the Reef, in order.

```bash
nereus release apply \
  --from-file release/
```

``` { .text .output title="output" }
✓ release/releases/keycloak-reference created
NAME                SOURCE    TARGET        VERSION  NEREID             STATUS
keycloak-reference  keycloak  dev-identity  -        reference-release  Pending
keycloak-reference  keycloak  dev-identity  7.0.1    reference-release  Ready

Next steps:

  nereus release list
```

### release-list

Every release.

```bash
nereus release list
```

``` { .text .output title="output" }
NAME                SOURCE    TARGET        VERSION  NEREID             STATUS
keycloak-reference  keycloak  dev-identity  7.0.2    reference-release  Ready
```

### release-get

One release.

```bash
nereus release get keycloak-reference
```

``` { .text .output title="output" }
NAME                SOURCE    TARGET        VERSION  NEREID             STATUS
keycloak-reference  keycloak  dev-identity  7.0.2    reference-release  Ready
```

### release-delete

See what would go.

```bash
nereus release delete keycloak-reference \
  --dry-run
```

``` { .text .output title="output" }
release/releases/keycloak-reference would be deleted.
Nothing changed (--dry-run).
```

### ingress-crds

The Gateway API CRDs v1.7.0, standard channel.

```bash
kubectl apply \
  --server-side \
  --filename https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.7.0/standard-install.yaml
```

``` { .text .output title="output" }
customresourcedefinition.apiextensions.k8s.io/backendtlspolicies.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/gatewayclasses.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/gateways.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/grpcroutes.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/httproutes.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/listenersets.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/referencegrants.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/tcproutes.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/tlsroutes.gateway.networking.k8s.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/udproutes.gateway.networking.k8s.io serverside-applied
validatingadmissionpolicy.admissionregistration.k8s.io/safe-upgrades.gateway.networking.k8s.io serverside-applied
validatingadmissionpolicybinding.admissionregistration.k8s.io/safe-upgrades.gateway.networking.k8s.io serverside-applied
```

### ingress-repository

Istio's Helm repository.

```bash
nereus release repository create istio \
  --url https://blob.istio.io/istio-release/charts \
  --type http
```

``` { .text .output title="output" }
✓ release/repositories/istio created
NAME   TYPE  URL                                                  READY
istio  http  https://blob.istio.io/istio-release/charts  False

Next steps:

  nereus release source create <name> --repository istio --chart <chart> --version <version>
```

### ingress-sources

The CRDs of Istio.

```bash
nereus release source create istio-base \
  --repository istio \
  --chart base \
  --version 1.30.4
```

``` { .text .output title="output" }
✓ release/sources/istio-base created
NAME        REPOSITORY  CHART  VERSION  DIGEST  READY
istio-base  istio       base   1.30.4   -       True

Next steps:

  nereus release target create <name> --namespace <namespace>
```

### ingress-sources-gateway

The ingress gateway.

```bash
nereus release source create istio-gateway \
  --repository istio \
  --chart gateway \
  --version 1.30.4
```

``` { .text .output title="output" }
✓ release/sources/istio-gateway created
NAME           REPOSITORY  CHART    VERSION  DIGEST  READY
istio-gateway  istio       gateway  1.30.4   -       True

Next steps:

  nereus release target create <name> --namespace <namespace>
```

### ingress-istio-base

Istio's CRDs, through the flux Mandate.

```bash
nereus release create istio-base \
  --source istio-base \
  --target istio-system \
  --mandate flux
```

``` { .text .output title="output" }
✓ release/releases/istio-base created (nereid: flux)

Next steps:

  nereus release get istio-base --watch
```

### ingress-istiod

The control plane, once istio-base is Ready.

```bash
nereus release create istiod \
  --source istiod \
  --target istio-system \
  --mandate flux
```

``` { .text .output title="output" }
✓ release/releases/istiod created (nereid: flux)

Next steps:

  nereus release get istiod --watch
```

### ingress-istio-gateway

The ingress gateway, once istiod is Ready.

```bash
nereus release create istio-gateway \
  --source istio-gateway \
  --target istio-system \
  --mandate flux
```

``` { .text .output title="output" }
✓ release/releases/istio-gateway created (nereid: flux)

Next steps:

  nereus release get istio-gateway --watch
```

### ingress-curl

The Gateway ingress: class istio, the gateway's Service, HTTP on port 80.

```bash
kubectl apply \
  --filename gateway.yaml
```

``` { .text .output title="output" }
gateway.gateway.networking.k8s.io/ingress created
```
