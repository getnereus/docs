# Send messages

Give a project a topic and a queue on NATS, each with a Secret that says where to reach it, made by the `nats` Nereid. The Mandate picks the Nereid, so the code asks for an engine, never for a server.

A topic carries each message to everyone who listens, on the subject `topics.<name>`. A queue keeps each message until one worker takes it, in the JetStream stream `queue-<name>` on `queues.<name>`. To put a coding agent in the team's room, see [Join the team's room](team-room.md).

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md), with the [tenancy tree](../../concepts/tenancy-and-access.md) its profile seeds: the owner of each topic and queue, here the project `triton`, must exist in it.

## Steps

### 1. Apply the messaging reef

[`nereus reef apply`](../../specs/cli/reefs/messaging.html#apply-reef) brings the two kinds.

```bash
nereus reef apply messaging
```

``` { .text .output title="output" }
✓ core/reefs/messaging 0.1.0 created (messaging.getnereus.dev/v1alpha1: queues, topics)

Next steps:

  nereus messaging --help
  nereus nereid apply <nereid> --reef messaging
```

### 2. Apply the nats Nereid and its Mandate

[`nereus nereid apply nats`](../../specs/cli/reefs/messaging.html#apply-nats) runs NATS next to the Nereid in its Pod, with JetStream on the claim `nats-data`.

```bash
nereus nereid apply nats \
  --reef messaging
```

``` { .text .output title="output" }
✓ core/nereids/nats created, Ready, pinned to sha256:<digest>: see 'nereus messaging --help'

Next steps:

  nereus mandate create messaging-nats --reef messaging --nereid nats --match engine=nats --param jetstream=true
```

The Mandate takes every request of engine `nats`; `jetstream=true` is what queues need. A second Mandate with the same match is refused.

```bash
nereus mandate create messaging-nats \
  --reef messaging \
  --nereid nats \
  --match engine=nats \
  --param jetstream=true
```

``` { .text .output title="output" }
✓ core/mandates/messaging-nats created (reef: messaging, nereid: nats, match: engine=nats)
```

### 3. Create a topic

[`nereus messaging topic create`](../../specs/cli/reefs/messaging.html#topic-create) names the owner and the engine. An owner missing from the tree is refused before anything is written.

```bash
nereus messaging topic create orders \
  --owner project/triton \
  --engine nats
```

``` { .text .output title="output" }
✓ messaging/topics/orders created (mandate: messaging-nats, nereid: nats)

Next steps:

  nereus messaging topic get orders
```

### 4. Create a queue

[`nereus messaging queue create`](../../specs/cli/reefs/messaging.html#queue-create) takes the same flags.

```bash
nereus messaging queue create builds \
  --owner project/triton \
  --engine nats
```

``` { .text .output title="output" }
✓ messaging/queues/builds created (mandate: messaging-nats, nereid: nats)

Next steps:

  nereus messaging queue get builds
```

### 5. Create one from a file

A dry run writes the YAML that [`nereus messaging queue apply`](../../specs/cli/reefs/messaging.html#queue-apply) takes. `--deletion-policy delete` drops the stream and its messages with the queue; `retain`, the default, keeps them.

```bash
nereus messaging queue create scratch \
  --owner project/triton \
  --engine nats \
  --deletion-policy delete \
  --dry-run \
  --output yaml > scratch.yaml
```

```bash
nereus messaging queue apply \
  --from-file scratch.yaml
```

``` { .text .output title="output" }
✓ messaging/queues/scratch created

Next steps:

  nereus messaging queue list
```

A topic works the same way, with `nereus messaging topic apply`.

## Check it worked

`nereus messaging topic list` and `nereus messaging queue list` show each one `Ready`, with the Mandate and the Nereid that took it. [`nereus messaging queue get`](../../specs/cli/reefs/messaging.html#queue-get) names the Secret that says where to reach it: `builds-queue` in `nereus-system`, with the keys `host`, `port`, `uri`, `subject` and `stream`.

## Clean up

[`nereus messaging queue delete`](../../specs/cli/reefs/messaging.html#queue-get) follows the queue's deletion policy.

```bash
nereus messaging queue delete builds
```

``` { .text .output title="output" }
✓ messaging/queues/builds deleted (deletionPolicy: retain, its messages are kept)

Next steps:

  nereus messaging queue list
```

```bash
nereus messaging queue delete scratch
```

``` { .text .output title="output" }
✓ messaging/queues/scratch deleted (deletionPolicy: delete)

Next steps:

  nereus messaging queue list
```

```bash
nereus messaging topic delete orders
```

``` { .text .output title="output" }
✓ messaging/topics/orders deleted (deletionPolicy: retain, its messages are kept)

Next steps:

  nereus messaging topic list
```

## Next

- [Join the team's room](team-room.md): a coding agent's session on the same NATS.

## Learn more

- [The messaging reef](../../reference/reefs/messaging.md): topics, queues and sessions, every command.
- [Reef, Nereid and Mandate](../../concepts/model.md): why the Mandate, not the code, picks NATS.
