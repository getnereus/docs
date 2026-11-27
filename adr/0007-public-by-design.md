# 0007. Public by design: Apache-2.0, no identifying data in the history

!!! note "In short"
    The project is Apache-2.0 and public by design: no identifying data in any commit, and public names chosen as if already public. Status: Accepted (2026-10-17).

**Status:** Accepted (2026-10-17)

## Context

The repository starts private and is meant to be opened, so other projects can build their platform with it. When a repository goes public, its whole history goes with it, and the names it chose (API group, image names, commands) become a contract with whoever uses it.

## Decision

- **License: Apache-2.0**, the license of Kubernetes, Helm, Argo and Crossplane: companies can adopt it without legal review, and it carries a patent grant.
- **No identifying data in any commit:** no e-mails, personal or company names, internal domains, tenant or account ids, tokens. Examples use `example.com`, `maria@example.com`, `123456789012`. Personal notes live in `CLAUDE.local.md`, which is gitignored.
- **Public names are chosen as if already public:** the Kubernetes API group, image names and CLI commands.

## Consequences

- A leaked value is fixed by rewriting history before the repository is opened, which gets harder with every clone. Review diffs for identifying data before each push.

## Open questions

- **The API group** of the CRDs: answered by ADR 0009, `<reef>.getnereus.dev`, a domain the project controls.
- **Contributions:** whether to require DCO sign-off (`Signed-off-by`) from the first external contribution.

*Aligned in wording 2026-10-25 from voice session (Reef, Nereid, Mandate, `nereus`); raw data in Drive #pontos/raw/2026-10-25.*
