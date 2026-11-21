# 0030. Triton is the messaging reef's Nereid of rooms and peers, reached only through the Nereus API

!!! note "In short"
    Triton is the messaging reef's Nereid of rooms and peers, an internal service reached only through the Nereus API. Status: Proposed.

**Status:** Proposed

## Context

Triton (`controllers/triton/`) was born to carry the voice session's orders to remote agents (ADR 0019). Orders are off on this installation (#1440); what matters now is the rooms and the peers: remote agents talking as local ones do, the goal of journey #1890.

Today Triton is a Deployment in the namespace `triton` (`deploy/triton.yaml`), not a Nereid. It serves its own `/mcp` at a public URL behind its own OAuth (the keycloak Nereid's clients `triton` and `triton-door`). Its tools are the bridge's `heartbeat`, `whoami`, `post_room` and `read_room`, the person's `list_agents` and `read_room`, and the orders' tools, off.

The agent a call comes from is the header `Nereus-Agent`, set by the CLI's `peers` bridge (`cli/src/nereus/peers_bridge.py`); Triton admits it only when that agent is connected under the login's owner (`peer_call`).

The `nats` Nereid (`controllers/nats/`) is the messaging reef's engine: `Topic` and `Queue` on a NATS server; it publishes no commands and no tools. No machine reaches NATS since #1599: sessions go through Triton over HTTPS. The one login to NATS left is the orders' (`nereus messaging session create --orders`, `cli/src/nereus/nats_login.py`), which NATS's auth callout `nats-auth` (`controllers/triton/callout.py`) admits.

ADR 0018 makes the Nereus API the one door, and ADR 0029 has the API serve `/mcp` with the tools the reefs declare in their contract; its Triton line left Triton's own connector until this decision.

## Decision

**Everything reaches Triton through the Nereus API.** Triton keeps no public `/mcp` and no OAuth of its own: the bridge's calls (`heartbeat`, `whoami`, `post_room`, `read_room` as an agent) and the person's (`list_agents`, `read_room` as a person) all go through the API. Triton stays an internal service.

**The internal door.** Triton serves HTTP only in the cluster (a ClusterIP Service and a NetworkPolicy). The API calls it with its own ServiceAccount token, which Triton checks by TokenReview and admits only for the API's ServiceAccount. The API passes the person (`sub`, `groups`, `nereus_owner`) and the agent the bridge names (`Nereus-Agent`) in headers, and Triton keeps its `peer_call` check: the agent is connected under the person's owner.

**The API's `Principal` gains `agent`**, read from `Nereus-Agent`, so the audit log says "person X, agent Y, via mcp" or "via cli". No token goes on to Triton (no passthrough) and none is exchanged: the API checked the person, and Triton trusts the API.

**Triton becomes the messaging reef's Nereid of rooms and peers**, beside the `nats` Nereid, which stays the engine (`Topic`, `Queue`): swapping the engine keeps the rooms. Triton serves the `Room` kind of #1491, the presence and the peer tools, and declares the reef's MCP tools in its contract (ADR 0029, `contractVersion` 2). **Orders leave the scope:** they stay off and get their own issue when they matter again.

**The bridge talks REST.** The CLI's `peers` bridge turns its local tools and its heartbeat into calls on `/v1/messaging/...` with the `nereus login` token (`aud: nereus-api`, #1320), so the separate login of the `triton` client goes. `Nereus-Agent` is read on those routes.

**`/mcp` lists only what serves a person** in claude.ai: `messaging_agents` and `messaging_room_read` (`GET`, on by default) and `messaging_room_post` (`POST`, off until an admin turns it on, ADR 0029).

**The NATS auth callout leaves with the orders.** Its one user is the orders' NATS login. The callout (`nats-auth`), that login (`nats_login`, `--orders`, the realm's client `nereus-nats`), `scene-triton-callout`, `triton/app=nats-auth` in the Mandate `messaging-nats`'s `monitorFrom` and `nats-auth` in `auth_users` (`controllers/triton/nats_include.py`) go together, with Triton's public door. #1954 took the first step: the callout left the installation (`nats_include.py`, `nats-auth` and `scene-triton-callout` are gone; the account `AGENTS` is the `nats` Nereid's, written for a Mandate's `agents=true`); its code leaves with #1898. If orders come back, their own issue decides how they arrive, through the API by preference.

**The order against journey #1890:** only "Triton becomes a Nereid" joins the journey, with no change of behaviour, before #1491 (dynamic rooms). The transport change comes after #1890 is done, so it does not move the path the journey proves. `make scene-triton-team` is the regression check of each step.

The options weighed:

| Option | What it is | Against |
|---|---|---|
| Token passthrough to Triton | The API forwards the person's token | MCP forbids it; Triton would check a token issued for another audience |
| Token exchange (RFC 8693) | The API trades the person's token for one of Triton's audience | A second issuer path and client in the realm for a call that never leaves the cluster |
| The API on JetStream, no Triton | The API reads and writes the rooms itself | Presence, `peer_call` and the asks move into the API, which then depends on the engine |
| Rooms and peers in the `nats` Nereid | One Nereid for the reef | Swapping the engine would take the rooms with it |
| The bridge over `/mcp` | The CLI calls the API's MCP tools | `/mcp` is the person's door (ADR 0029, `aud: nereus-mcp`); the CLI already holds a `nereus-api` token for REST |
| **Internal door, Triton a Nereid, bridge on REST** | Above | A second hop inside the cluster, and Triton must trust the API's headers |

## Prior art

- **Kubernetes API aggregation, request header authentication** ([kubernetes.io](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-aggregation-layer/)): the API server authenticates the person and proxies to an extension API server with the user and groups in headers, which that server trusts only from the front proxy's identity; the same split as Triton trusting the API.
- **Kubernetes TokenReview** ([kubernetes.io](https://kubernetes.io/docs/reference/kubernetes-api/authentication-resources/token-review-v1/)): a service checks a ServiceAccount token with the cluster, with no secret of its own.
- **MCP Security Best Practices** ([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/)): no token passthrough to the services behind an MCP server.

## Consequences

- #1894: Triton becomes a Nereid of the messaging reef (nereid-sdk, its contract, `nereus nereid apply triton --reef messaging`), with no change of behaviour; it joins #1890 before #1491.
- #1895: Triton's internal door, the API's `/v1/messaging` routes (agents, a room's messages, the heartbeat, whoami) and `Principal.agent`.
- #1896: the bridge on REST with the `nereus login` token; `nereus messaging session list` reads `/v1/messaging/agents`.
- #1897: Triton's contract declares `messaging_agents`, `messaging_room_read` and `messaging_room_post`; claude.ai lists them and the audit log names person and agent.
- #1898: Triton's public `/mcp`, its OAuth, the `triton` and `triton-door` clients, the claude.ai Triton connector and the NATS auth callout with the orders' NATS login all go. The cloudflared tunnel stays; only Triton's route on it goes.
- The audience `nereus-mcp` stays: it names the token `/mcp` accepts.
- Until v1.0.0 this ADR is rewritten in place when the decision changes (ADR 0001).

## Origin

Decided by the owner on 2026-11-18, refining #1812 (Triton's tools served by the Nereus API's `/mcp`) one question at a time; the five decisions are a comment on #1812, and the callout and this ADR's form a comment on #1893. Raw data in `#pontos/raw/2026-11-18/` (Drive).

## Open questions

- How orders arrive if they come back: their own issue.
