# The messaging reef

Every command of the messaging reef: topics and queues, the engine under the rooms reef.

## Commands

- [`nereus reef apply messaging`](../../specs/cli/reefs/messaging.html#apply-reef) One command applies the messaging reef and its kinds
- [`nereus nereid apply nats`](../../specs/cli/reefs/messaging.html#apply-nats) [planned #1597] The nats Nereid looks after topics and queues
- [`nereus messaging topic create orders`](../../specs/cli/reefs/messaging.html#topic-create) A topic carries each message to everyone who listens
- [`nereus messaging topic get orders`](../../specs/cli/reefs/messaging.html#topic-get) One topic shows where to reach it, and delete removes it
- [`nereus messaging topic create events`](../../specs/cli/reefs/messaging.html#topic-apply) A topic from a file: the dry run writes it, apply takes it
- [`nereus messaging queue create builds`](../../specs/cli/reefs/messaging.html#queue-create) A queue keeps each message until one worker takes it
- [`nereus messaging queue get builds`](../../specs/cli/reefs/messaging.html#queue-get) A queue names its stream, and delete keeps its messages
- [`nereus messaging queue create scratch`](../../specs/cli/reefs/messaging.html#queue-apply) A queue from a file, whose delete drops its messages

## Examples

### apply-reef

Apply the messaging reef.

```bash
nereus reef apply messaging
```

``` { .text .output title="output" }
✓ core/reefs/messaging 0.1.0 created (messaging.getnereus.dev/v1alpha1: queues, topics)

Next steps:

  nereus messaging --help
  nereus nereid apply <nereid> --reef messaging
```

### apply-nats

Apply the nats Nereid to the messaging reef.

```bash
nereus nereid apply nats \
  --reef messaging
```

``` { .text .output title="output" }
✓ core/nereids/nats created, Ready, pinned to sha256:<digest>: see 'nereus messaging --help'

Next steps:

  nereus mandate create messaging-nats --reef messaging --nereid nats --match engine=nats --param jetstream=true
```

### topic-create

A topic for the orders, owned by a project.

```bash
nereus messaging topic create orders \
  --project triton \
  --engine nats
```

``` { .text .output title="output" }
✓ messaging/topics/orders created (mandate: messaging-nats, nereid: nats)

Next steps:

  nereus messaging topic get orders
```

### topic-get

Every detail of one topic.

```bash
nereus messaging topic get orders
```

``` { .text .output title="output" }
Name:             orders
Organization:     getnereus
Project:          nereus/triton
Engine:           nats
Mandate:          nats
Nereid:           nats
Deletion policy:  retain
Max age:          unlimited
Max bytes:        unlimited
Access:           shared
Ready:            True
Connection:       secret nereus-system/orders-topic (host, port, uri, subject)
```

### topic-apply

The YAML of a topic, written by a dry run.

```bash
nereus messaging topic create events \
  --project triton \
  --engine nats \
  --dry-run \
  --output yaml
```

``` { .text .output title="output" }
apiVersion: messaging.getnereus.dev/v1alpha1
kind: Topic
metadata:
  name: events
spec:
  owner:
    kind: Project
    name: triton
  engine: nats
```

### queue-create

A queue for the builds to run.

```bash
nereus messaging queue create builds \
  --project triton \
  --engine nats
```

``` { .text .output title="output" }
✓ messaging/queues/builds created (mandate: messaging-nats, nereid: nats)

Next steps:

  nereus messaging queue get builds
```

### queue-get

Every detail of one queue.

```bash
nereus messaging queue get builds
```

``` { .text .output title="output" }
Name:             builds
Organization:     getnereus
Project:          nereus/triton
Engine:           nats
Mandate:          nats
Nereid:           nats
Deletion policy:  retain
Ready:            True
Connection:       secret nereus-system/builds-queue (host, port, uri, subject, stream)
```

### queue-apply

The YAML of a queue, written by a dry run.

```bash
nereus messaging queue create scratch \
  --project triton \
  --engine nats \
  --deletion-policy delete \
  --dry-run \
  --output yaml
```

``` { .text .output title="output" }
apiVersion: messaging.getnereus.dev/v1alpha1
kind: Queue
metadata:
  name: scratch
spec:
  owner:
    kind: Project
    name: triton
  engine: nats
  deletionPolicy: delete
```
