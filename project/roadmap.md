# Roadmap

Where Nereus is going: the work in order, and every idea on a ring around Nereus, far out when new and inward as it is refined. [planned #1978]

The queue is the [board](https://github.com/orgs/getnereus/projects/1); what already runs is in [What is built](../reference/what-is-built.md). The radar takes its shape from the [Thoughtworks Technology Radar](https://www.thoughtworks.com/radar) with the axis flipped: distance is how refined an idea is, not how ready a technology is.

## Next, in order

Open issues only; each carries its context, dependencies and "Done when".

| Step | Issue | Status |
|---|---|---|
| Auth0 Nereid and the swap from keycloak by a Mandate | [#91](https://github.com/getnereus/nereus/issues/91) | [planned #91] |
| The terraform reef and its stack Nereid (AKS Stack) | [#92](https://github.com/getnereus/nereus/issues/92) | [planned #92] |
| `terraform-packager` with workload identity | [#93](https://github.com/getnereus/nereus/issues/93) | [planned #93] |
| Bootstrap from the local seed: pivot to the overcloud | [#61](https://github.com/getnereus/nereus/issues/61) | [planned #61] |
| Azure Nereid of the cost reef | [#156](https://github.com/getnereus/nereus/issues/156) | [planned #156] |
| Azure Key Vault Nereid that creates or adopts vaults | [#81](https://github.com/getnereus/nereus/issues/81) | [planned #81] |
| A real Azure test in CI | [#170](https://github.com/getnereus/nereus/issues/170) | [planned #170] |
| Messaging: a `nats` Nereid applied by `nereus` on naxos | [#576](https://github.com/getnereus/nereus/issues/576) | [planned #576] |
| Edge: the `cloudflare` Nereid publishes naxos's endpoints | [#577](https://github.com/getnereus/nereus/issues/577) | [planned #577] |
| Build: Dockerfile with named contexts and build arguments | [#1614](https://github.com/getnereus/nereus/issues/1614) | [planned #1614] |
| Every published image is a catalog Workload with a Trigger | [#1615](https://github.com/getnereus/nereus/issues/1615) | [planned #1615] |
| Publish a release from the Builds of main | [#1616](https://github.com/getnereus/nereus/issues/1616) | [planned #1616] |
| Reference Nereids for every reef a tool serves | [#1502](https://github.com/getnereus/nereus/issues/1502) | [planned #1502] |
| An always-on environment: `main` deployed to a live cluster | [#159](https://github.com/getnereus/nereus/issues/159) | [planned #159] |
| Release on merge: a labelled PR publishes the next version | [#1531](https://github.com/getnereus/nereus/issues/1531) | [planned #1531] |
| Flux installs only the chart digest a Nereid pinned | [#662](https://github.com/getnereus/nereus/issues/662) | [planned #662] |
| Plain manifests from git in the release reef | [#751](https://github.com/getnereus/nereus/issues/751) | [planned #751] |
| Private images resolved with the registry credential | [#953](https://github.com/getnereus/nereus/issues/953) | [planned #953] |
| Keycloak brokers a GitHub login through the github Mandate | [#1282](https://github.com/getnereus/nereus/issues/1282) | [planned #1282] |
| Teams, roles and Users: how they relate | [#1306](https://github.com/getnereus/nereus/issues/1306) | [planned #1306] |
| The teams reef: Team, Position and Member | [#1307](https://github.com/getnereus/nereus/issues/1307) | [planned #1307] |
| A certificate reef with cert-manager | [#1101](https://github.com/getnereus/nereus/issues/1101) | [planned #1101] |
| Tide as the ideas reef's portal screen | [#1108](https://github.com/getnereus/nereus/issues/1108) | [planned #1108] |
| Presentations journey: a talk driven from the phone | [#1687](https://github.com/getnereus/nereus/issues/1687) | [planned #1687] |
| The phone shows how the instance is doing | [#738](https://github.com/getnereus/nereus/issues/738) | [planned #738] |
| A war room for agents in Triton | [#618](https://github.com/getnereus/nereus/issues/618) | [planned #618] |
| Flow metrics for the queue, with a forecast | [#95](https://github.com/getnereus/nereus/issues/95) | [planned #95] |
| Opening the repository (deferred) | [#9](https://github.com/getnereus/nereus/issues/9) | [planned #9] |

## The radar

| Ring | An idea is here when |
|---|---|
| In Nereus | it is code on `main` |
| Refining | it is decided, with an issue or a beach order |
| Exploring | it was discussed and has a direction |
| Parked | it is promising, and stopped |

When an idea moves, its row changes ring and date in the same pull request.

### In Nereus

| Idea | Moved | Source |
|---|---|---|
| Triton's room: agents say hello on a NATS subject | 2026-10-28 | [#468](https://github.com/getnereus/nereus/pull/468) |
| Triton: an MCP server that sends orders over NATS | 2026-10-28 | [#469](https://github.com/getnereus/nereus/pull/469) |

### Refining

| Idea | Moved | Source |
|---|---|---|
| `nereus init` creates the k3d cluster with external volumes | 2026-10-29 | no issue yet |
| An `edge` reef with a `cloudflare` Nereid, behind a tunnel | 2026-10-29 | [#470](https://github.com/getnereus/nereus/issues/470) |
| The beach watcher claims an order while it serves the only agent | 2026-10-28 | no issue yet |

### Exploring

| Idea | Moved | Source |
|---|---|---|
| Triton's sync to another store becomes a Nereus component | 2026-10-29 | no issue yet |
| One mental dump, two doors, classified by Doris | 2026-10-29 | no issue yet |
| Triton checks who speaks: a credential per agent | 2026-10-29 | no issue yet |
| Triton remembers: JetStream survives a restart | 2026-10-29 | no issue yet |
| Triton bridges agents, every word on record | 2026-10-29 | no issue yet |
| Triton becomes the Nereid of a `messaging` reef | 2026-10-29 | [ADR 0030](../adr/0030-triton-messaging-nereid.md) |
| Amphitrite: an `Agent` reef that wraps kagent | 2026-10-28 | [#467](https://github.com/getnereus/nereus/pull/467) |

### Parked

| Idea | Moved | Source |
|---|---|---|
| Cluster intent: a `Cluster` resource and provisioner Nereids | 2026-10-29 | no issue yet |
| An `azure-dns` Nereid of the `edge` reef | 2026-10-29 | [#470](https://github.com/getnereus/nereus/issues/470) |

## Ideas being refined

Each ends in a spec or an ADR, not in code. Open issues only.

| Idea | Issue | Status |
|---|---|---|
| The Nereid registry: a public site of Nereids anyone can add | [#22](https://github.com/getnereus/nereus/issues/22) | [idea] |
| Inception: the platform's services built and run on the platform | [#24](https://github.com/getnereus/nereus/issues/24) | [idea] |
| Autonomous agents on ready issues | [#25](https://github.com/getnereus/nereus/issues/25) | [idea] |
| How every feature is born: alpha, beta, stable | [#28](https://github.com/getnereus/nereus/issues/28) | [idea] |
| The getnereus ecosystem of public examples | [#31](https://github.com/getnereus/nereus/issues/31) | [idea] |
| A contribution policy for autonomous agents | [#40](https://github.com/getnereus/nereus/issues/40) | [idea] |
| A visual identity: palette, type and mark | [#44](https://github.com/getnereus/nereus/issues/44) | [idea] |
| FinOps: costs of the project's clouds | [#56](https://github.com/getnereus/nereus/issues/56) | [idea] |
| Cost from the clouds, in the CLI | [#64](https://github.com/getnereus/nereus/issues/64) | [idea] |
| Observability as a cross-cutting reef | [#68](https://github.com/getnereus/nereus/issues/68) | [idea] |
| Appearance as a reef | [#74](https://github.com/getnereus/nereus/issues/74) | [idea] |
| A declarative installer: an Operator reading a `Platform` | [#77](https://github.com/getnereus/nereus/issues/77) | [idea] |
| A collaborative Lean Inception session | [#83](https://github.com/getnereus/nereus/issues/83) | [idea] |
| A misbehaviour policy for Nereids | [#86](https://github.com/getnereus/nereus/issues/86) | [idea] |
| A registry reef for private images | [#87](https://github.com/getnereus/nereus/issues/87) | [idea] |
| The storytelling of the presentation | [#190](https://github.com/getnereus/nereus/issues/190) | [idea] |
| A survey of what bothers developers | [#192](https://github.com/getnereus/nereus/issues/192) | [idea] |
| Feedback at every presentation | [#197](https://github.com/getnereus/nereus/issues/197) | [idea] |
| The platform as a place for ideas | [#214](https://github.com/getnereus/nereus/issues/214) | [idea] |
| Live ideation sessions | [#217](https://github.com/getnereus/nereus/issues/217) | [idea] |
| Building a talk by thinking aloud | [#219](https://github.com/getnereus/nereus/issues/219) | [idea] |
| Presenting from the platform | [#221](https://github.com/getnereus/nereus/issues/221) | [idea] |
| Decisions as records of the platform | [#275](https://github.com/getnereus/nereus/issues/275) | [idea] |
| Agent runs as Instances | [#276](https://github.com/getnereus/nereus/issues/276) | [idea] |
| A repository reef: repositories born private with CI | [#279](https://github.com/getnereus/nereus/issues/279) | [idea] |

## Next

[What is built](../reference/what-is-built.md) lists what already runs; [Decisions](decisions.md) lists the ADRs behind it.
