# 0001. Record architecture decisions

!!! note "In short"
    Every architecture decision is recorded in `docs/adr/`, one file per decision in Nygard's format. A number is valid only once its ADR is merged into `main`. Status: Accepted (2026-10-17, rewritten 2026-10-25).

**Status:** Accepted (2026-10-17, rewritten 2026-10-25)

## Context

The project starts from ideas worked out in conversation: a model of layers, how Controllers are installed and how they extend the CLI. Without a record, each decision gets argued again, and someone reading the code later cannot tell a rule from an accident.

## Decision

Record every architecture decision in `docs/adr/`, in the format of Michael Nygard: Title, Status, Context, Decision, Consequences. One file per decision, named `NNNN-short-title.md`.

- Status is `Proposed`, `Accepted`, `Superseded by NNNN` or `Rejected`.
- **A number is valid only once its ADR is merged into `main`.** A draft in a branch, a pull request or a work order carries no number: it is named by its title, and takes the next free number when it is merged. Two drafts never claim the same number, and a dropped draft leaves no hole.
- **Until the first release (v1.0.0)**, an ADR may be rewritten in place when its decision changes: the number stays, the file may be renamed to the new words, and a line at the end says `*Rewritten <date> ...*`. The history keeps the old text.
- **From v1.0.0 on**, an accepted ADR is not edited, except to change its status. A changed decision is a new ADR that supersedes the old one.
- An ADR states what was decided and why. Open questions are listed as such, never presented as decided.

## Prior art

*Editorial addition (#332): credits only; the Context, Decision and Consequences are unchanged.*

- **Michael Nygard, "Documenting Architecture Decisions" (2011)** ([Cognitect blog](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)): the format this ADR adopts (Title, Status, Context, Decision, Consequences), one short file per decision, numbered and kept with the code, and a superseded decision kept rather than erased.
- **Architecture decision records, the community's hub** ([adr.github.io](https://adr.github.io/)): templates, tools and the other formats that grew from Nygard's.
- **Thoughtworks Technology Radar, "Lightweight Architecture Decision Records"** ([thoughtworks.com](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)): ADRs kept in the repository next to the code, rather than in a wiki.

## Consequences

- The ADRs are the place to learn the rules. `CLAUDE.md` summarises them and points here.
- A pull request that adds an ADR checks the next free number against `main` right before it is merged, and renames the file and its links when another ADR took that number first.
- Before v1.0.0 an ADR always says what is decided now, at the cost of reading `git log` to learn what it said before.

*Rewritten 2026-10-25 from voice session (order 20261025-1724): ADRs may be rewritten in place until v1.0.0; raw data in Drive #pontos/raw/2026-10-25.*

*Rewritten 2026-10-26 from order 20261026-0508 (divergence 2 of the idea timeline of 2026-10-25): a number is valid only once the ADR is merged; raw data in Drive #pontos/raw/2026-10-25.*
