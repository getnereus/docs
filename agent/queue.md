# The queue

- **The board is the queue:** Project v2 #1 of `getnereus` (`https://github.com/orgs/getnereus/projects/1`), top first. The next task (`/next`) is one of your own `In Progress` items, else the top of `Todo` nobody holds; never an item assigned to someone else. `Todo` holds only what can start now; the rest waits in `Backlog`. Ideas (`Refine` issues) and agents' proposals wait in `Ideas`, out of the order, until the owner's triage moves one to `Backlog`; `/next` never takes from `Ideas`. There is no `HANDOFF.md`.
- **`board-queue`** (global, smsilva/linux#203, configured by `.claude/next.md`) is what `/next` runs: `next [--filter Track=<t>] [--filter Theme=<t>] [--new]`, `claim`, `release`, `mine`, `team`, `list`, `status`, `move`, `doctor`. Its `claim` also triggers the room's `[claim]` (`.claude/hooks/room-announce`).
- **`scripts/board/queue`:** `next [--track] [--theme]`, `claim` (refuses an item someone else holds or with an open dependency), `release`, `mine`, `team`, `milestone`, `journey <n>`, `doctor`, `list [--status]`, `metrics [--weeks <n>]`, `move <n> --top | --after <m>`, `status <n> <status>`. Needs a `gh` token with the `project` scope.
- **Milestones hold the golden path's order, under three rules** (owner, 2026-11-03, #915):
  1. A milestone closes only when the scene in its `Done when` passes, not when its issues end.
  2. A new gap becomes an issue, and joins a milestone only on the owner's word.
  3. Only the current milestone's issues are in `Todo`, in order of execution; the later ones wait in `Backlog`. The current milestone is the open one with the lowest number. An issue with no milestone may be in `Todo`.
- **`queue milestone` shows each open milestone's progress, and `queue doctor` checks what a script can:** a later milestone's issue in `Todo`, and a description that does not start with `Done when`.

  ```console
  $ scripts/board/queue milestone
  MILESTONE              DONE  OPEN  TODO  IN PROGRESS  BACKLOG
  IDP 1: Deploy             5    10     9            1        0
  IDP 2: Build              0     3     0            0        3
  IDP 3: CI and install     0     4     0            0        4
  ```

- **An issue with an open dependency waits** (owner, 2026-11-03, #915): `next` skips it; `claim` and `status <n> "In Progress"` refuse it.

  ```console
  $ scripts/board/queue claim 846
  #846 depends on #845, #853, still open
  ```

  A dependency is a `#n` in the list right after `Depends on` in the body (`scripts/board/dependencies.jq`), or an open issue in GitHub's native `blockedBy`. Prose never blocks, nor does a number in parentheses, a code block, a closed issue or the issue's own parent. To correct a wrong dependency, edit the issue's line.
- **`queue metrics` measures the flow from `Backlog` on, so ideas stay free** (#813): registering an idea changes no figure; it counts once it leaves `Ideas`. Per ISO week (UTC), from the `Status` history in the issue timeline:
  - **Arrived:** the issue's first `Status` after its last move to `Ideas`, since the board adds every new issue in `Backlog` and triage moves an idea to `Ideas` seconds later; a return to `Backlog` from a later column does not count again. Closed straight from `Ideas`, it never arrived. An older issue's first recorded change stands in for its arrival, and with no history at all it arrived at `createdAt`, unless it is still in `Ideas` or has no status.
  - **Completed:** closed as completed in that week, among the issues that arrived. Not planned and duplicate closures are left out.
  - **Net:** arrived minus completed.
  - **Backlog age:** for each open issue in `Backlog`, the days since its latest entry to that column: p50, p85 and the oldest, never averages.
  - The calculation is `scripts/board/metrics.jq`, tested with fixtures in `scripts/board/tests/`.
- **Board ids** (for `gh project item-edit`): project `PVT_kwDOFAuFDM4BnccI`.
  - `Status` `PVTSSF_lADOFAuFDM4BnccIzhmBCzY`: `Ideas` `ffb2ebf8`, `Backlog` `7bb2c7ea`, `Todo` `eed7cbe2`, `In Progress` `45af3f21`, `Done` `050281cc`.
  - `Track` `PVTSSF_lADOFAuFDM4BnccIzhmBC8A`: `Platform` `df08a980`, `Docs` `a1ad169c`.
  - `Theme` `PVTSSF_lADOFAuFDM4BnccIzhmBC9U`: `Workflow & Tooling` `4409c391`, `First slice` `ccba8c7a`, `Controllers` `1b157991`, `Security` `40d2b056`, `Public release` `f70adc90`.
- **Opening an issue follows the `issue` skill:** search first, one issue per deliverable, sub-issues under a shared goal, a type (`Feature`, `Bug`, `Idea`, `Proposal`, `Decision`, `Docs`, `Task`) and labels on creation (`enhancement`/`bug`/`documentation`, one `area: <name>` per part, `mvp`, `proposed-by-agent`, `dogfood` on a feature that retires a stand-in, one `reef`, `nereid` or `mandate` per piece of the model it delivers or refines), `Track` and `Theme` set, placed in the order. Each issue carries every detail an agent needs to deliver it alone (the Definition of Ready, #25): context, decisions with who took them, dependencies, checked facts stated directly, a checkable "Done when".
- **Classified by the model** (owner, 2026-10-29): `reef`, `nereid` and `mandate` say which piece of the model (ADR 0002, ADR 0011) an issue delivers or refines, so `gh issue list --label nereid` lists every Nereid planned or built. An issue may carry more than one (#470 (the edge reef with a cloudflare Nereid) carries `reef` and `nereid`); `area: <name>` still says which part of the repository it touches.
- **Agents' proposals** keep `proposed-by-agent` and wait for the owner's triage: `triage/accepted` or closed as `not planned`; `/next` never takes one without `triage/accepted`.
- **Agents propose the state of the art, the owner decides** (#332): a technique, practice or study that could improve the product, the code or the process becomes a `Proposal` issue with `proposed-by-agent` (named, credited, linked, its evidence, where it applies, a recommendation); an agent never adopts it on its own.
- **Before stopping mid-task, leave a handoff comment** on the issue: last step, next step, open decision.
- **`Closes #n` in English.** When an issue closes, move the next one to `Todo`.
- **Skills grow with use:** when a request asks for something a skill in `.claude/skills/` does not produce, ask whether to update it, in the same session.
- **A cloud session cannot** reach the board (GraphQL is blocked) or delete branches; the owner runs `scripts/board/queue` locally.
