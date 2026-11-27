# What is built

What runs on `main` today, area by area, each with a status chip and where it is decided. [built]

Planned work and ideas are on the [roadmap](../project/roadmap.md); each Reef's commands are in [the Reef pages](reefs/secrets.md).

A chip says how far a feature is: `built` is code on `main`, `planned` has an issue that builds it, `idea` is still being refined.

## The CLI and the model

| Feature | What it gives | Status |
|---|---|---|
| `nereus init` | Prepares a cluster and installs nothing else; settings kept in a file. [ADR 0003](../adr/0003-init-and-nereids-at-runtime.md) | [built] |
| Time limit for `init` | A time SLO for `nereus init`, checked in CI. [spec 0004](../specs/0004-init-time-slo.md) | [built] |
| Installation identity | One `Installation` object per cluster, written by the first `init`. [spec 0006](../specs/0006-installation-identity.md) | [built] |
| Reefs at runtime | `nereus reef create | apply | list | delete`. [ADR 0010](../adr/0010-reefs-at-runtime.md) | [built] |
| Nereids at runtime | `nereus nereid apply` reads the image's labels from the registry. [ADR 0003](../adr/0003-init-and-nereids-at-runtime.md) | [built] |
| Required Reefs | A Nereid is refused when a Reef it requires is missing. [spec 0003](../specs/0003-nereid-conformance.md) | [built] |
| Commands from a Nereid | A Reef's command group is built from data in the Nereid's status. [ADR 0004](../adr/0004-reefs-extend-the-cli.md) | [built] |
| The CLI design commands | `reef`, `nereid`, `mandate` and the conventions. [ADR 0013](../adr/0013-command-conventions.md) | [built] |
| One writer per field | The CLI writes `spec`, a Nereid writes only `status`. [ADR 0005](../adr/0005-one-writer-per-field.md) | [built] |
| Profiles | `core` and `internal-developer-platform`; `nereus profile apply`. [ADR 0014](../adr/0014-profiles.md) | [built] |
| `nereus doctor` | Whether an instance is healthy, from `GET /v1/doctor`. [#799](https://github.com/getnereus/nereus/issues/799) | [built] |
| Swap checked in CI | Swapping a Nereid changes no command. [#124](https://github.com/getnereus/nereus/issues/124) | [built] |
| Untrusted Nereid output | What a Nereid publishes is untrusted input, with a test. [#134](https://github.com/getnereus/nereus/issues/134) | [built] |
| Nereid recovery | A Nereid that stops is reported and recovers by itself. [#133](https://github.com/getnereus/nereus/issues/133) | [built] |

## The Nereus API and MCP

| Feature | What it gives | Status |
|---|---|---|
| Nereus API | `nereus-api` in the cluster; `nereus whoami` calls `GET /v1/me`. [#607](https://github.com/getnereus/nereus/issues/607) | [built] |
| MCP tools from Reefs | A Reef declares tools; the API serves them at `/mcp`. [ADR 0029](../adr/0029-mcp-tools.md) | [built] |
| Chosen MCP tools | `nereus mcp tool enable | disable` in the `Installation`. [#1809](https://github.com/getnereus/nereus/issues/1809) | [built] |
| `/mcp` in Claude Code | `nereus mcp client add claude-code`. [#1880](https://github.com/getnereus/nereus/issues/1880) | [built] |
| `nereus-mcp` retired | The instance's entrance serves `/mcp`. [#1810](https://github.com/getnereus/nereus/issues/1810) | [built] |

## Cloud and identity

| Feature | What it gives | Status |
|---|---|---|
| Reef kinds shipped by a Reef | The `cloud` Reef ships its kind `Cloud` and its Mandate. [spec 0005](../specs/0005-cloud-reef.md) | [built] |
| Cloud plans | A Nereid's plan is checked, approved and run with the person's login. [#307](https://github.com/getnereus/nereus/issues/307) | [built] |
| Requester tags | Every cloud resource says which installation created it and why. [#155](https://github.com/getnereus/nereus/issues/155) | [built] |
| Undercloud | `nereus init --target <name>` brings up the k3d undercloud. [#263](https://github.com/getnereus/nereus/issues/263) | [built] |
| Cloud grants | A Nereid that requires `cloud` is granted access by the person. [#310](https://github.com/getnereus/nereus/issues/310) | [built] |

## Reefs

| Feature | What it gives | Status |
|---|---|---|
| secrets | Vault and Secret, encrypted on the client. [#530](https://github.com/getnereus/nereus/issues/530) | [built] |
| release | Repository, Source, Target and Release. [ADR 0010](../adr/0010-reefs-at-runtime.md) | [built] |
| environment | An Environment per agent, with an expiry; the kept cluster `nereus`. [ADR 0026](../adr/0026-environment-reef.md) | [built] |
| catalog | `Workload`, `Package`, `WorkloadType` and `PackageType`. [ADR 0016](../adr/0016-catalog-reef.md) | [built] |
| database | A PostgreSQL per Database. [ADR 0017](../adr/0017-resource-reefs.md) | [built] |
| messaging | Topics and queues on NATS. [ADR 0019](../adr/0019-messaging-reef.md) | [built] |
| registry | Registry, Repository, publish and purge, with the `zot` Nereid. [ADR 0021](../adr/0021-registry-reef.md) | [built] |
| build | Builds of a Workload's source and Triggers on new commits. [spec 0009](../specs/0009-build-security.md) | [built] |
| scm | A GitHub App Mandate, a Forgejo `Mirror` and a one-hour `Token`. [ADR 0024](../adr/0024-scm-reef.md) | [built] |
| metrics | The `victoriametrics` Nereid. [#742](https://github.com/getnereus/nereus/issues/742) | [built] |
| ideas | The `doris` Nereid and Tide, its portal tab. [#1106](https://github.com/getnereus/nereus/issues/1106) | [built] |
| portal | A PWA that says who you are. [spec 0008](../specs/0008-portal-first-slice.md) | [built] |
| usage | A coding agent's quota window and its forecast. [#1590](https://github.com/getnereus/nereus/issues/1590) | [built] |
| teams | `Team` and `Member` on the tenancy tree. [#1646](https://github.com/getnereus/nereus/issues/1646) | [built] |
| presentations | A deck kept by the platform and a Session to follow. [ADR 0028](../adr/0028-presentations-reef.md) | [built] |
| authorization | `Role` and `Binding`, asked before every read and write. [ADR 0027](../adr/0027-teams-roles-and-users.md) | [built] |

## Building Nereids and the platform

| Feature | What it gives | Status |
|---|---|---|
| `nereid-sdk` | The Nereids' shared library, used by five Nereids. [#754](https://github.com/getnereus/nereus/issues/754) | [built] |
| Nereid template | `scripts/nereid/new --reef <reef> --tool <tool>`. [#752](https://github.com/getnereus/nereus/issues/752) | [built] |
| Reference Nereids | `reference-build`, `reference-delivery`, `reference-registry`. [#1502](https://github.com/getnereus/nereus/issues/1502) | [built] |
| Checks on every pull request | Tests, deck tests, strict docs build, `shellcheck`. [#49](https://github.com/getnereus/nereus/issues/49) | [built] |
| Deploy `main` to live | `scripts/deploy/live`, and the line of `main`. [#162](https://github.com/getnereus/nereus/issues/162) | [built] |
