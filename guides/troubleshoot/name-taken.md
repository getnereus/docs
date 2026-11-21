# ✗ names: storage account is taken in Azure

`nereus init --target azure` stops at the names plan, before it creates anything in Azure.

## You see

``` { .text .output title="output" }
✗ names                         0.1s  storage account issuers0b7e4c1a93d24f6e is taken in Azure
  total                         0.2s  slo 20m, 0% green
  Record it for issuer.storage, then prepare the undercloud again with it:
    nereus config installation set --naming-override issuer.storage=issuers0b7e4c1a93d24f6e2
    nereus init --target azure
```

## Why

A storage account name is unique across Azure, and the issuer's is `issuers<id16>`. The likely owner is a deleted installation with the same id.

## Fix

Record the suggested name with [`nereus config installation set`](../../specs/cli/core.html#installation-set), then prepare the undercloud again:

```bash
nereus config installation set \
  --naming-override issuer.storage=issuers0b7e4c1a93d24f6e2
nereus init --target azure
```

In a terminal without `--yes`, `init` asks instead, and a yes does the same:

``` { .text .output title="output" }
? Use issuers0b7e4c1a93d24f6e2 for issuer.storage? (Y/n) y
✓ installation tailwind  naming.overrides.issuer.storage = issuers0b7e4c1a93d24f6e2
```

## Check

The next `init` recreates the cluster with the new issuer and runs to the end: every line starts with `✓`.
