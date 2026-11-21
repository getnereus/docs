# Grant access

Grant a Nereid that reaches the cloud the roles it asks for: the Nereid acts as its reef's identity, `<installation>-<reef>-<role>`, with no secret of its own; it asks, and you approve with your own login.

## Before you start

- An installation [connected to the cloud](../operate/cloud.md): the cloud reef with its Nereid `azure`.
- A Nereid whose image declares `requires: cloud` ([spec 0005](../../specs/0005-cloud-reef.md)), here `keyvault` for the secrets reef.
- A cloud login that can create identities and role assignments. A role it cannot write is printed as the command an administrator runs.

!!! note "Recorded against fakes"
    The outputs below come from the CLI's tests, against a fake cloud Nereid and a fake cloud. `test/scene-azure` runs a real subscription.

## Steps

### 1. Apply the Nereid

[`nereus nereid apply`](../../specs/cli/core.html#nereid-apply) gives the Nereid a short-lived token for the cloud, writes its reef's access entry and shows the plan that creates its identity.

```bash
nereus nereid apply keyvault \
  --reef secrets
```

``` { .text .output title="output" }
✓ image            0.0s  secrets-keyvault-controller:0.1.0 implements secrets, requires cloud
✓ login            0.0s  az, account 00000000-…
✓ mandate          0.0s  core/mandates/keyvault created (reef: secrets, nereid: keyvault, default)
✓ plan             0.1s  2 requests for secrets (r-01m5bk)
  1  create  managed identity      tailwind-secrets-reader  in westeurope
  2  create  federated credential  tailwind-undercloud-keyvault
  tagged with the installation and who asked
  --show-requests for the why, URLs and tags
  log: ~/.local/state/nereus/logs/20261019T221500Z-install.log
Approve 2 requests? [y/N]: y
✓ requests         0.0s  2 applied
✓ ready            0.0s  keyvault reports Ready
  total            0.1s
✓ keyvault added to secrets · acts as tailwind-secrets-reader
```

Another Nereid of the same reef later keeps the identity and its grants: the plan only swaps the federated credential.

### 2. See what is asked

`nereus system access list` shows each reef's access entries and the roles its Nereid asks for but nobody approved yet.

```bash
nereus system access list
```

``` { .text .output title="output" }
REEF       REQUEST        WHAT                                                                                                              STATE
cloud      r-01jaq3…m2n3  identity tailwind-cloud-provisioner                                                                               Applied
secrets    r-01m59t…zejf  identity tailwind-secrets-reader                                                                                  Applied
secrets    -              grant Key Vault Secrets User on key vault vault-0123456789abcdef in resource group tailwind-platform              Asked
terraform  -              grant Storage Blob Data Contributor on storage account state0123456789abcdef in resource group tailwind-platform  Asked
```

An ask for `Owner`, `User Access Administrator` or `Role Based Access Control Administrator` shows `Refused` and is never copied into a plan.

### 3. Approve

`nereus system access approve --all` turns every reef's asks into plans, shows them and runs them after one question; `--dry-run` shows them and runs none.

```bash
nereus system access approve --all
```

``` { .text .output title="output" }
1/2 secrets  r-01m5bk…5563  2 requests
  1  check   managed identity  tailwind-secrets-reader
  2  access  Key Vault Secrets User on vault-0123456789abcdef to tailwind-secrets-reader
2/2 terraform  r-01m5bk…dh0a  3 requests
  1  create  managed identity      tailwind-terraform-runner  in westeurope
  2  create  federated credential  tailwind-undercloud-stacks
  3  access  Storage Blob Data Contributor on state0123456789abcdef to tailwind-terraform-runner
  tagged with the installation and who asked
  --show-requests for the why, URLs and tags
  log: ~/.local/state/nereus/logs/20261019T221500Z-approve.log
Approve 2 plans (5 requests)? [y/N]: y
✗ 1/2 secrets  r-01m5bk…5563  grant Key Vault Secrets User on vault-0123456789abcdef to tailwind-secrets-reader refused: AuthorizationFailed: The client cannot write role assignments on the account.
    ${0.properties.principalId} = 33333333-3333-4333-8333-333333333333
An administrator can grant Key Vault Secrets User to tailwind-secrets-reader:
  az role assignment create --assignee-object-id 33333333-3333-4333-8333-333333333333 --assignee-principal-type ServicePrincipal --role "Key Vault Secrets User" --scope /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/tailwind-platform/providers/Microsoft.KeyVault/vaults/vault-0123456789abcdef
✓ 2/2 terraform  r-01m5bk…dh0a  3 applied
    ${0.properties.principalId} = 33333333-3333-4333-8333-333333333333
✗ 1 of 2 plans applied: run 'nereus system access approve --all' again to apply what is missing
  log: ~/.local/state/nereus/logs/20261019T221500Z-approve.log
```

A failed plan undoes none of the others. Hand the printed `az` line to an administrator, or approve with a login that holds the right.

## Check it worked

Run the approval again: it plans only what is still missing, and ends with every plan applied.

```bash
nereus system access approve --all
```

``` { .text .output title="output" }
1/1 secrets  r-01m5bk…satf  2 requests
  1  check   managed identity  tailwind-secrets-reader
  2  access  Key Vault Secrets User on vault-0123456789abcdef to tailwind-secrets-reader
  --show-requests for the why, URLs and tags
  log: ~/.local/state/nereus/logs/20261019T221500Z-approve.log
Approve 2 requests? [y/N]: y
✓ 1/1 secrets  r-01m5bk…satf  2 applied
    ${0.properties.principalId} = 33333333-3333-4333-8333-333333333333
✓ 1 plan applied
```

## Next

- [Authorize people](authorization.md): who may run which command in the installation.

## Learn more

- [Undercloud and overcloud](../../concepts/undercloud-overcloud.md): why the installation's identity lives in the cloud.
- [Spec 0005](../../specs/0005-cloud-reef.md): the cloud reef, its plans and what a Nereid may ask.
