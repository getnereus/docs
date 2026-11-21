# Deploy main to the live cluster

Upgrade the `live` cluster in place to the commit of `main`, from the published charts, and check it with the smoke test.

## Before you start

- `live` is today the kept cluster `k3d-nereus` (see [Rebuild the kept cluster](kept-cluster.md)). The scenes use it too, so the script refuses it without `--allow-kept-cluster`, and the other sessions on the repository are asked first.
- A clone of the repository: the script runs on your machine, by hand; no GitHub Action is involved, and the trigger on every push comes later (#914).
- `NEREUS_LIVE_CONTEXT=k3d-nereus` exported, the kubeconfig context the script uses; `kubectl --context k3d-nereus get nodes` answers.

## Steps

### 1. See the plan

A dry run prints every command, resolves the commit of `main` and touches nothing.

```bash
scripts/deploy/live --allow-kept-cluster --dry-run
```

### 2. Deploy and test

The script fetches `origin/main`, runs `helm upgrade --install` for `nereus-reefs`, then `nereus`, from `oci://ghcr.io/getnereus/nereus/charts`, records the commit as the annotation `deploy.getnereus.dev/commit` on `nereus-system`, then runs the smoke test. The first run on a cluster names the installation, which never changes after that.

```bash
scripts/deploy/live --allow-kept-cluster --installation-name nereus
```

A failed upgrade ends the run before the commit is recorded. Each upgrade runs with `--force-conflicts`: on `live`, the chart decides over a field another manager changed.

### 3. Drop values the chart owns now

A release installed by hand or by `nereus init` may hold values such as an `image` pointing at the local registry. `--reset-values` drops them, so the chart's published images, by digest, apply; give the installation's name again.

```bash
scripts/deploy/live --allow-kept-cluster --reset-values --installation-name nereus
```

### 4. Verify main before it is published

`scripts/deploy/line` compares the new `main` with the last green commit, else the highest tag, on the paths a release is built from, and runs `make scene-core` on it in a kept worktree. A merge that changed none of those paths is green by inheritance.

```bash
scripts/deploy/line run
```

``` { .text .output title="output" }
fetch: origin/main is dde5f73 (last verified none)
paths: changed since v0.1.8: api/ cli/ controllers/ Makefile
scene: make scene-core on dde5f73 in ../nereus-line
ok: scene-core passed in 13m05s
publish: off (would run: make release)
== line green: dde5f73
```

A failed scene marks the line red, keeps its log in `~/.local/state/nereus/line/<commit>.log` and exits non-zero. `run --publish` runs `make release` only after a green scene; a file `.deploy-paused` in the main clone's root suspends every run.

## Check it worked

The smoke test only reads: every Deployment of `nereus-system` rolled out, the annotation equals the commit, the API answers `/healthz`, and [`nereus doctor`](../../specs/cli/core.html#doctor) passes. Run it alone any time.

```bash
scripts/deploy/live --allow-kept-cluster --smoke-only
```

`scripts/deploy/line status` shows the last verified commit and whether the line is paused.

```bash
scripts/deploy/line status
```

``` { .text .output title="output" }
main     dde5f73  green  2026-11-15 05:25  scene-core 13m05s
paused   no   (<main clone>/.deploy-paused)
```

## Next

- [Meet the time SLO](slo.md) for the scenes the line runs.

## Learn more

- `scripts/deploy/live --help`: the settings, all options or environment variables (`NEREUS_CHART_REF`, `NEREUS_CHART_VERSION`, `NEREUS_LIVE_INGRESS_ADDRESS`), so the repository holds no address or token.
- The line is a stand-in: on the platform, naxos mirrors `main` and builds it (#159, #1613).
