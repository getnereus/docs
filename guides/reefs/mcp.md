# Use the MCP server

Reach the tools of the installed Reefs from Claude Code or claude.ai: the [Nereus API](../../concepts/nereus-api.md) serves `/mcp` itself, each tool run as you, through the installation's entrance as `/v1` is.

## Before you start

- An installation reachable at `https://nereus.example.com`, and `nereus login` done, from [Turn on authentication](../access/authentication.md).
- To choose the tools the installation offers, a login in `nereus-admins`.

## Steps

### 1. See the tools you may call

[`nereus mcp tool list`](../../specs/cli/core.html#mcp-tool-list) shows each tool the installed Reefs declare whose route you may call, the core's `status` first. A tool whose route is a `POST` shows `off (write)`: it starts off until an admin enables it.

```bash
nereus mcp tool list
```

``` { .text .output title="output" }
REEF           TOOL                STATE
core           status              on
presentations  presentations_list  on
```

### 2. Choose the tools the installation offers

An admin turns tools off or on with [`nereus mcp tool disable` and `enable`](../../specs/cli/core.html#mcp-tool-switch), by name or every tool of a Reef (`<reef>_*`). An exact name beats a pattern.

```bash
nereus mcp tool disable presentations_list
```

``` { .text .output title="output" }
✓ tool presentations_list disabled for the instance
```

```bash
nereus mcp tool enable 'presentations_*'
```

``` { .text .output title="output" }
✓ tools presentations_* enabled for the instance
! presentations_list stays off: disabled by its own name, which beats a pattern
```

The switch lives in the `Installation`'s `spec.mcp.tools`; `/mcp` lists and calls only the tools `on`, and the list shows the others as `off (instance)`. It is never changed through `/mcp` itself.

### 3. Add it to Claude Code

[`nereus mcp client add`](../../specs/cli/core.html#mcp-client-add) runs Claude Code's own `claude mcp add`, so it never writes the agent's settings or copies your token into them. `--dry-run` shows that command; `--scope user`, the default, adds the server to every project.

```bash
nereus mcp client add claude-code \
  --dry-run
```

``` { .text .output title="output" }
would run: claude mcp add --transport http --scope user --client-id claude-code --callback-port 33418 nereus https://nereus.example.com/mcp
```

```bash
nereus mcp client add claude-code
```

``` { .text .output title="output" }
✓ claude-code: MCP server nereus added (https://nereus.example.com/mcp, scope user, OAuth client claude-code)

Next steps:

  claude    # then /mcp, and log in to nereus
```

In Claude Code, `/mcp` opens the realm's login page in the browser.

A chat that needs only some Reefs takes a server of its own with `--reef`, named `nereus-<reefs>`: its URL carries `?reefs=`, so it offers only those Reefs' tools and the core's, whose generic reads reach only those Reefs (#2296). A Reef the instance lacks is refused at the connection, naming the installed ones.

```bash
nereus mcp client add claude-code \
  --reef edge,catalog
```

``` { .text .output title="output" }
✓ claude-code: MCP server nereus-edge-catalog added (https://nereus.example.com/mcp?reefs=edge,catalog, scope user, OAuth client claude-code)

Next steps:

  claude    # then /mcp, and log in to nereus-edge-catalog
```

### 4. Add it to claude.ai

In claude.ai, add a custom connector with the URL `https://nereus.example.com/mcp` (or `https://nereus.example.com/mcp?reefs=edge,catalog` for a subset, which keeps a chat on the phone light) and the OAuth Client ID `claude`. The client finds the issuer from the protected resource metadata (RFC 9728) and logs in with a token only `/mcp` accepts.

```bash
curl --silent https://nereus.example.com/.well-known/oauth-protected-resource/mcp
```

``` { .json .output title="output" }
{"resource":"https://nereus.example.com/mcp","authorization_servers":["https://auth.example.com/realms/nereus"],"scopes_supported":["openid","offline_access"],"bearer_methods_supported":["header"]}
```

## Check it worked

After the login, the Claude Code session lists the same tools as `nereus mcp tool list`. `/mcp` is stateless: a Reef installed or uninstalled shows on the client's next connection. `nereus mcp client list` shows the coding agents that have it, one row per server.

```bash
nereus mcp client list
```

``` { .text .output title="output" }
CLIENT       SERVER               REEFS          URL                                                SCOPE
claude-code  nereus               all            https://nereus.example.com/mcp                     user
claude-code  nereus-edge-catalog  edge, catalog  https://nereus.example.com/mcp?reefs=edge,catalog  user
```

## Clean up

```bash
nereus mcp client remove claude-code
nereus mcp client remove claude-code --reef edge,catalog
```

``` { .text .output title="output" }
✓ claude-code: MCP server nereus removed
✓ claude-code: MCP server nereus-edge-catalog removed
```

## Next

- [Join the team's room](team-room.md): your coding agent among the team's agents.

## Learn more

- [ADR 0029](../../adr/0029-mcp-tools.md): each Reef declares its tools in its Nereid's contract, and the Nereus API serves them.
