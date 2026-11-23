# 0030. Triton is the rooms reef's Nereid: Room and Peer, on a Topic of the messaging reef, reached only through the Nereus API

!!! note "In short"
    The conversation between agents is a reef of its own, `rooms` (`Room`, `Peer`), looked after by Triton, which requires the `messaging` reef and asks it for a Topic per Room. Triton is an internal service reached only through the Nereus API. Status: Accepted.

**Status:** Accepted

## Context

The goal of Triton and NATS was always one thing: agents on different machines talk to each other as if they were on the same machine, with peers, rooms and Claude Code's cross-session messaging (owner, 2026-11-21; journey #1890 proves it for two people).

The first form of this ADR (2026-11-18) made Triton a second Nereid of the `messaging` reef, beside `nats`, and said that swapping the engine keeps the rooms. Checked on 2026-11-21, on the kept cluster and in the code:

- **Nobody uses the engine's kinds.** The reef has `Topic` and `Queue`, both reconciled by `nats`; the cluster holds none of either.
- **Triton does not use the reef.** It opens its own JetStream streams (`rooms.<room>`, `controllers/triton/rooms.py`) and two KV buckets (`orders`, `agents`) in a NATS account of its own, `AGENTS`.
- **The engine knows its client by name.** A Mandate's `agents=true` makes the `nats` Nereid write the account `AGENTS` and the user `triton`.
- **Triton declares no required reef** in its image, though it needs the NATS the `nats` Nereid runs.
- **Triton reconciles no kind,** so `nereus nereid list` shows it `NotConformant`: a Nereid reconciles every kind of each reef it looks after (#2065), and a `Room` kind in `messaging` would make `nats` not conformant instead.
- **A session's presence is a key in the bucket `agents`,** one revision per change of state; its heartbeats stay in memory.

So the engine's swap kept nothing: the rooms were NATS streams by another name. What an agent on another machine lives through is the same whatever the shape: the CLI's bridge, the Nereus API, Triton, over HTTPS; no machine reaches NATS (#1599).

ADR 0018 makes the Nereus API the one door, and ADR 0029 has the API serve `/mcp` with the tools the reefs declare in their contract.

## Decision

**The measure of the feature** (owner, 2026-11-22): a Nereus user creates a room, and their agent joins it beside a teammate's agent. No extra configuration, no paperwork, no request to an admin, no change to Nereus's settings. Every step below is checked against it, and an end-to-end scene with two ordinary users, neither of them an admin, is its acceptance test.

**The flow, as a person lives it:**

1. Ana creates the room: `nereus rooms create ops`. Without a name, the room takes the repository's name; without `--owner`, her own team (the token's `nereus_owner`). The API checks that she may create it, as it checks a Topic.
2. Triton sees the Room and asks the messaging reef for a Topic `room-ops`; the `nats` Nereid makes the stream and a NATS user of the owner, and gives the credential back in a binding beside the Topic; Triton opens the room with it. The Room is `Ready`, with no agent in it.
3. Ana and Bruno each run `nereus rooms list`, see `ops`, and run `nereus rooms join ops`. The join registers their Peer with `ops` in `spec.rooms`.
4. When a room goes from no agent to one, a new **room session** starts; it ends when the last agent leaves, and its data is kept for analysis afterwards (below).
5. Their agents post and read through the CLI's MCP server, the API and Triton; a hook brings each new message into the session's context.

**Who may create a Room is the authorization reef's answer on the Room's `spec.owner`,** and the profile installs what lets a member of a team create Rooms owned by that team (owner, 2026-11-22): a grant of the authorization reef, either a Role and its Binding seeded with the reef or a rule the openfga Nereid computes, as it does for a Session's staff (#1727); #1491 settles which. It is a setting of the installation, made once, not a request to an admin: without it only `nereus-admins` could create a Room, and the measure of the feature would fail. Policies will refine it later (owner, 2026-11-22), outside the journey #2067, as the hard and soft gates of *Thinking in Platforms*: a hard gate refuses, a soft gate lets an ordinary user ask and waits for an admin's approval, the Room standing in a pending phase (its name to be decided) until then; which part is the authorization engine's (OpenFGA) and which is a policy's is to be worked out.

**`nereus rooms join` is one command, wherever it runs** (owner, 2026-11-22). It takes the room as its argument, the repository's name without one, and `nereus rooms session create` and its `--room` go:

- **Outside Claude Code,** it does what `session create` did: it draws the agent's name, registers the Peer and opens Claude Code with the Nereus MCP server's `rooms` tools on.
- **Inside Claude Code** (the variable `CLAUDECODE`, which Claude Code sets in the processes it starts), it draws the agent's name when the session has none, registers the Peer, and turns the `rooms` tools on in that session, with no restart.

```text
$ nereus rooms join ops          # outside Claude Code
starting doto with claude-code: in the room ops on Triton

$ nereus rooms join              # inside, in the repository nereus
doto joined the room nereus

$ nereus rooms leave ops
doto left the room ops
```

**An agent leaves a room two ways** (owner, 2026-11-22): `nereus rooms leave <room>` takes the room off its Peer at once, inside or outside Claude Code as `join` does, so an agent changes rooms with its session open; and its session ending takes it out of every room (the heartbeats stop, the Peer goes `Away`).

**A room session is a `RoomSession` in the cluster** (owner, 2026-11-22, narrowed 2026-11-23 in #2100). Beside its Room and written by Triton, it says who came and went, when, and how many messages were posted. Its messages stay on the Topic while the Topic's own retention (`maxAge`, short) keeps them: no file, no Drive and no automatic delete. Keeping the history goes with #1269 (history out of etcd) and #2099 (the observability reef, VictoriaLogs first, Drive as an export).

**The CLI is the agent's MCP server, with groups of tools** (owner, 2026-11-22: "the Nereus MCP server with different tools that can be turned on or not by calling the CLI"). Today `session create` passes the bridge (`--mcp-config`) and the pull hooks (`--settings`) to each Claude Code it opens, so a session already open cannot join. Instead:

- `nereus mcp local add` registers, once and in the user's scope, one MCP server, `nereus mcp local serve`, and the hooks, as `claude mcp add` does for any server; `nereus rooms join` runs it when it is missing.
- The server's tools come in groups, `rooms` the first; `nereus mcp local list` shows them, `nereus mcp local enable` and `disable` turn one on or off, and `join` turns `rooms` on for its session. When a group changes, the server tells Claude Code (`notifications/tools/list_changed`, of the MCP protocol), so tools appear and go with the session open.
- The hooks call the CLI and print nothing while the session is in no room.
- The `rooms` group is today's bridge: it holds the person's token (refreshed, never in the session's argv or environment), names the agent in `Nereus-Agent`, lets through the peer tools only, and sends the heartbeat that makes the Peer `Ready`; with the session in no room it sends none.

This server is local and serves an agent on its machine; the API's `/mcp` below is a remote one, for a person in claude.ai. The word `local` keeps the two apart in the CLI (owner, 2026-11-22): `nereus mcp tool` and `nereus mcp client` stay the remote `/mcp`'s.

**Two small reefs, composed** (owner, 2026-11-21). `messaging` is the engine's reef: `Topic` and `Queue`, looked after by `nats`. `rooms` is the conversation's reef: `Room` and `Peer`, looked after by `triton`. Each Nereid reconciles every kind of its reef, with no exemption. Triton looks after `rooms` only: `messaging` leaves its `spec.reefs` and stays as the reef it requires, so it never answers for `Topic` or `Queue`.

**Triton knows the contract, not the engine** (owner, 2026-11-21: "it only needs to understand the contract and depend on the reef"). Its image declares `requires=messaging`, as keycloak's declares `secrets`, so a profile installs the engine first and refuses to leave it out. There are two planes:

- **The control plane is the reef's contract.** For each `Room`, Triton applies a `Topic` named `room-<room>`, owned by the Room, with the Room's `spec.owner`, and reads the binding the reef gives back. It opens no stream of its own.
- **A Room has an owner,** an Organization or a Project of the tenancy tree (ADR 0015), as a Topic has, and it cannot change (owner, 2026-11-21, #2073): its Topic takes it, so each team's room lives in that owner's NATS account, and the API checks a Room as it checks a Topic, on its `spec.owner`.
- **Rooms live in the namespace `nereus-rooms`** (owner, 2026-11-21, #2073: "create a room and join it with your teammates", so a new Room works at once, with no list to change): a Room's Topic sits beside it, the reef writes a Topic's binding in the Topic's own namespace, and Triton reads Secrets there only, never in `nereus-system`.
- **The Mandate stays the only routing key** (#2065). Triton names no engine and no Nereid in a Topic (a Topic's `spec.engine` is optional, #2073): the messaging reef's Mandate picks who reconciles it, and the binding's `provider` only reports who did.
- **One writer per field** (ADR 0005). A Room's Topic is Triton's to ask for: Triton alone writes its `spec`, as keycloak writes the Release it requires, and `nats` writes its `status` and its binding.
- **The data plane is an adapter** chosen by the binding's `provider`. A room needs four operations of an engine: open, read the last sequence, append only if the last sequence is still the expected one, and read after a cursor. One adapter exists, for NATS. A second engine asks for a second adapter, and that is the whole of "swapping the engine keeps the rooms".

**What a room asks of a Topic.** Its messages are kept, in order, each with a sequence, and a reader starts after a sequence; the Topic carries its own retention (`spec.maxAge`, `spec.maxBytes`). Its binding carries a credential of its owner, and the Topic is closed to every other client (`spec.access: owner`): in a room, the sender of a message is the agent Triton checked, so Triton stays the only writer.

**A `Peer` is an agent's session in the rooms** (owner, 2026-11-21). Its name is `<owner>.<agent>`. One writer per field (ADR 0005): the session writes `spec` through the API (`owner`, a `{kind: User, name}` as ADR 0015 and ADR 0027 name a person; `agent`; `tool`; `rooms`, a list from the start, so an agent in several rooms changes no schema). Triton writes `status` (`phase`: `Arriving`, `Ready` or `Away`; `since`), and only when the phase changes: a heartbeat never writes the object. An `Away` Peer is deleted after 24 hours. A person who posts from the CLI or from claude.ai is not a Peer: a person has no presence.

**The orders' code leaves Triton** (owner, 2026-11-21). Orders have been off since #1440. Their code is what else keeps Triton on NATS directly; the idea stays in #2068.

**Everything reaches Triton through the Nereus API.** Triton keeps no public `/mcp` and no OAuth of its own: the bridge's calls (the heartbeat, whoami, a post and a read as an agent) and the person's (the peers and a read as a person) all go through the API. Triton stays an internal service.

**The internal door.** Triton serves HTTP only in the cluster (a ClusterIP Service and a NetworkPolicy). The API calls it with its own ServiceAccount token, which Triton checks by TokenReview and admits only for the API's ServiceAccount. The API passes the person (`sub`, `groups`, `nereus_owner`) and the agent the bridge names (`Nereus-Agent`) in headers, and Triton keeps its `peer_call` check: the agent is a Peer of the person's.

**The API's `Principal` gains `agent`**, read from `Nereus-Agent`, so the audit log says "person X, agent Y, via mcp" or "via cli". No token goes on to Triton (no passthrough) and none is exchanged: the API checked the person, and Triton trusts the API.

**The bridge talks REST.** The CLI's MCP server (its `rooms` group, the bridge) turns its local tools and its heartbeat into calls on `/v1/rooms/...` with the `nereus login` token (`aud: nereus-api`, #1320), so the separate login of the `triton` client goes.

**`/mcp` lists only what serves a person** in claude.ai: `rooms_peers` and `rooms_read` (`GET`, on by default) and `rooms_post` (`POST`, off until an admin turns it on, ADR 0029).

**The names:**

| What | Name |
|---|---|
| The reef of the conversation | `rooms`, API group `rooms.<domain>/v1alpha1` |
| Its kinds | `Room` (the reef's default kind), `Peer`, `RoomSession`, all namespaced, as `Topic` is; Rooms in `nereus-rooms` |
| Its Nereid | `triton`, whose image declares `requires=messaging` |
| The engine's reef | `messaging`: `Topic`, `Queue`, Nereid `nats` |
| A Room's Topic | `room-<room>`, owned by its Room |
| A Room's fields | `spec.owner`, `spec.description`, `spec.maxAge`, `spec.maxBytes`, `spec.deletionPolicy`; `status.topic` |
| A Peer's name | `<owner>.<agent>` |
| A Peer's fields | `spec.owner`, `spec.agent`, `spec.tool`, `spec.rooms`; `status.phase`, `status.since` |
| A Topic's new fields | `spec.maxAge`, `spec.maxBytes`, `spec.access` (`shared`, the default, or `owner`) |
| CLI | `nereus rooms create`, `apply`, `list`, `get`, `delete`, `join`, `leave`; `nereus rooms peer list`, `get`; `nereus rooms follow`, `pull`, `post`; `nereus rooms session list`, `get`; `nereus mcp local add`, `serve`, `list`, `enable`, `disable` |
| The agent's MCP server | `nereus mcp local serve`, its groups of tools, `rooms` the first |
| A room's activity | a room session, from the first agent in to the last one out: kind `RoomSession`, written by Triton; its messages on the Topic while its retention keeps them (#1269, #2099 keep the history) |
| Routes | `/v1/rooms/...` |
| MCP tools | `rooms_peers`, `rooms_read`, `rooms_post` |

```text
$ nereus rooms create ops --description "Operations peers"
✓ rooms/rooms/ops created

$ nereus messaging topic list
NAME      OWNER  READY  AGE
room-ops  ops    True   5s

$ nereus rooms list
NAME  OWNER  AGENTS  READY
ops   ops    0       True

$ nereus rooms join ops
starting doto with claude-code: in the room ops on Triton

$ nereus rooms peer list
NAME      ROOMS  PHASE  SINCE
ana.doto  ops    Ready  10:02:11
```

The options weighed:

| Option | What it is | Against |
|---|---|---|
| One Nereid for one reef | `nats` and `triton` merged, reconciling `Topic`, `Queue` and `Room` | Two code bases merged; a second engine's Nereid would have to do rooms too |
| The conversation alone | One reef with `Room` only, `Topic` and `Queue` removed, NATS inside Triton | Drops the `nats` Nereid already built and the queue a Workload will ask for |
| No engine | Rooms kept in the Kubernetes API or in SQLite | The rooms' storage and the asks rewritten, with nothing an agent would notice |
| Triton on NATS directly, said so | Today's code, the ADR saying "rooms on NATS" | The engine keeps a parameter for one client, and Triton depends on a Nereid, not on a reef |
| The messaging name for the conversation | `messaging` holds `Room`, the engine moves to a new reef | Moves the kinds ADR 0017 named; the owner is the only user of the session commands, so renaming those is the cheaper side |
| **Two reefs, Triton on the reef's contract** | Above | A Room costs a Topic and a binding, and the Topic's contract grows by retention and a credential |

On the door, weighed on 2026-11-18 and unchanged:

| Option | What it is | Against |
|---|---|---|
| Token passthrough to Triton | The API forwards the person's token | MCP forbids it; Triton would check a token issued for another audience |
| Token exchange (RFC 8693) | The API trades the person's token for one of Triton's audience | A second issuer path and client in the realm for a call that never leaves the cluster |
| The API on the engine, no Triton | The API reads and writes the rooms itself | Presence, `peer_call` and the asks move into the API, which then depends on the engine |
| The bridge over `/mcp` | The CLI calls the API's MCP tools | `/mcp` is the person's door (ADR 0029, `aud: nereus-mcp`); the CLI already holds a `nereus-api` token for REST |
| **Internal door, bridge on REST** | Above | A second hop inside the cluster, and Triton must trust the API's headers |

## Prior art

- **Service Binding Specification for Kubernetes** ([servicebinding.io](https://servicebinding.io/spec/core/1.1.0/)): a binding is a Secret whose `type` entry "identifies the abstract classification of the binding" and whose `provider` entry "identifies the provider of the binding", beside well-known entries such as `host`, `port`, `uri`, `username` and `password`. Triton picks its adapter by `provider`, and reads the rest.
- **Kubernetes Leases** ([kubernetes.io](https://kubernetes.io/docs/concepts/architecture/leases/)): a kubelet's heartbeats are updates of a small Lease object. A Peer goes one step further for the same reason: the heartbeat is kept in memory, and only a change of phase is written.
- **Kubernetes API aggregation, request header authentication** ([kubernetes.io](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-aggregation-layer/)): the API server authenticates the person and proxies to an extension API server with the user and groups in headers, which that server trusts only from the front proxy's identity; the same split as Triton trusting the API.
- **Kubernetes TokenReview** ([kubernetes.io](https://kubernetes.io/docs/reference/kubernetes-api/authentication-resources/token-review-v1/)): a service checks a ServiceAccount token with the cluster, with no secret of its own.
- **MCP Security Best Practices** ([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/)): no token passthrough to the services behind an MCP server.

## Consequences

The journey #2067 carries the change, all at once, in steps that each fit one agent's context:

- #2070: a Topic keeps its messages by its own spec, `maxAge` and `maxBytes`.
- #2071: a Topic's binding carries its owner's credential, so only the owner publishes.
- #2072: the `rooms` reef and its two kinds; `triton` looks after it and requires `messaging`; no kind of either reef joins the list of exempt kinds, which #2066 freezes.
- #2073: Triton reconciles `Room`: the Topic, the binding, the adapter.
- #1491: the Room's verbs in the CLI and the bound on rooms per installation.
- #2074: Triton reconciles `Peer`, and the bucket `agents` goes.
- #2075: a Peer's rooms: `nereus rooms join`, outside and inside Claude Code, and the bridge and the pull hook over several rooms (rewritten 2026-11-22: no `--room`, no `.nereus/room` file).
- #2101: `nereus mcp local`, the CLI as the agent's MCP server, its tools in groups, `rooms` the first.
- #2100: the room sessions, `RoomSession`, read with `nereus rooms session list` and `get` (narrowed on 2026-11-23: no file on Drive).
- #1491 also carries who may create a Room (a team member, their team's Rooms); the hard and soft gates are #2102, outside the journey.
- #2076: the CLI's surface moves to `nereus rooms`; #1889: a person posts with `nereus rooms post`.
- #2077: the orders' code leaves Triton.
- #2078: the `nats` Nereid loses `agents=true`, the account `AGENTS` and the user `triton`.
- #2079: the docs and the peers protocol say `rooms`.

Under #1812, with the names above: #1895 (the internal door, the API's `/v1/rooms` routes and `Principal.agent`), #1896 (the bridge on REST), #1897 (Triton's contract declares the three tools) and #1898 (Triton's public `/mcp`, its OAuth, the `triton` and `triton-door` clients, the claude.ai Triton connector and the NATS auth callout all go; the cloudflared tunnel stays).

- Triton is `NotConformant` from #2072 until #2073 and #2074 are both merged: the contract saying what is missing, not a defect.
- The old streams `rooms.<room>` of the account `AGENTS` are not migrated: a room's messages are short-lived coordination.
- The audience `nereus-mcp` stays: it names the token `/mcp` accepts.
- Until v1.0.0 this ADR is rewritten in place when the decision changes (ADR 0001).

## Origin

Decided by the owner on 2026-11-18, refining #1812 (Triton's tools served by the Nereus API's `/mcp`) one question at a time: the door, the bridge, the tools. Decided again on 2026-11-21, evaluating the messaging reef one question at a time: the two reefs, the name `rooms`, Triton on the reef's contract, the `Peer` kind, the orders' code, and one journey for all of it (#2067). Decided again on 2026-11-22, the flow as a person lives it, one question at a time: the measure of the feature, who may create a Room, `nereus rooms join` and `leave`, the room sessions and what they keep, and the CLI's MCP server. Narrowed on 2026-11-23 (#2100, #2079, the owner's word): a room session keeps no file on Drive.

## Open questions

- A `RoomSession`'s retention in the cluster, and where a room's history is kept: #1269 (history out of etcd).
- Later, most likely, a room session's logs and metrics go to the observability reef, VictoriaLogs first and Drive as an export (owner, 2026-11-22): #2099, outside this journey.
- Whether Claude Code applies `notifications/tools/list_changed` in an open session: checked before the CLI's MCP server is built.
- The hard and soft gates on creating a Room: the pending phase's name, and what is OpenFGA's and what a policy's (#2102).

- How orders arrive if they come back: #2068.
- Who may join a room: any member of the team group for now; a room's own members wait for the teams reef (#1307).
- How NATS learns a Topic's new user without a restart (#2071, #600).
- The rooms reef's Mandate carries the bound on rooms per installation (`maxRooms`, 20 by default): its value on the kept cluster is the owner's (#1491).

*Extended 2026-11-22 with the flow as a person lives it (#2067); raw data in `#pontos/raw/2026-11-22/`. Rewritten 2026-11-21 from the owner's evaluation of the messaging reef (#2067, #2069); raw data in `#pontos/raw/2026-11-21/`. First written 2026-11-18 (#1893); raw data in `#pontos/raw/2026-11-18/`.*
