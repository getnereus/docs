# 0002. Conceptual model: Reef, Instance, Mandate, Nereid, Tool

!!! note "In short"
    The platform is five layers plus Vendor: Reef, Instance, Mandate, Nereid and Tool. A Reef is a capability, an API group, and may exist with no Nereid. Status: Proposed (2026-10-17, rewritten 2026-10-25).

**Status:** Proposed (2026-10-17, rewritten 2026-10-25)

## Context

An Internal Developer Platform offers capabilities (a database, an environment, a login, a place for secrets) that are delivered differently in each place: a Postgres in the cluster or a managed one, Keycloak or Auth0, Azure Key Vault or OpenBao. Without a shared vocabulary, the API ends up knowing each implementation by name, and swapping one means changing the API.

Kubernetes already solved this for storage and traffic: a PersistentVolumeClaim names a StorageClass, the StorageClass names a provisioner, and the provisioner is the only part that knows the storage backend and holds its credentials. Gateway API does the same with Gateway, GatewayClass and `controllerName`.

## Decision

The platform is described in five layers, plus Vendor as an attribute:

| Layer | Answers | Kubernetes | Platform |
|---|---|---|---|
| Reef | what exists? | traffic entry | `secrets`, `authentication`, `release` |
| Instance | which occurrence, whose? | Gateway `shop-edge` | `secret/google-sso`, a database for an app |
| Mandate | which Nereid handles this Reef here, with which parameters? | GatewayClass `aws-alb`, StorageClass | `vault` (secrets by `azure-key-vault`), `corporate` (authentication by `keycloak`) |
| Nereid | who fulfils the contract? | the provisioner, `gateway.k8s.aws/alb` | `azure-key-vault`, `keycloak`, `sao` |
| Tool | what does it work with? | the ELB API | Azure Key Vault, the Auth0 Management API |
| Vendor (attribute) | whose thing is it? | AWS | Microsoft, Auth0, local |

- **A Reef is a capability, an API group** `<reef>.getnereus.dev/v1alpha1` (ADR 0009). A Reef can exist with no Nereid; it then waits. The `core` Reef is built in.
- **A Nereid is a controller installed in the platform**, top-level, with a name global to the platform. One Nereid may look after many Reefs, as one controller manager looks after many kinds; one Reef may have many Nereids. Its name is free: the Tool's name (`keycloak`) or a name from the myth (`sao`, `nereus nereid suggest`).
- **A Nereid owns its authentication and its default target parameters** (for example `authentication=workload-identity` and a default `vaultUrl`), as the provisioner holds the credentials and the StorageClass only selects. They are set once, when the Nereid is added.
- **A Mandate binds one Reef to one Nereid.** It may override the Nereid's target parameters with `--param` (a Nereid may serve several vaults); one Mandate per Reef is the default. A Mandate's `match` may also route requests (ADR 0017).
- **The platform's own kinds are `Reef`, `Nereid` and `Mandate`**, in the API group `core.getnereus.dev/v1alpha1`, owned by the `core` Reef (ADR 0009). Today's code names them `Interface`, `Implementation` and a per-reef class such as `CloudClass`, in `platform.wasp.silvios.me` (current code, to be renamed).
- **The API knows Reefs and Instances, never a Nereid by name.** It reads what the Nereid publishes in `status` and acts on that.
- **The person asking names the Reef, never the Tool.** The Mandate, when not given, is the Reef's default, and it is recorded in the Instance's `status`.
- The word is Nereid; Controller, as in Kubernetes, is the mechanism that runs it (ADR 0011). "Driver", "plugin" and "provider" are not used for either.

## Prior art

- **Kubernetes storage classes and Gateway API** ([StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/); [GatewayClass](https://gateway-api.sigs.k8s.io/reference/api-types/gatewayclass/)): a claim names a class, the class names who fulfils it, and only that part knows the backend; the model takes that split for every capability, with the Mandate in the role of the class.

## Consequences

- Swapping a Nereid (Keycloak for Auth0) changes no API code: only which Mandate is the default and what the Nereid publishes.
- Each Reef needs a written contract: the fields a Nereid must publish for the API and the CLI to work, and the capabilities it must offer (for `secrets`, client-side encryption, ADR 0011).
- Credentials of a Tool are never repeated per Mandate: they live with the Nereid.

*Rewritten 2026-10-25 from voice session; raw data in Drive #pontos/raw/2026-10-25. Rewritten again 2026-10-25 (order 20261025-1724): "Mandate" is the working term and "Instance" keeps its name. Rewritten again 2026-10-25 (order 20261025-1805): the kinds are `Reef`, `Nereid` and `Mandate` in `core.getnereus.dev/v1alpha1`.*
