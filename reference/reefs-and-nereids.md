# Reefs and Nereids

The rules behind `nereus reef` and `nereus nereid`: what each command checks, writes and refuses. The model is in [Reef, Nereid and Mandate](../concepts/model.md); a first run is in [Apply a Reef and its Nereid](../start/first-reef.md).

## Apply a Reef

[`nereus reef apply release`](../specs/cli/core.html#reef-apply) applies the Reef's kinds from the version this CLI pins; applying again reports `unchanged` when no resourceVersion moved, as `kubectl apply` does.

[`nereus reef create release`](../specs/cli/core.html#reef-create) fails on an existing Reef, as `kubectl create` does, and shows the installed version: `reef cloud already exists (0.1.0)`.

`apply` takes three sources: the pinned version, local YAML with [`--from-file`](../specs/cli/core.html#reef-apply-file) (a file or a folder, alias `--path`), or a Reef package with `--image` (an OCI artifact of YAML layers). `--dry-run` lists what it would create.

With `--from-file`, it reports `configured` when the files changed a kind and `unchanged` when the same files come again.

## What a Reef may ship

A Reef is a `Reef` object, and may ship kinds of its own: the `cloud` Reef ships `Cloud` with the CLI, never with a Nereid ([spec 0005](../specs/0005-cloud-reef.md#the-objects)).

Whatever the source, the CLI checks every document first: only CustomResourceDefinitions of the platform's group, never a platform kind (`Reef`, `Nereid`, `Mandate`, `Installation`, `ServiceLevelObjective`), nor one another Reef owns.

A Reef may also ship a `ValidatingAdmissionPolicy` and binding, named `<name>.<reef group>`, matching only its own group, without parameters. The API then refuses for every client, as the tenancy Reef refuses a Project that is its own parent ([#646](https://github.com/getnereus/nereus/issues/646)).

## A Reef with no Nereid

The Reef's command group exists, empty until a Nereid is applied:

```bash
nereus release --help
```

``` { .text .output title="output" }
 Usage: nereus release [OPTIONS] COMMAND [ARGS]...

 Reef release: no Nereid applied.

 Apply one: nereus nereid apply <nereid> --reef release --image <image>
```

[`nereus reef list`](../specs/cli/core.html#reef-list) shows `-` under `NEREIDS`. Without the Reef, `nereid apply` is refused with `Apply it first: nereus reef apply release`.

## Apply a Nereid

[`nereus nereid apply reference-release`](../specs/cli/core.html#nereid-apply) reads the image's labels in the registry (manifest and config, no layer): name, Reef, required Reefs, version, repository.

It checks the Reef exists, writes the `Nereid` object pinned to the digest, runs the image as its controller and waits until it reports `Ready`. The same image again reports `core/nereids/reference-release unchanged`.

- A name argument wins over the label.
- `--reef <reef>` names a Reef the label lacks, or picks one when the label lists several; it repeats.
- An image that declares no Reef is refused: `declares no reef (label core.getnereus.dev/reef)`.

## The digest

The tag is resolved once to a digest (`pinned to`, the first 12 hex characters), so pushing the tag again never changes what runs.

An image given by digest (`--image <repository>@sha256:<64 hex>`) is applied as is, once its manifest matches. The full reference is in `spec.image`.

## Update a Nereid in place

[`nereus nereid apply reference-release --image`](../specs/cli/core.html#nereid-apply-image) moves a Nereid to another image with no delete: rules, Deployment and record move together; the apply ends once the new pod runs ([#386](https://github.com/getnereus/nereus/issues/386)).

`--dry-run` shows the digest it would move to. The same image with outdated rules names what it wrote, ending `clusterrole/controller-reference-release rules updated`.

A new image that fails prints the `nereus nereid apply` line with the last image that worked, which the Nereid records until a new pod has run.

Another Reef is refused: moving a Nereid between Reefs is a delete and an apply.

## List and get

[`nereus nereid list`](../specs/cli/core.html#nereid-list) shows each Nereid with its Reefs, image and status; [`nereus nereid get`](../specs/cli/core.html#nereid-get) adds the pinned digest, title, description and the Mandates naming it.

`reef list|get`, `nereid list|get` and `nereus status` read through the Nereus API with the token of `nereus login`, so they need no kubeconfig; only a member of `nereus-admins` reads them.

Logged out, they print `Not logged in` with the `nereus login` line. Until the instance offers sign-in (core alone), they read the cluster with the kubeconfig and print the same.

## Delete

[`nereus nereid delete reference-release`](../specs/cli/core.html#nereid-delete) removes the Nereid with its commands, Deployment, Service and identity, which belong to the `Nereid` object. The Reef stays, and its group says `no Nereid applied`.

`nereid delete` refuses the last Nereid of a Reef that applied Nereids require ([Require a Reef](../guides/build/requires.md)), unless `--force`.

[`nereus reef delete release`](../specs/cli/core.html#reef-delete) removes the `Reef` object and keeps its kinds, so a Nereid's objects stay. It is refused while a Nereid of the Reef is applied, and names the `nereid delete` to run first.

## The objects

A Reef and a Nereid are Kubernetes objects, `Reef` and `Nereid` of `core.getnereus.dev`: `kubectl get reefs` and `kubectl get nereids` list them.

One writer per field (ADR 0005, one writer for each field of an object): the CLI writes the Reef and the Nereid's `spec.image`, `spec.reefs`, `spec.requires` and `spec.version`; the controller writes only `status.conditions` and `status.commands`.

The CLI caches each Reef's group and its Nereid's commands in `~/.cache/nereus/commands.json`, as `kubectl` caches API discovery; `reef` and `nereid` commands refresh it.
