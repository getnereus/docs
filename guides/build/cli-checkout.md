# Run the CLI from a checkout

Put `nereus` on the `PATH` from a checkout of the repository, editable: a change in `cli/` takes effect at the next run.

## Before you start

- A checkout of `github.com/getnereus/nereus` and [uv](https://docs.astral.sh/uv/).

## Steps

### 1. Install it editable

```bash
make cli
```

It also installs `nrs`, the same program under a short name for typing ([#606](https://github.com/getnereus/nereus/issues/606)). It replaces any other `nereus` installed with `uv tool`.

### 2. Turn on Tab completion

From bash or zsh, for `nereus` and `nrs`, then open a new terminal:

```bash
nereus --install-completion
```

`nrs <Tab>` lists the commands, `nrs nereid apply --<Tab>` the options, and `nrs reef get <Tab>` the Reefs the CLI last saw on the cluster, with no call to it ([#795](https://github.com/getnereus/nereus/issues/795)).

## Check it worked

[`nereus --help`](../../specs/cli/core.html#groups) lists the command groups. `git pull` updates the CLI; `nereus upgrade` refuses an editable install.

## Clean up

`make cli-uninstall` removes `nereus` and `nrs`.

## Next

[Prepare the cluster](../../start/init.md): a checkout's `init` installs the Nereids from the local registry, after `make nereids`.

## Learn more

- [Start a new Nereid](new-nereid.md) from the template.
- [Keep the CLI up to date](../operate/cli-update.md), for a CLI installed from a release.
