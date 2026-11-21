# Docs

The style guide of the docs site (`make docs`), from the docs restructure (#1985): one information architecture, one format per page type, one identity, AI affordances and a phone reader mode. `scripts/docs/lint` enforces every rule below that a script can check; the rest is judgement.

## The six tabs

| Tab | Directory | Page type | Reader |
|---|---|---|---|
| Home | `docs/index.md` | `landing` | everyone |
| Start | `docs/start/` | `tutorial` | evaluator |
| Concepts | `docs/concepts/` | `concept` | evaluator, author |
| Guides | `docs/guides/<topic>/` | `howto`, `troubleshoot` | operator, author |
| Reference | `docs/reference/` | `reference` | operator, author, AI agent |
| Project | `docs/project/`, `docs/adr/`, `docs/specs/`, `docs/research/`, `docs/agent/`... | its own form | contributor |

A new page goes to the tab of its reader, never to a flat list; an old page rewritten into the tabs is deleted in the same change, with its line in `scripts/docs/moves.yaml` and `scripts/docs/relink`.

## Front matter

Every page of `docs/index.md`, `docs/start/`, `docs/concepts/`, `docs/guides/`, `docs/reference/` and `docs/project/` opens with:

```yaml
---
type: howto            # landing | tutorial | concept | howto | troubleshoot | reference
goal: Keep a secret in the installation and read it from a Nereid   # at most 120 characters, no Markdown
audience: [operator]   # any of evaluator, operator, author, contributor
status: built          # built | planned | idea | stub
issue: 1234            # required when status is planned or stub: the issue that builds or writes it
proof: scene           # required on tutorial, howto and troubleshoot: the test whose run prints the outputs shown (a test/ scene or a test file's path), or none
---
```

`goal` feeds `llms.txt`, the prompts and the search; write it as the reader's goal ("Install the CLI"), not as the page's subject. `proof: none` means no scene runs those outputs: the page goes to the list of #1984 for a scene run on the owner's word.

A `stub` page holds the front matter, its H1 and one line, `Being written in #<issue>.`; the lint skips its template, and `scripts/docs/lint --no-stubs` (the final check of #1984) fails on any stub left.

## Templates

H1 once, `##` for the blocks below, in this order, with these exact names; `###` only inside Steps or Fix; no `####`. Words count prose only: code blocks, tables, front matter and headings are not counted.

| Type | H1 | `##` blocks, in order (optional in italics) | Caps |
|---|---|---|---|
| `tutorial` | a verb: "Install the CLI" | Run, What you get, Next | 250 words, at most 3 commands |
| `howto` | the goal: "Keep a secret" | Before you start, Steps, Check it worked, *Clean up*, Next, *Learn more* | 600 words, at most 7 steps (`###` in Steps) |
| `concept` | a noun: "Reef, Nereid and Mandate" | Example, *Overview*, How it works, Not this, Next | 400 words, at most 1 diagram, How it works at most 5 bullets |
| `troubleshoot` | the symptom as printed | You see, Why, Fix, Check | 200 words, Why at most 2 sentences |
| `reference` | the name: "Glossary" | free; one example per entry | paragraphs at most 40 words |
| `landing` | the product | free | 300 words |

Every page: the first paragraph under the H1 says the goal or the definition in one sentence; prose paragraphs at most 60 words (40 on `reference`); at most 2 callouts, each at most 40 words.

## Commands and outputs

A command is a ` ```bash ` block with one command (a `\` continuation counts as one); its output follows at once in a ` ``` { .text .output title="output" } ` block. Lines at most 80 characters.

A command exists in `docs/specs/cli/**/*.yaml` and its flags in `uv run --project cli nereus <command> --help`; link the first mention to its spec (`[nereus init](../../specs/cli/core.html#init)`). Outputs are real: printed by a command that needs no cluster, or kept from a page whose scene prints them (`proof:`). Never write an output by hand.

## Identity

- Graphite (owner, 2026-11-20): the page, header, tabs and footer in greys, links in the text color, underlined; the only color is inside a terminal (the prompt, option values, ✓ and ✗), on a neutral graphite panel. Color only through the tokens of `docs/stylesheets/extra.css` (`--doc-page`, `--doc-text`, `--doc-muted`, `--doc-rule`, `--doc-ink*` for the terminal, `--doc-warn` for a warning, the `--t-*` terminal ones); no raw hex outside `:root` and the scheme blocks; a token built from another goes in the `[data-md-color-scheme]` block.
- Inter for text, JetBrains Mono for code; the terminal look is `docs/javascripts/terminal.js`.
- Callouts: `!!! note`, `!!! warning` (something changes or is deleted), `!!! tip`; no other kind.
- Status: a chip only on what does not run yet, after the H1's first paragraph or a command link: `[planned #1234]`, `[idea]` (grey, told apart by a dashed or dotted border). What runs today carries no chip (owner, 2026-11-20): the front matter's `status` says it; the one exception is the Status column of `reference/what-is-built.md`. Never free text such as `· built` on a new page.
- Diagrams: an SVG drawn by `scripts/docs/diagrams` between the page's markers (`<!-- diagram:<name>:start -->`), a wide drawing and a narrow one for a phone, in the line of Red Hat's OpenShift diagrams (square boxes, grey zones, thin right-angle arrows), a caption line in italics right below; `make docs-diagrams` redraws them and `make docs-lint` fails on a stale one or on a ` ```mermaid ` block (#2021).
- Icons: Material outline icons on Home's cards only; no emoji in prose.
- Phone: tables at most 3 columns, no side-by-side layouts; a terminal runs edge to edge, square, as Material's own code blocks do. No `$ ` before a command.

## AI affordances

`scripts/docs/ai`, run at the end of every build, writes into `site/`: `<page>.md` beside every page (the source without front matter), `llms.txt` (one line per nav page, `[title](url.md): goal`, Project under `## Optional`), `llms-full.txt` (Start, Concepts, Guides, Reference in nav order) and `ai.json` (the prompts and each page's goal).

`docs/javascripts/ai.js` adds the row Copy page, Copy prompt, View as Markdown, and Open in Claude only when `site_url` is set (it is not while the repository is private); and an Ask AI button under each ` ```bash ` example (after its output), which copies a prompt about that example.

The prompts live only in `scripts/docs/prompts.yaml`; change the wording there, never in the JS.

## Reader mode

The Reader button (and `?reader=1`) sets `data-reader="on"` on `<html>`: header, tabs, sidebars, footer and the button row hide, the article fills the screen at 18px. `Esc` or the exit button leaves; the choice stays in `localStorage["nereus.reader"]`, and `?reader=0|1` wins over it, so a link can open a page in reader mode.

## Text size

A− and A+ at the end of the button row, and beside the exit button in reader mode, scale the article's text from 85% to 160% (`docs/javascripts/font.js`, owner, 2026-11-20); the choice stays in `localStorage["nereus.font"]` and is applied before the page is drawn.

## Writers of the restructure

Each package of #1985 writes and deletes only its file list, in its own worktree (`git worktree add ../nereus-<issue>-<pkg> -b docs/<issue>-<pkg> <base>`; `scripts/worktree/new` takes only `origin/main`), one commit per page (`docs(<section>): <goal>`), checks with `make docs-build` only.

A writer never edits `mkdocs.yml`, the CSS, the JS, `scripts/` or a page of another package: it says what it needs in its report. Deleting an old page and fixing the links to it is the orchestrator's, at integration, with `scripts/docs/relink` and the map `scripts/docs/moves.yaml`.
