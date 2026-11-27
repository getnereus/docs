# 0004. Reefs and their Nereids extend the CLI with their own commands

!!! note "In short"
    Each Reef describes its commands as data published in `status`, and the CLI builds them at runtime, grouped by Reef, never by Nereid or Tool. Status: Proposed (2026-10-17, rewritten 2026-10-25).

**Status:** Proposed (2026-10-17, rewritten 2026-10-25)

## Context

If Reefs and Nereids are added at runtime (ADR 0003), the CLI cannot know their commands in advance. Shipping a new CLI release for each would undo the point. The Azure CLI solves a similar problem with extensions, but an extension is code installed on the client.

## Decision

Each Reef describes the commands it serves, and the CLI builds them at runtime:

- The commands are grouped by Reef, never by Nereid or Tool: adding the `secrets` Reef adds `nereus secrets apply`, whichever Nereid keeps the secrets.
- The description of the commands (names, arguments, flags, help text, examples) is data, not code, published in `status`.
- The CLI caches these descriptions when it lists Reefs or logs in, as `kubectl` caches API discovery.
- Running a command reaches the Reef's resources or the Nereid that handles it under the Reef's Mandate. In the first test, the CLI reaches the Nereid through the Kubernetes API's Service proxy, with no Platform API and no login. Later the Platform API sits in between and decides who may run what.

```bash
nereus reef apply secrets --from-file ./reefs/secrets/
nereus secrets --help
nereus secrets apply google-sso --from-file google-sso.json
```

### Amendment: named options and the answer's steps (2026-11-09)

Decided by the owner on 2026-11-09 for #1290 (a command a Nereid publishes appears under its Reef, takes named options, and can open the browser and write the Mandate's params), the generic mechanism the github Nereid's `app-register` uses first:

- **Every Nereid of a Reef publishes into the Reef's group.** The same path published by two Nereids is one command, routed by `--mandate`: the Nereid of that Mandate, else the Reef's default Mandate's; a path one Nereid publishes goes to it. `--mandate` is the option the CLI adds to every published command of a Reef with several Nereids, unless the command declares it; a Mandate whose Nereid does not publish the command is refused, naming it. The CLI's own commands of a Reef still win.
- **Named options:** a command declares `options` (`name`, `help`, `required`, `pattern`) beside its positional `arguments`; the CLI checks each value against its `pattern` before sending it, and sends the options by name.
- **The answer's steps:** `POST /run` answers JSON with `output`, `error` and `exitCode`, and may ask two steps the CLI carries out as the person's client, in this order:
  - `browser` (`url`, `callback`, `timeoutSeconds`, optional `form`): the CLI listens on `127.0.0.1` only, generates a `state` and checks it on the callback, opens the URL (or, with a `form`, a local page that POSTs it, for GitHub's manifest flow, served once at an unguessable path), keeps only the listed callback parameters, and refuses every request after the first valid callback. `{{callback}}` and `{{state}}` in the URL and the form become the listener's callback URL and that state.
  - `mandateParams` (`mandate`, `params`): the CLI merges the params into the spec of that Mandate, which must be one the answering Nereid serves on this Reef (ADR 0005: the person, through the CLI, writes `spec`), and prints `core/mandates/<name> configured (...)`.
- **The Nereid stays stateless:** after a `browser` step, the CLI posts the command again with the original options plus everything the steps collected (`collected`), until an answer asks no `browser` step, at most five rounds. A failed answer (`exitCode` other than 0) runs no step.
  - `nextSteps` (a list of lines, #1291): the CLI closes the run with them in its own `Next steps:` block (ADR 0013), after the other steps, so a line like the App's install URL comes after the Mandate is written.
- No step carries a secret: a Nereid answers with secret names, never their values.
- **A Mandate made with no params** names, in the Next steps of `mandate create`, every command its Nereid publishes with a required `--mandate` option, the Mandate filled in and the other required options as placeholders (#1291: `nereus authentication app-register --mandate github --org <org>`).

## Consequences

- A Reef extends the MCP door the same way: its Nereid's contract lists its tools, and the Nereus API serves them at `/mcp` (ADR 0029).
- No client-side code is downloaded: a Nereid cannot run anything on the user's machine.
- Swapping a Nereid changes no command a person types.
- What a Nereid publishes is untrusted input: validated before the CLI renders or routes it.

## Open questions

- How a Reef's contract becomes commands: built from the schema of its resources, published by its Nereids for actions that are not resources, or both (ADR 0010).

*Rewritten 2026-10-25 from voice session; raw data in Drive #pontos/raw/2026-10-25.*

*Amended 2026-11-09 from the owner's decisions on #1290; raw data in Drive #pontos/raw/2026-11-09.*
