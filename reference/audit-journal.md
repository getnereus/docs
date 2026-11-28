# The audit journal

The audit journal is the installation's history from `nereus init` on: a file on the machine that runs `init`, one CloudEvent per line, each chained to the line before by its hash ([#2385](https://github.com/getnereus/nereus/issues/2385)).

## Where it is

One file per installation, under the CLI's state folder: `${XDG_STATE_HOME:-~/.local/state}/nereus/installations/<installation id>/audit/journal.jsonl`, the file `0600` in folders `0700`. `init` prints its path:

```text
Audit journal: ~/.local/state/nereus/installations/<installation id>/audit/journal.jsonl
```

A second `init` of the same installation continues the same chain. A run that fails before the cluster holds its Installation writes to the settings file's id, else to a journal of its own.

## What init records

Init started, each Reef and Nereid installed or failed, and init ended, succeeded or failed. A failed `init` still leaves its entries. [`nereus audit list`](../specs/cli/core.html#audit-list) prints them, oldest first:

```bash
nereus audit list
```

``` { .text .output title="output" }
SEQUENCE  TIME                  TYPE                                     ACTOR           OUTCOME
1         2026-11-28T09:06:36Z  dev.getnereus.core.installation.init.v1  local:f5198a52  started
2         2026-11-28T09:06:36Z  dev.getnereus.core.reef.installed.v1     local:f5198a52  succeeded
3         2026-11-28T09:06:36Z  dev.getnereus.core.reef.installed.v1     local:f5198a52  succeeded
4         2026-11-28T09:06:36Z  dev.getnereus.core.installation.init.v1  local:f5198a52  succeeded

Next steps:

  nereus audit verify
```

`--since 1d12h` keeps the entries of the last day and a half (days `d`, hours `h` and minutes `m`); `--output json` prints the lines as they are written; `--installation <id>` reads another installation's journal.

## The entry

Each line is a CloudEvent 1.0 in its JSON format, the envelope of ADR 0019 (the messaging Reef), with four extension attributes:

| Attribute | What it holds |
|---|---|
| `sequence` | 1 for the first entry, then one more per line |
| `previoushash` | `sha256:` and the SHA-256 of the line before, its bytes as written, without the newline |
| `correlationid` | the run's id, the same on every entry of one `init` |
| `actor` | who ran it: `local:<hash>` for a person on this machine with no login |

The first entry's `previoushash` is the genesis value, `sha256:` and 64 zeros. The schema version is the type's `.v1` suffix and the `dataschema`; a renamed attribute is a new version.

## What it never holds

Never a secret, a token, a header or a value. A credential is named by its identity: the kubeconfig context's name, or a signed-in person's issuer, subject and token id.

The client's version, operating system, architecture and session id go in clear.

The operating system's user and the host name go in only as SHA-256 hashes, salted with a random value made at the installation's first entry and kept in its folder, outside `audit/`, never in the journal (LGPD).

!!! note
    Whoever holds both the salt and the journal can test a guessed user or host name against its hash.

## Verify it

[`nereus audit verify`](../specs/cli/core.html#audit-verify) checks that every entry carries the hash of the one before:

```bash
nereus audit verify
```

``` { .text .output title="output" }
✓ Verified 4 entries of ~/.local/state/nereus/installations/0b5a3f2e-8c1d-4e7f-9a2b-3c4d5e6f7a8b/audit/journal.jsonl: the chain is whole, its head is sha256:ea72889cd7ff.

Next steps:

  nereus audit list
```

After a byte of entry 2 changed, it names the first broken entry and exits 1; a line removed or two lines swapped are named the same way (`Entry 2 is missing`, `Entry 2 is out of place`):

``` { .text .output title="output" }
✗ Entry 2 does not match the hash entry 3 carries: the journal was changed after it was written; check: nereus audit list --installation 0b5a3f2e-8c1d-4e7f-9a2b-3c4d5e6f7a8b --output json
```

## What it does not prove yet

The chain shows a change in the middle of the file. It does not stop whoever owns the machine from rewriting the whole file, or from changing the last line, which no later entry vouches for.

The proof against that is the journey's next steps ([#2173](https://github.com/getnereus/nereus/issues/2173)): the `audit` Reef's Nereids taking the journal over ([#2386](https://github.com/getnereus/nereus/issues/2386)), WORM storage and signed checkpoints.

Each append takes an exclusive lock on the file: a second run that cannot take it within 5 seconds fails and says so, and never writes out of order.
