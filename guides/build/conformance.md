# Pass the conformance tests

Prove that a Nereid serves every verb of every kind of its Reef, with the status its contract declares, before anyone else relies on it.

## Before you start

- A throwaway k3d cluster, never the kept cluster `k3d-nereus`: the check creates and deletes objects, and refuses any other context.
- The Nereid applied and `Ready` ([Build a Nereid's image](image.md)), and named by the Reef's default Mandate.

## Steps

### 1. Ship a sample per kind

Each kind of the Reef has a sample in its contract, `cli/src/nereus/interfaces/<reef>/samples/<kind>.yaml`: the objects the kind needs first, the object as created, then the same object with a change to its spec. The `release` Reef ships `release.yaml`, `repository.yaml`, `source.yaml` and `target.yaml`.

### 2. Write the status the contract declares

Every object the Nereid answers gets a `Ready` condition whose reason the contract declares, `status.observedGeneration`, and the finalizer `<reef>.getnereus.dev/cleanup`, removed only once what it made is gone. A kind the Nereid does nothing with still answers, with the reason `NotApplicable`.

### 3. Run the check

`test/conformance` drives `nereus` and `kubectl` kind by kind: apply with `--dry-run` then for real, the status checked against the kind's schema, the finalizer, a change, `get`, `list`, then delete.

```bash
test/conformance release --nereid reference-release
```

``` { .text .output title="output" }
✓ reference-release serves every verb of every kind of the release reef and honours its contract: Release Repository Source Target
```

`--timeout` sets the seconds each wait lasts, 120 by default.

## Check it worked

The last line of the run names every kind it proved; any `FAIL:` line before it names the object, the field and the rule it breaks.

`make scene-release` runs the same check against the reference Nereid, then against `flux`.

## Next

- [See what happened](../troubleshoot/see-what-happened.md) when a step of the check fails.
- [Require a Reef](requires.md).

## Learn more

- [Spec 0003](../../specs/0003-nereid-conformance.md): what every Nereid answers, and the check kind by kind.
- [ADR 0013](../../adr/0013-command-conventions.md): the verbs every kind serves.
