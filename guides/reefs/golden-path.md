# Follow the golden path

Run your own image in an Environment of its own, a vcluster, from `docker build` to a Pod that answers, through a ready-made chart and with no product code.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`, and `nereus login` done: it brings the environment Reef with the Nereid `vcluster`, the catalog, the delivery Reef with the Nereid `kubernetes`, and the release Reef with `flux`.
- The workload type `service` from the repository's catalog, as in [Say what Nereus has](catalog.md).
- Your image pushed to the registry that `nereus status` names, such as `docker build --tag localhost:5111/hello:0.1.0 test/golden-path`, then `docker push localhost:5111/hello:0.1.0`. The same reference pushes and pulls, from your machine and from the nodes.

## Steps

### 1. Get an Environment

[`nereus environment create`](../../specs/cli/reefs/environment.html#create) makes a vcluster for an owner, deleted when it expires. It is `small` unless its Mandate says otherwise: 20 Pods, 512Mi per container. Its Pods reach one another and the Internet, never the platform's own Services.

```bash
nereus environment create dev \
  --owner project/nereus \
  --expires 2h
```

``` { .text .output title="output" }
✓ environment/environments/dev created (mandate: vcluster, nereid: vcluster)

Next steps:

  nereus environment get dev --watch
  nereus environment kubeconfig dev
```

### 2. Say what runs

A Workload is the catalog's entry: who owns it, its type and who talks to it. [`nereus workload create`](../../specs/cli/reefs/catalog.html#workload-create) is short for `nereus catalog workload create`.

```bash
nereus workload create hello \
  --owner project/nereids \
  --type service \
  --audience programs
```

``` { .text .output title="output" }
✓ catalog/workloads/hello created (owner: Project/nereids, type: service)

Next steps:

  nereus catalog workload list
```

### 3. Deploy it

[`nereus workload deploy`](../../specs/cli/reefs/delivery.html#workload-deploy) takes `hello@dev`, the Workload and the Environment: a bare `hello` is refused, since a deploy always says where it goes. The Nereid `kubernetes` resolves the tag to a digest, reads the port the image exposes, and releases a ready-made chart in the vcluster.

```bash
nereus workload deploy hello@dev \
  --image localhost:5111/hello:0.1.0
```

``` { .text .output title="output" }
✓ delivery/deliveries/hello-dev created

Next steps:

  nereus delivery get hello-dev
```

A tag moves only with a deploy: push the same tag with other content and deploy again for a new digest, the previous one kept. `--wait` waits on the deploy and prints the Nereid's reason when it cannot deliver.

## Check it worked

[`nereus delivery get --watch`](../../specs/cli/reefs/delivery.html#delivery-get) follows the Delivery until its Pod is ready.

```bash
nereus delivery get hello-dev \
  --watch
```

``` { .text .output title="output" }
NAME       WORKLOAD  ENVIRONMENT  DIGEST  NAMESPACE  READY
hello-dev  hello     dev          -       -          Unknown
hello-dev  hello     dev          sha256:fdeec3  hello-dev  False
hello-dev  hello     dev          sha256:fdeec3  hello-dev  True

Next steps:

  nereus workload logs hello-dev
```

[`nereus workload logs`](../../specs/cli/reefs/delivery.html#workload-logs) reads the Pods' output through the Nereus API, with no kubeconfig and no port-forward of yours; `--follow` stays until Ctrl+C.

```bash
nereus workload logs hello-dev
```

``` { .text .output title="output" }
[::ffff:127.0.0.1]:53792: response:200
```

## Clean up

!!! warning "Deleted for good"
    Deleting the Environment deletes its vcluster and everything inside it.

Delete the Delivery first: an Environment that a Delivery still targets is refused. [`nereus delivery delete`](../../specs/cli/reefs/delivery.html#delivery-delete) removes its Release, so Flux uninstalls the chart.

```bash
nereus delivery delete hello-dev \
  --timeout 300
```

``` { .text .output title="output" }
2026-11-04T17:26:05Z  … release  Deleting release/releases/hello-dev: Flux uninstalls the chart.
2026-11-04T17:26:06Z  · target   Deleting release/targets/hello-dev.
2026-11-04T17:26:38Z  ✓ release  release/releases/hello-dev deleted.
2026-11-04T17:26:37Z  … target   Deleting release/targets/hello-dev.
✓ delivery/deliveries/hello-dev deleted

Next steps:

  nereus workload list
```

```bash
nereus environment delete dev \
  --timeout 600
```

``` { .text .output title="output" }
2026-11-04T17:26:47Z  … release    Deleting release/releases/env-dev: Flux uninstalls the vcluster chart.
2026-11-04T17:26:47Z  · namespace  Deleting the namespace env-vcluster-dev.
2026-11-04T17:27:15Z  ✓ release    release/releases/env-dev deleted.
2026-11-04T17:27:14Z  … namespace  Deleting the namespace env-vcluster-dev.
✓ environment/environments/dev deleted

Next steps:

  nereus environment list
```

## Next

- [Run a registry](registry.md) of your own, and deploy from it.
- [Collect metrics](metrics.md): see how each Nereid is doing.

## Learn more

- [The environment Reef](../../reference/reefs/environment.md): sizes, expiry, kubeconfig and every command.
- [The delivery Reef](../../reference/reefs/delivery.md): Deliveries, the chart they release and why one fails.
