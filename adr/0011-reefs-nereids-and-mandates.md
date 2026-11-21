# 0011. Reefs, Nereids and Mandates, managed with top-level commands

!!! note "In short"
    Reefs, Nereids and Mandates are managed with top-level commands, with `--reef` and `--nereid` as the flags everywhere; a Mandate binds one reef to one Nereid. Status: Proposed (2026-10-17, rewritten 2026-10-25).

**Status:** Proposed (2026-10-17, rewritten 2026-10-25)

## Context

The model's words changed twice. The first ADRs said Concept and Controller; the Lean Inception of #79 changed them to Interface and Implementation, managed under a `platform system` group, with an Implementation installed into an Interface and one active Instance per Interface. The owner's voice sessions of 2026-10-25 reviewed the CLI command by command on the MVP's journey (secrets first, then authentication with two identity brokers side by side) and found:

- A capability and whoever fulfils it are different things: a reef can exist with no Nereid, and one controller can look after several reefs, as in Kubernetes. Nesting the Nereid under the reef is wrong.
- A Tool's credentials repeated in every Class or Instance are wrong: they belong to the controller's installation, as a StorageClass's provisioner holds them.
- A secret travelling in plain text inside the platform can be captured in logs, even over HTTPS.

## Decision

**Words.** A **reef** is the contract of a capability, an API group (ADR 0009); a **Nereid** fulfils one or more reefs; a **Mandate** binds one reef to one Nereid (ADR 0002). **Controller** stays the mechanism, in ADRs and code: each Nereid runs as a Kubernetes controller that reconciles and writes `status` (ADR 0005). Instance, Tool and Vendor keep their meaning from ADR 0002.

**Commands that change the platform are top-level nouns**, with `--reef` and `--nereid` as the flags everywhere:

```bash
nereus reef list
nereus reef apply authentication --from-file ./reefs/authentication/

nereus nereid suggest --reef authentication
nereus nereid apply keycloak \
  --reef authentication
nereus nereid apply sao \
  --reef authentication \
  --image ghcr.io/getnereus/nereus/authentication-auth0-controller:0.1.0

nereus mandate create corporate \
  --reef authentication \
  --nereid keycloak \
  --default

nereus status
```

- **Nereid names are global** to the platform and free: the Tool's name or a name from the myth, suggested by `nereus nereid suggest`. `--reef` repeats when one Nereid looks after several reefs.
- **`--image` names an image** other than the one the CLI pins for that name.
- **`nereus status` shows the mechanism**: one row per reef and Nereid pair, columns `REEF`, `NEREID`, `VERSION`, `STATUS`, `AGE`.
- **`nereus nereid list` shows the Nereids**: one row per Nereid, columns `NEREID`, `REEFS`, `IMAGE`, `STATUS`, `AGE`; `nereus nereid get <nereid>` adds the image's title, description and digest. `--param` is the only flag for parameters (no `--set`), and `--reef` the only flag naming a reef (no `--implements`).

```text
$ nereus status
REEF            NEREID           VERSION  STATUS  AGE
authentication  keycloak         0.1.0    Ready   3m
                sao              0.1.0    Ready   3m
core            built-in         0.1.0    Ready   38m
secrets         azure-key-vault  0.1.0    Ready   8m

$ nereus nereid list
NEREID           REEFS           IMAGE                                                               STATUS  AGE
azure-key-vault  secrets         ghcr.io/getnereus/nereus/secrets-azure-key-vault-controller:0.1.0   Ready   8m
keycloak         authentication  ghcr.io/getnereus/nereus/authentication-keycloak-controller:0.1.0   Ready   3m
sao              authentication  ghcr.io/getnereus/nereus/authentication-auth0-controller:0.1.0      Ready   3m
```

**The kinds and their fields**, in `core.getnereus.dev/v1alpha1` (ADR 0009): `Reef.spec` holds the contract (API group, version, commands); `Nereid.spec.reefs` (a list), `Nereid.spec.image` and `Nereid.spec.params` (authentication and default target parameters); `Mandate.spec.reef`, `Mandate.spec.nereid`, `Mandate.spec.params` (overrides) and `Mandate.spec.default`. A reef's own objects key their entries by reef (`reef:` in a `Cloud` access entry). Today's names (`spec.interface`, `interface:`) are current code, to be renamed.

**Where parameters live.**

- **The Nereid owns its authentication and its default target parameters**, set once at `nereid apply` (`authentication=workload-identity`, a default `vaultUrl`). A Nereid may serve several targets (several vaults). The first secrets Nereid, its default Mandate `vault` and the Mandate's RSA key are made by `nereus init` (ADR 0003), never by the person.
- **The Mandate may override the target parameters** with `--param` and adds the parameters of its own choice (`identityProvider`, `credentials=secret:<name>`); the common case needs only `--reef` and `--nereid`.
- **An Instance's fields are generic:** fields the reef defines, common to its Nereids. A Nereid ignores what it does not use and says so in `status`. What one Nereid needs and the others lack becomes a new common field of the reef, never a Nereid-specific kind.

**A reef's contract may require capabilities of every Nereid.** The `secrets` reef requires client-side encryption: every secrets Nereid publishes a public key for each Mandate naming it and decrypts inside its own boundary, and the CLI encrypts each secret before sending it, with envelope encryption (an AES-256-GCM data key encrypts the value; the Mandate's RSA-OAEP-256 public key wraps the data key). The key belongs to the Mandate, not to the reef or the Nereid: a Mandate picks the target vault, and a Nereid may serve several vaults through its params. `nereus secrets apply` encrypts with the key of the Mandate it targets, the reef's default one unless a Mandate is named. The CLI stays provider-agnostic; only the Nereid differs:

| Nereid | The private key |
|---|---|
| Azure Key Vault (`--target azure`) | a non-exportable RSA key in Key Vault; the Nereid calls Key Vault to decrypt |
| OpenBao, local k3d with no target | a non-exportable RSA key of the Transit engine (`rsa-4096`, `exportable` and `allow_plaintext_backup` false; reading the key returns its public key); the Nereid calls Transit to decrypt, which uses OAEP with SHA-256 for the hash and MGF1 (RSA-OAEP-256), checked against OpenBao 2.7.1 |
| fallback, a Nereid with no vault | Sealed Secrets style: the private key in a cluster Secret |

```text
$ nereus secrets apply google-sso --from-file google-sso.json
encrypted locally with the public key of mandate vault (envelope: AES-256-GCM + RSA-OAEP-256)
secret/google-sso stored by nereid azure-key-vault (2 keys, values hidden)
```

Log redaction stays, whatever the encryption.

**Repositories and images:** one per Nereid's Tool, named `<reef>-<tool>-controller` (`secrets-azure-key-vault-controller`, `authentication-keycloak-controller`); the image is `ghcr.io/getnereus/nereus/<reef>-<tool>-controller` while the monorepo holds them.

## Prior art

- **The Lean Inception (Paulo Caroli)** ([martinfowler.com](https://martinfowler.com/articles/lean-inception/)): the workshop of #79 that first exercised the model on the MVP's journey.
- **Kubernetes storage classes** ([StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)): the provisioner holds the credentials and the class selects the target with parameters; the Nereid and the Mandate split them the same way.
- **Sealed Secrets (Bitnami)** ([github.com/bitnami-labs/sealed-secrets](https://github.com/bitnami-labs/sealed-secrets)): the controller holds the private key, and `kubeseal` encrypts on the client with its public certificate; the secrets reef's contract takes the same shape, and the fallback Nereid the same storage of the key.
- **OpenBao's Transit secrets engine** ([openbao.org](https://openbao.org/docs/secrets/transit/), [API](https://openbao.org/docs/api/secret/transit/)): encryption as a service, with RSA keys (`rsa-2048`, `rsa-3072`, `rsa-4096`), keys not exportable by default and a `decrypt` endpoint; the local secrets Nereid decrypts through it.

## Consequences

- ADR 0002's words changed for people: reef, Nereid, Mandate. The legacy `platform system interface ...`, `platform system install ...` and `platform system interface use ...` map to `nereus reef ...`, `nereus nereid apply ...` and `nereus mandate create ... --default` (`docs/agent/cli.md`).
- No secret value crosses the platform in plain text: the API, the logs and the cluster see only the envelope, until the Nereid writes it to its vault.
- The reef's schema must be designed for every Nereid it expects, at the risk of a lowest common denominator; new common fields are the way out.
- The code still names Interface and Implementation; renaming it is a change of its own.

## Open questions

- **Published (#404):** the Nereid writes the key in its Mandate's `status.publicKey` (`pem`, `algorithm`, `fingerprint`, `version`, and where the vault keeps it, `storage`); `version` grows by one each time the key changes, and `storage: memory` says the vault keeps nothing across a restart (OpenBao in dev mode). Until the API exists, the CLI reads it through the kubeconfig, so the trust is the cluster's TLS and RBAC, and `nereus init` prints the fingerprint.
- How the key is rotated, and how the CLI pins it (trust on first use, with `nereus secrets apply`) (open).

*Rewritten 2026-10-25 from voice session; raw data in Drive #pontos/raw/2026-10-25. Rewritten again 2026-10-25 (order 20261025-1724): init makes the first secrets Nereid and its Mandate; OpenBao Transit keys are non-exportable; "Mandate" is the working term. Rewritten again 2026-10-25 (order 20261025-1805): `nereid list` and `status` columns, `--param` and `--reef` as the only flags. Rewritten again 2026-10-25 (order 20261025-1812): the fields of the kinds, and `nereid get`. Rewritten again 2026-10-25 (order 20261025-2158): the public key is the Mandate's, published in its status, and its OAEP hash.*
