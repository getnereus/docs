# 0003. `nereus init` prepares the platform; Reefs and Nereids are added at runtime

!!! note "In short"
    `nereus init` prepares a cluster with the built-in `core` Reef, the `tenancy` Reef and a profile's Reefs; every other capability arrives later as a Reef, with Nereids added at runtime. Status: Accepted (2026-11-24, by the owner; proposed 2026-10-17, rewritten 2026-10-25). What init installs is revised by ADR 0014.

**Status:** Accepted (2026-11-24, by the owner; proposed 2026-10-17, rewritten 2026-10-25)

## Context

In the project this one grew from, `platform init` installs the whole platform: identity, API, every controller, ingress, observability. Adding or swapping a capability means changing init, and there is no way to run the platform with less, or with something else.

There is one exception to "less": secrets. Every other Reef needs a place for credentials, and the first Nereid that keeps secrets needs something to exist outside the cluster before any Nereid runs (in Azure: a Key Vault, a Managed Identity federated with the cluster's issuer). That chicken-and-egg can only be solved by the person's own login, once.

## Decision

`nereus init` prepares a cluster with the built-in `core` Reef, then installs the Reefs of a profile (ADR 0014, profiles: core is only the engine, and a profile lists what to install). The secrets Reef is not fixed at init: it comes when the profile, or a Nereid it installs, requires it. Every other capability arrives later as a Reef, added by name, and Nereids that look after it:

```bash
# Core only, the default profile core: to build piece by piece
nereus init

# A local platform on k3d: core, then the profile internal-developer-platform: authentication with
# keycloak, after what keycloak requires, the secrets reef kept by OpenBao
nereus init --profile internal-developer-platform

# A platform whose first secrets Nereid is Azure Key Vault
nereus init --target azure

# Every other reef and its Nereids, added at runtime
nereus reef list
nereus reef apply authentication --from-file ./reefs/authentication/
nereus nereid apply keycloak --reef authentication
```

- **The profile decides whether the secrets Reef comes with init** (#420). `core`, the default, installs nothing beyond core (#424). `internal-developer-platform` installs `authentication` with the `keycloak` Nereid, which requires the `secrets` Reef: so the `secrets` Reef, its first Nereid, the Reef's default Mandate `vault`, and the Mandate's RSA key come first, with its public key published in the Mandate's status for the CLI (ADR 0011). With no target that Nereid is `openbao`, with OpenBao in dev mode in its Pod (in memory: a restart makes a new key, which `init` and the Mandate's status say). A Nereid that needs secrets declares that it requires the Reef; nothing installs secrets because it is secrets.
- **With `--target azure`, init still installs the secrets Reef with Azure Key Vault**, since the cloud bootstrap needs it; how a profile follows the target is left to its own issue (ADR 0014).
- **Adding the secrets Reef again is not part of the person's flow** once a profile installed it. `nereus reef create secrets` fails as any `create` of a thing that exists (ADR 0013), and the message points to `nereus reef list`; `nereus reef apply secrets` reports `reef/secrets unchanged`, or `configured` when it changed something.
- **`--target <provider>` decides the first secrets Nereid** and provisions what it needs to be reachable. For `azure`: Key Vault, Storage, DNS zone and a Managed Identity, with the RSA key of the secrets Reef (ADR 0011). Init uses the person's own `az` login, since no Nereid exists yet; from then on, the Nereid uses workload identity, with no stored secret.
- **The cluster's issuer is made public:** the OIDC discovery document and the JWKS of the cluster are published to the Storage account, and the Managed Identity is federated with that URL, so Azure accepts tokens signed by the local cluster.
- **Undercloud and overcloud.** A local k3d cluster (the undercloud) bootstraps and provisions the overcloud (for example AKS); then the platform pivots to the overcloud, the federated credential moves to the overcloud's issuer as an explicit step, and the undercloud is deleted.
- `nereid apply` records the Nereid (name, image, Reefs, parameters) and runs its image as a Deployment. The Nereid reports `Ready` in its `status` when it is up.
- Until the Platform API exists, the CLI does this with the kubeconfig, as `helm` does. The API itself becomes one more Nereid added this way; after it, everything goes through the API.
- **`init` installs the chart `nereus` with Helm** (amended 2026-11-05, #1044): the kinds, the namespace and the Nereus API come from `cli/src/nereus/charts/nereus`, the API through `helm upgrade --install nereus` in `nereus-system`, so the cluster holds a release a HelmRelease can take over later (#1045). Helm runs with the same kube context and kubeconfig as the Kubernetes client, and no other credential; it is the one tool besides the client, checked at `init`'s `prerequisites` step (4.0 or newer, for `--take-ownership` and `--force-conflicts`, which takes a kind or an object changed in the cluster back to the chart's). The kinds come before it from their own chart, `cli/src/nereus/charts/nereus-reefs`, as templates with `helm.sh/resource-policy: keep` (amended 2026-11-05, #1050): `helm upgrade --install nereus-reefs` updates them on every run, and `helm uninstall` never deletes one. The chart holds the `Installation` too (#1051), named by `installation.name`, its id kept by `lookup` of the stored one; init still creates it with the client before Helm, until #1055. The profile's Reefs stay with the client.
- Removing a Nereid removes its Deployment and the commands it added to the CLI (ADR 0004).

### The Vault kind

The secrets Nereid is installed once; each vault it keeps is a `Vault`, a kind of the `secrets` Reef (`secrets.getnereus.dev/v1alpha1`), one object per vault inside that Nereid. A person names the vault a secret goes to with `--vault`, and leaves it out to use the default vault (order 20261026-0640):

```bash
# The default vault, when --vault is left out
nereus secrets apply google-sso --from-file google-sso.json

# Another vault the same Nereid keeps
nereus secrets apply google-sso --from-file google-sso.json --vault team-a

kubectl get vaults.secrets.getnereus.dev
#   NAME     NEREID   DEFAULT   FINGERPRINT
#   default  openbao  true      SHA256:aA57xN3...
#   team-a   openbao            SHA256:Qm9vY2...
```

```yaml
apiVersion: secrets.getnereus.dev/v1alpha1
kind: Vault
metadata:
  name: team-a
spec:
  nereid: openbao
  default: false
  params: {}          # where the Nereid keeps it: a path, a Key Vault URL
status:
  publicKey: {}       # what the Mandate's status.publicKey holds today (ADR 0011)
```

- **One Nereid, many vaults:** the Nereid is not installed again for a second vault; a new `Vault` object is enough, and the Nereid makes it ready.
- **One default:** at most one `Vault` has `spec.default: true`, and a secret with no `--vault` goes to it. A command that would make a second default fails and names the current one.
- **The profile** that installs the secrets Reef (ADR 0014) creates its default vault, as it creates the default Mandate `vault` today.
- **No `--vault` exists yet:** on 2026-10-26 the CLI has no secrets command at all (`nereus secrets apply` is designed in ADR 0011, not built), so the flag is born with the command.

## Prior art

- **Kubernetes default StorageClass** ([kubernetes.io, "Storage Classes"](https://kubernetes.io/docs/concepts/storage/storage-classes/)): a claim that names no `storageClassName` gets the class annotated `storageclass.kubernetes.io/is-default-class: "true"`. A secret with no `--vault` takes the default `Vault` the same way; Nereus allows one default, where Kubernetes takes the most recent of several.
- **cert-manager Issuers** ([cert-manager.io, "Issuer"](https://cert-manager.io/docs/concepts/issuer/)): one installed cert-manager serves many `Issuer` and `ClusterIssuer` objects, each a certificate authority it signs with. A `Vault` is the same shape: one secrets Nereid, many vaults as objects.
- **Cluster API, bootstrap and pivot** ([`clusterctl move`](https://cluster-api.sigs.k8s.io/clusterctl/commands/move)): a temporary bootstrap cluster creates the management cluster, and `clusterctl move` transfers the resources to it; the undercloud and overcloud take the same shape and the word "pivot".

## Consequences

- A platform is the set of Reefs and Nereids in it. Two installations can differ in what they offer.
- Adding a Nereid is running code with permissions in the cluster. Once the API exists, `nereid apply` is for platform admins only, and images are pinned by digest. Before that, whoever holds the kubeconfig already has that power.
- The order matters (the secrets Reef and its Nereid come first, a Nereid that installs others before them); init takes the first part on itself, and the rest has to be visible to the person running it: each output ends with `Next steps:` (ADR 0013).
- With `--target`, the platform starts with a cloud dependency; with no target, the secrets Nereid runs in the cluster (OpenBao), when the profile requires it.
- After a plain `nereus init` (the profile `core`), `nereus nereid apply keycloak` is refused until a Nereid looks after the `secrets` Reef, as any Nereid whose required Reef has none.

## Open questions

- How a `Vault` relates to the Mandate: ADR 0011 says the key belongs to the Mandate, which picks the target vault through its params. Recommendation: the key and the target move to the `Vault`, and the Mandate only binds the Reef to its Nereid.
- The default vault's name: `default`, or `vault` as the default Mandate is named today.

- Whether init prints what the person's login granted, so it can be removed afterwards (least privilege).
- How OpenBao, the secrets Nereid of `nereus init` with no target, is unsealed after a restart. Demos may run it in dev mode or with auto-unseal; the production answer is open.

*Rewritten 2026-10-25 from voice session; raw data in Drive #pontos/raw/2026-10-25. Rewritten again 2026-10-25 (order 20261025-1724): init installs the secrets Reef, its first Nereid, the default `vault` Mandate and the Reef's RSA key. Rewritten 2026-10-26 (order 20261026-0508, divergence 4): the secrets Reef is not fixed at init; the profile decides, and keycloak requires it (#420). Revised 2026-10-26 (order 20261026-0640): the default profile is `core` (#424); the `Vault` kind, one object per vault inside the secrets Nereid; the ADR stays Proposed.*
