# 0008. The CLI is written in Python, with uv and typer

!!! note "In short"
    The CLI is written in Python, managed with `uv`, with `typer` for commands and the official `kubernetes` client. Status: Accepted (2026-10-17).

**Status:** Accepted (2026-10-17)

## Context

The first slice (spec 0001) needs a CLI that talks to a cluster and builds command groups at runtime from what reefs and Nereids publish (ADR 0004). Go gives one static binary and the `kubectl`/`helm`/`k3d` toolchain (`client-go`, `cobra`); Python gives a faster start and simpler dynamic command building.

## Decision

The CLI is written in Python, managed with `uv`, with `typer` for commands and the official `kubernetes` client for the cluster. The binary name is set in one place: the `[project.scripts]` entry of `pyproject.toml` (`platform` in today's code, `nereus` in the new design).

## Consequences

- The proof of concept moves faster: commands built from data are plain Python objects, with no code generation.
- Users need a Python runtime; `uv tool install` covers it. Distribution as a single binary is harder and is revisited before the project is opened.
- The fake Controller (spec 0001) can share the language, but it does not have to: it only speaks HTTP and writes `status`.

*Aligned in wording 2026-10-25 from voice session (reef, Nereid, Mandate, `nereus`); raw data in Drive #pontos/raw/2026-10-25.*
