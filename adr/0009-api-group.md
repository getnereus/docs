# 0009. Each Reef is an API group `<reef>.getnereus.dev`, starting at `v1alpha1`

!!! note "In short"
    Each Reef is its own API group `<reef>.getnereus.dev`, starting at `v1alpha1`; the platform's own kinds live in `core.getnereus.dev`. Status: Proposed (2026-10-17, rewritten 2026-10-25; the first version was Accepted).

**Status:** Proposed (2026-10-17, rewritten 2026-10-25; the 2026-10-17 version was Accepted)

## Context

ADR 0007 asks for an API group on a domain the project controls, not a personal one. The proof of concept used `platform.wasp.silvios.me`, a personal domain, for every CRD. The project now has the domain `getnereus.dev`, and each capability is a Reef (ADR 0002), so the group can say which Reef a resource belongs to.

## Decision

- Each Reef is its own API group: `<reef>.getnereus.dev`, starting at version `v1alpha1` (`secrets.getnereus.dev/v1alpha1`, `authentication.getnereus.dev/v1alpha1`).
- The platform's own kinds (`Reef`, `Nereid`, `Mandate`) live in the `core` Reef's group, `core.getnereus.dev/v1alpha1`.
- The domain is kept in one constant in the CLI and in the generated manifests, so changing it is a one-line change plus a regeneration.

## Consequences

- The CRDs of today's code still use `platform.wasp.silvios.me`; renaming them is a change of its own, and clusters created before it are recreated, with no migration.
- The old group stays in the history. Before opening the repository, either rewrite the history or accept that it stays visible.
- A Reef's version moves on its own (`v1alpha1`, `v1beta1`, `v1`), independent of the others.

*Rewritten 2026-10-25 from voice session; raw data in Drive #pontos/raw/2026-10-25. Rewritten again 2026-10-25 (order 20261025-1805): the platform's own kinds live in `core.getnereus.dev/v1alpha1`.*
