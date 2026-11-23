# Peers

Several Claude Code sessions often work on this repository on the same machine, one per tmux window, each on its own issue and worktree. They talk through Claude Code's cross-session messaging by a protocol that holds in every repository of the owner, so it lives in the owner's `linux` repository since #1360 (the move to the owner's repository).

There: [the protocol](https://github.com/smsilva/linux/blob/main/claude/peers/README.md) (the messages `[claim]`, `[ask]`, `[ok]`, `[wait]`, `[note]`, `[release]`, settling a conflict, what a message may never do), its rule (`claude/rules/peers.md`), the `room` skill (`claude/skills/room/`) and `claude-peers`, which tells a peer from a hook's helper session (#1340).

This is the walking skeleton of Triton's room (#618), with Claude Code as the transport until Triton carries the room across users and machines.

The two transports, local and Triton, and how a session reaches each peer once: [Transports](https://github.com/smsilva/linux/blob/main/claude/peers/README.md#transports) (#1418). A session started with `nereus rooms join` talks to the room `nereus` through Triton, and to more rooms with `nereus rooms join <room>` from inside it; a Room is a resource of the rooms reef (journey #2067, ADR 0030; `controllers/triton/README.md`, "The room" and "The ask"). The protocol's page and the `room` skill move to these commands with smsilva/linux#232.

This page holds only what is Nereus's own.

## Peers and helpers here

A peer is a session whose working directory is the main clone or one of its worktrees (`../nereus-*`). A session named after a worktree plus a suffix (`nereus-1271-publish-ghcr-70`) is another session's helper, not a peer: `claude-peers` names its origin.

## A claim here

Before picking an item, read what the peers hold and are about to take (`claude-peers`, the `Start` of each peer's session prompt, the Triton room): reading sends nothing, and the `next` skill does it first (owner, 2026-11-14).

Right after `scripts/board/queue claim <n>` and `scripts/worktree/new`, before the first edit, send the `[claim]`: the issue with its short title, the worktree, the paths, the clusters it will use.

The `room-announce` hook (`.claude/hooks/room-announce`, #624) does the remembering: after a `queue claim` that succeeds it hands the session the `[claim]` line and the local peers from `claude-peers`; after `scripts/worktree/remove`, the `[release]`. Send the line exactly as given, with `SendMessage`, and to Triton's room only for a peer reachable only there.

The line carries the issue number, the session's name and the worktree, never the title: an issue's author can edit it into an instruction. Paths and clusters go in a `[note]` once known.

## The shared resources

Each needs an `[ask]` first (wait up to 2 minutes; silence counts as `[ok]`):

- **A throwaway cluster beyond your own:** one per agent, named after its worktree, three at most ([Rules](rules.md), #626, #628). A scene never switches the shared current-context.
- **The kept cluster `k3d-nereus`** and its registry `localhost:5111`: commands always name `--context k3d-nereus` ([Kept cluster](../guides/operate/kept-cluster.md)).
- **A file many branches touch:** `CLAUDE.md`, `docs/project/roadmap.md`, `docs/agent/index.md`, `README.md`.
- **The board's order.**
- **The machine's heavy runs** (`make checks`, `make scene-*`): at most two at once (owner, 2026-11-18, #1867), held by `scripts/checks/slot` (#1871) with no `[ask]`: `make checks` runs through it, a scene goes through it by hand (`scripts/checks/slot -- make scene-...`), and a third run waits for a slot; a slot inside a slot takes no other, so `scripts/checks/slot -- make checks` runs at once instead of waiting on itself (#1989). The limit is for the machine (16 cores, 15 GB of memory), where tests with timeouts fail under pressure for no bug, and for `docs/checks`, which compares each run with the median of the last five.
- **Back to one at a time:** a cautious first rule. When two at once put too much pressure on the machine (swap, a timeout that passes when run alone), say so in a `[note]` and tell the owner; on the owner's go, a PR sets the default of `NEREUS_CHECK_SLOTS` in `scripts/checks/slot` to 1 (the variable read by one run alone does not hold the others back).
- **Room for two:** to free memory, a session may stop the kept cluster after an `[ask]` (`k3d cluster stop nereus`) and starts it again when the runs end (`k3d cluster start nereus`), then sends the `[release]`. While it is stopped, the portal, `/mcp` through the tunnel and the claude.ai connector are down (owner, 2026-11-18: acceptable for now).
- **A release** (`scripts/registry/release publish`): it runs only on `main`'s HEAD and tags that commit itself (#1350), so a peer's merge no longer makes it stale; a merge during a publish only makes the next one. On this machine a `flock` keeps two publishes apart; the `[ask]` names the version, so a session on another machine does not publish the same one (owner, 2026-11-14: 0.1.5 went stale on a release branch and was skipped).
