# Keep the CLI up to date

Keep a `nereus` installed from a release up to date: it upgrades itself in the background, and you choose how ([#1782](https://github.com/getnereus/nereus/issues/1782)).

## Before you start

- `nereus` installed from a release, as in [Install the CLI](../../start/install.md). An editable install from a checkout updates with `git pull` instead: [Run the CLI from a checkout](../build/cli-checkout.md).

## Steps

### 1. Let it upgrade itself

At most once a day, a call starts `nereus upgrade --background` on its own, detached, and the next call says so on stderr:

``` { .text .output title="output" }
nereus upgraded 0.1.22 → 0.1.23
```

The worker reads the release manifest (`latest.json` of the `getnereus/install` releases), refuses a wheel whose sha256 differs, and installs it with `uv tool install --force`. It logs to `~/.local/state/nereus/upgrade.log` (`$XDG_STATE_HOME`).

### 2. Upgrade now, or only look

```bash
nereus upgrade
```

`nereus upgrade --check` only says which release is the latest.

### 3. Choose how it upgrades

The CLI's config, `~/.config/nereus/config.yaml`, holds the mode: `background` installs (the default), `notify` only says that a release is available, `off` never looks.

```bash
nereus config set auto_upgrade notify
```

`nereus config set check_interval 7d` looks once a week. For one shell, `NEREUS_AUTO_UPGRADE=off` wins over the config.

## Check it worked

`nereus --version` prints the release you upgraded to. It never upgrades on its own an editable install, a dev version (`0.1.23.dev4`), a run with `CI` set, or shell completion.

## Next

[Write the settings](../../start/settings.md) of an installation, or [prepare a cluster for Nereus](cluster.md).

## Learn more

- `NEREUS_VERSION=0.1.23` pins a version at install time; `sh -s -- --help` lists the installer's options.
- [The settings file](../../reference/settings.md) holds the settings of `nereus init`, not the CLI's own config.
