# 0032. Machines assume a role in a person's name: a key pair signs in, the Nereus API hands a short token that never exceeds the person

!!! note "In short"
    A `Machine` of core signs a short assertion with its own key and asks the Nereus API for a role bound to it; the API answers with a token of minutes that acts in the name of the machine's person and never grants more than that person holds. The first role is `usage-reporter`: the owner's status line reports the usage window with no login to expire. Status: Accepted (2026-11-28).

**Status:** Accepted (2026-11-28)

## Context

ADR 0025 (the metrics intake) decided machine identities: a `Machine` of core with a key pair made on the machine, an assertion checked by the Nereus API against its public key, and a short token of the API's own, with no login Nereid involved (ADR 0006 points there as the one exception to OIDC). It was step 7 of #1565 and is not built.

On 2026-11-28 the portal's Usage tab stayed at 66% for nine hours while the real share was 68%. The owner's status line runs `nereus usage report` detached, with the person's offline token. Two `nereus` processes refreshed that token 11 ms apart; Keycloak rotates refresh tokens with no reuse (`refreshTokenMaxReuse: 0`), so one of them lost the session, and every report after it failed silently. A separate change locks the refresh and makes the failure visible; this ADR removes the dependency itself: an unattended reporter should not ride on a person's interactive login.

Two facts shape the design. The usage window belongs to a person and an Anthropic account (`cli/src/nereus/usage_service.py`): the person comes from the token, never from the body. And ADR 0027 (teams, roles and Users) already gives `Role` and `Binding` on the tenancy tree, checked by the `openfga` Nereid, with rules `<reef>:<kinds>:<verbs>`.

The owner chose (2026-11-28): the machine acts in the person's name, as AWS's assume role (a principal trusted by a role gets short credentials of that role), and the first slice of machine identities is the usage report, ahead of the metrics.

## Decision

**A machine assumes a role; the token acts in its person's name.** Three objects say who may do what, in AWS's terms:

| AWS | Nereus | Says |
|---|---|---|
| the principal | `Machine` (core) | which key signs in, and which User answers for it |
| the role's permission policy | `Role` (authorization Reef, ADR 0027) | what the token may do |
| the role's trust policy | `Binding` of the Role to `machine:<name>` | which machines may assume it, and where (the node) |
| `sts:AssumeRole` | `POST /v1/machines/<name>/token` | the exchange: an assertion in, a token of minutes out |

**`Machine` is a kind of core** (`core.getnereus.dev/v1alpha1`), beside `User`, as ADR 0025 said. Its `spec`:

- `publicKey`: an Ed25519 public key as a JWK (`kty: OKP`, `crv: Ed25519`), with its `kid`.
- `user`: the User who answers for the machine, written by the API from the creator's token, never from the body. Only that User, or an administrator, changes or deletes it.

**`nereus machine create owner-laptop`** (a person's login, ADR 0013's verbs) makes the key on the machine, at `~/.config/nereus/machines/<name>.key`, mode `0600`, never sent anywhere, and registers only the public key. `nereus machine rotate <name>` makes a new key and replaces the public one; `nereus machine delete <name>` revokes it; `list` and `get` show the machine, its User, its key id, its bindings and when it last signed in.

**The trust is a `Binding`**, with a new subject type: `nereus authorization binding create --role usage-reporter --machine owner-laptop` (on the instance, or on a node of the tree). Only the machine's User may bind a role to it, and only a role whose every rule that User holds at that node: a person never gives a machine more than they have.

**The exchange.** The CLI signs a JWT with the machine's key: `iss` and `sub` `machine:<name>`, `aud` the Nereus API, `jti` used once, `iat`, and `exp` at most 60 seconds ahead. It sends it with the role: `POST /v1/machines/<name>/token {assertion, role}`. The API, in order:

1. Verifies the signature against the `Machine`'s public key, the `aud`, the times (30 seconds of clock skew) and that the `jti` was not seen in the last two minutes.
2. Finds a `Binding` of that role to `machine:<name>`; none is 403 with ADR 0012's cause and fix (the `binding create` to run).
3. Checks that the machine's User still holds every rule of the role at the binding's node (the `openfga` check, as for any person); a User who lost a right takes it from the machine at the next exchange.
4. Answers with a token it signs itself (EdDSA, `kid`), valid 10 minutes: `sub` `machine:<name>`, `act` `{sub: user:<User name>}` (RFC 8693's actor claim, read the other way: the machine acts, in the User's name), `role`, `node`, `aud`, `exp`, `jti`.

The API's signing key is a secret of its own, made at install and rotated by a command; its public key is published at `/.well-known/nereus-configuration` beside the issuer of the person's tokens, so a Nereid could verify it later.

**The exchange sits behind a Nereid's contract** (owner, 2026-11-28). Checking an assertion, keeping a signing key and minting tokens is authentication, which the platform delivers through a Nereid of the `authentication` Reef, not through core. In this first slice the API runs it in process, behind two calls shaped like a Nereid's contract: `verify(assertion) -> machine` and `mint(machine, user, role) -> token`. Nothing else in the API touches the key or the claims, so moving the exchange out changes no route and no client.

**A request with a machine token.** The verifier tells the two tokens apart by `iss`. A machine token gives a `Principal` with the machine and the User; every check asks both: the route's question is checked for `machine:<name>` (through its binding) and for the User, and is allowed only when both answer yes. The usage routes key the window by the User, so the machine's report lands in the person's window, the same one the portal shows. The emergency exit of `api/authorization.py` (a token in `nereus-admins`) never applies to a machine token.

**The first role is `usage-reporter`**: one rule, `usage:windows:report`. The CLI reports with the machine when `nereus config` names one for usage (`usage.machine: owner-laptop`), else with the person's token as today. It keeps the machine's token until a minute before it expires, beside the usage cache, under the same lock.

**Audit.** The API logs every exchange (machine, User, role, node, allowed or why not) and every request made with a machine token with both names, to the audit journal of #2385 when it exists.

**OpenFGA.** The model gains `type machine`, and `grant`'s subject accepts `machine`. The `Binding` writes the tuple; deleting the machine deletes its bindings and tuples.

## The order of the work

The thin slice first, end to end, then the rest:

1. `Machine` in core, `nereus machine create|get|list|delete`, the key on disk.
2. `machine` as a Binding subject, in the API and the OpenFGA model, with the no-escalation rule.
3. The exchange route and the API's signing key; the verifier accepts machine tokens, the check asks both subjects.
4. `nereus usage report` with `usage.machine`; the owner's status line switches to it.
5. `rotate`, the audit lines, the docs page.

Metrics (#1565 step 7 onwards) reuse the same `Machine` and exchange: `--machine` on a source becomes a binding of a sender role.

## Evolution

- **The exchange moves to an `sts` Nereid of the `authentication` Reef** (#2395, owner, 2026-11-28): the Nereus API delegates `verify` and `mint` to the default Mandate's Nereid, as for any Reef, and only verifies the tokens by the JWKS it publishes; the signing key leaves the API. It is separate from the login Nereids, so the exchange still holds the same with Keycloak, Auth0 or any other (ADR 0025's reason). Whether `Machine` itself stays in core beside `User` is decided then.

## Prior art

- AWS IAM roles and `sts:AssumeRole`: a trust policy names who may assume a role, the permission policy what it grants, and the credentials last minutes.
- GitHub Apps: a JWT signed with the App's private key is exchanged for an installation token of an hour.
- OAuth 2.0 Token Exchange (RFC 8693): the `act` claim names who acts for whom; JWT client assertions (RFC 7523) for the signed request.
- Kubernetes RBAC: a `RoleBinding` subject may be a ServiceAccount as well as a user.

## Out of scope

- A pipeline signing in with its own OIDC issuer (federation, no stored key): ADR 0025 leaves it for later, and so does this one.
- Several API replicas sharing the `jti` memory: one replica today; a shared store comes with the second.
- A portal screen for machines.

## The builder's calls

Settled while writing, after a builder's read (2026-11-28); each can be changed in review:

- **Names are global**, like other core objects: `owner-laptop` taken by one person is refused (409) to another, who picks another name. The subject is `machine:<name>`.
- **A machine's role holds concrete rules only** in this slice: no `*` in a rule bound to a machine, so the no-escalation check is one `/v1/check` question per rule, asked for the User at the binding's node.
- **The check path:** `/v1/check` takes the subject as `machine:<name>` beside `user:<name>`; the `Binding` gains `spec.subject.machine`, and the `openfga` Nereid writes its tuple as for the other subjects. A person's request asks exactly what it asks today; only a machine token asks twice (the machine, then the User).
- **The usage routes:** they are `anyone` today (any token with a User), and stay so for people. For a machine token `anyone` is not enough: the machine's role must cover the route's reef, kind and verb. The window's PUT declares the verb `report`, the word of the CLI and of the role's rule; its node is the instance.
- **The `Principal`** gains `machine` and `actor` (the User's name), with no groups. The User is read by name; a User deleted or unlinked fails the next exchange (403) and the next request with a live token.
- **The API's signing key** is a Secret the install writes (`nereus init`, and the k3d dev path), never the API at runtime. `rotate` adds a new `kid`, publishes both, and drops the old one after the token's lifetime.
- **The `jti` memory** is in the API's process: a restart forgets the last two minutes, and a replayed assertion only gets the same machine the same token, so it is accepted.
- **`nereus machine create`** calls its own route (`/v1/machines`), which writes `spec.user` from the token; `status.lastExchangeTime` is written at most every five minutes.

## Open questions

- None the owner must answer before the build.

## Consequences

- Core gains `Machine`; the authorization Reef gains `machine` as a subject; the Nereus API becomes an issuer of its own short tokens, with a key to keep and rotate.
- The usage report stops depending on a person's login: a lost session no longer freezes the portal.
- A machine never holds more than its person, and loses a right at its next exchange when the person does.
- OWASP A01 (broken access control: the double check, no escalation), A02 (cryptographic failures: Ed25519, keys at `0600`), A07 (identification and authentication failures: no shared secret, single-use assertions, tokens of minutes) and A09 (logging failures: the audit lines) are the categories this touches.
- ADR 0025's machine section points here for the exchange and the roles.

## Origin

The owner's request of 2026-11-28, after the Usage tab froze at 66% (investigated with a Fable agent the same day); the owner chose the machine acting in the person's name and the token exchange the same day, asked for the exchange to sit behind a Nereid's contract with an `sts` Nereid as its destination (#2395), and accepted this ADR the same day (PR #2393). Raw data in `#pontos/raw/2026-11-28/`.
