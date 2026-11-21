# The registry reef

Every command that runs an image registry in the cluster and publishes to it.

## Commands

- [`nereus registry create main`](../../specs/cli/reefs/registry.html#registry-create) create asks for a registry, and names who makes it
- [`nereus registry create main`](../../specs/cli/reefs/registry.html#registry-create-exists) create fails when it exists, and lists what to run
- [`nereus registry get main`](../../specs/cli/reefs/registry.html#registry-get) get gives the address an image reference uses
- [`nereus registry list`](../../specs/cli/reefs/registry.html#registry-list) list shows every registry, one line each
- [`nereus registry apply`](../../specs/cli/reefs/registry.html#registry-apply) apply takes files, and waits for the Nereid
- [`nereus registry delete main`](../../specs/cli/reefs/registry.html#registry-delete) delete removes the registry and what its Nereid made
- [`nereus registry create main`](../../specs/cli/reefs/registry.html#registry-purge) A registry purges, when set, the images no Delivery runs
- [`nereus registry repository publish hello`](../../specs/cli/reefs/registry.html#repository-publish) publish pushes an image with the platform's credential

## Examples

### registry-create

A registry, through the reef's default Mandate.

```bash
nereus registry create main
```

``` { .text .output title="output" }
secrets/vaults/registries created
registry/registries/main created (mandate: zot, nereid: zot)

Next steps:

  nereus registry get main
```

### registry-create-exists

The same name twice.

```bash
nereus registry create main
```

``` { .text .output title="output" }
✗ registry/registries/main already exists. To change it, run:
  # write it as a file, then apply the file
  nereus registry create main --dry-run --output yaml > main.yaml
  nereus registry apply --from-file main.yaml
```

### registry-get

Who runs it, the address to pull from, and whether it is ready.

```bash
nereus registry get main
```

``` { .text .output title="output" }
NAME  NEREID  PURGE  PULL-ADDRESS     READY
main  zot     168h   localhost:31874  True

credential: secret registries/main-pull (vault registries)

localhost:31874 is a NodePort, for an image reference on this cluster's nodes. Reading it takes the credential above.

Next steps:

  nereus registry repository publish hello --registry main --image hello:v1
```

### registry-list

Every registry, in alphabetical order.

```bash
nereus registry list
```

``` { .text .output title="output" }
NAME  NEREID  PURGE  PULL-ADDRESS     READY
main  zot     168h   localhost:31874  True

Next steps:

  nereus registry get main
```

### registry-apply

Create or update from a file or a folder, and return at once.

```bash
nereus registry apply \
  --from-file main.yaml \
  --wait false
```

``` { .text .output title="output" }
registry/registries/main created

Next steps:

  nereus registry list
```

### registry-delete

Delete it, and wait until it is gone.

```bash
nereus registry delete main
```

``` { .text .output title="output" }
registry/registries/main deleted

Next steps:

  nereus registry list
```

### registry-purge

A registry that deletes the images no Delivery runs, a week after they were built.

```bash
nereus registry create main \
  --purge-unused 168h
```

``` { .text .output title="output" }
registry/registries/main created (mandate: zot, nereid: zot; purge: images no Delivery runs, after 168h)

Next steps:

  nereus registry get main
```

### repository-publish

The first tag of a repository.

```bash
nereus registry repository publish hello \
  --registry main \
  --image hello:v1
```

``` { .text .output title="output" }
registry/registries/main/repositories/hello created
registry/registries/main/repositories/hello/tags/v1 published (sha256:ab12…)

Next steps:

  kubectl run hello --image localhost:31874/hello:v1
```
