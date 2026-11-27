# Prepare the undercloud

Create the installation's undercloud, `<installation>-undercloud`, a local cluster with the `cloud` Reef whose public OIDC issuer a cloud trusts, here Azure.

!!! note "Recorded against fakes"
    The outputs are what `init` prints in its tests, against a fake k3d, a fake Nereid, a fake `az` and recorded Azure answers. A real subscription is checked by hand (#266).

## Before you start

- What [Prepare the cluster](../../start/init.md) needs, plus the image of the Nereid `azure` in the local registry: `init` reads its login label before the cluster exists, and stops naming it when it is missing.
- `az login` done, with rights to create a resource group, a storage account and a managed identity.

## Steps

### 1. Name the cloud and the installation

The settings file names both; a cloud target needs the installation's name, since it names everything created in the cloud. `--target azure --installation-name tailwind` does the same without a file.

```yaml
apiVersion: core.getnereus.dev/v1alpha1
kind: InitConfig
spec:
  cloud: azure
---
apiVersion: core.getnereus.dev/v1alpha1
kind: Installation
metadata:
  name: tailwind
spec:
  id: 0b7e4c1a-93d2-4f6e-8a1b-2c3d4e5f6a7b
  alias: tailwind
```

### 2. See the plan

[`nereus init --dry-run`](../../specs/cli/core.html#init-target) computes the issuer's URL from the installation's id, creates the cluster with it, and prints the plan for Azure; nothing runs there. `--show-requests` adds why each resource exists, each request's URL and its tags.

```bash
nereus init --dry-run --yes
```

``` { .text .output title="output" }
✓ undercloud tailwind-undercloud on k3d    0s
✓ installation tailwind, new               0s
✓ Reef cloud, Nereid azure    0s

Plan for Azure · northeurope · 9 requests · not run (--dry-run)
  1  create   resource group        tailwind-platform
  2  create   storage account       issuers0b7e4c1a93d24f6e
  3  create   container             oidc
  4  access   Storage Blob Data Contributor on issuers0b7e4c1a93d24f6e to you
  5  publish  issuer documents (3)
  6  create   managed identity      tailwind-cloud-provisioner
  7  create   federated credential  tailwind-undercloud-azure
  tagged with the installation and who asked
  --show-requests for the why, URLs and tags

Nothing ran in Azure. To run it:
$ nereus init --yes --approve-access
```

### 3. Approve and run it

Without `--approve-access`, `init` asks `Approve 9 requests? [y/N]`, and a non-interactive run stops. Each line then shows its progress, ending with the proof that Azure trusts the undercloud: the Nereid `azure` exchanging its token.

```bash
nereus init --yes --approve-access
```

A request Azure refuses marks its line `✗` and says what an administrator has to run ([Connect to the cloud](cloud.md)).

### 4. Run it again

The cluster, the installation and the Reef are kept, and the plan is made again. When the published keys are the cluster's own, nothing is uploaded; when they changed, the issuer is marked `Stale` and the upload planned. A cluster presenting another issuer is recreated, but only one whose namespace says `undercloud` and whose Installation has this name and id.

## Check it worked

The run ends with `✓ azure exchanged its token as tailwind-cloud-provisioner`. Each run that sends requests writes a log, readable by you alone, in `~/.local/state/nereus/logs/`: the plan, each request and its answer's status, never a token.

## Next

- [Connect to the cloud](cloud.md): the Nereid `azure` and what it may do.
- [Meet the time SLO](slo.md): the cloud target counts against 20 minutes.

## Learn more

- [Undercloud and overcloud](../../concepts/undercloud-overcloud.md).
- [Spec 0005](../../specs/0005-cloud-reef.md): the cloud Reef and the issuer.
