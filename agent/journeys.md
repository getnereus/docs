# Journeys

The owner's working agreement of 2026-11-14: to cut the owner's load of deciding across several anchored sessions, each session owns a **journey**, a clear goal it carries end to end inside a **decision envelope** agreed at the start. The first pilot is #1559 (the continuous deploy of Nereus on Nereus).

## What a journey is

- **A parent issue with the `journey` label**; its sub-issues are the steps, in order. An existing issue that already has another parent is named in the body instead (GitHub allows one parent per issue).
- **One owner:** the session of one tmux window, named in a comment on the parent issue ("Owner session: <name>"). Another session that touches a step asks the owner session first (`docs/agent/peers.md`).
- **At most about three active journeys:** a soft limit; `queue doctor` warns above it, never refuses (#1566).

## The decision envelope

Written in the parent issue when the journey opens, agreed with the owner:

- 🟢 **Decide and record:** what the session decides alone and writes down (scripts, tests, dry runs, the merge of what passed `make checks`).
- 🟠 **Decide and report in a batch:** what the session decides and reports in one summary; the owner's silence accepts it (thresholds, new sub-issues, pages of `docs/agent/`).
- 🔴 **Wait for the owner:** the one-way doors (a first real publish, a change to `k3d-nereus`, an ADR, anything irreversible); the session asks and waits.

A delegation of something the owner does by hand (#1559's click on ghcr.io) goes in the envelope with its limits and the event that ends it.

## Where a journey stands

When a session works on a journey, it opens with one line of the journey's progress, in pt-BR, e.g. "2/7 (28,6%) da jornada #1890 (os agentes de duas pessoas do time, em máquinas diferentes, se encontram numa sala do Triton)" (owner, 2026-11-18, #1916).

The count comes from `scripts/board/queue journey <n>` (the closed sub-issues over all of them), never from the agent's own count; the agent writes only the description. The detail per issue comes only when the owner asks for it.

## Measuring it

Whether journeys cut the owner's decisions is measured by a script, never by an agent remembering: the 🔴 items asked and answered, the 🟠 items reported, how long a 🔴 waited, the steps closed, sent through `nereus metrics send journeys` (ADR 0025, #1566). The owner sees the open items and each journey's progress on the portal's decisions inbox (#1563).

## Where it comes from

One-way and two-way doors (Jeff Bezos, Amazon's 2015 letter to shareholders); Delegation Poker's levels between "tell" and "delegate" (Jurgen Appelo, Management 3.0); limiting work in progress (Kanban).
