# Look around

See what the new installation holds before you add anything: its reefs and the Nereids that look after them.

## Run

See how each reef is doing, one row per reef and Nereid: [`nereus status`](../specs/cli/core.html#status)

```bash
nereus status
```

On core alone there are two rows, `core` and `tenancy`, both `Ready`.

List the reefs: [`nereus reef list`](../specs/cli/core.html#reef-list)

```bash
nereus reef list
```

`tenancy` is the only one, with `-` under `NEREIDS`: the Nereus API keeps its objects itself, so no Nereid serves it.

List the Nereids: [`nereus nereid list`](../specs/cli/core.html#nereid-list)

```bash
nereus nereid list
```

There are none yet; the line it prints points to `nereus nereid apply --help`.

## What you get

- A map of the installation: a reef is a capability with its own API group, a Nereid is the controller that looks after it ([Reef, Nereid and Mandate](../concepts/model.md)).
- These commands read the cluster with your kubeconfig, since core alone offers no sign-in; once an installation has the authentication reef, they read through the Nereus API and ask for `nereus login` first.

## Next

[Apply a reef and its Nereid](first-reef.md).
