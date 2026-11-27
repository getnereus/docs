# Connect to the cloud

Apply the Nereid `azure` of the `cloud` Reef: it plans the cloud requests, and the CLI shows them in plain words, asks, and runs them on your machine with your short-lived token, which never leaves it.

!!! note "Recorded against fakes"
    The outputs are what the CLI prints in its tests, against a fake Nereid, `az` and cloud. A real subscription is checked by hand with `test/scene-azure` (#266).

## Before you start

- A cluster whose issuer Azure can reach: [Prepare the undercloud](undercloud.md) runs these steps for you; run them by hand on an existing cluster or for another subscription.
- `az login` done, and a default location (`az config set defaults.location=westeurope`) or `--param location=<region>` below.
- The `cloud` Reef applied: `nereus reef apply cloud --from-file ./reefs/cloud/`.

## Steps

### 1. See the plan, run nothing

[`nereus nereid apply`](../../specs/cli/core.html#nereid-apply) reads your login, writes the Mandate and the `Cloud` Instance `default`, waits for the Nereid's plan and shows it. With `--dry-run`, no cloud request is sent.

```bash
nereus nereid apply azure \
  --reef cloud \
  --dry-run \
  --param location=northeurope
```

``` { .text .output title="output" }
✓ image            0.0s  cloud-azure-controller:0.1.0 implements cloud, login az
✓ login            0.0s  az, account 00000000-…, organization from the login
✓ plan             0.0s  3 requests for cloud (r-01m5bk)

Plan for Azure · northeurope · 3 requests · not run (--dry-run)
  1  create  resource group        tailwind-platform
  2  create  managed identity      tailwind-cloud-provisioner
  3  create  federated credential  tailwind-undercloud-azure
  tagged with the installation and who asked
  --show-requests for the why, URLs and tags

Nothing ran in Azure. To run it:
$ nereus nereid apply azure --reef cloud --param location=northeurope --approve-access
```

The CLI derives each line's words from the request's method, URL and body, never from text the Nereid sends, so what you read is what runs. `--show-requests` adds each step's why, method, URL and tags.

### 2. Approve and run it

Without `--approve-access`, the CLI asks `Approve 3 requests? [y/N]`; a non-interactive run prints the plan and stops. Each line then gets `✓` and its time, and the run ends with the proof: the Nereid exchanging its token.

```bash
nereus nereid apply azure \
  --reef cloud \
  --param location=northeurope \
  --approve-access
```

### 3. Pick another subscription or location

`--param account=<subscription id>` uses another subscription of the same login; `--param location=<region>` writes the location, which a later run keeps.

### 4. Use an identity an administrator created

When you may not create identities, `--param identity=<client-id>` names one an administrator created. A first plan checks it is in the account; only once its client id matches does the Nereid plan its federated credential, so another identity is never trusted.

## Check it worked

The run ends with `✓ azure exchanged its token as tailwind-cloud-provisioner`. Every resource carries tags naming the installation, who asked and why it exists; the CLI shows no plan with a resource that lacks them.

## Next

- [The Nereid refused the Instance](../troubleshoot/issuer-not-public.md), when the cluster's issuer is not public.
- [A cloud request is refused](../troubleshoot/request-refused.md), when you lack a right.
- [Grant access](../access/grant-access.md): what the Reefs ask of the cloud.

## Learn more

- [Spec 0005](../../specs/0005-cloud-reef.md#the-azure-nereid): the Nereid `azure` and the requester tags.
