# The delivery Reef

Every command that takes a Workload to an Environment, and says what runs.

## Commands

- [`nereus reef apply delivery`](../../specs/cli/reefs/delivery.html#reef-apply) The Reef, then the Nereid that delivers to Kubernetes
- [`nereus workload deploy hello@dev`](../../specs/cli/reefs/delivery.html#workload-deploy) One command takes a Workload to an Environment
- [`nereus workload deploy hello`](../../specs/cli/reefs/delivery.html#deploy-refuses) deploy never guesses the target
- [`nereus workload deploy hello@dev`](../../specs/cli/reefs/delivery.html#deploy-build) deploy runs what a Build pushed, by its digest
- [`nereus workload deploy hello-dev`](../../specs/cli/reefs/delivery.html#deploy-update) Every deploy is a new request, even with the same tag
- [`nereus workload deploy hello@dev`](../../specs/cli/reefs/delivery.html#deploy-dry-run) --dry-run shows the Delivery, with the tag as typed
- [`nereus workload deploy hello@dev`](../../specs/cli/reefs/delivery.html#deploy-wait) --wait brings the Nereid's reason to the terminal
- [`nereus workload list`](../../specs/cli/reefs/delivery.html#workload-list) workload list says what the catalog has
- [`nereus delivery list`](../../specs/cli/reefs/delivery.html#delivery-list) delivery list says what was deployed
- [`nereus delivery get hello-dev`](../../specs/cli/reefs/delivery.html#delivery-get) delivery get says what runs and where
- [`nereus workload logs hello-dev`](../../specs/cli/reefs/delivery.html#workload-logs) workload logs reads a Delivery by its name or its pair
- [`nereus workload deploy hello@dev`](../../specs/cli/reefs/delivery.html#delivery-apply) A Delivery in a file resolves once
- [`nereus delivery delete hello-dev`](../../specs/cli/reefs/delivery.html#delivery-delete) Deleting a Delivery takes the app out of the Environment
- [`nereus template render python-service`](../../specs/cli/reefs/delivery.html#template-render) [planned #851] A template writes files, and the catalog registers them

## Examples

### reef-apply

The delivery Reef's contract.

```bash
nereus reef apply delivery \
  --from-file ./reefs/delivery/
```

``` { .text .output title="output" }
✓ core/reefs/delivery created (delivery.getnereus.dev/v1alpha1)
```

### workload-deploy

A Workload of the catalog, in the dev Environment.

```bash
nereus workload deploy hello@dev \
  --image registry.example.com/hello:a1b2c3d
```

``` { .text .output title="output" }
✓ delivery/deliveries/hello-dev created

Next steps:

  nereus delivery get hello-dev
```

### deploy-refuses

A bare name could change target in silence when a second Environment appears.

```bash
nereus workload deploy hello \
  --image registry.example.com/hello:a1b2c3d
```

``` { .text .output title="output" }
✗ deploy needs the target. To deploy hello, run:
  # to the dev Environment
  nereus workload deploy hello@dev --image registry.example.com/hello:a1b2c3d
```

### deploy-build

The image of a Build that succeeded, never a tag that may move.

```bash
nereus workload deploy hello@dev \
  --build hello-a1b2c3d
```

``` { .text .output title="output" }
✓ delivery/deliveries/hello-dev created

Next steps:

  nereus delivery get hello-dev
```

### deploy-update

The same tag, pushed again: the unique name works too.

```bash
nereus workload deploy hello-dev \
  --image registry.example.com/hello:a1b2c3d
```

``` { .text .output title="output" }
✓ delivery/deliveries/hello-dev configured

Next steps:

  nereus delivery get hello-dev
```

### deploy-dry-run

Changes nothing; the digest comes from the Nereid, after the deploy.

```bash
nereus workload deploy hello@dev \
  --image registry.example.com/hello:a1b2c3d \
  --dry-run
```

``` { .text .output title="output" }
delivery/deliveries/hello-dev would be created
  workload: hello
  environment: dev
  image: registry.example.com/hello:a1b2c3d
```

### deploy-wait

A tag that does not exist fails after the Delivery is written.

```bash
nereus workload deploy hello@dev \
  --image registry.example.com/hello:does-not-exist \
  --wait
```

``` { .text .output title="output" }
✓ delivery/deliveries/hello-dev configured
✗ delivery/deliveries/hello-dev not ready: The registry does not have the tag does-not-exist of the repository registry.example.com/hello. To fix it, run:
  # deploy a tag that exists
  nereus workload deploy hello@dev --image registry.example.com/hello:<tag>
```

### workload-list

One row per Workload; DELIVERIES counts them, 0 means not deployed.

```bash
nereus workload list
```

``` { .text .output title="output" }
WORKLOAD  ORGANIZATION  PROJECT  TYPE     AUDIENCE  DELIVERIES  STATUS
billing   example       shop     service  programs  0           Ready
hello     example       hello    service  people    2           Ready

Next steps:

  nereus delivery list
```

### delivery-list

One row per Workload and Environment pair.

```bash
nereus delivery list
```

``` { .text .output title="output" }
NAME         WORKLOAD  ENVIRONMENT  DIGEST         READY
hello-dev    hello     dev          sha256:9f2c1e  True
hello-stage  hello     stage        sha256:77ab40  True
```

### delivery-get

The digest running, the namespace, and the previous digest.

```bash
nereus delivery get hello-dev
```

``` { .text .output title="output" }
NAME       WORKLOAD  ENVIRONMENT  DIGEST         NAMESPACE  READY
hello-dev  hello     dev          sha256:9f2c1e  hello-dev  True

Previous digest: sha256:77ab40

Next steps:

  nereus workload logs hello-dev
```

### workload-logs

Follow what the app prints.

```bash
nereus workload logs hello-dev \
  --follow
```

``` { .text .output title="output" }
[::ffff:127.0.0.1]:53792: response:200
```

### delivery-apply

Write it as a file, then apply the file.

```bash
nereus workload deploy hello@dev \
  --image registry.example.com/hello:a1b2c3d \
  --dry-run \
  --output yaml
```

``` { .text .output title="output" }
apiVersion: delivery.getnereus.dev/v1alpha1
kind: Delivery
metadata:
  name: hello-dev
```

### delivery-delete

The Workload stays in the catalog.

```bash
nereus delivery delete hello-dev
```

``` { .text .output title="output" }
✓ delivery/deliveries/hello-dev deleted

Next steps:

  nereus workload list
```

### template-render

The files of a new Workload, with Copier.

```bash
nereus template render python-service \
  --path ./hello \
  --param name=hello
```

``` { .text .output title="output" }
✓ catalog/templates/python-service rendered at ./hello

Next steps:

  nereus catalog apply --from-file ./hello/catalog/
```
