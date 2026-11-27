# Beach

Glaucus (Glauco in Portuguese) is the messenger between the owner's voice session and the local agent (Claude Code): in the myth, the fisherman who became a sea god, next to Nereus and the Nereids. The channel is temporary: it ends when the first Nereid (the interlocutor, exposed as a remote MCP connector) runs on a Nereus instance. Conceptually, an order is a message of a future `messaging` Reef; the Drive folder is its first, rudimentary implementation.

## Layout

Everything lives under `#pontos/beach/` on Google Drive:

| Path | What it holds |
|---|---|
| `beach/` | the open orders, `YYYYMMDD-HHMM-<slug>.md`, plus `00-local-agent-prompt.md` (the standing prompt, not an order). "Open" means not archived yet: a finished order stays here, next to its `.done.md`, until the session is closed |
| `beach/replies/<order-name>/` | everything the agent writes for that order: `<order-name>.ack.md`, `<order-name>.done.md` and every output file |
| `beach/archive/<YYYY-MM-DD>/` | finished orders, each with its `replies/<order-name>/` folder |

## The order header

Every order opens with a YAML front matter of five fields, in this order. The watcher reads only `assigned_to` (or, when an order has none, `agent`); the others say where the order comes from.

| Field | What it holds |
|---|---|
| `order` | the order's file name without `.md`: `YYYYMMDD-HHMM-<slug>` |
| `assigned_to` | the agent that does the work, the `agent` of its machine's `.nereus-agent` (for example `m15`); `agent:` is read the same way when an order has no `assigned_to:` (the owner, 2026-10-26); never `assignee:` |
| `initiator` | who asked for it: `human:<first-name>` or `agent:<name>` |
| `requested_via` | the channel it came through, for example `voice conversation (claude.ai), coordinator Claude` |
| `created_at` | when it was written, ISO 8601 with the offset: `2026-10-26T19:24-03:00` |

A complete order:

```markdown
---
order: 20261026-1924-watcher-flags-unassigned-orders
assigned_to: m15
initiator: human:maria
requested_via: voice conversation (claude.ai), coordinator Claude
created_at: 2026-10-26T19:24-03:00
---

# Order 20261026-1924 - The beach watcher flags orders it cannot assign

Context: one paragraph on why.

## What to build
- ...

## Rules
- ...

## Reply
- Done file in replies/ with issue/PR links and the merge commit.
```

While the watcher knows only its own agent (no other in `agents=`, as long as m15 is the only one), an order whose `assigned_to` is missing or empty, with no likely typo of it in the header, is that agent's by default (the owner, 2026-10-28): `claim.json` and the ack say `assigned_by: default`, and `explicit` when `assigned_to` names the agent.

Otherwise an order whose `assigned_to` is missing, empty or names an agent the watcher does not know is never claimed: the watcher writes `replies/<order-name>/unassigned.md` once, saying what is wrong, which agents it knows, and asking "did you mean `assigned_to:`?" for a likely typo (`agent:`, `assignee:`, `assigned-to:`). Fix the header and the watcher picks the order up on its next poll.

## The protocol

- When the owner says "manda jangada" ("send it by raft"), the voice session writes one self-contained work order, in English, to `beach/`: a jangada (raft) is one order, the boat Glaucus sails.
- The local agent lists the folder with `rclone lsf` and reads with `rclone cat`, or copies it with `rclone copy` (the FUSE mount is slow). A pending order is a `*.md` in `beach/` without `replies/<order-name>/<order-name>.ack.md`.
- On pickup, write `replies/<order-name>/<order-name>.ack.md`: a timestamp and a one-line understanding. Then do the work in this repository.
- When finished, write `replies/<order-name>/<order-name>.done.md`: a summary, commit hashes, links to PRs and issues, open questions. Never edit the original order.
- A cancelled order gets `replies/<order-name>/<order-name>.cancelled.md`, naming the order that superseded it.
- Open questions go into the reply; the agent does not decide them.
- An ambiguous or risky order (destroying resources, secrets, pushing to `main`) stops at the ack, with the questions written in it.
- An order may say to wait for the owner's go; then it waits, even when it is the next one in the folder.
- Only when the owner says "close the session" ("fecha a sessão"), move each finished order and its `replies/<order-name>/` folder to `beach/archive/<YYYY-MM-DD>/`.

## The watcher

`scripts/beach/watch` picks up the orders for the agent of its machine. It reads its settings from `.nereus-agent` (git-ignored): the agent's name (for example `m15`), the Drive owner whose orders it trusts, and the intervals.

It polls the beach with rclone every 15 seconds, or every 60 while a run is active. It skips any file another owner wrote, writes `claim.json` first, and starts `claude -p` with bypass permissions on each new order whose `assigned_to:` names it; an order it cannot assign gets `unassigned.md` instead ([The order header](#the-order-header)). Addenda go to the agent holding the claim.

How to set it up and run it: [`scripts/beach/README.md`](https://github.com/getnereus/nereus/blob/main/scripts/beach/README.md). It is a stand-in for an event bus on Nereus.

## The evaluation of an order

Every reply to an order ends with these two blocks, filled by the agent, and the agent records the row with `scripts/metrics/order record` (#803), in `getnereus/internal`, `metrics/orders/<year>-W<week>.csv`.

Never ask the owner for a rating: it did not help (owner, 2026-11-03). The row keeps its rating empty, unless the owner gives one unasked, which goes in with `scripts/metrics/order rate`. Asking for a rating where a command is used is a separate idea, #885.

```text
## Evaluation
- Performance: start -> PR opened (time), PR -> merge (time), review rounds, smoke test / nereus doctor passed (yes/no)
- Cost: tokens and estimated cost, per agent (source/tool used)
## Session metrics
- Duration (start -> end), active vs idle
- Orders sent / done / blocked
- Tokens and estimated cost (tool/source)
- Interruptions / rework (times the plan changed or a detail had to be repeated)
```
