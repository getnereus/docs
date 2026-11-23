# The CLI design

The target CLI, from the owner's voice session of 2026-10-25 (raw data in Drive `#pontos/raw/2026-10-25`, files 38 to 47; the flow in `last-terminal.html`). It wins over any legacy command: the commands of today's code (`platform ...`) are reference only, mapped below.

**Every command lives in a deck, one per reef** (#477): `docs/specs/cli/reefs/<reef>.yaml`, with a section per kind and the index in `docs/specs/cli/index.yaml`. The YAML is the source of truth, an outline of the deck engine (`docs/presentations/render-outline`, [Decks](decks.md)); each command slide has a `status` (`built`, `planned` with its `issue`, or `idea`), shown as a tag after its label.

A new command, or a change to one, goes into its reef's deck first, and the issue that builds it points to the slide (`reefs/edge.html#domain-get`). The get-started, release and edge decks in `docs/walkthrough/decks/` link each step to its command's slide; the engine refuses a link to a slide that does not exist.

`make decks` renders them all; `make deck-test` checks them and fails when an HTML is stale. The reefs not ported yet keep their commands in this page and in the walkthroughs.

## The words

| Word | What it is | Legacy word |
|---|---|---|
| **reef** | A capability of the platform, an API group `<reef>.getnereus.dev/v1alpha1` (for example `secrets.getnereus.dev/v1alpha1`). A reef can exist with no Nereid; then it waits. `core` is built in. | Interface |
| **Nereid** | A controller installed in the platform, top-level, with a name global to the platform. One Nereid may look after many reefs (`--reef` repeats), and one reef may have many Nereids. It owns its authentication (for example `workload-identity`) and its default target parameters (for example a default `vaultUrl`). Its image is `<reef>-<tool>-controller`. | Implementation |
| **Mandate** | Binds one reef to one Nereid, top-level. It may override the Nereid's target parameters with `--param` (a Nereid may serve several vaults); `--default` makes it the reef's default; `--match <key>=<value>` picks it for the requests whose keys equal the values, the most specific match winning (ADR 0017, #1598). | Class |
| **tenancy** | The reef that holds whose a thing is (ADR 0015): `tenancy.getnereus.dev/v1alpha1`, its kinds from each instance's `reefs/tenancy/` (here `Organization`, the boundary, and `Project`), every kind a node with `spec.parent: {kind, name}`. Its commands are ideas in [its deck](../specs/cli/reefs/tenancy.html) (#569) until #573 builds them. | none |
| **catalog** | The reef that says what Nereus has (ADR 0016): `catalog.getnereus.dev/v1alpha1`, its kinds `Workload` (what runs, the default kind, so `nereus catalog list` is `nereus catalog workload list`), `Package` (what is published), the configurable `WorkloadType` and `PackageType`, and `Template` (its `render` is the delivery deck's). Every entry names its `owner` and a Workload its `audience`; `source.ref` is structured as Flux's (`--ref <field>=<value>`, repeatable, never one string); `--audience none` is `audience: []`. Its commands are ideas in [its deck](../specs/cli/reefs/catalog.html) (#570) until #574 builds them. | none |
| **delivery** | The reef that takes a Workload to an Environment (ADR 0020): `delivery.getnereus.dev/v1alpha1`, its kind `Delivery` (the default kind), one per pair. `nereus workload deploy` writes it, and the Nereid `kubernetes` resolves the image's digest and writes a `Release`. Its commands are planned in [its deck](../specs/cli/reefs/delivery.html) until #845 builds them. | none |
| **database** | The first resource reef (ADR 0017, #653): `database.getnereus.dev/v1alpha1`, its kind `Database` (the default kind, so `nereus database create`) with `owner: {kind, name}` in the tenancy tree, which must exist, and `engine` (`postgres`), in the nereus namespace only; the Nereid `cloudnative-pg` of its default Mandate `cloudnative-pg` (applied by the `internal-developer-platform` profile) writes in `status.binding.secret` the Secret of the connection. | none |
| **messaging** | A resource reef (ADR 0017, #1597, the first cut of #576): `messaging.getnereus.dev/v1alpha1`, its kinds `Topic` and `Queue` (no default kind, so `nereus messaging topic create` and `nereus messaging queue create`; the agents' sessions moved to the rooms reef, #2076) with `owner: {kind, name}` in the tenancy tree, `engine` (`nats`) and `deletionPolicy` (`retain`, the default, or `delete`), in the nereus namespace only; the Nereid `nats` of the admin's default Mandate (`--param jetstream=true`) runs NATS next to it and writes in `status.binding.secret` the Secret `<name>-topic` or `<name>-queue`. | none |
| **rooms** | The reef of the conversation between agents (ADR 0030, #2067): `rooms.getnereus.dev/v1alpha1`, its kinds `Room` (the default kind, so `nereus rooms create`, `apply`, `list`, `get` and `delete`) and `Peer` (an agent's session in the rooms, `nereus rooms peer list` and `get`), with `nereus rooms join` and `leave` (#2075), `nereus rooms follow` and `pull` (#2076) and `post` (#1889). The Nereid `triton` requires the messaging reef and asks it for a Topic `room-<room>` per Room. `create`, `apply`, `list`, `get` and `delete` of a Room go through the Nereus API, asked on the Room's owner: a team's members create rooms owned by the team's owner, admins delete them (#1491), and a new room past the default Mandate's `maxRooms` (20) fails. Triton writes a `RoomSession` per room's activity, read with `nereus rooms session list` and `get` (#2100). Every command is in [its deck](../specs/cli/reefs/rooms.html); the old names are mapped in [Legacy commands](#legacy-commands). | none |
| **registry** | The reef that runs a registry of images in the cluster (ADR 0021): `registry.getnereus.dev/v1alpha1`, its kinds `Registry` (the default kind) and `Repository` (#1013, its own push credential). The Nereid writes `status.pullAddress` for a node and `status.internalAddress` for a Pod. Not the Nereid registry (#22). See [its deck](../specs/cli/reefs/registry.html). | none |
| **scm** | The reef that holds what a source host is to Nereus (ADR "The scm reef", #927): `scm.getnereus.dev/v1alpha1`, its kind `Connection` (one organisation of a host, reached through the GitHub App that its scm Mandate's param `identity` names; the default kind). Who the platform is towards the host (the App, a short-lived `Token`) is the authentication reef's (ADR 0006). The `github` Nereid serves both reefs, opt-in. See [its deck](../specs/cli/reefs/scm.html). | none |
| **owner** | Whatever points to the tenancy tree names `owner: {kind, name}`, a kind of the tenancy group, never an apiVersion or a namespace: the catalog's Workloads and Packages, an Environment, a resource Instance, a Mandate's `match`. On the command line `--owner <kind>/<name>`, optional once `nereus config set owner` names the current one; the flag wins and the output line names the owner used. | `spec.project` |
| **target** | What `nereus init --target <provider>` prepares (for `azure`: Key Vault, Storage, DNS zone, Managed Identity), with the person's own login, since no Nereid exists yet. | `--target` of `platform init` |

"Mandate" is the working term, and "Instance" keeps its name (ADR 0002). The CLI binary is `nereus` (formerly `platform`, #396); its commands are the ones below since #409, and the legacy ones are deprecated aliases (see [Legacy commands](#legacy-commands)).

## The commands

```text
# Prepare a cluster: core, then a profile (ADR 0014). core, the default: core only;
# internal-developer-platform: authentication with keycloak, after the secrets reef it
# requires (OpenBao on k3d, its default vault Mandate and RSA key)
nereus init
nereus init --profile internal-developer-platform
nereus init --target azure

# Profiles (ADR 0014): one YAML file each, charts/nereus/profiles/<name>.yaml, rendered by the chart
# into the Profile's spec, which thetis reads alone (spec.reefs required, #1370); apply layers one on core, idempotent, and
# `init --profile <name>` is init, then this. `profile create` is parked
nereus profile list
nereus profile describe <profile>
nereus profile apply <profile> [--without <nereid>]... [--dry-run]   # on a Profile (the charts), --without leaves a Nereid out (#1231); the Nereids install side by side, NEREUS_PROFILE_LANES at once (4, #1297)

# Reefs (after the profile internal-developer-platform, `reef create secrets` fails as "already exists",
# `reef apply secrets` reports unchanged or configured)
nereus reef list
nereus reef apply <reef> --from-file ./reefs/<reef>/

# Nereids
nereus nereid suggest --reef <reef>
nereus nereid apply <nereid> --reef <reef> [--reef <reef> ...] [--image <image>] [--param <key>=<value> ...]

# Mandates
nereus mandate create <mandate> --reef <reef> --nereid <nereid> [--param <key>=<value> ...] [--match <key>=<value> ... | --default]

# The reefs' own commands: nereus <reef> <kind> <verb> <name>; `nereus <reef> <verb>` is the
# reef's default kind (ADR 0013), so `nereus secrets create` is `nereus secrets secret create`.
# create builds from flags, apply takes files or folders of .yaml
nereus secrets create <secret> --from-env <variable> [--from-env <variable> ...]
nereus secrets create <secret> --from-env <variable> --dry-run --output yaml > <file>
nereus secrets apply --from-file <file or folder>

# The release reef (ADR 0010, #445): a kind named after its reef takes the reef's own verbs,
# so `nereus release create` is `nereus release release create`
nereus release repository create|apply|list|get|delete <repository> [--url <url> --type http|oci|git] [--secret <secret>]
nereus release source create|apply|list|get|delete <source> [--repository <repository> --chart <chart> --version <version>]
nereus release target create|apply|list|get|delete <target> [--namespace <namespace>] [--environment <environment>]
nereus release create|apply|list|get|delete <release> [--source <source> --target <target>] [--values-file <file>] [--mandate <mandate>]
nereus release get <release> --watch

# The tenancy reef (ADR 0015, ideas in its deck until #573): parents before children,
# the output names each node by its full path (#647); a flag per string field of the
# kind's spec; apply is the group's, never a kind's; spec.parent never changes (#646)
nereus tenancy organization create|list|get|delete <organization>
nereus tenancy project create|list|get|delete <project> [--parent <kind>/<name>] [--repository <url>] [--cascade]
nereus tenancy apply --from-file tenancy/ [--dry-run]

# The catalog reef (ADR 0016, built by #902, check an idea until #903): workload is the default kind;
# apply is the group's, never a kind's; a template writes files before the catalog, so
# --template is not a flag of create (its render is the delivery deck's); check fails on a
# contradiction (✗) and only points at a gap (!)
nereus catalog workload create|list|get|delete <workload> [--owner <kind>/<name>] [--type <type>] [--audience programs|people|agents|none] [--repository <url>] [--ref <field>=<value>] [--path <path>]
nereus catalog package create|list|get|delete <package> [--owner <kind>/<name>] [--type <type>] [--registry <registry>] [--name <name>] [--audience <audience>]
nereus catalog workload-type create|list|get|delete <type> [--runs always|once] [--trigger event|request|schedule]
nereus catalog package-type create|list|get|delete <type> [--registry <registry>]
nereus catalog apply --from-file catalog/ [--dry-run]
nereus catalog check

# The delivery reef (ADR 0020, planned in its deck until #845): deploy never guesses the
# target; workload list is the catalog's, delivery list is what was deployed
nereus workload deploy <workload>@<environment>|<delivery> --image <reference> [--wait] [--timeout <seconds>] [--dry-run]
nereus workload list
nereus workload logs <workload>@<environment>|<delivery>|<workload> [--environment <environment>] [--follow]
nereus delivery create|list|get|delete <delivery>
nereus delivery apply --from-file <path> [--wait=true|false] [--timeout <seconds>] [--dry-run]
nereus template render <template> --path <folder> [--param <name>=<value>] [--dry-run]

# The registry reef (ADR 0021): the zot Nereid is #1012, Repository and publish are #1013
nereus registry create <registry> [--owner <kind>/<name>] [--mandate <mandate>] [--dry-run]
nereus registry list|get|delete <registry>
nereus registry apply --from-file <path> [--wait=true|false] [--timeout <seconds>] [--dry-run]
nereus registry repository publish <repository> --registry <registry> --image <image>:<tag>
nereus registry repository list|get|delete <repository>

# The rooms reef (ADR 0030, #1491): Room, its default kind, owned by an organization or a project; without a name the
# repository's, without --owner the owner of your team; a new room past the default Mandate's maxRooms (20) fails
nereus rooms create [<room>] [--owner <kind>/<name>] [--description <text>] [--max-age <duration>] [--max-bytes <size>] [--deletion-policy retain|delete] [--dry-run]
nereus rooms apply --from-file <path> [--dry-run]
nereus rooms list|get <room>
nereus rooms delete <room> --yes [--dry-run]
nereus rooms peer list|get <owner>.<agent>

# The platform's identity (ADR 0006, planned in the authentication deck): a GitHub App is a Mandate
# of the opt-in github Nereid (#1273), its key a plain secret; Token is #1274, the browser action #1275
nereus nereid apply github --reef authentication --reef scm
nereus mandate create github --reef authentication --nereid github --param appId=<id> --param privateKey=<secret> --param allow=<namespace>:<repository or *>:<permission>=<level>[,...] [--default]
nereus authentication token create <token> --repository <org>/<repository> [--permission <name>=<access>] [--mandate <mandate>] [--dry-run]
nereus authentication token list|get|delete <token>

# The scm reef (ADR 0024, built in #1281): a Connection names an organisation
# reached through the App its scm Mandate names (--param identity=<authentication mandate>, #1281); no vendor, no key, no verify
nereus scm connection create <connection> --org <org> [--mandate <mandate>] [--default] [--dry-run]
nereus scm connection list|get|delete <connection>

# The current owner (ADR 0016, with #574): --owner becomes optional; the flag wins
nereus config set owner <kind>/<name>

# How the reefs are doing
nereus status

# Whether this instance is healthy: pass or fail per check, exit code 1 when one fails (#799)
nereus doctor

# The CLI keeps itself up to date (#1782): upgrade now, or only report; a normal call starts a
# detached upgrade once per check_interval (auto_upgrade: background, notify or off)
nereus upgrade [--check|--dry-run]
nereus config set auto_upgrade background|notify|off
nereus config set check_interval 24h
```

- **Output:** every command with `--output` (`-o`) takes `table` (the default), `yaml`, `yamlc` (coloured YAML), `json` and `jsonc` (coloured JSON); the coloured forms colour even in a pipe, since the person asked for them (#409). Every `-o` also has the long form `--output` (owner, 2026-10-31). Every `get`, `list`, `describe` and `show` takes it, and every `--output` has `-o` (owner, 2026-11-16, #1734): `cli/tests/test_help.py` walks the command tree and fails otherwise. A `get` or `list` of an API object prints the object without `managedFields`; a command that shows settings or a table of its own prints its rows keyed by their headers in camelCase (`REQUIRED BY` is `requiredBy`). A command may add a form of its own that writes an export: `presentation get --output html` (#1703) and `session get --output agent` (#1718, a YAML for an agent, with a `✓ … written` line on stderr when stdout is not a terminal). An export made to be redirected writes its summary line on stderr, never stdout, so the file holds only the export (owner, 2026-11-18).
- **Order:** `status` and every `list` come in alphabetical order; `--sort-by <path>`, as kubectl's, sorts by any field of the objects (`.metadata.creationTimestamp`; `.createdAt` on `status`), in every form of `--output`; rows without the field go last, a field no row has is refused (#808). `sorted_by` in `output.py` is the one place. Over secrets it reads what the command shows, never the encrypted values. A table whose order means something keeps it (plan steps, `doctor`, `profile describe`, settings).
- **Help:** every command and group takes `-h` as well as `--help`, with the same output and the same precedence over `--version` and `--examples` (#1733); the root sets both in its `context_settings`, and every command inherits them.
- **Examples:** every command and group takes `--examples` (#674): each example after a `# <what it does>` line, as tldr prints them; a group lists every command under it, each after a `## <path>` line, and `nereus --examples` lists the whole CLI. With `--output`, they come as data for agents: `command` and `description`, plus `path` on a group (#675). In code, `examples()` takes `(description, command)` pairs, and `cli/tests/test_help.py` requires a description for each.
- **Help:** flat, Click's plain text, no Rich markup or colours (`TYPER_USE_RICH=0`, set in `cli/src/nereus/__init__.py`, #704). `nereus --help` lists its commands in sections `Platform`, `Session`, `Model` and `Reefs`, each sorted by name, one line per command; a new top-level command sets `short_help` (at most 60 characters) and `rich_help_panel` (one of those four), and `cli/tests/test_help.py` requires both.
- **Flags:** `--param <key>=<value>` for every parameter (never `--set`); `--reef` and `--nereid` everywhere (never `--implements`), never prepositions (`--on-reef`, `--to-nereid`); examples use long-form options, one per line.
- **Verbs:** kubectl's, ADR 0013 (command conventions): `create` builds from flags and fails when the thing exists, `apply` creates or updates from files or folders of `.yaml` only (every former `add`), `delete` deletes, plus `get` and `list`; every noun takes all five, and every command that changes something takes `--dry-run`. `add` and `remove` are not verbs. Installing a reef or a Nereid by name (`nereus nereid apply <nereid>`) keeps today's form until #487 (the verb that installs a reef or a Nereid by name) decides it.
- **Output lines** name the object by its full path, as Azure's resource ids do: the reef, then each kind in the plural and its name, parents before children, the platform's kinds under `core`, and end in `created`, `configured`, `unchanged` or `deleted`:

    ```text
    secrets/vaults/default/secrets/google-oauth created (key SHA256:Xy3…)
    release/releases/keycloak created
    core/mandates/default unchanged (reef: secrets, nereid: openbao, default)
    ```

- **Delete waits, as kubectl's does (#526):** an object whose Nereid keeps its cleanup finalizer (#525) stays until the Nereid removed what it made; meanwhile `list` and `get` show `Terminating` in the state column (computed by the CLI from `metadata.deletionTimestamp`, never written in status, ADR 0005; the `--output` forms carry the object as it is). `delete` waits until the object is gone, printing each step of `status.steps` as it changes (the time it changed, `✓` Done, `…` InProgress, `·` Pending, `✗` Failed, its name, its message), then the deleted line; a step `Failed` or `Ready=False` with `reason: CleanupFailed` ends it with exit 1 and `Next steps:` naming `get`. `--wait=false` (kubectl's spelling: `--wait` takes `true` or `false`) returns at once with `<path> is Terminating: <nereid> removes what it made.`; `--timeout` (seconds, as `get --watch`'s) ends the wait with a failure naming the step in progress, the object left as it is. `get --watch` prints the steps too, and stops once a Terminating object is gone. The shared part lives in `cli/src/nereus/reefkinds.py`, for every reef's commands.
- **What a delete must respect lives behind the API (#874):** the vcluster Nereid holds an Environment's finalizer while a Target names it and says why in the status, for any client; `nereus environment delete` checks first only to refuse early, and refuses when it cannot check.
- **Discovery (#839):** a reef's commands come from a cache, as `kubectl`'s discovery. `nereus login` fills it from `GET /v1/discovery`, open to any signed-in person (the kubeconfig without sign-in); a run naming a reef refreshes it past one hour or from another instance; an unknown first word rediscovers once, then fails naming `nereus status`. `--help` and completion never call.
- **Next steps:** every output ends with a `Next steps:` label, a blank line before and after it, and the command indented two spaces:

    ```text
    core/reefs/secrets created (secrets.getnereus.dev/v1alpha1: secrets, secretbindings, vaults)

    Next steps:

      nereus nereid apply --help
    ```

## Kinds

The platform's own kinds are `Reef`, `Nereid` and `Mandate`, in `core.getnereus.dev/v1alpha1`, owned by the `core` reef (ADR 0002, ADR 0009); a reef's own kinds live in `<reef>.getnereus.dev/v1alpha1`. Today's code applies these kinds in these groups (#20, #402): the `cloud` reef ships only its `Cloud` kind, and its Nereid's binding is a `Mandate`.

Their fields:

| Kind | Field | Holds |
|---|---|---|
| `Reef` | `spec` | the contract: API group, version, commands |
| `Nereid` | `spec.reefs` | the reefs it looks after (a list) |
| `Nereid` | `spec.image` | the image it runs, pinned by digest |
| `Nereid` | `spec.params` | its authentication and default target parameters |
| `Mandate` | `spec.reef`, `spec.nereid` | the reef and the Nereid it binds |
| `Mandate` | `spec.params` | the overrides of the Nereid's target parameters |
| `Mandate` | `spec.default` | `true` for the reef's default Mandate |

A reef's own objects key their entries by reef, never by Nereid: a `Cloud` access entry is `{reef: secrets, ...}`. Today's code uses `reef:` in those entries and `spec.reefs` (a list) on `Nereid`.

## Listing

```text
$ nereus status
REEF            NEREID           VERSION  STATUS  AGE
core            built-in         0.1.0    Ready   38m
secrets         azure-key-vault  0.1.0    Ready   8m

$ nereus nereid list
NEREID           REEFS    IMAGE                                                              STATUS  AGE
azure-key-vault  secrets  ghcr.io/getnereus/nereus/secrets-azure-key-vault-controller:0.1.0  Ready   8m
```

`nereus status` has one row per reef and Nereid pair; `nereus nereid list` one row per Nereid, its reefs comma-separated (ADR 0011). `nereus nereid get <nereid>` shows one Nereid in full, with the image's OCI labels `org.opencontainers.image.title` and `org.opencontainers.image.description` and its digest, which `nereid list` leaves out.

`STATUS` is computed by the CLI, not written by the Nereid (spec 0003, layer 2, #527): the Nereid's own `Ready` condition, unless its Controller has no pod serving (`Unavailable`, which wins) or it does not honour its reefs' kinds (`NotConformant`): a reef that exposes no kind has no `Ready` Nereid, unless it has none by design (`authentication`, `portal` and `metrics`, pinned in `contracts.REEFS_WITHOUT_KINDS`, #794), and a Nereid serves every kind its reef exposes, declared in its `status.kinds` as `<plural>.<group>`.

`core` is built in and always `Ready`; a reef with no Nereid is `Waiting`, unless it needs none by design: every CRD of the reef annotated `core.getnereus.dev/nereid: "none"` (the tenancy reef, whose objects the API keeps, ADR 0015; #651) makes its row `Ready` with `-` as its Nereid, and its `reason` says why.

`nereus nereid get` prints why on a `Reason` line, `nereus status --output json|yaml` as the `reason` field of each row, and a command to a `NotConformant` Nereid is refused with that reason.

## Secrets are encrypted on the client

A mandatory capability of the `secrets` reef contract: every secrets Nereid publishes a public key for each Mandate naming it, in the Mandate's `status.publicKey`, and decrypts inside its own boundary. The CLI encrypts each secret locally with envelope encryption: an AES-256-GCM data key encrypts the value, and the Mandate's RSA-OAEP-256 public key wraps the data key.

`nereus secrets create` uses the key of the Mandate it targets, the default one unless a Mandate is named. The CLI stays provider-agnostic; only the Nereid differs:

| Where | The private key |
|---|---|
| Azure (`--target azure`) | A non-exportable RSA key in Key Vault; the Nereid calls Key Vault to decrypt. |
| Local k3d, no target | A non-exportable RSA key of the OpenBao Transit engine ([API](https://openbao.org/docs/api/secret/transit/): `exportable` defaults to `false`); the Nereid calls Transit to decrypt. |
| Fallback | Sealed Secrets style: the private key in a cluster Secret. |

Log redaction stays, whatever the encryption.

Through the Nereus API (#1323), the CLI still seals each value on the machine: the API stores the envelopes as they come, never returns `spec.data` in an answer or an error, and logs the route and the person, never a body. It hands the CLI the Mandate's public key, which the CLI checks (fingerprint, size) as it did from the apiserver.

## Legacy commands

The aliases of `nereus system` that #409 kept for the legacy commands are gone (#410): only `nereus system access list|approve` stays, until its form is designed.

| Legacy (`platform ...`) | New form |
|---|---|
| `platform init [--yes]` | `nereus init` |
| `platform init --target azure` | `nereus init --target azure` (it also adds the secrets reef with Azure Key Vault, its default `default` Mandate, its RSA key and the vault `default`, ADR 0003) |
| `platform system` interface, install, uninstall, implementation | `nereus reef ...`, `nereus nereid apply`, `delete`, `list`, `nereus mandate create ... --default`; the aliases went in #410 |
| `platform controller list`, `platform controller install` | `nereus nereid list`, `nereus nereid apply` |
| `platform system access list`, `approve` | No new form yet (open, designed later) |
| `platform config installation set`, `show` | No new form yet (open, designed later) |
| `platform config slo set`, `show`, `reset` | No new form yet (open, designed later) |
| `platform release ...`, `platform helm repo ...`, `platform namespace ...`, `platform cloud ...` | The reef's own commands: `nereus <reef> <verb>` |
| `platform login`, `platform user ...` | Old form, no new form: users come through SSO (authentication reef); `nereus user` commands will be designed when Nereus needs them |
| none | `nereus status`, `nereus doctor`, `nereus nereid suggest`, `nereus mandate create` (new) |

The commands of the room moved under the rooms reef (#2076, #2075). Each old name is hidden from the help and prints one line, `<old> moved: run \`<new>\``, exiting 2; `nereus room pull` stays a silent alias, since the hooks of sessions started before #2076 run it, and `nereus mcp local add` rewrites those hooks.

| Old name | New form |
|---|---|
| `nereus room follow` | `nereus rooms follow` |
| `nereus room pull` (a hook's command) | `nereus rooms pull`, the old name still runs |
| `nereus messaging session list` | `nereus rooms peer list` |
| `nereus messaging session create` | `nereus rooms join` (#2075) |

## First implementation step

Before any command of this design is built, the code's binary `platform` became `nereus` and the MCP server's name `platform-mcp` became `nereus-mcp` (#396; the names live in `cli/src/nereus/names.py` and one build setting, `docs/agent/rules.md`), so the legacy commands now run as `nereus system ...`, `nereus config ...`. The sequence after that:

- The kinds `Interface`, `Implementation` and the per-reef classes (`CloudClass`) became `Reef`, `Nereid` and `Mandate` in `core.getnereus.dev/v1alpha1` (#402).
- `nereus init` with no target came with the secrets reef, the `openbao` Nereid, the default `vault` Mandate and its public key (#404).
- `nereus nereid apply keycloak --reef authentication` (then a legacy alias under `system`) added the authentication reef's local Nereid, the authorization server of the claude.ai connector (#407).
- `nereus reef create|apply|list|delete`, `nereus nereid apply|list|get|delete`, `nereus mandate create|apply|list` and `nereus status` came, with `nereus status --output json` as the contract of the first MCP tool, `status`, served today by the Nereus API's `/mcp` (#409, ADR 0029).
- `nereus reef get`, `nereus nereid create`, `nereus mandate get` and `nereus mandate delete` completed the five verbs, and the legacy aliases of `nereus system` went (#410).
