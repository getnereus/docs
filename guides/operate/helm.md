# Install with Helm

Install Nereus and the profile `internal-developer-platform` on a cluster you made, with two `helm upgrade --install` lines and no `nereus init`.

## Before you start

- The k3d cluster `nereus` of [Prepare a cluster for Nereus](cluster.md), with its folder `nereus/` kept: the nodes mount it, and the chart `nereus` takes the registry CA from it.
- `helm` and `kubectl` pointed at that cluster. Both charts and every image are published on `ghcr.io/getnereus/nereus`, by digest, so nothing is built.

## Steps

### 1. Install the kinds

The chart `nereus-reefs` holds every kind, kept on uninstall, so a plain `helm upgrade` updates them.

```bash
helm upgrade --install nereus-reefs \
  oci://ghcr.io/getnereus/nereus/charts/nereus-reefs \
  --version 0.1.6 \
  --namespace nereus-system \
  --create-namespace \
  --wait
```

``` { .text .output title="output" }
Release "nereus-reefs" does not exist. Installing it now.
Pulled: ghcr.io/getnereus/nereus/charts/nereus-reefs:0.1.6
Digest: sha256:50389e42b8f2ed45423ca3c221607cc28aa1984c411c528912ec18daa5ac8246
NAME: nereus-reefs
NAMESPACE: nereus-system
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

### 2. Install the Gateway API's kinds

The chart `nereus` renders the API's route only when the Gateway API's kinds exist, so apply them first, at the version `nereus init` uses.

```bash
kubectl apply --server-side --filename \
  https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.7.0/standard-install.yaml
```

### 3. Install Nereus and the profile

The chart `nereus` brings the API and thetis, the installer Nereid, plus the Installation, the Profile and the registry CA as the Secret `registry-ca`. `--take-ownership` adopts the namespace of step 1.

```bash
helm upgrade --install nereus oci://ghcr.io/getnereus/nereus/charts/nereus \
  --version 0.1.6 \
  --namespace nereus-system \
  --take-ownership \
  --set installation.name=nereus \
  --set profile=internal-developer-platform \
  --set ingress.address=http://localhost:8080 \
  --set-file registryCA.certificate=nereus/registry/ca.crt \
  --set-file registryCA.key=nereus/ca.key
```

``` { .text .output title="output" }
Release "nereus" does not exist. Installing it now.
Pulled: ghcr.io/getnereus/nereus/charts/nereus:0.1.6
Digest: sha256:2beceb8078d35e6ac4ebc90a0ba4cdd0bd873664794336fd22f5d953920e9a7f
NAME: nereus
NAMESPACE: nereus-system
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

The profile is the file `profiles/<profile>.yaml` of the chart; a name with no file fails before anything is installed, listing the profiles there are.

The metrics Reef scrapes every 30s; `--set metrics.scrapeInterval=15s` changes it, whole seconds from 10s to 60s, before thetis creates the metrics Reef's Mandate ([#2199](https://github.com/getnereus/nereus/issues/2199)). Any other value fails the chart.

### 4. Remove the CA key

The key now lives in the Secret, kept on uninstall, and in Helm's release history in `nereus-system`. Delete the file with `rm nereus/ca.key`.

### 5. Wait for the profile

thetis installs each Reef, Nereid and Mandate in the order of what each requires; the Profile is Ready when the last one is, in about 8 minutes.

```bash
kubectl get profiles.core.getnereus.dev nereus --watch
```

``` { .text .output title="output" }
NAME     PROFILE                       READY   AGE
nereus   internal-developer-platform   True    8m30s
```

### 6. Log in

Helm writes no CLI config: set `NEREUS_API_URL=http://localhost:8080` so every command finds the instance, then [`nereus login`](../../specs/cli/reefs/authentication.html#login-device) keeps that URL.

```bash
nereus login --use-device-code
```

## Check it worked

[`nereus reef list`](../../specs/cli/core.html#reef-list) shows the same Reefs `nereus init --profile internal-developer-platform` gives; `nereus nereid list` shows each Nereid Ready, from `ghcr.io/getnereus/nereus`.

```bash
nereus reef list
```

``` { .text .output title="output" }
REEF            NEREIDS
authentication  keycloak
build           buildkit
catalog         catalog
database        cloudnative-pg
delivery        kubernetes
environment     vcluster
metrics         victoriametrics
portal          nereus-portal
registry        zot
release         flux
scm             forgejo
secrets         openbao
tenancy         -
```

## Clean up

Delete the cluster with `k3d cluster delete nereus` and its folder with `rm -r nereus`.

## Next

- [Rebuild the kept cluster](kept-cluster.md) from a published version.
- [Keep a secret](../reefs/secrets.md) in the vault the profile made.

## Learn more

- [Runtime and profiles](../../concepts/runtime-and-profiles.md): what a profile installs and in what order.
