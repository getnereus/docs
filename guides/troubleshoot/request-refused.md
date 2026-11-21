# ✗ create managed identity refused: AuthorizationFailed

An approved plan of `nereus nereid apply azure` stops at the first request the cloud refuses.

## You see

``` { .text .output title="output" }
✓ 1  create  resource group        tailwind-platform              0s
✗ 2  create  managed identity      tailwind-cloud-provisioner     0s
  3  create  federated credential  tailwind-undercloud-azure
  tagged with the installation and who asked
  --show-requests for the why, URLs and tags

✗ create managed identity tailwind-cloud-provisioner refused: AuthorizationFailed: The client cannot create managed identities in tailwind-platform.
  ran: create resource group tailwind-platform
  not run: create managed identity tailwind-cloud-provisioner, create federated credential tailwind-undercloud-azure
An administrator can create the identity, and give you Managed Identity Contributor on it:
  az identity create --resource-group tailwind-platform --name tailwind-cloud-provisioner
  az role assignment create --assignee <your-object-id> --role "Managed Identity Contributor" --scope <identity-id>
Then run:
  nereus nereid apply azure --reef cloud --param identity=<client-id>
  log: ~/.local/state/nereus/logs/20261019T221500Z-install.log
```

## Why

Your login lacks the right to create that resource (`403`). The later requests did not run.

## Fix

Ask an administrator to run the two `az` lines printed, then name the identity they created:

```bash
nereus nereid apply azure --reef cloud --param identity=<client-id>
```

## Check

The run ends with `✓ azure exchanged its token as tailwind-cloud-provisioner`. The log named in the output holds each request and its answer's status.
