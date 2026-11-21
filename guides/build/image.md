# Build a Nereid's image

Build a Nereid's image whose labels name its reef, push it to the local registry and apply it: the CLI reads the labels before anything runs in the cluster.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md): `nereus init` creates the local registry `localhost:5111`.
- The reef applied, here `release`: [Apply your first reef](../../start/first-reef.md).
- Docker, to build and push. The example is the reference Nereid of `controllers/reference`, whose commands only simulate output.

## Steps

### 1. Declare the reef in labels

The `Dockerfile` names the reef the Nereid looks after, the reefs it requires, its name and its version:

```dockerfile
LABEL ${API_GROUP}/reef=${REEF} \
      ${API_GROUP}/requires=${REQUIRES} \
      ${API_GROUP}/nereid=${NEREID} \
      ${API_GROUP}/reference=${REFERENCE} \
      org.opencontainers.image.version=${VERSION} \
      org.opencontainers.image.title=${TITLE}
```

`${API_GROUP}` is `core.getnereus.dev`. The reference Nereid's commands are data, in `commands.yaml`, each with its help and an example:

```yaml
- path: [repo, add]
  help: Add a chart repository.
  arguments:
    - name: name
      help: Name of the repository.
    - name: url
      help: URL of the repository.
```

### 2. Build and push

`make reference` builds the image for the `release` reef and pushes it; a Nereid from the template builds with `make nereids`.

```bash
make reference
```

``` { .text .output title="output" }
✓ localhost:5111/reference-release-controller:0.1.0 pushed: nereus nereid apply --image localhost:5111/reference-release-controller:0.1.0
```

### 3. Apply it

[`nereus nereid apply`](../../specs/cli/core.html#nereid-apply) reads the labels, pins the image to its digest and waits for `Ready`.

```bash
nereus nereid apply reference-release \
  --reef release \
  --image localhost:5111/reference-release-controller:0.1.0
```

``` { .text .output title="output" }
✓ core/nereids/reference-release created, Ready, pinned to sha256:ffb8e8957c6e: see 'nereus release --help'

Next steps:

  nereus nereid list
```

### 4. Move it to a new image

Applied again with another image, the Nereid is updated in place; `--dry-run` shows what would change and writes nothing.

```bash
nereus nereid apply reference-release \
  --image localhost:5111/reference-release-controller:0.1.1 \
  --dry-run
```

``` { .text .output title="output" }
Would configure core/nereids/reference-release for reef release: image sha256:ffb8e8957c6e → sha256:3f2a9c1d7e4b.
Nothing changed (--dry-run).
```

Without `--dry-run`, the apply waits for the new pod and says what the image was:

```bash
nereus nereid apply reference-release \
  --image localhost:5111/reference-release-controller:0.1.1
```

``` { .text .output title="output" }
✓ core/nereids/reference-release configured, Ready, pinned to sha256:3f2a9c1d7e4b (was sha256:ffb8e8957c6e): see 'nereus release --help'
```

## Check it worked

[`nereus nereid list`](../../specs/cli/core.html#nereid-list) shows the Nereid `Ready` on its reef:

```bash
nereus nereid list
```

``` { .text .output title="output" }
NEREID             REEFS    IMAGE                                                 STATUS  AGE
reference-release  release  localhost:5111/reference-release-controller:0.1.0     Ready   10s
openbao            secrets  localhost:5111/openbao-controller:0.1.0               Ready   1m
```

The commands it published are under its reef: `nereus release --help`.

## Clean up

[`nereus nereid delete`](../../specs/cli/core.html#nereid-delete) removes it; its reef stays.

```bash
nereus nereid delete reference-release
```

``` { .text .output title="output" }
✓ core/nereids/reference-release deleted
```

## Next

- [Require a reef](requires.md): a label that makes one Nereid depend on another reef.
- [Pass the conformance tests](conformance.md).

## Learn more

- [Reef, Nereid and Mandate](../../concepts/model.md).
- [Spec 0003](../../specs/0003-nereid-conformance.md): the labels read at install, and what `Ready` means.
