# The checks

`make checks` runs six checks locally, because CI is off, and records each result in `docs/checks/<name>.json`.

Run one check alone with `make <name>`. Its record holds the result, the time, how many checks passed, the first failure and the commit.

## make checks

| Check | What it checks | Record |
|---|---|---|
| `lint` | ruff on the CLI, the Python scripts, the sessions sketch and nereid-sdk: pycodestyle, pyflakes, complexity at most 10 | `lint.json` |
| `test` | the unit tests of the CLI, the Nereids, the API, the hooks and the scripts, after `nereid-check` and `cli-check` | `test.json` |
| `deck-test` | the deck renderer and the follow page, in headless Chromium | `deck-test.json` |
| `docs-build` | the docs lint, then a strict build of the site | `docs-build.json` |
| `shellcheck` | shellcheck on every bash script of the repository | `shellcheck.json` |
| `kubeconfig-ban` | no kubeconfig access in the CLI outside `nereus init`, against an allowlist that only shrinks | `kubeconfig-ban.json` |
| `mcp-coverage` | every Reef kind readable through the MCP server's generic tools (a list route on the Nereus API), against an allowlist that only shrinks (#2294) | `mcp-coverage.json` |

## Before a pull request

Run `make checks` always. Add `make scene-core` when the change touches a cluster, and `make catalog-check` when it touches `catalog/`, `reefs/catalog/` or the tenancy.

## Scenes

A scene runs a Reef end to end on a throwaway k3d cluster, and `make scene-<name>` records `scene-<name>.json` beside the checks. Scenes with the real tools run only on the owner's word.

| Scene | Runs | When |
|---|---|---|
| `scene-core` | the core with a reference Nereid in place of every tool | the change touches a cluster |
| `scene` | the platform end to end, with the real tools | the owner's word |
| `scene-idp` | the profile `internal-developer-platform` | the owner's word |
| `scene-helm` | Nereus from the charts alone, no `nereus init` | the owner's word |
| `scene-<reef>` | one Reef with its tool: `release`, `environment`, `messaging`, `delivery`, `build` | the owner's word |

## Next

[What is built](what-is-built.md) says what each Reef delivers today.
