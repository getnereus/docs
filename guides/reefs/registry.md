# Run a registry

Run a [zot](https://zotregistry.dev) registry of your own in the cluster, publish an image to it and run that image: TLS only, nothing anonymous, images kept on its own volume.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`: it brings the registry reef with the Nereid `zot`, the release reef that installs zot, and the secrets reef that keeps each registry's read credential.
- `nereus login` done: publishing pushes through the Nereus API, for a person in `nereus-admins`.
- The namespace `builds`, which `nereus nereid apply buildkit --reef build` makes: each repository's push identity lives there.
- An image built locally with a tag, such as `docker build --tag hello:v1 .`.
- A k3d cluster: on AKS the registry reef is [planned], since the nodes pull only from registries whose certificate they trust, and they do not trust the CA of a registry in the cluster ([Prepare a cluster for Nereus](../operate/cluster.md)).

## Steps

### 1. Create a registry

[`nereus registry create`](../../specs/cli/reefs/registry.html#registry-create) makes a namespace `registry-<name>` with zot and a 10 GiB volume. The first registry also makes the vault `registries`. `--purge-unused` is optional: it deletes each image no Delivery runs once older than the duration, keeping the newest of each repository.

```bash
nereus registry create main \
  --purge-unused 168h
```

``` { .text .output title="output" }
secrets/vaults/registries created
registry/registries/main created (mandate: zot, nereid: zot; purge: images no Delivery runs, after 168h)
```

### 2. Publish an image

[`nereus registry repository publish`](../../specs/cli/reefs/registry.html#repository-publish) creates the repository with a push identity of its own and pushes the local image through the Nereus API with your login; your docker configuration stays untouched. A tag is published once: the same tag again is refused.

```bash
nereus registry repository publish hello \
  --registry main \
  --image hello:v1
```

``` { .text .output title="output" }
registry/registries/main/repositories/hello created
registry/registries/main/repositories/hello/tags/v1 published (sha256:97683bd68ee3e86c6560172b9f6e0b371a6bbcebf06041dbe7284355a7703797)

Next steps:

  nereus workload deploy hello@<environment> --image localhost:30763/hello:v1
```

### 3. Run it

[`nereus workload deploy`](../../specs/cli/reefs/delivery.html#workload-deploy) runs the image in an Environment, here `dev` from [Follow the golden path](golden-path.md). Name the address the publish printed; the Pod runs the digest found behind the tag. A registry with an owner serves only a Workload and an Environment of that owner or under it in the [tenancy tree](../../concepts/tenancy-and-access.md).

```bash
nereus workload deploy hello@dev \
  --image localhost:30763/hello:v1 \
  --wait
```

``` { .text .output title="output" }
✓ delivery/deliveries/hello-dev configured
✓ delivery/deliveries/hello-dev ready (sha256:de1338)

Next steps:

  nereus workload logs hello-dev
```

## Check it worked

[`nereus registry get`](../../specs/cli/reefs/registry.html#registry-get) shows the registry ready, its pull address for the nodes and the credential that reads it.

```bash
nereus registry get main
```

``` { .text .output title="output" }
NAME  NEREID  PURGE  PULL-ADDRESS     READY
main  zot     168h   localhost:30763  True

credential: secret registries/main-pull (vault registries)

localhost:30763 is a NodePort, for an image reference on this cluster's nodes. Reading it takes the credential above.
```

## Clean up

!!! warning "Deleted for good"
    The registry's namespace and volume go with it, and every image on the volume.

A repository that a Delivery runs is refused, and so is a registry that still has repositories: delete the Deliveries first.

```bash
nereus registry repository delete hello
```

``` { .text .output title="output" }
✗ registry/repositories/hello is still in use by delivery/deliveries/hello-dev. To delete it, run:
  # first, the Deliveries that run its images
  nereus delivery delete hello-dev
  nereus registry repository delete hello
```

```bash
nereus registry delete main
```

``` { .text .output title="output" }
registry/registries/main deleted

Next steps:

  nereus registry list
```

## Next

- [Follow the golden path](golden-path.md): an Environment of your own, and a Workload deployed into it.
- Run what a Build pushed: [`nereus workload deploy --build`](../../specs/cli/reefs/delivery.html#deploy-build) takes the Build's digest instead of a tag.

## Learn more

- [The registry reef](../../reference/reefs/registry.md): registries, repositories, purge and every command.
- [Tenancy and access](../../concepts/tenancy-and-access.md): who may read a registry with an owner.
