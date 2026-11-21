# Install the CLI

Install `nereus`, the CLI of the platform, on Linux (x86_64 or aarch64); the installer fetches [uv](https://docs.astral.sh/uv/) when it is missing.

## Run

Install the latest release:

```bash
curl -fsSL https://getnereus.github.io/install/install.sh | sh
```

Check that it answers:

```bash
nereus --help
```

``` { .text .output title="output" }
Usage: nereus [OPTIONS] COMMAND [ARGS]...

  nereus: a composable API platform: reefs add the APIs, Nereids look after
  them, installed at runtime.
```

## What you get

- `nereus`, and `nrs`, the same program under a short name for typing.
- A CLI that upgrades itself in the background; `NEREUS_AUTO_UPGRADE=off` turns that off.
- No cluster yet: the CLI prepares one in the next steps.

## Next

[Write the settings](settings.md) of your first installation.
