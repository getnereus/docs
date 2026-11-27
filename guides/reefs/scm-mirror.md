# Mirror a repository

Copy a public Git repository into the cluster, where the `forgejo` Nereid keeps it in a Forgejo it runs, pulled again on an interval. A public source needs no [Connection](scm-connection.md) and no App.

## Before you start

- The release Reef with the flux Nereid, and the secrets Reef with the openbao Nereid and the vault `default`: Forgejo comes from its upstream chart through the release Reef, and its admin is sealed into the vault.
- The profile `internal-developer-platform` brings the scm Reef and the forgejo Nereid already: then go to step 2.

## Steps

### 1. Apply the scm Reef and the forgejo Nereid

```bash
nereus reef apply scm
```

``` { .text .output title="output" }
✓ core/reefs/scm created (scm.getnereus.dev/v1alpha1: connections)
```

[`nereus nereid apply`](../../specs/cli/reefs/scm.html#mirror-apply) installs the Nereid. It makes its own Mandate `forgejo`, asks the release Reef for Forgejo (SQLite on a volume, no Ingress) and makes Forgejo's admin.

```bash
nereus nereid apply forgejo \
  --reef scm
```

``` { .text .output title="output" }
✓ core/nereids/forgejo created, Ready: see 'nereus scm --help'
  core/mandates/forgejo created (reef: scm, nereid: forgejo)

Next steps:

  nereus scm mirror create <name> --from https://github.com/<owner>/<repository>
```

Forgejo copies from `github.com` only. The Nereid's setting `MIRROR_ALLOWED_DOMAINS` adds hosts, comma-separated (`--set MIRROR_ALLOWED_DOMAINS=git.example.com`).

### 2. Mirror a repository

[`nereus scm mirror create`](../../specs/cli/reefs/scm.html#mirror-create) copies the repository at `--from`, pulled again every `--interval`. It goes through `--mandate`, else the Reef's default Mandate; a Mandate whose Nereid serves no mirrors, such as `github-scm`, is refused.

```bash
nereus scm mirror create nereus \
  --from https://github.com/getnereus/nereus \
  --interval 10m
```

``` { .text .output title="output" }
✓ scm/mirrors/nereus created (mandate forgejo)

Next steps:

  nereus scm mirror get nereus
```

A source is `https://`. A plain `http://` host in the cluster needs both `--allow-http` here and the setting `MIRROR_ALLOW_HTTP=true` on the Nereid.

## Check it worked

[`nereus scm mirror list`](../../specs/cli/reefs/scm.html#mirror-list) shows the commit each copy holds: `Syncing` until the first pull, then `Ready`.

```bash
nereus scm mirror list
```

``` { .text .output title="output" }
MIRROR   FROM                                       MANDATE  LAST SYNC             COMMIT   STATUS
nereus   https://github.com/getnereus/nereus        forgejo  2026-11-10T12:00:00Z  68d7a0d  Ready
outside  https://example.com/example/outside        forgejo  -                     -        SourceUnreachable
```

`nereus scm mirror get` adds the address the cluster clones from, and the default branch.

```bash
nereus scm mirror get nereus
```

``` { .text .output title="output" }
Name:         nereus
From:         https://github.com/getnereus/nereus
Interval:     10m
Mandate:      forgejo
Nereid:       forgejo
Status:       Ready
Repository:   getnereus/nereus
Clone:        http://forgejo-http.nereus-system-forgejo.svc:3000/getnereus/nereus.git
Branch:       main
Commit:       68d7a0d6f1c2b3a4d5e6f708192a3b4c5d6e7f80
Last sync:    2026-11-10T12:00:00Z
Message:      getnereus/nereus holds 68d7a0d6f1c2 of main, pulled every 10m.
```

Any other status names what to fix:

| Status | Meaning |
|---|---|
| `SourceUnreachable` | a host outside `MIRROR_ALLOWED_DOMAINS`, a repository that is not there, or a plain `http://` source without `MIRROR_ALLOW_HTTP` |
| `Taken` | another Mirror, the oldest, holds the same `<owner>/<repository>`, or Forgejo holds one there copied from another source |
| `NoMandate` | no scm Mandate names the forgejo Nereid |
| `WaitingForForgejo` | Forgejo is not up yet; the message gives the reason the Mandate `forgejo` carries |

## Clean up

`nereus scm mirror delete` removes the copy in Forgejo too, never the source.

```bash
nereus scm mirror delete nereus
```

## Next

- [Connect an organisation](scm-connection.md) to reach its private repositories through a GitHub App.

## Learn more

- [The scm Reef](../../reference/reefs/scm.md): Connections and Mirrors, every command.
