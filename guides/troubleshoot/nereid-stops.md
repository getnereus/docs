# ✗ nereid reference-release is Unavailable

A command of a Reef stops at once, sends nothing and exits non-zero, because its Nereid has no pod serving.

## You see

```bash
nereus release repo list
```

``` { .text .output title="output" }
✗ nereid reference-release is Unavailable: its Controller has no pod serving.
  Its commands work again by themselves once the Controller is back: see 'nereus nereid list'.
```

[`nereus nereid list`](../../specs/cli/core.html#nereid-list) shows the Nereid's `STATUS` as `Unavailable`, computed by the CLI from its Deployment.

## Why

The Nereid's Deployment has no ready pod: scaled to zero, or its pod crashing. A deleted pod is replaced by the Deployment, and the new one starts with an empty work directory.

## Fix

Bring the Deployment back, here scaled up from zero: `kubectl scale deployment reference-release --namespace nereus-system --replicas 1`. For a crashing pod, read why first in [See what happened](see-what-happened.md).

## Check

The same command works again by itself, with no retry flag:

```bash
nereus release repo add chaos-scaled https://charts.example.com
```

``` { .text .output title="output" }
"chaos-scaled" has been added to your repositories
```

`test/scene` kills the pod and scales the Deployment to zero and back, then checks these lines.
