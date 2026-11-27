# 0005. One writer per field: `spec` by the API, `status` by the Nereid

!!! note "In short"
    The API writes `spec`; each Nereid writes only its own part of `status`. A field that needs two writers is split. Status: Proposed (2026-10-17).

**Status:** Proposed (2026-10-17)

## Context

With Nereids swapped and added at runtime, several processes touch the same objects. When two of them write the same field, the last write wins and the bug shows up far from its cause.

## Decision

- The API (or the CLI, before the API exists) writes `spec`: what was asked.
- Each Nereid (its controller) writes only its own part of `status`: what it did and what it publishes. When several Nereids look after the same Reef side by side, each writes under its own key, `status.nereids.<name>`.
- Choosing which Nereid handles a request is a Mandate's `spec` (ADR 0002), written through the API.

## Prior art

- **Kubernetes API conventions, "Spec and Status"** ([kubernetes/community](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md#spec-and-status); [Kubernetes objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/#object-spec-and-status)): `spec` is the desired state, written by its user, and `status` the observed state, written by the system; this ADR takes the split as is and adds one key per Nereid under `status`.
- **The controller pattern** ([Kubernetes, "Controllers"](https://kubernetes.io/docs/concepts/architecture/controller/)): a control loop that reads the desired state, works towards it and reports what it observes.

## Consequences

- Every new field is designed with its writer. A field that needs two writers is split.
- Reading `status` is how the API and the CLI learn what a Nereid offers: endpoints, commands (ADR 0004), readiness.
- **One handover, for held objects** (ADR 0031): while an object carries the hold of a soft gate, the `authorization` Reef's gate Nereid is the one writer of its `status`; the kind's own Nereid writes it from the moment the API lifts the hold.

*Aligned in wording 2026-10-25 from voice session (Reef, Nereid, Mandate, `nereus`); raw data in Drive #pontos/raw/2026-10-25.*
