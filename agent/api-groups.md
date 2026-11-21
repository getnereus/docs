# API groups

**Status: proposed, to be written as an ADR and reviewed with the owner.** Until that ADR is accepted, this page records the intent, not a rule.

An API group is a reef ([The CLI design](cli.md)): `<reef>.getnereus.dev/v1alpha1`, for example `secrets.getnereus.dev/v1alpha1`.

1. Every new idea is first modelled as an API group (a reef), before any Nereid.
2. Then we design how the API and the CLI interact with it, as CLI examples first.
3. Every API group is born with the standard verbs of ADR 0013 (command conventions), kubectl's: `create` fails when the thing exists and lists the `apply` commands to run; `apply` creates or updates (it is the update verb); plus `list`, `get` and `delete`. Any other verb is an API extension.
4. Every API group has a reference Nereid: once installed, the CLI answers every command and the resources are really created in Kubernetes. It is one Nereid for every reef (`controllers/reference`, #486), the subject of each reef's TCK: a reef is a module of its `reefs/`, the Nereid `reference-<reef>`, and every real Nereid of the reef must behave as it does. A port adds the reef's module there ("A port adds its reef" in its README). Not to be confused with a *fake*, an imitation of an outside tool's API that tests a real Nereid without the tool (`test/fake-github`).

Open points for the ADR:

- The CRDs follow ADR 0009 (#20): a reef's own kinds in `<reef>.getnereus.dev/v1alpha1` (`clouds.cloud.getnereus.dev`), the platform's in `core.getnereus.dev/v1alpha1`, which also prefixes the keys of the platform's labels and annotations. The platform's kinds are `Reef`, `Nereid` and `Mandate` (renamed by #402).
