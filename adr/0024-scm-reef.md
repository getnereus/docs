# 0024. The scm reef: a Connection names a source host's organisation, reached through the App its scm Mandate names

!!! note "In short"
    An `scm` reef holds what a source host is to Nereus: a `Connection` names an organisation, reached through the App its scm Mandate names, and a `Mirror` copies a repository. Status: Proposed.

**Status:** Proposed

## Context

#927 asks Nereus to reach a source host as an application, not as a person. The first need is the catalog Nereid (#904): `getnereus/nereus` is private, so its entries report `SourceResolved` False `SourceUnreachable` ("a private one needs a connection"). Three more wait on the same answer: #1070 (a Build clones a private repository with a token minted for that build alone), #1250 (publishing to ghcr.io with a short-lived App token instead of a personal one) and #1255 (the forgejo Nereid mirrors a GitHub repository into the cluster).

The first version of this ADR put everything in the scm reef: the GitHub App (its id and key, with a vendor flag), a command to verify it and the `Token` lent to a consumer. Two of those are not a source host's concern: the App is the platform's identity towards GitHub, which #234 (the platform's own identity towards external systems) asks to keep in one place, and the token serves #1250, which publishes a package and reads no source. ADR 0006 (the authentication reef) now holds both: the App is a Mandate of the `github` Nereid, and the `Token` is a kind of the authentication reef.

What exists: `nereus secrets create` seals a value on the client with the vault Mandate's public key, and a `SecretBinding` turns a secret into a Kubernetes Secret in a namespace the vault allows; ADR 0023 (an external registry's push credential) has a Nereid read its credential that way, never the person. A working version exists outside this repository (wasp-idp's `scm connection`, its ADR 0025), with the per-organisation statuses this ADR keeps.

## Decision

**An `scm` reef, `scm.getnereus.dev/v1alpha1`, holds what a source host is to Nereus: an organisation reached, a repository mirrored, a push received.** Who the platform is towards the host belongs to the authentication reef (ADR 0006). One writer per field (ADR 0005); the commands follow ADR 0013 (command conventions), and the deck is `docs/specs/cli/reefs/scm.yaml`.

| Kind | `spec` (the person, or a Nereid as a client) | `status` (the Nereid only) |
|---|---|---|
| `Mirror` | `from` (a public `https://<host>/<owner>/<repository>`), `interval` (`10m` by default), `mandate` | `observedGeneration`, `conditions`, `nereid`, `mandate`, `repository`, `url`, `branch`, `commit`, `lastSync` |
| `Connection` (default) | `org`, `mandate` (an scm Mandate, ADR 0011; empty: the reef's default), `default` | `observedGeneration`, `conditions`, `nereid`, `mandate`, `installationId`, `repositorySelection`, `permissions` |

```bash
nereus nereid apply github --reef authentication --reef scm
nereus mandate create github-scm --reef scm --nereid github --param identity=github --default
nereus scm connection create example --org example
# ✓ scm/connections/example created (mandate github-scm)
nereus mandate create github-scm-labs --reef scm --nereid github --param identity=other-app
nereus scm connection create labs --org example-labs --mandate github-scm-labs
```

- **A Connection is one organisation of one host, reached through the App its scm Mandate names** (owner, 2026-11-09). It names no vendor, no App and no key. `--mandate` keeps ADR 0011's meaning, a Mandate of the object's own reef: an scm Mandate, with none the reef's default. That Mandate's param `identity` names the authentication Mandate whose App reaches the organisation (ADR 0006); a second App is a second scm Mandate, so no command gains a flag that points into another reef. The host is the Nereid's, never an attribute the API reads.
- **The statuses are per organisation and stay on the Connection,** in this order: `NotInstalled` (the App is not installed on the organisation), `NotAllRepositories` (installed on a selection), `MissingPermissions` (less than asked), `Ready`. There is no `verify` command: `nereus scm connection get` and `list` show the status.
- **Permissions start at `metadata` and `contents` read** (owner, 2026-11-09), the least #904 needs. A feature that needs more widens them in its own issue, and the Connection reports `MissingPermissions` until the App's owner accepts the new ones.
- **`--default` on a Connection, one in the reef.** A second default is refused.
- **One `github` Nereid serves both reefs, opt-in** (owner, 2026-11-09): `nereus nereid apply github --reef authentication --reef scm`. The `internal-developer-platform` profile does not install it, since it needs an App the person owns. The scm reef's own Mandate says which Nereid serves Connections and, through `identity`, which App they use; Mandate names are global, so it takes its own name by the convention `<nereid>-<reef>` (`github-scm`; owner, 2026-11-09), which a second host follows too (`forgejo`).
- **The App has one webhook, received by the scm reef** (owner, 2026-11-09): the webhook's secret is a param of the authentication Mandate (the App's), and its URL points at the scm reef's receiver, which checks the signature before anything reads the event. The push webhook of #914 (a push starts a build) builds on it.
- **`Mirror` copies one public repository into the cluster, with no Connection** (#1255, owner, 2026-11-10): a public source needs no App. It goes through an scm Mandate like a Connection, and the CLI refuses one whose Nereid does not list `mirrors` in its `status.kinds`. The `forgejo` Nereid serves it through its own Mandate `forgejo`; the `internal-developer-platform` profile installs it, with `forgejo` as the scm reef's default, since the profile runs on open source and the `github` Nereid is not in it; a `github-scm` Mandate takes the default only when asked (#1327, owner, 2026-11-11): Forgejo from its upstream Helm chart through the release reef, on SQLite, its admin sealed into the secrets reef, copying from `github.com` only unless the setting `MIRROR_ALLOWED_DOMAINS` adds a host. One Mirror per place (`<owner>/<repository>`, any case); the oldest keeps it, the other is `Taken`.
- **No `Token` here:** a consumer that needs to read a repository asks the authentication reef's `Token` (ADR 0006, #1274).

## Prior art

- GitHub, [Generating an installation access token for a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app): the installation and its repository selection, which the Connection's status reports.
- GitHub, [Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries): the HMAC signature the scm reef's receiver checks.
- Flux, [GitRepository](https://fluxcd.io/flux/components/source/gitrepositories/), and Argo CD, [Private repositories](https://argo-cd.readthedocs.io/en/stable/user-guide/private-repositories/): both reach GitHub with a GitHub App's credential held by the controller, never by the person.
- wasp-idp's `scm connection` and its ADR 0025 (SCM connections in the platform API): the per-organisation statuses, ported here with Nereus's verbs.

## Consequences

- The catalog Nereid resolves a private repository's commit with an authentication `Token` (#1274), with no Connection needed; `SourceUnreachable` stays for a repository no App reaches.
- #1281 builds the Connection and the receiver, after #1273 (the github Nereid's Mandate); #927 closes with it.
- Another host needs only another Nereid serving both reefs: the commands and kinds stay.
- OWASP A01 (broken access control: a Connection exposes an organisation's status, never a credential) and A08 (software and data integrity failures: a webhook event is trusted only after its signature checks) are the categories this reef touches; the key and the token are ADR 0006's.

*Origin: the owner's cut of #927 into #1272, #1273, #1274 and #1275, and the decisions above, on 2026-11-09. Raw data in Drive `#pontos/raw/2026-11-09/`.*

*Rewritten 2026-11-09 from the owner's decisions on #927 (the App is a Mandate of the authentication reef, the Token is its kind, no `--vendor`, no `verify`; #1280); raw data in Drive `#pontos/raw/2026-11-09/`.*
