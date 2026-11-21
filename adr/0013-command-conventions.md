# 0013. Command conventions: one shape, kubectl's verbs (create, apply, delete), dry runs, examples, and refusals that list what to run

!!! note "In short"
    Commands share one shape, `nereus <noun> <verb> <name>`, with kubectl's verbs, dry runs, examples, and refusals that list the commands to run. Status: Proposed (2026-10-18, rewritten 2026-10-25, amended 2026-10-29, 2026-11-03 and 2026-11-15).

**Status:** Proposed (2026-10-18, rewritten 2026-10-25, amended 2026-10-29, 2026-11-03 and 2026-11-15)

## Context

ADR 0010 gave the commands that extend the platform one shape: a noun, a verb, and the name as an argument (`nereus reef apply release`). Reviewing the commands of spec 0005 (PR #151), the owner asked for more than the shape: how a command behaves when what it creates already exists, how a person changes it, how they check a change before making it, and how a person or an agent learns to use a command. Every command added later, by the CLI or by a Nereid, should answer these the same way, so a person who learned one command knows them all.

The first version of this ADR, decided in an earlier review, used `add` (fails when the thing exists) and `remove`. On 2026-10-25 the owner replaced them with kubectl's own verbs: a person who knows `kubectl` should not learn a second vocabulary for the same three acts.

On 2026-10-29, designing the secrets reef's commands (#529) and porting the Keycloak login (#89), the owner sharpened four points: what `create` and `apply` each take, what a reef's commands mean without a kind, how an output line names an object that lives inside another, and which commands take `--dry-run`.

## Decision

**The shape** stays ADR 0010's: `nereus <noun> <verb> <name>`, with the platform's nouns top-level (`reef`, `nereid`, `mandate`) and a reef's nouns under its group (`nereus release source apply`). Options are long-form (`--reef`, `--nereid`), one per line in examples.

**The verbs:**

| Verb | Does | When it exists |
|---|---|---|
| `create` | creates, from the flags given and the defaults this CLI pins | fails, and the error lists the commands to run instead |
| `apply` | creates or updates, declaratively, from files only: `--from-file <path>` (a `.yaml` file or a whole folder of them) or `--path <path>` (one local file or folder, given once) | updates it, or reports it unchanged |
| `list` | shows every one, as a table | |
| `get` | shows one | |
| `delete` | deletes | refused while something depends on it, naming the command that frees it |

The verbs are kubectl's: `create`, `apply` and `delete` mean what `kubectl create`, `kubectl apply` and `kubectl delete` mean. `add` and `remove` are not verbs. `nereus reef delete authentication` deletes.

**`create` builds an object from flags; `apply` takes only files or whole folders of `.yaml`** (owner, 2026-10-29), as kubectl does. `create` fails when the object exists, and leaves it unchanged: `nereus mandate create corporate --reef authentication --nereid keycloak --default`. To change an object built from flags, write it as a file and apply the file, as `kubectl create --dry-run=client -o yaml | kubectl apply -f -` does:

```text
# Build a secret from two environment variables
$ nereus secrets create google-oauth --from-env GOOGLE_CLIENT_ID --from-env GOOGLE_CLIENT_SECRET
secrets/vaults/default/secrets/google-oauth created (key SHA256:Xy3…)

# Write it as a file instead of creating it
$ nereus secrets create google-oauth --from-env GOOGLE_CLIENT_ID --from-env GOOGLE_CLIENT_SECRET --dry-run --output yaml > secrets/google-oauth.yaml

# Apply a whole folder of them
$ nereus secrets apply --from-file secrets/
secrets/vaults/default/secrets/google-oauth configured
secrets/vaults/default/secrets/github-app unchanged
```

`nereus reef apply secrets --from-file ./reefs/secrets/` applies a reef from its folder. **Installing a reef or a Nereid by its name** (`nereus nereid apply keycloak --reef authentication`, `nereus reef apply cloud`, `--image <reference>`) is not decided here: #487 (the verb that installs a reef or a Nereid by name, with `apply` kept for files) holds it, and until it closes those commands keep today's form.

**Each reef declares a default kind** (owner, 2026-10-29): `nereus <reef> <verb>` is `nereus <reef> <default kind> <verb>`, so `nereus secrets create` is `nereus secrets secret create`, as `nereus release create` is already `nereus release release create`. The reef's contract declares it with the annotation `core.getnereus.dev/default-kind: "true"` on that kind's CRD, on one kind at most. A shortcut at the top of the CLI is the same idea one level up (the first: `nereus login` for `nereus authentication login`, #89): allowed, with no limit per reef, each decided by the owner. `nereus workload` and `nereus template` are both shortcuts into `catalog` (ADR 0016).

**Every noun takes the five verbs**, as kubectl's resources do: `create`, `apply`, `delete`, `get` and `list`, for the platform's nouns and a reef's alike. Both `create` and `apply` are valid for every noun: `create` from flags, `apply` from files.

**A noun Nereus ships and nobody writes takes only `get` and `list`** (owner, 2026-11-17, #1700): the presentations reef's `schema`, the deck outline's JSON Schema of each `outlineVersion`, shipped with the CLI and the API; nothing creates, applies or deletes it.

**Four more verbs, for what the five do not say** (owner, 2026-11-02, ADR 0020):

| Verb | What it does | Example |
|---|---|---|
| `deploy` | creates or updates a `Delivery`, across reefs | `nereus workload deploy hello@dev --image <reference>` |
| `render` | writes a template's files, with Copier | `nereus template render python-service --path ./hello` |
| `logs` | reads what a thing prints | `nereus workload logs hello-dev --follow` |
| `publish` | publishes an artifact with the platform's credential | `nereus release source publish nereus` |

**`can-i` asks before acting** (owner, 2026-11-15, ADR 0027): `nereus authorization can-i <verb> <reef>/<kinds> [--owner <kind>/<name>] [--user <name>]` asks the question the Nereus API asks before it acts and changes nothing, so it takes no `--dry-run`. The answer names the binding that grants it, and the exit code is 0 for yes and 1 for no, for scripts. With no `--user` it answers for the caller; asking about another User is itself a permission. The shortcut `nereus can-i` is the same command. A rule of a role names it as any other verb (`authorization:can-i:get`).

```text
# May bruno create Environments in the Project payments?
$ nereus authorization can-i create environment/environments --owner project/payments --user bruno
no: no binding gives bruno create on environment/environments at project/payments
```

**`@` names a pair:** `hello@dev` is sugar for `hello --environment dev`. The argument rule, and why `deploy` refuses a bare name, are in ADR 0020.

**Output lines end in kubectl's words:** `created`, `configured` (updated), `unchanged`, `deleted`, plus `rendered at <path>` for `render`, which changes no object. **They name the object by its full path** (owner, 2026-10-29), as Azure's resource ids do: the reef, then each kind in the plural followed by its name, parents before children, never shortened, even when a word repeats. The platform's own kinds (`Reef`, `Nereid`, `Mandate`) are under `core`:

```text
secrets/vaults/default created
secrets/vaults/default/secrets/google-oauth created (key SHA256:Xy3…)
secrets/vaults/default/secrets/google-oauth/secretbindings/keycloak created
release/repositories/codecentric created
release/releases/keycloak created
core/reefs/secrets created
core/nereids/openbao configured
core/mandates/default unchanged (reef: secrets, nereid: openbao, default)
```

A path is read without knowing the reef: `release/releases/keycloak` keeps `release` twice, so nobody learns an exception. A Mandate's line adds, in a parenthesis, the reef and the Nereid it binds and whether it is the reef's default: `core/mandates/flux created (reef: release, nereid: flux, default)`, `core/mandates/reference configured (reef: release, nereid: fake, no longer the default)` (owner, 2026-10-26, order 20261026-1843): a Mandate is a binding, and the line says what it binds.

**A refusal lists what to run.** Every error follows ADR 0012 (every error message says what happened and how to fix it); for a command that refuses, its fix gives the command or commands that would do what the person meant, each with what it does:

```text
$ nereus secrets create google-oauth --from-env GOOGLE_CLIENT_ID --from-env GOOGLE_CLIENT_SECRET
✗ secrets/vaults/default/secrets/google-oauth already exists. To change it, run:
  # write it as a file, then apply the file
  nereus secrets create google-oauth --from-env GOOGLE_CLIENT_ID --from-env GOOGLE_CLIENT_SECRET --dry-run --output yaml > google-oauth.yaml
  nereus secrets apply --from-file google-oauth.yaml
```

**Every output ends with `Next steps:`**: a blank line before and after the label, then the command to run next, indented two spaces.

```text
core/reefs/secrets created (secrets.getnereus.dev/v1alpha1)

Next steps:

  nereus nereid apply --help
```

**`--dry-run` on every command that changes something, no exception** (#242, owner, 2026-10-29): `create`, `apply` and `delete` of every noun, and every other imperative command. It shows exactly what would change, the objects and, for a cloud, the requests of a plan, and changes nothing; with `--output yaml` it prints the objects, ready for `apply --from-file`. #242 (every command that changes something has `--dry-run`) tracks the commands that miss it.

**Lists come in alphabetical order, and `--sort-by` changes it** (owner, 2026-11-02, #808): `status` and every `list` by name; `--sort-by` takes kubectl's path into each object (`--sort-by .metadata.creationTimestamp`), in every form of `--output`, and refuses a field no row has. A table whose order means something keeps it: the steps of a plan, the checks of `doctor`, what a profile installs.

**`--examples` on every command and group** (#243), next to `--help`: each example is a line saying what it does, then the command; `-o json` prints them for agents. In every code block of the docs and the deck, a comment line comes before each command and a blank line between commands.

**Commands a reef or a Nereid adds** follow the same conventions, and the CLI checks them as untrusted input before rendering them (spec 0003).

## Prior art

- **`kubectl get --sort-by`** ([Kubernetes, "Command line tool (kubectl)"](https://kubernetes.io/docs/reference/kubectl/#sorting-list-objects)): a path into each object, the form `--sort-by` takes as it is.
- **`kubectl create`, `kubectl apply` and `kubectl delete`** ([Kubernetes, "Managing Kubernetes objects"](https://kubernetes.io/docs/concepts/overview/working-with-objects/object-management/)): imperative creation that fails when the object exists, next to a declarative create-or-update, and the verb that deletes; the three are taken as they are. The output lines (`created`, `configured`, `unchanged`, `deleted`) are what `kubectl` prints per object, and `kubectl create --dry-run=client -o yaml | kubectl apply -f -` is the way from flags to a file, in the project's own observation.
- **Azure resource ids** ([Azure REST API, "Resources - Get By Id"](https://learn.microsoft.com/en-us/rest/api/resources/resources/get-by-id)): `/subscriptions/{guid}/resourceGroups/{resource-group-name}/{resource-provider-namespace}/{resource-type}/{resource-name}`, as in `/subscriptions/<sub>/resourceGroups/rg-demo/providers/Microsoft.KeyVault/vaults/kv-demo/secrets/google-oauth`: the provider first (here, the reef), then type and name in pairs, types in the plural, a child after its parent, and a repeated word kept (`Microsoft.Batch/batchAccounts`). The output lines' full path follows it.
- **Command Line Interface Guidelines** ([clig.dev](https://clig.dev/)): examples first in the help, `--dry-run` for commands that change something, and errors that suggest the next command.

## Consequences

- `nereus reef create` fails when the reef exists, naming `apply`; `nereus reef apply` on a reef that exists reports `unchanged` or `configured` (in today's code, `platform system interface add` behaves as `create`, #18).
- Today's code and the docs written before 2026-10-25 say `add` and `remove`; they map to `apply` (or `create`) and `delete` ([The CLI design](../agent/cli.md)).
- The code and the decks' recorded outputs adopt the 2026-10-29 amendment in #523 (the CLI's commands adopt the amended conventions): the full-path output lines, `apply` from files only, `create` from flags, `--dry-run` everywhere. Each reef's own commands follow it from their first slice (the secrets reef, #530).
- Each reef's contract names its default kind with the annotation; a reef without one has no `nereus <reef> <verb>` shortcut.
- `cli/tests/test_help.py` grows to check these conventions on every command: `--dry-run` where a command changes something, a description for each example.
- A new command is reviewed against this list before it merges; a command that needs another verb or behaviour gets an ADR that extends this one.

*Aligned in wording 2026-10-25 from voice session (reef, Nereid, Mandate, `nereus`). Rewritten 2026-10-25 (order 20261025-1741): the verbs are kubectl's, `create`, `apply` and `delete`, replacing `add` and `remove`. Rewritten again 2026-10-25 (order 20261025-1805): every noun takes create, apply, delete, get and list; raw data in Drive #pontos/raw/2026-10-25. Amended 2026-10-26 (order 20261026-1843): a Mandate's output line names its reef, its Nereid and whether it is the default. Amended 2026-10-29 (owner, while designing the secrets reef, #529, and porting the Keycloak login, #89; #522): `create` builds from flags and `apply` takes only files or folders, each reef declares a default kind, output lines name the object by its full path as Azure's resource ids do, and every imperative command has `--dry-run`; installing a reef or a Nereid by name stays open in #487. Amended 2026-11-03 (the owner's decisions of 2026-11-02 in #835, the delivery model of the internal-developer-platform profile; #843, the delivery reef's ADR): no limit of shortcuts per reef, the verbs `deploy`, `render`, `logs` and `publish`, and the `@` sugar. Amended 2026-11-15 (the owner's decisions refining #897 into spec 0011, decision 19; ADR 0027): the verb `can-i`; raw data in Drive `#pontos/raw/2026-11-15/`. Amended 2026-11-17 (the owner's go on #1700, the deck outline's JSON Schema): a read-only noun takes only `get` and `list`.*
