# 0029. A reef declares its MCP tools in the Nereid contract, and the Nereus API serves them at /mcp

!!! note "In short"
    MCP is a door of the Nereus API, not a reef: each reef declares its MCP tools in its Nereid contract, and the API serves them at `/mcp`. The core's generic tools read every kind; a reef's task tools do its writes and name the CLI commands they cover, and a check proves every command that changes something was decided. Status: Accepted.

**Status:** Accepted

## Context

`nereus-mcp` (#415) is the MCP server people and their agents reach the platform through: an entry point of the CLI's package (`cli/src/nereus/nereus_mcp.py`) that runs on the person's machine, reads the cluster with the kubeconfig, and serves one hand-written tool, `status`, on `/mcp` (Streamable HTTP). It serves the OAuth protected resource metadata (RFC 9728) and proxies the realm `nereus` of the keycloak Nereid, and a cloudflared tunnel gives it a public HTTPS URL, which the claude.ai connector needs. Its tokens carry `aud: nereus-mcp`. The Nereus API (ADR 0018) checks tokens for `aud: nereus-api` (`api/auth.py`) and says `nereus-mcp` "becomes a client of the API, or a part of it, in a later issue".

Every feature planned "through MCP" (#350 the Claude app as a connector acting as the person, #137 the board, #214 ideas, #245 examples, #1196 presentations) would add tools to that one process by hand, so the tools would drift from the reefs installed in an instance. Reefs already extend the CLI with their commands (ADR 0004) and the portal with their screens (ADR 0022), each declared in the Nereid's contract; MCP has no such extension point.

Two kinds of client use MCP. A Claude Code session on the person's machine already runs the `nereus` CLI, with its login. claude.ai and the Claude app, the voice path, reach only a public URL with OAuth and never see the CLI's local token: they are the clients this decision is for.

The owner asked on 2026-11-17 whether the MCP tools should come from the reefs, staying in step with the platform and its authentication, and that the tools offered be chosen per instance, maybe per person (#1803).

On 2026-11-26 the owner made it a pillar, **whatever the CLI reaches, MCP reaches** (`docs/vision.md`, #2297, the journey #2298): everything a person can do from the CLI, an agent can do as that person through `/mcp`. Parity is of capability, not of commands. With contract v2 nothing proved it: a reef could ship a command that changes something and no tool for it, and nobody would know. A tool's route could only be `GET` or `POST`, while the API's routes also use `PUT` (19) and `DELETE` (12).

## Decision

**MCP is a door of the Nereus API, not a reef.** A reef is an API group with kinds (ADR 0002); MCP holds none, it is a way in, as the portal is. The API serves `/mcp` (Streamable HTTP) and its protected resource metadata itself, behind the same public name. The options weighed:

| Option | What it is | Against |
|---|---|---|
| Keep `nereus-mcp` and add tools to it | Today's process, on the person's machine | Reads the cluster with the kubeconfig (ADR 0018, #1320); every reef's tools in one place, by hand |
| A central `mcp` reef with hand-written tools | One server in the cluster | The "module of the portal" ADR 0022 refused: the server must know every reef |
| **Each reef declares its tools; the API serves them** | A `tools` list in the Nereid contract, read from status | A contract to keep stable, and descriptions that are untrusted input |
| Tools generated from the API's routes or the CRDs | No declaration | Many CRUD tools, badly described for a model |

**Two kinds of tool** (owner, 2026-11-26):

- **Generic reads, the core's:** `nereus_kinds` (the reefs and kinds the API serves, `GET /v1/core/kinds`), `nereus_list` and `nereus_get` (`GET /v1/{reef}/{kind}` and `GET /v1/{reef}/{kind}/{name}`, the same answer as `nereus REEF KIND list|get --output json`). Three tools read every kind of every reef installed, so a reef declares no read tool to be reachable; the API refuses a reef or kind it does not serve before the call (#2294).
- **Task tools, a reef's:** designed for what people come to the reef to do (`approval_approve`, `presentations_share`), declared in its contract. **Every write goes through a task tool.** There is no generic `apply` or `delete` tool: one such tool would be a single switch for every write of every reef, and would undo the instance's default of writes off per tool (below). A reef may still declare a read task tool when a goal needs more than one list (`approval_list`, the requests a person may decide).

A tool is never generated from a command, a route or a CRD (the last option of the table): the generic reads cover what generation would give for reads, and a write deserves a description written for its goal.

**The contract gains a `tools` list**, read with `contractVersion` `2` or `3`; a Nereid on `1` (or none) publishes no tool. Version `3` adds `covers` and the `PUT` and `DELETE` routes; the API and nereid-sdk read both, and an entry on `2` with a v3 field is ignored, as any unknown field. Each entry has exactly these fields; an unknown field makes the entry ignored:

```json
{
  "name": "authorization",
  "commands": [],
  "contractVersion": 3,
  "screens": [],
  "tools": [
    {
      "name": "approval_approve",
      "description": "Approve a request waiting for your decision, by name.",
      "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
      "route": {"method": "POST", "path": "/v1/authorization/approvals/{name}/approve"},
      "covers": ["authorization approval approve"]
    }
  ]
}
```

- `name`: `<reef>_<verb>`, by the reef, never by the Nereid, so two reefs never collide and swapping the Nereid keeps the names; lowercase letters, digits and `_`, at most 64 characters.
- `description`: at most 300 characters, printable text with no markup. It reaches a model's context, so it is untrusted input (ADR 0004 already treats the contract as such; here it can steer a model, which MCP calls tool poisoning): the API drops an entry that breaks the rule and shows the reef next to each tool.
- `inputSchema`: a JSON Schema object, as MCP's `tools/list` carries it, and as untrusted as the description, since it reaches the same context: only `type`, `properties`, `required`, `items`, `enum` of scalars, `format` (date, date-time, email, uri, uuid), `description`, `title`, `default`, `additionalProperties` as a boolean and the length and range bounds; every `description` and `title` under the description's rule, at most 5 levels and 4096 characters as JSON; anything else drops the tool.
- `route`: the `/v1` route that runs the tool, `GET` or `POST` (v2), also `PUT` or `DELETE` (v3), under the reef's own `/v1/<reef>/`, so a reef never routes a tool to another reef's API; a `{name}` of the path takes the argument of that name, the others go as the query of a `GET` or a `DELETE` or the body of a `POST` or a `PUT`. No reef code runs in the API: the API carries data, as with screens.
- `covers` (v3, optional): the CLI commands whose work the tool does, each as `"<reef> <kind> <verb>"` in the reef's and kind's names (`authorization approval approve`), not the command's spelling: a shortcut (`nereus workload deploy`, `nereus notify`) maps to its reef's kind and verb. At most 16 entries, each of lowercase words; the kind under the tool's own reef, as for the route. It is what the write half of the check below reads; the API serves it in `GET /v1/tools` and never sends it to a model.
- **No ceiling on the count** (owner, 2026-11-18): every tool listed fills a model's context, but which tools are on is the instance's and the person's choice (below), not the reef's; how many are on and what they cost in tokens is measured later.

**The SDK copies the list to the Nereid's `status.tools`**, as it copies `screens`; the API reads the installed reefs' status and answers `GET /v1/tools`, as it answers `GET /v1/screens`. `tools/list` on `/mcp` is that list. Uninstalling a reef removes its tools with nothing to delete. `/mcp` is stateless, with JSON answers (owner, 2026-11-18): no session to keep, any replica answers, and so no `notifications/tools/list_changed`; a client lists the tools again on each connection. The platform's own `status` tool belongs to the `core` reef. When two Nereids publish tools for one reef, the first by name answers, as for screens.

**The token.** Only `/mcp` accepts `aud: nereus-mcp`; every other route keeps `aud: nereus-api`. A `tools/call` runs the declared route **in process**, as the person: the API's authorization and its audit log see the person's `sub`, as for the CLI. Its Principal says `via: mcp` (#1809): the log names it, and a route that must never run on a model's call refuses it (the instance's switch is one). No token goes on to another service (MCP forbids token passthrough) and no token exchange is needed, since the API is the MCP server.

**Which tools a person gets.** The client's own toggles (the claude.ai connector settings, Claude Code's permissions) stay; the platform filters before them, in this order:

1. **The instance:** an enabled and a disabled list of tool names and `<reef>_*` patterns in the `Installation`'s `spec.mcp.tools` (#1809: the instance's own object, validated by its CRD, kept across an upgrade of the chart, unlike a ConfigMap of the API), changed only by `nereus-admins` through the API (`PUT /v1/tools/{name}`), so the audit log records who turned what off. An exact name beats a pattern; within one, disabled wins. With no rule, a tool whose route is a `GET` is on and one whose route is a `POST`, a `PUT` or a `DELETE` is off (owner, 2026-11-18, from the security review of #1808): a model steered by text it reads must not write as an admin until an admin chose that tool. Each write tool is turned on by name or by its reef's pattern; no switch turns every write on. A tool off is never listed nor called on `/mcp`; `GET /v1/tools` shows it with why.
2. **The person's permissions:** the core's tools (`status` and the three generic reads) are open: listed to any valid token, since their route depends on the call's arguments, and the route each call reaches decides, with the same answer as the CLI's. Any other tool appears only when the person may call its route, so it never appears just to fail: the API asks the authorization reef for the route's verb (`list`, `get`, `create` or `apply`, read from the method and the path) on the instance; with no default Mandate of that reef, only `nereus-admins` get the reefs' tools, as the routes answer. A person whose bindings sit only on a Project does not see a listing tool yet. The route decides again on each call.
3. **The person's own choice**, below what the instance allows: decided later (#1811).

The command, under `mcp` since a Nereid's `Tool` is the upstream program it runs (#1263), with ADR 0013's verbs:

```
$ nereus mcp tool list
REEF           TOOL                 STATE
core           status               on
presentations  presentations_list   on
presentations  presentations_share  off (write)

$ nereus mcp tool disable presentations_list
✓ tool presentations_list disabled for the instance
```

**A check keeps the parity** (`scripts/checks/mcp-coverage`, one of `make checks`):

- **Reads** (#2294): every kind of a CRD in `reefs/` needs the list route the generic reads reach, `GET /v1/<reef>/<plural>`; a kind without one sits in a ratchet with the issue that serves it.
- **Writes** (#2295): the check walks the CLI's command tree (the static commands and the reefs' groups) and requires every command that changes something to appear in **exactly one** place: a tool's `covers`; the CLI-only list, each line with its reason (`login`, `logout`, `init`, `version`, `upgrade`, `mcp local *`, `mcp client *`, `mcp tool enable|disable`, `config get|set`: what acts on the person's machine or on the MCP door itself); or the ratchet, which only shrinks. A command in none fails, and so does one in two. Reads (`list`, `get`) stay outside the write half, since the generic tools reach them.

The ratchet starts with every write command not yet covered, and each reef's task tools lower it; a new command lands covered, CLI-only with a reason, or not at all.

**The cloudflared tunnel stays** (owner, 2026-11-17): it exposes the authentication, the site and the claude.ai connector, now pointed at the API's `/mcp`. The `nereus-mcp` process retired once the API served `/mcp` (#1810).

## Prior art

- **Backstage's Actions Registry and `mcp-actions-backend`** ([backstage.io](https://backstage.io/)): each plugin registers actions and one backend serves them as MCP tools; the same split of a declaration per extension and one server.
- **Kubernetes API aggregation and discovery** ([kubernetes.io](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/)): registration is data in the cluster and disappears with its object.
- **GitHub MCP server's toolsets** ([github.com/github/github-mcp-server](https://github.com/github/github-mcp-server)): grouping and switching tools off, their answer to too many tools for a model.
- **MCP Authorization and Security Best Practices** ([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/)): the protected resource metadata (RFC 9728), tokens issued for the MCP server itself (RFC 8707), and no token passthrough.

A second opinion on this design came from an agent on another model, on 2026-11-17; its corrections (MCP as a door, not a reef; `/mcp` inside the API instead of a token exchange) are part of the decision above.

## Consequences

- A reef offers tools with no release of the API or of an MCP server: install the reef, and its tools appear in claude.ai.
- The Nereid SDK and `templates/nereid` learn the `tools` field and `contractVersion` `2` (#1807); `leagore` declares `presentations_list` first.
- The API serves `/mcp` and `GET /v1/tools`, and `nereus mcp tool list` reads it (#1808); the instance's switch comes with `nereus mcp tool enable | disable` (#1809); `nereus-mcp` and its line in the kubeconfig allow-list went (#1810).
- A reef's description reaches a model through the person's connector: installing a reef trusts its text as it trusts its screens' code (ADR 0022). The length, character and count limits narrow it; they do not make it trusted.
- Triton, today a second MCP server, becomes the Nereid of the `rooms` reef behind the Nereus API, and its own connector goes (ADR 0030, #1812).
- Contract v3 (#2295): the API and nereid-sdk accept `covers` and the `PUT` and `DELETE` routes, and keep reading v2; `templates/nereid` moves to v3. The approval tools of #2221 are the first to declare `covers`, and lower the ratchet in the same change.
- A reef that adds a command that changes something adds its task tool, or a CLI-only line with a reason, in the same change: `make checks` refuses the command otherwise.
- The generic reads, `GET /v1/core/kinds` and the reef/kind guard of `/mcp` shipped with #2294.
- Until v1.0.0 this ADR is rewritten in place when the decision changes (ADR 0001).

## Origin

Asked by the owner on 2026-11-17 in #1803, refined in the same session with a second opinion; the owner accepted the recommendations the same day. Raw data in `#pontos/raw/2026-11-17/` (Drive). The generic reads, the task tools for every write, no generic `apply` or `delete`, and the check were decided by the owner on 2026-11-26 in #2298 and #2295.

## Open questions

- A person's own choice of tools (#1811).
- A subset of reefs on the MCP URL, so a client sees only the tools of the reefs it asks for (#2296, after #2295).
- Whether a tool may run a Nereid's command (`POST /run`) instead of a `/v1` route, for reefs whose verbs live in their commands.

*Rewritten 2026-11-26 from #2295 (contract v3, task tools with covers, the write half of mcp-coverage); raw data in `#pontos/raw/2026-11-26/`.*
