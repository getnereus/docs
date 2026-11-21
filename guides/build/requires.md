# Require a reef

Make a Nereid require another reef through a label of its image: the CLI refuses to apply it until that reef has a Nereid, and refuses to delete that reef's last Nereid while it is needed.

A Nereid requires reefs, never Nereids ([spec 0003](../../specs/0003-nereid-conformance.md)): any Nereid of the reef will do.

## Before you start

- The `release` reef with its Nereid `reference-release`, from [Build a Nereid's image](image.md).
- An image whose label `core.getnereus.dev/requires` lists the reefs it needs, comma-separated. Build the reference Nereid as a Nereid of a `docs` reef that requires `release`: `docker build --build-arg API_GROUP=core.getnereus.dev --build-arg REEF=docs --build-arg REQUIRES=release --tag localhost:5111/reference-docs-controller:0.1.0 controllers/reference`, then `docker push` it.

## Steps

### 1. Create the reef

[`nereus reef create`](../../specs/cli/core.html#reef-create) adds the `docs` reef the new Nereid looks after.

```bash
nereus reef create docs
```

### 2. Apply the Nereid that requires a reef

[`nereus nereid apply`](../../specs/cli/core.html#nereid-apply) reads `requires` from the image's labels and records it in the Nereid's `spec.requires`.

```bash
nereus nereid apply reference-docs \
  --reef docs \
  --image localhost:5111/reference-docs-controller:0.1.0
```

`release` has a Nereid, so the apply goes ahead. Without one, it is refused before anything runs, with `reference-docs requires reefs with no Nereid: release.` and the command that applies one. When the required reef's Nereid is there but not `Ready`, the apply warns and goes ahead.

## Check it worked

[`nereus nereid list`](../../specs/cli/core.html#nereid-list) shows both Nereids `Ready`: `reference-docs` on `docs`, `reference-release` on `release`.

```bash
nereus nereid list
```

## Clean up

`reference-release` is the last Nereid of `release`, which `docs` requires, so [`nereus nereid delete`](../../specs/cli/core.html#nereid-delete) refuses it first:

```bash
nereus nereid delete reference-release
```

``` { .text .output title="output" }
✗ reference-release is the last Nereid of reef release, which added Nereids require: reference-docs.
  Remove them first, or go ahead with: nereus nereid delete reference-release --force
```

Delete `reference-docs` first, then the `docs` reef with [`nereus reef delete`](../../specs/cli/core.html#reef-delete); `reference-release` stays:

```bash
nereus nereid delete reference-docs
```

```bash
nereus reef delete docs
```

## Next

- [Pass the conformance tests](conformance.md).
- [When the Nereid stops](../troubleshoot/nereid-stops.md): what a required reef's Nereid does to its commands.

## Learn more

- [Reef, Nereid and Mandate](../../concepts/model.md).
- [Spec 0003](../../specs/0003-nereid-conformance.md): the labels read at install, `requires` among them.
