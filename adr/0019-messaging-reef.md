# 0019. The messaging reef: threads, orders and claims as records, a bus behind a Nereid

!!! note "In short"
    The conversation joins the `messaging` reef as records (`Thread`, `Order`, `Claim`, `Message`), with a bus behind a Nereid. Status: Proposed (2026-10-26).

**Status:** Proposed (2026-10-26)

## Context

Work orders reach the local agents through a stand-in: the voice session writes a Markdown file to a Google Drive folder (the beach, [Beach](../agent/beach.md)), and `scripts/beach/watch` on each machine polls it and starts Claude Code on the orders assigned to its agent. A security review of the watcher found two gaps in its only gate, "the file's Drive owner is the trusted owner":

1. **Owner is not author.** Drive keeps the owner when an editor changes a file, so anyone with edit access to the folder can rewrite an order that still passes the check.
2. **Checked is not what runs.** The watcher checks the owner, then the run reads the order from Drive again; the text may have changed in between (a time-of-check to time-of-use gap).

The owner accepted that risk for now and made the replacement the priority: a `messaging` reef, where an order is a message of the platform rather than a file. The owner also asked for threads: with remote agents, every subject arrives in one conversation, and the person must work out which subject each message belongs to.

Two earlier ideas touch the same ground: a contract for Controllers to exchange events with the platform (#254), and a `communication` reef for queues and topics, RabbitMQ first (#257, #374, both closed since).

**Since this was first written (2026-10-26):**

- **Triton** (`controllers/triton`) carries orders today: its door, an MCP server behind OAuth through the keycloak Nereid (#495), takes an order from the voice session and hands it to an agent's open Claude Code session over NATS; the orders and their status live on JetStream and survive a restart (#506); every agent joins NATS with its own login through NATS's auth callout (#497). The beach is its backup.
- **ADR 0017** (resource reefs) puts the machine side in this same reef: `messaging` holds `Topic` and `Queue`, fulfilled by a `nats` Nereid through the Mandate `messaging-nats`, and Triton becomes a Nereid of it (#576, #483).
- **ADR 0018** (the Nereus API is the one door) makes the Nereus API, not the Kubernetes API, what clients talk to.

**Origin:** the owner, in the voice session of 2026-10-26, through order 20261026-1236 (messaging reef design) and its addendum 01 (threads); raw data in Drive `#pontos/beach/` and `beach/replies/20261026-1236-messaging-reef-design/design.md`, which holds the survey of buses in full.

## Decision

**The conversation joins the `messaging` reef**, API group `messaging.getnereus.dev/v1alpha1` (ADR 0009, ADR 0010), next to ADR 0017's `Topic` and `Queue`: its records are kinds of the same reef; a bus only carries notifications of those records, behind a Nereid (ADR 0002).

**The records** (kind names proposed, to decide with the owner):

| Kind | What it is | Who creates it |
|---|---|---|
| `Thread` | one subject: a client-chosen id, a title, an optional issue; `status` sums it up (state, counts, last message) | a person |
| `Order` | a work order to one agent, in one thread; immutable; an addendum is an `Order` with `spec.amends` | a person with the publisher role |
| `Claim` | an agent takes an order; named after the order, so a second claim fails with `AlreadyExists`; records the digest it ran | an agent's runner |
| `Message` | everything else in a thread: ack, question, answer, reply, done, failed, cancelled; `inReplyTo` names the record it answers | a person or an agent |

Separate kinds, rather than one message with a type field, because RBAC authorises by resource: only a publisher may create an `Order`, and an agent may create `Claim` and `Message` only.

**A thread groups one or more orders.** The common case is one order per thread, as an order and its replies folder are today; a follow-up order may join the same thread. Thread ids are chosen by the client, so a conversation can open several planned threads at once, and new ones on the way. Every record and every event carries its thread.

**Deterministic first:** routing (`spec.to`), the claim (create-if-absent), the digest and the end of a run are code; AI only runs the order's text.

**Closing the two gaps:**

- **An authenticated identity publishes.** People publish through `nereus` or the Nereus API's `/mcp` with an OIDC token of the authentication reef (ADR 0006), through the Nereus API (ADR 0018), which acts as the person, so RBAC and the audit log see the person. A ValidatingAdmissionPolicy refuses a record whose `spec.author` is not the caller. Each agent has an identity of its own, as it has on NATS since #497.
- **The text checked is the text run.** `Order.spec` is immutable (a CEL rule `self == oldSelf`); the Nereid writes `status.digest`; the runner reads the order once, checks the digest, records it in the `Claim`, and passes that text to the run on stdin.
- **Each run is isolated:** a rootless container (podman first, a Kubernetes Job later) with the worktree only, no sudo, a one-hour GitHub App token scoped to the repository, egress limited to GitHub, the model's API and Nereus; pushing to `main` and merging are refused by a ruleset, not by the agent's restraint.

**The bus is a Nereid, and not part of the first slice.** A Kubernetes watch already delivers each change to a subscriber; the first Nereid only keeps the records and writes `status`. When #254's events or the number of subscribers need one, the bus is NATS with JetStream, the one Triton runs on and ADR 0017's `nats` Nereid serves (#576): it publishes one CloudEvent per record (`type` `dev.getnereus.messaging.<kind>.created.v1`, extension `thread`), with a reference to the record and never the order's body.

**The terminal is the first client** (ADR 0013 verbs), the voice session the second, through the `/mcp` tools of the Nereus API (ADR 0029) with the same nouns:

```bash
nereus thread create messaging-reef-design --title "Design the messaging reef"
nereus order create 20261026-1236-messaging-reef-design \
  --thread messaging-reef-design \
  --to ln28 \
  --from-file order.md
nereus thread list
nereus thread get messaging-reef-design
nereus message create \
  --thread messaging-reef-design \
  --in-reply-to messaging-reef-design-0004 \
  "fix first"
nereus order list --to ln28 --watch
```

```text
$ nereus thread list
THREAD                  TITLE                       STATE      AGENT  LAST             AGE
messaging-reef-design   Design the messaging reef   working    ln28   claim, 13:09     34m
merge-readme-pr-437     Merge the README PR         needs-you  m15    question, 13:20  25m
```

**Migration:** Triton's door becomes a client of the `Order` kind: an order sent through it is a record, its JetStream status follows the `Claim` and the `Message`s; runs move into containers; then the Drive source is turned off and the beach retires.

## Prior art

- **NATS and JetStream** ([docs.nats.io](https://docs.nats.io/)): subject-based routing with per-subject permissions, durable consumers, and a key-value `create` that fails when the key exists ([key-value store](https://docs.nats.io/using-nats/developer/develop_jetstream/kv)); the recommended bus and the shape of the claim.
- **RabbitMQ** ([OAuth 2.0 backend](https://www.rabbitmq.com/docs/oauth2), [Kubernetes operators](https://www.rabbitmq.com/kubernetes/operator/operator-overview)): the alternative, the working choice of `communication` until #257 closed.
- **Knative Eventing, Argo Events and Dapr pub/sub** ([triggers](https://knative.dev/docs/eventing/triggers/), [EventBus](https://argoproj.github.io/argo-events/concepts/eventbus/), [pub/sub](https://docs.dapr.io/developing-applications/building-blocks/pubsub/pubsub-overview/)): evaluated and not chosen as the reef's contract; Argo Events stays a candidate for "an order starts a Job".
- **CloudEvents** ([spec](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md), [extensions](https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/README.md)): the envelope of every event; the spec has no correlation attribute, so the thread travels as an extension.
- **Threads in chat systems:** Matrix's `m.thread` relation and its root summary ([spec](https://spec.matrix.org/latest/client-server-api/#threading)), Zulip's topics ([topics](https://zulip.com/help/introduction-to-topics)), Slack's `thread_ts` ([messaging](https://docs.slack.dev/messaging/)), and Google Chat's client-chosen `thread_key` ([spaces.messages.create](https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces.messages/create)), the model for planned threads.
- **Kubernetes:** immutability with CEL ([blog](https://kubernetes.io/blog/2022/09/29/enforce-immutability-using-cel/)), ValidatingAdmissionPolicy ([docs](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)) and user impersonation ([docs](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#user-impersonation)).
- **Claude Code development containers** ([docs](https://docs.anthropic.com/en/docs/claude-code/devcontainer)): unattended runs inside an isolated container with a firewall, and the warning that the container does not protect what it holds.

## Consequences

- An order's author is a platform identity, audited by the API server, and the text a run receives is the text that was checked.
- The voice session publishes with no secret of its own, but only while the instance behind `/mcp` is reachable: the reef depends on an always-on instance.
- The beach watcher stand-in of `docs/features.md` gets its replacement; it retires when the Drive source is turned off.
- The first slice needs no broker; the bus arrives with #254 and is swappable through a Mandate.
- Agents need identities and RBAC roles of their own, and the repository needs a ruleset that makes merging without the owner impossible.

## Open questions

- Whether Triton's door writes `Order` records itself, or the records replace the door's JetStream orders.
- Whether the conversation kinds belong in `messaging` with ADR 0017's `Topic` and `Queue`, or in a reef of their own.
- Where the always-on instance runs.
- The kind names: `Thread`, `Order`, `Claim`, `Message`, or `Conversation`, `WorkOrder`, a core `Lease`.
- Whether a thread closes only by a person's word, and whether a claim expires.
- How an agent's NATS login (#497) maps to its identity on the Nereus API.
- Whether an agent's question blocks its run or ends it.

*Reviewed 2026-10-31 against Triton (#495, #497, #506), ADR 0017 and ADR 0018, at the owner's request, before its first merge; renumbered from the draft's 0015, taken by ADR 0015 (tenancy).*
