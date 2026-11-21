# Apply a reef and its Nereid

Add the release reef, the reference Nereid that serves it, and the Mandate that makes that Nereid the reef's answer.

## Run

Apply the reef, from the version this CLI pins: [`nereus reef apply release`](../specs/cli/core.html#reef-apply)

```bash
nereus reef apply release
```

``` { .text .output title="output" }
✓ core/reefs/release 0.1.0 created (release.getnereus.dev/v1alpha1: releases, repositories, sources, targets)

Next steps:

  nereus release --help
  nereus nereid apply <nereid> --reef release
```

Apply the reference Nereid, which answers every command of the reef with no tool behind it: [`nereus nereid apply`](../specs/cli/core.html#nereid-apply)

```bash
nereus nereid apply reference-release
```

The CLI reads the reef from the image's label, pins the image to its digest and waits until the Nereid reports `Ready`; its next step names the Mandate below.

Bind the reef to it, as the reef's default: [`nereus mandate create`](../specs/cli/core.html#mandate-create)

```bash
nereus mandate create reference --reef release --nereid reference-release --default
```

It prints `core/mandates/reference created (reef: release, nereid: reference-release, default)`.

## What you get

- The reef `release`, with its four kinds, and a `release` command group in the CLI: `nereus release --help` lists the commands its Nereid published.
- The Nereid `reference-release`, running in the cluster as the reef's controller.
- The Mandate `reference`, which sends every request of the reef to that Nereid ([Reef, Nereid and Mandate](../concepts/model.md)).

## Next

[Run its commands](run.md).
