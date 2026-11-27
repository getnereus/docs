# Inception

How Nereus started: a [Lean Inception](https://martinfowler.com/articles/lean-inception/) (Paulo Caroli's method) run with an agent as facilitator, which fixed the vision, the goals and the sequence of the MVP.

The words are the model's: [Reef, Nereid and Mandate](../concepts/model.md). The work that followed is on the [roadmap](roadmap.md) and in [What is built](../reference/what-is-built.md).

## Product vision

For platform teams whose IDP is a fixed set of tools glued by hand, where swapping one means rewriting the platform, Nereus is a composable platform API and CLI built out of Nereids added at runtime.

Unlike Humanitec (commercial, with its own resource model) and Kratix (each Promise bundles contract and implementation), Nereus separates the contract, the Reef, from what implements it, the Nereid, and swaps one for another without changing the API.

## Is, is not

| Is | Is not |
|---|---|
| A composable API and CLI, the CLI first | A portal, for now |
| Built out of Nereids added at runtime | A fork of Backstage |
| Compatible with the Backstage catalog | A secrets vault |
| Open source | An installer of a fixed stack of tools |

| Does | Does not |
|---|---|
| Comes up from zero from the CLI | Keep copies of secrets |
| Logs in with Google through Keycloak, swappable for Auth0 | Tie anyone to a tool: the API never names a Nereid |
| Reads secrets where they are already kept | Require a kubeconfig from people |
| Helps to build itself | In the MVP: several tenants or a cloud other than Azure |

## Goals

The MVP served the first five; the last three wait for later waves.

| Goal | In the MVP |
|---|---|
| Prove the swap: replace Keycloak with Auth0 without changing the contract or the API | yes |
| From zero through the CLI, in a guided sequence with progress | yes |
| Build itself: add and configure its own first Nereids | yes |
| Reuse what exists: Terraform as Stacks, secrets where they are, the Backstage catalog | yes |
| Secure by default: no copy of a secret, federated identity in the cloud | yes |
| Run its own lifecycle after the pivot, with recovery and destroy tested | no |
| Tell its own story in docs, talks and courses | no |
| Attract the community with "bring your Terraform" | no |

## Persona

The platform engineer betting on the idea. Wants to run it first, end to end, and show the result to other platform engineers. The only persona of the MVP, so the MVP had to be demonstrable, live or recorded.

## The journey

1. Already there: the CLI, an Azure CLI login and a Key Vault holding the Google OAuth client.
2. Bring up the undercloud: `nereus init --target azure` creates a local k3d cluster and the installation's identity.
3. Connect to Azure: the `cloud` Reef and its Nereid `azure`.
4. Secrets: the `secrets` Reef and the Key Vault Nereid, which adopts the vault with no copy.
5. Authentication: the `authentication` Reef and the Keycloak Nereid, with Google keys read from `secrets`.
6. Auth0 alongside, then `nereus mandate create` makes it the default: the same commands, the same API.
7. Show it: record the session or run it live.

## Undercloud and overcloud

Names from OpenStack TripleO, behaviour from Cluster API. See [Undercloud and overcloud](../concepts/undercloud-overcloud.md).

- **Undercloud:** a local k3d that bootstraps a cloud; it publishes its OIDC issuer so Azure can verify service-account tokens, and the signing key never leaves the cluster.
- **Identities:** one managed identity per Reef and per installation, trusted through a federated credential; no client secret or certificate is kept.
- **Overcloud:** AKS, created by running Stacks; after the pivot it takes over its own lifecycle and the k3d is deleted.
- **First wave:** stays on k3d and proves the handshake with Azure; AKS and the pivot come second.

## Sequence of the MVP

Waves respect the dependencies; the biggest risk, the connection to Azure, comes early on purpose.

| Wave | What can be seen at its end |
|---|---|
| 1. The base | `nereus reef apply` and `nereus nereid apply`, with the reference Nereid |
| 2. Ready for agents | Agents work in parallel; `init` with progress |
| 3. Azure answers | The handshake with the Key Vault |
| 4. Secrets with no copy | The first real Nereid |
| 5. First login | Login with Google through Keycloak |
| 6. The swap | Auth0 alongside, then active |
| 7. The demo | The walkthrough as the talk's script |

## Canvas

| Block | Content |
|---|---|
| Proposal | Prove that a platform of swappable Nereids works end to end from the CLI |
| Result | The demo runs end to end with no change to the CLI or the API across the swap |
| Metrics | Time from `init` to first login; zero changes across the swap; flow of the work ([#95](https://github.com/getnereus/nereus/issues/95)) |
