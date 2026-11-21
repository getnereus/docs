# ADRs

ADR 0001 (record architecture decisions) is the rule; this page is the checklist.

- One file per decision: `docs/adr/NNNN-short-title.md`, the next free number on `main`, and its line in the `Decisions` section of `mkdocs.yml`.
- **A number is valid only once the ADR is merged** (ADR 0001): a draft in a branch, a PR or a work order is named by its title, never by a number. Right before the merge, check the next free number on `main` again, and rename the file and its links if another ADR took it.
- Nygard format: Title, Status, Context, Decision, `## Prior art` (credits, #332), Consequences.
- **Origin:** when and by whom the decision was taken, and the path of the raw file it came from (see [Raw data](raw-data.md)), without personal names.
- Status starts `Proposed`; only the owner moves it to `Accepted`.
- **Until v1.0.0**, a changed decision rewrites its ADR in place: keep the number, rename the file to the new words when they changed, fix every link, and end it with `*Rewritten <date> from <source>; raw data in <path>.*`. **From v1.0.0 on**, an accepted ADR is immutable: a changed decision is a new ADR that supersedes it.
- Open questions are listed as such, never presented as decided.
