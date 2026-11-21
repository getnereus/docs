# ✗ plan: the Nereid refused the Instance: IssuerNotPublic

`nereus nereid apply azure` stops at the plan, before any cloud request.

## You see

``` { .text .output title="output" }
✓ image            0.0s  cloud-azure-controller:0.1.0 implements cloud, login az
✓ login            0.0s  az, account 00000000-…, organization from the login
✗ plan             0.0s  the Nereid refused the Instance: IssuerNotPublic
  what     the undercloud of installation tailwind presents Kubernetes' default issuer https://kubernetes.default.svc.cluster.local, which Azure cannot reach
  cause    probably created by nereus init without --target azure (k3d is the default): the issuer is set when the cluster is created and never changes after
  check    kubectl get --raw /.well-known/openid-configuration
  fix      nereus init --target azure --installation-name tailwind
  Nothing ran in the cloud.
```

## Why

The cluster presents Kubernetes' default issuer, which Azure cannot reach. The issuer is set when the cluster is created and never changes after.

## Fix

Create the undercloud with a public issuer, as in [Prepare the undercloud](../operate/undercloud.md):

```bash
nereus init --target azure --installation-name tailwind
```

## Check

`kubectl get --raw /.well-known/openid-configuration` shows an issuer under `blob.core.windows.net`, and the next `nereus nereid apply azure` prints its plan.
