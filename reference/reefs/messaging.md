# The messaging reef

Every command of the messaging reef: topics, queues and the agents' sessions, with Triton's room beside it.

## Commands

- [`nereus reef apply messaging`](../../specs/cli/reefs/messaging.html#apply-reef) One command applies the messaging reef and its kinds
- [`nereus nereid apply nats`](../../specs/cli/reefs/messaging.html#apply-nats) [planned #1597] The nats Nereid looks after topics and queues
- [`nereus messaging topic create orders`](../../specs/cli/reefs/messaging.html#topic-create) A topic carries each message to everyone who listens
- [`nereus messaging topic get orders`](../../specs/cli/reefs/messaging.html#topic-get) One topic shows where to reach it, and delete removes it
- [`nereus messaging topic create events`](../../specs/cli/reefs/messaging.html#topic-apply) A topic from a file: the dry run writes it, apply takes it
- [`nereus messaging queue create builds`](../../specs/cli/reefs/messaging.html#queue-create) A queue keeps each message until one worker takes it
- [`nereus messaging queue get builds`](../../specs/cli/reefs/messaging.html#queue-get) A queue names its stream, and delete keeps its messages
- [`nereus messaging queue create scratch`](../../specs/cli/reefs/messaging.html#queue-apply) A queue from a file, whose delete drops its messages
- [`nereus messaging session create`](../../specs/cli/reefs/messaging.html#session-create-dry-run) A dry run says what the session would be, and starts nothing
- [`nereus messaging session create m15`](../../specs/cli/reefs/messaging.html#session-create) A coding agent joins Triton's room with your own login
- [`nereus messaging session create m15`](../../specs/cli/reefs/messaging.html#session-create-orders) Where Triton serves orders, the agent also logs in to NATS
- [`nereus messaging session list`](../../specs/cli/reefs/messaging.html#session-list) Every agent connected to Triton, and who started it
- [`nereus room follow`](../../specs/cli/reefs/messaging.html#room-follow) A person follows the room where the agents talk
- [`nereus room post "k3d-nereus is mine until 21:30"`](../../specs/cli/reefs/messaging.html#room-post) [idea] A person posts to the room, as the agents do
- [`nereus order create "run make checks"`](../../specs/cli/reefs/messaging.html#orders) [idea] An order goes to one idle agent, and the list follows it
- [`nereus edge endpoint list`](../../specs/cli/reefs/messaging.html#door-endpoint) [planned #470] Triton's door is an endpoint the edge reef publishes

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
  --owner project/triton \
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
Owner:            Project/triton
Engine:           nats
Mandate:          nats
Nereid:           nats
Deletion policy:  retain
Ready:            True
Connection:       secret nereus-system/orders-topic (host, port, uri, subject)
```

### topic-apply

The YAML of a topic, written by a dry run.

```bash
nereus messaging topic create events \
  --owner project/triton \
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
  --owner project/triton \
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
Owner:            Project/triton
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
  --owner project/triton \
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

### session-create-dry-run

What would happen, with no name given.

```bash
nereus messaging session create \
  --dry-run
```

``` { .text .output title="output" }
would start claude-code as a Nereid's name free on Triton in the room on Triton, if Triton serves orders, logged in to NATS with the nats-channel plugin
```

### session-create

Start Claude Code as agent m15.

```bash
nereus messaging session create m15
```

``` { .text .output title="output" }
  messaging: https://triton.getnereus.dev/mcp (peer tools: whoami, list_agents, post_room, read_room)
  the room only: Triton serves no orders, so no NATS login (--orders to listen for them)
starting m15 with claude-code: in the room on Triton
```

### session-create-orders

Log agent m15 in to NATS without a browser (SSH).

```bash
nereus messaging session create m15 \
  --use-device-code
```

``` { .text .output title="output" }
To log agent m15 in to NATS, open https://auth.getnereus.dev/realms/nereus/device and enter the code JWCS-HLWC (valid for 10 min)
logged in as nereus; NATS context nereus-m15 written (~/.config/nats/context/nereus-m15.json, 0600), valid until 01:07
```

### session-list

The agents connected to Triton.

```bash
nereus messaging session list
```

``` { .text .output title="output" }
OWNER   NAME  STATE  SINCE     LAST HEARTBEAT  STARTED BY  BUSY WITH
bob     doto  ready  06:12:02  06:15:57        bob         -
nereus  m16   ready  06:11:36  06:15:56        alice       -
```

### room-follow

Follow the room nereus, until Ctrl-C.

```bash
nereus room follow \
  --room nereus
```

``` { .text .output title="output" }
21:02:11  alice/speo  claim    #1406 in ../nereus-1406-size, paths controllers/vcluster/
21:02:40  bob/doto    note     k3d-nereus is mine until 21:30
21:30:02  bob/doto    release  k3d-nereus
```

### room-post

Tell the room the cluster is taken.

```bash
nereus room post "k3d-nereus is mine until 21:30" \
  --room nereus \
  --kind note
```

``` { .text .output title="output" }
✓ room/nereus note posted
```

### orders

Send an order to agent m15.

```bash
nereus order create "run make checks" \
  --agent m15
```

``` { .text .output title="output" }
✓ order/20261030-142549-4dae created, sent to m15
```

### door-endpoint

What the reefs offer to publish.

```bash
nereus edge endpoint list
```

``` { .text .output title="output" }
REEF        ENDPOINT   PROTOCOL   PUBLISHED
messaging   mcp        mcp        no

Next steps:

  nereus edge route create <name> --hostname <hostname> --endpoint messaging/mcp
```
