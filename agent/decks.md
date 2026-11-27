# Decks

The rules for an agent that makes a deck or an HTML page for Nereus. They come from the deck engine of the first proof of concept (beach order 20261026-0030, its section 4), with the owner's decisions of 2026-10-26 (order 20261026-0035) where they differ.

The decks of the repository are rendered by `docs/presentations/render-outline` from an outline YAML (`docs/presentations/README.md`); a one-off page or companion screen follows the same rules. The CLI's specs are decks too, one per Reef in `docs/specs/cli/` ([The CLI design](cli.md), #477).

## Before writing

1. **Gather the content first:** what to show, to whom, for how long, and which commands. Ask one question at a time.
2. **Write the script before the slides:** one line per moment. Show it, adjust it with the person, then build.
3. **Start from the engine, never from scratch.** A deck is an outline rendered by `render-outline`: the CSS and the script are the same in every deck, so whoever learns one deck knows them all. A one-off page copies the page template of the engine and changes only the content.
4. **Plan from the commands:** when a feature is involved, write the commands a person types and what they print before anything else.

## The file

1. **One self-contained HTML file:** CSS and scripts inline, system fonts, no external script, stylesheet, font or image. It opens from disk, from an attachment and on a phone. The portal takes the same deck rendered with `--split` (an HTML, `deck.css` and `deck.js`), since its policy refuses inline code (#1693); so no style attribute, event-handler attribute or `eval` goes into a deck: the script styles through the CSSOM.
2. **A title of two to four words** in `<title>`, a name and not a sentence.
3. **Colours only as tokens on `:root`**, with both themes and the manual toggle: the natural theme on `:root` (dark for a deck, light for a page), the other under `prefers-color-scheme` guarded by `:not([data-theme])`, and again under `[data-theme]`; an explicit `body` background. The terminal is the one exception: always dark.
4. **Phone first:** 16px gutters, no horizontal page scroll, touch targets of 44px, then check it on a computer.
5. **Storage is a convenience:** wrap every `localStorage` call in `try/catch` and render correctly without it.
6. **Respect reduced motion:** turn off blinking, typing rises and pops under `prefers-reduced-motion`.

## Content

1. **One moment per slide.** A terminal of more than about 12 output lines, or one that mixes two moments, becomes two slides.
2. **A list stays on one slide while it fits.** A list that does not fit continues on the next slide, repeats the message, and numbers the parts in the label (`The model · Vocabulary · 1/2`); `render-outline` splits a `screen` this way, estimating the height on a phone, the tightest screen. A diagram is measured by its `viewBox`, drawn on the last part, with the items that fit beside it (#1458); a slide with a terminal or a code frame keeps at most two items, since its height is not known from the text.
3. **Each slide has** a label ("Part · topic"), a message of one sentence, **at most 60 characters** and with **no full stop** (`?` and `!` stay) and at most one accent in amber (`accent` in the outline), an optional subtitle, which appears after the title as its own step and never with it, and the content. On a slide, Reef, Nereid and Mandate are capitalized and carry their color (`{reef:Reef}`); a command, a path and a terminal's output keep them literal. The subtitle and the items add to the message, never repeat it. A message with two parts splits: the second part becomes the subtitle, or goes when the items already say it; `;` or `:` in a message with no subtitle is the sign.
4. **Every acronym carries its meaning** the first time it appears. URLs and values are written in full, never cut with "…".
5. **One discreet colour per concept,** kept from the first slide to the last, in the slide text, the terminals and the cards, only on the concept's own name: Reef `#1D9E75` (teal), Nereid `#7F77DD` (purple), Mandate `#D85A30` (coral), secret `#BA7517` (amber). In an outline: `{reef:environment}`, `{nereid:vcluster}`, `{mandate:vcluster}`, `{secret:...}`. The roles of the work have theirs too: order `#BA7517`, PR `#1D9E75`, agent `#7F77DD`, raw data `#9aa0a6` (`#6b7280` in light), human `#D85A30`, handoff `#4FA3D9`: `{order:...}`, `{pr:...}`, `{agent:...}`, `{raw:...}`, `{human:...}`, `{handoff:...}` (#1458).
6. **Notes say what to speak,** with the first sentence of each paragraph in bold; external references go as links.
7. **Credit the sources:** a deck ends with the references its ideas came from (the talk, book or tool, and who created it). The deck style follows "How to avoid death by PowerPoint" by David JP Phillips.
8. **Show, don't fill:** fewer colours, fewer words, consistent sizes. Less is more.
9. **Every list item opens with a bold label:** `**Label:** short phrase`, and the details go to the notes.

## Commands on screen

1. **Always as a terminal** with the fixed palette (`docs/agent/owner.md`), a comment line before each command and a blank line between commands; a Reef, Nereid or Mandate takes its concept colour there too.
2. **A toolbar folded behind `⋯`** in the terminal's title bar (#2361): a tap shows copy (the whole terminal as shown, its comments, prompts and output), A−/A+ and narrow/widen, as small icons; they fold back on a tap outside, Esc, a slide change or 4 s with no tap. The font and the width are one setting for every terminal of the deck, kept on the device per deck (owner, 2026-11-27); an open toolbar on a narrow terminal hides the window title, then the dots, so it never needs the phone turned sideways.
3. **The commands of the CLI design** (`docs/agent/cli.md`, ADR 0013, command conventions): `nereus <group> <verb> <name>`, with the verbs `create`, `apply`, `delete`, `get` and `list`; never `add`. Full names only.
4. **Long options only, one per line:** the command stays on the first line ending in `\`, each option with its value on its own line, indented 2 spaces from where `nereus` starts (4 with `$ `). A terminal never scrolls sideways: long output lines wrap.
5. **Output reads `kind/name verb`** in kubectl's words (`core/reefs/environment created`, `configured`, `unchanged`, `deleted`), success in green with `✓`, and the `Next steps:` label with a blank line before and after, then the next commands indented two spaces; not the engine's yellow "next:" hint.
6. **Examples use today's model:** the Reef `environment`, its `vcluster` Nereid and its Mandate, on the local k3d. A command that does not exist yet is shown as its contract, and the notes say so.
7. **Messages are polite and actionable:** what happened, who decided and what to do next; never a generic error (ADR 0012, error messages).

## Language and neutrality

1. **Decks are bilingual,** English first and Portuguese second, every slide in both (`pt:` in the outline; `render-outline` refuses a slide without it). A terminal, a code frame or a diagram whose text changes with the language has its Portuguese version in `pt:` too (`pt.terminal`, `pt.code`, `pt.diagram`, with the same parts), checked like the English one; without it, both languages share one (#1457). A page is in English unless asked otherwise.
2. **No real names:** no company, client, person, account or tenant. Use `example.com`, `maria@example.com`, `123456789012` (`docs/agent/rules.md`).
3. **No secrets or personal data** in a file meant to be shared.
4. **Search before delivering** for names that should not leak (the old product name, company names, people), and remove them.

## Pages that browse data

The owner's feedback on Tide v4 (2026-10-30), read on a phone: a page that lets a person explore many items (notes, ideas, events) follows these rules too.

1. **The viewport meta lives in the file:** `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`. A hosted page gets one from its host, but the same file downloaded and opened in a phone browser renders at desktop width without it.
2. **The content travels inside the page:** the in-app file viewer blocks external links, so the item's own text is embedded (capped, with a note that the rest is at the source), and the link to the source stays as a link plus a copy button that falls back to selectable text.
3. **Markdown is rendered, never shown as source,** and the reading view has A− and A+ (12 to 26 px), remembered in `localStorage`. The renderer (marked) is inlined in the file, checked against its published hash, never loaded from a CDN.
4. **Filters fold behind one button** that says how many are active; the search stays visible, so the items show on the first screen. The chips follow the search and the other filters: each one counts only the matching items, and a chip with no match disappears unless it is on.
5. **A group with no match disappears** (a day with no matching note), with a short message when nothing matches; the summary chart keeps every group and shows `matches/total`, and each group's heading says `shown of total`.
6. **The selected item and its relations are all that stays:** a tap hides every item with no link to the selected one (cites, cited by, close in topic), groups left empty disappear, the count says how many are related, and the selected item stays in view; clearing the selection brings everything back without losing the place.
7. **Navigation follows real links:** the links between items come from a script (the notes' own citations, "file 150", file names), not from shared tags. The first tap draws the thread (cites, cited by, a few close in topic); the second opens the item, which lists the thread to walk and has earlier and later buttons.
8. **Tags are normalized by a script** (case, plural folded into the singular) before they become filters.
9. **A timeline, not a grid:** on a phone, many items read as a vertical timeline, one row per item (44 px, a touch target), in time order under each group's heading, with the title and a meta line (time, types) beside the mark; a grid of small dots is too dense to read or tap. The marks encode measures, as in a data poster: the length of a dashed stem from the axis is how many items it builds on (its citations followed back), the number in its circle is how many items cite it, and its colours are its types. Links are arcs in the margin beside the axis.
10. **A thread can be replayed,** as in `docs/presentations/doris-demo.html`: the selected item has a "▶ Replay · N" button that rebuilds its thread (every item it comes from and every item that comes from it) one item at a time, in time order, about 1.3 s each, lighting the new item and drawing its new link while the rest stays faded. While it plays, its bar folds into a ball in a corner (a ring of progress and `k/N`); a tap pauses and unfolds it (resume, open, close), and the end offers "again". A tap elsewhere, a filter or Esc stops it; leaving the tab pauses it.
11. **The header is a title and a subtitle, nothing more:** the name, with the version small and aligned to the top of the line (`Tide v4`), and a subtitle of a few words (`Ideas ebb and flow`). Where the data came from goes to the notes or the delivery message, not above the content.
12. **The legend sits in a box** like the chart's: the colours first, then, below a rule, a sample of each encoding (a dashed stem, a numbered circle) with what it means.
13. **A link to an item off screen keeps its reference:** when a replay step links to an item above or below the viewport, a bar slides in at the top for about 2 s with an arrow (↑ or ↓), the item's mark (its colours and number), its title and its date and time, at most two items at once; it goes away when the replay stops.

## Screens on a phone

The owner's feedback on the speaker's screen of the presentations Reef (#1712, 2026-11-18, a Galaxy S23 Ultra): every screen a person uses from a phone (a deck, the portal's screens, a companion page) follows these rules.

1. **The top center is under the front camera:** a phone's punch-hole hides what sits there, so live information (a clock, a pace, a status) goes to the bottom bar, beside the controls, never to the top center. The speaker's clock line lost its tail, the pace, until it moved to the deck engine's bottom bar.
2. **Check both languages, measured:** English words are longer than Portuguese ones (Audience, Projector, Presentation against Plateia, Projetor, Apresentação), and a row that fit in one language ran past the screen's edge in the other. Check every row of controls in both languages at 340, 360, 390 and 412 px, and measure it (each control's right edge inside its bar, no horizontal scroll, no text cut), not only by eye in one screenshot.
3. **Controls share the row and shrink:** a row of controls gives each one `flex: 0 1 auto; min-width: 0`, so the longest words never push the last one out; on a phone the primary control drops its icon first, since its fill already marks it.
4. **A short mark, the sentence behind it:** on a phone a status is a short coloured mark (`+0:40` amber behind, `−0:40` green ahead, `±0` even), and the whole sentence is its `title` and `aria-label`, for a screen reader and a desktop's hover.
5. **The portal's language is the person's choice:** the words of a widget inside a page (the clock, its labels) follow the language the person chose in the portal, never the language of the content it frames (owner, 2026-11-18, "Não força o idioma").
6. **Try it with data that means something:** a measure checked on data made for something else is right but meaningless (a pace against a rehearsal skipped through in 50 s, a talk whose clock started half an hour before). Give the owner a small fixture made for the try (`pace-check`, a five-slide deck of about two minutes, then a fresh rehearsal and a fresh talk), and explain a new measure in one line when showing it.

## Check and deliver

1. **Render:** `make decks` re-renders every deck (the CLI reference, the walkthrough decks and the presentations), opens none and stops at the first that fails: run it after a change that crosses the docs, like a rename (#1962). `make deck OUTLINE=<name>` renders one presentation and opens it, for looking at it.
2. **Validate:** `make deck-test` (the outline's validation, the terminal format, both languages, a fresh render equal to the committed deck); every `<script>` parses (`node --check`); every step, ⏎, A−/A+, button of the bar and of the navigation pad, and key works.
3. **Look at it:** render it at phone width and at desktop width, in both themes and both languages, and check that every box fits its text (the measures of [Screens on a phone](#screens-on-a-phone)).
4. **Deliver to where the person is:** when they follow from a phone, send the file through the session, never a `localhost` link.
5. **Files to send keep their original:** when you convert something (a GIF, a PDF), keep the source next to it.
6. **One question per screen** when the page is used to decide: the recommended option first, its context, the options, and a "back" button; the chat only says the screen is up.
7. **Before finishing,** show a few lines of what you are delivering, and say plainly what was checked and what was not.
