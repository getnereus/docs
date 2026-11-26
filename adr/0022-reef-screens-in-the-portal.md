# 0022. A reef adds a screen to the portal as a Web Component its Nereid serves, named in its contract

!!! note "In short"
    A reef adds a screen to the portal as a Web Component its Nereid serves, named in its contract, loaded at runtime. Status: Accepted (2026-11-08).

**Status:** Accepted (2026-11-08)

## Context

The portal (spec 0008, #729) is a PWA with no build and no framework: `static/index.html`, `app.js` and `app.css`, served by the `nereus-portal` Nereid on port 8081. It forwards `/v1/*` to the Nereus API (ADR 0018, the one door) and sends a Content Security Policy of `default-src 'self'`, `connect-src 'self' <issuer origin>` and `frame-ancestors 'none'`. Reefs and their Nereids extend the CLI with their own commands (ADR 0004), and reefs are installed at runtime (ADR 0010); the portal has no such extension point, and #46 asks that "a new Controller adds screens without a portal release".

The owner asked on 2026-11-06 "microfrontends? Module? How?" (#1102, Tide in the portal; this is its step 1, #1103). Tide, the idea timeline, is the first screen that belongs to a reef that is not the portal: the `ideas` reef. The tabs already planned as portal features (#740 status, #750 orders, #777 threads) show the platform's own state, not a reef's.

The Nereid's contract today is `GET /` on its controller port (8080, inside the cluster only), an object such as `{"name": "nereus-portal", "commands": []}`. Errors follow ADR 0012: what happened, the cause, how to check, how to fix, in one line per field.

## Decision

**A reef adds a screen to the portal as a Web Component its Nereid serves.** The options weighed:

| Option | What it is | Fits | Against |
|---|---|---|---|
| Module of the portal | One more tab in `controllers/nereus-portal/static/` | The fastest first slice | Every capability needs a portal release; the portal grows to know every reef, the opposite of ADR 0004, ADR 0010 and #46 |
| **Microfrontend at runtime, Web Components** | The reef's Nereid serves an ES module that defines a custom element; its contract names it; the portal loads it when the reef is installed | Mirrors ADR 0004 for the portal; no build and no framework, like the portal; same origin, so the CSP stays `'self'` | A small contract to design and keep stable |
| Module Federation | Webpack or Rspack federated bundles | Mature for big SPA teams | Needs a build and a shared runtime; the portal has neither |
| single-spa | A root config that mounts apps | Framework-agnostic | A second router and lifecycle on top of a 200-line app |
| iframe | The Nereid serves a whole page, framed | Strong isolation | Breaks the PWA's theme, language and sign-in; `frame-ancestors 'none'` today |
| Backstage plugin | The `wasp-idp` path (#30) | Ecosystem | A Backstage instance the portal does not have |

**The contract gains a `screens` list**, versioned by a `contractVersion` field (an integer, `1` with this ADR; a Nereid with no `contractVersion` serves no screen). Each entry has exactly these fields; an unknown field makes the entry ignored, never half-loaded:

```json
{
  "name": "doris",
  "commands": [],
  "contractVersion": 1,
  "screens": [
    {"tab": "Tide", "element": "nereus-tide", "module": "tide.js", "icon": "waves"}
  ],
  "assets": ["tide.css"],
  "uiPort": 8082
}
```

- `tab`: the label of the tab. `element`: the custom element's tag name, which must start with `nereus-` and contain a hyphen. `module`: a file name of the Nereid's `ui/` folder, no slash and no dot segment, ending in `.js`. `icon`: the name of an icon the portal already has, else the reef's own icon (below), else a default.
- The portal's Nereid reads the screens from each Nereid's `status.screens` (the SDK copies the contract's list there, so the cluster holds one list and the API reads what Nereids publish, ADR 0018), and the portal asks the API for them (`GET /v1/screens`, built in #1105). A tab shows only while its reef is installed.

**The portal's Nereid forwards `/reefs/<reef>/ui/<file>`, not the API** (the open point of #1103, decided as recommended). The forward serves static files only, from an allow-list built from the contracts: `GET` only, a file that some `screens` entry names (`module`) or that sits in the Nereid's `ui/` folder and is listed by the same contract in `assets` (an optional list of file names, such as a stylesheet or an icon), no query, no dot segment, backslash or percent-encoded slash (the check `/v1` already has). It forwards to the reef's Nereid on its controller port, `GET /ui/<file>`, which answers only files it listed in the contract; anything else is 404. A Nereid may serve `ui/` on a port of its own instead, named by the contract's optional `uiPort` (an integer from 1024 to 65535, copied to its status like `screens`; #1108), so a NetworkPolicy opens that port to the portal's pods without opening the Nereid's data, since it holds a port, not a path; the forward then targets that port. Same origin, so the CSP stays `'self'` and no header is relaxed. The API does not carry code: it carries data.

**The element's interface.** The portal creates the element with `document.createElement(element)` after `import("/reefs/<reef>/ui/<module>")` and sets, as properties and never as globals:

- `api`: an object with `get(path)`, `post(path, body)` and `delete(path)`, each a `fetch` bound to `/v1` with the person's token; the token itself is never given. A path outside `/v1` is refused.
- `lang`: `pt-BR` or `en`, set again when the person switches the language.
- The theme as CSS custom properties the portal defines on `:root` (`--nereus-bg`, `--nereus-fg`, `--nereus-muted`, `--nereus-accent`, `--nereus-border`, `--nereus-radius`, `--nereus-font`), which cross the shadow boundary; the palette follows `prefers-color-scheme` as the portal's does.
- The element owns its **shadow DOM** (mode `open`) and its styles; the portal's CSS does not reach it.
- The element reads and writes data **only through `/v1`** (ADR 0018), never from the screen to the Nereid directly: `connect-src` has no other origin, so the browser enforces it.
- It dispatches `nereus-error` (a `CustomEvent` whose `detail` has the ADR 0012 fields `message`, `cause`, `check` and `fix`) when it cannot work, and the portal shows that line in the tab. It sets no title, route or history of its own.
- It may dispatch `nereus-focus` (a `CustomEvent` whose `detail.focused` is `true` or `false`) when it shows one item and when it goes back to its list (#1761): while focused, the portal hides its mark, its language switch and its tab bar, and the screen takes the whole view, as a phone app hides its tabs inside a detail.
- It may dispatch `nereus-signin` (a `CustomEvent` whose `detail.resume` is a small JSON value, at most 1 KB) when a call still answers 401 after the portal's renewal, the sign-in having ended (#1910): the portal signs in again by a full redirect and, back, opens that screen at once and sets its `resume` property to that value before `api`, so the screen reopens where it was.

**Each reef has its own icon** (#1773, amended 2026-11-24): its Nereid's image declares it in the label `<API_GROUP>/icon`, next to `/reef`, `/requires` and `/nereid`, as the name of an icon of the portal's set (Material Symbols, filled, an underscore written as a hyphen: `inventory-2`), checked as a screen's `icon` is. A label, not a field of the contract: every Nereid's image has labels, while only some publish a contract, and a reef with no screen (`metrics`, `release`) still needs an icon for its status rows. `nereus nereid apply` copies the label to the Nereid's `spec.icon`, leaving a bad name out; `GET /v1/status` gives each row its reef's icon (the first Nereid by name whose first reef it is, then one that serves it next to its own), and core and the reefs the API keeps (`tenancy`, `teams`) get theirs from the CLI, having no image; `GET /v1/screens` gives a screen with no `icon` of its own its reef's; `nereus reef get` prints it. The portal draws a row's icon, else its reef's screen's (an older API), else the default; a name it does not have draws the default too. A reef's own SVG, served by its Nereid, is a later decision (#2206).

**When a module fails to load** (a 404, a syntax error, a `customElements.define` that throws, the element never defined within 10 seconds, or a `nereus-error`), the tab shows the error line of ADR 0012, with the reef and the file named, and the rest of the portal keeps working. The portal never retries on its own; the person reloads the tab.

**The portal's built-in tabs (#740, #750, #777) stay modules of the portal**: they are the platform's own, not a reef's, and need no contract.

**Tide is the first consumer**: the `ideas` reef's Nereid `doris` serves `tide.js`, which defines `<nereus-tide>`, and reads its notes from `GET /v1/ideas/notes` (#1107). It proves the extension point against a real screen, not an abstract one.

## Prior art

- **Custom Elements and Shadow DOM** ([WHATWG HTML Standard, custom elements](https://html.spec.whatwg.org/multipage/custom-elements.html)): the browser's own component model, with no library; the contract is one tag name and one module.
- **Backstage's frontend plugins** ([backstage.io](https://backstage.io/docs/frontend-system/)): the portal loads a plugin's UI at runtime; Nereus keeps the idea and drops the build and the framework.
- **Module Federation** ([module-federation.io](https://module-federation.io/)) and **single-spa** ([single-spa.js.org](https://single-spa.js.org/)): the microfrontend patterns weighed above; the pattern is the same (an independent team ships a screen), the mechanism here is the platform's.
- **Micro Frontends** ([micro-frontends.org](https://micro-frontends.org/), Cam Jackson on martinfowler.com): the case for Web Components as the integration contract between a shell and its parts.

## Consequences

- The same contract carries a reef's MCP tools (ADR 0029, a `tools` list read with `contractVersion` `2` or `3`), served by the Nereus API at `/mcp`.
- A reef adds a screen with no portal release: install the reef and its Nereid, and the tab appears.
- The Nereid SDK and `templates/nereid` learn the `screens`, `assets` and `contractVersion` fields and serve `ui/` (#1105 builds the portal's side and the SDK's).
- The portal's Nereid gains a read of the Nereids' status and a forward to another Nereid's controller port; its admission policy and Role change in the same issue. A `screens` entry cannot make the portal fetch anything outside the allow-list.
- A reef's screen runs code in the portal's origin, with the person's token reachable through `api`. Installing a reef is therefore trusting its code as the portal's own (OWASP A08); the allow-list and the `'self'` CSP limit where it can reach, not what it does with the data it may read. A signed module is a later decision.
- The contract is versioned: a change that breaks an element's interface raises `contractVersion`, and the portal loads only the versions it knows, with the ADR 0012 line for the others.
- Until v1.0.0 this ADR is rewritten in place when the decision changes (ADR 0001).

## Origin

Decided as a recommendation on 2026-11-06 and 2026-11-08 in #1102 and #1103, from the owner's question about microfrontends; raw data in `#pontos/raw/2026-11-06/` (Drive) for the voice session of that day. The reef's own icon was approved by the owner on 2026-11-24 in #1773, after #1838 gave the portal its icon set.

## Open questions

- Signing the modules a Nereid serves, so the portal loads only code a Mandate approved.
- Whether a screen may offer a command to the CLI as well, as ADR 0004 does for commands.
- Isolating a reef's screen from the portal's origin (a sandboxed iframe or an origin of its own, with a narrow API over `postMessage`), so its code cannot reach the person's token; until then the portal keeps the browser's own `fetch` before any reef module loads, and its forward follows no redirect and sets each file's type from its extension (#1105).
