# The profiles

The four built-in profiles, `core`, `internal-developer-platform`, `reference` and `secrets`, and what each installs. What a profile is: [Runtime install and profiles](../concepts/runtime-and-profiles.md).

## Choose one

[`nereus init --profile internal-developer-platform`](../specs/cli/core.html#init-profile) installs core, then the profile ([ADR 0014](../adr/0014-profiles.md), [#420](https://github.com/getnereus/nereus/issues/420)). An unknown profile is refused before anything changes:

``` { .text .output title="output" }
'minimal' is not a profile: core, internal-developer-platform, reference, secrets
```

[`nereus profile list`](../specs/cli/core.html#profile-list) lists the four; `core` is the default. Profiles are built in; `profile create` is not built yet.

## core

No `--profile`, or `--profile core`, installs core alone with the tenancy reef ([ADR 0015](../adr/0015-tenancy.md), [#646](https://github.com/getnereus/nereus/issues/646)): no other reef, no Nereid.

## reference

`--profile reference` ([#1421](https://github.com/getnereus/nereus/issues/1421)) installs the reference Nereid of each reef that has one, such as `reference-secrets` ([#486](https://github.com/getnereus/nereus/issues/486)), in place of the tools: the reefs' kinds answer end to end and no tool image is pulled. `make scene-core` runs it.

## internal-developer-platform

Each Nereid comes after the Nereids of the reefs it requires. With this profile the instance offers sign-in, so `nereus status`, `reef` and `nereid` read through the Nereus API with your token.

- **Secrets:** Nereid `openbao`, Mandate `default` and the vault `default` ([Keep a secret](../guides/reefs/secrets.md)).
- **Release:** Nereid `flux` and Mandate `flux` ([Release a chart](../guides/reefs/release.md)).
- **Database:** Nereid `cloudnative-pg`, which installs CloudNativePG through a Release, and Mandate `cloudnative-pg`.
- **Authentication:** Nereid `keycloak`, its Database `keycloak` and Mandate `keycloak` ([Turn on authentication](../guides/access/authentication.md)).
- **The entrance:** the Gateway API CRDs, Istio through the release reef and the Gateway `istio-system/ingress` ([#951](https://github.com/getnereus/nereus/issues/951)).
- **Portal:** Nereid and Mandate `nereus-portal`, after the entrance ([#896](https://github.com/getnereus/nereus/issues/896)).
- **Metrics:** Nereid and Mandate `victoriametrics` ([Collect metrics](../guides/reefs/metrics.md)).
- **Environment:** Nereid and Mandate `vcluster` ([#827](https://github.com/getnereus/nereus/issues/827)).
- **Catalog and delivery:** Nereids `catalog` and `kubernetes` ([Follow the golden path](../guides/reefs/golden-path.md)).
- **Teams and authorization:** the `teams` reef and Nereid `openfga` ([Say who may do what](../guides/access/authorization.md)).
- **Registry:** Nereid `zot` ([Run a registry](../guides/reefs/registry.md)).
- **Messaging:** Nereid `nats` and Mandate `messaging-nats` ([Send messages](../guides/reefs/messaging.md)).
- **Build and scm:** Nereids `buildkit` and `forgejo`.

## The secrets reef's key

OpenBao runs next to the Nereid `openbao`, which creates a non-exportable `rsa-4096` key and writes its public key in the Mandate's status; thetis checks it, and `init` prints its fingerprint.

The key lives on the volume `openbao-data` and OpenBao unseals itself, so a restarted Pod keeps it; only a lost volume makes a new key. The token and the unseal key are generated once, in Secrets, and never printed.

## The addresses on k3d

On k3d, `init` reads the ingress port from k3d and passes it as the chart's `ingress.address` ([#1079](https://github.com/getnereus/nereus/issues/1079)). A new portal Mandate gets `publicUrl=http://localhost:<port>`, and the keycloak Mandate `http://auth.localhost:<port>` ([#1933](https://github.com/getnereus/nereus/issues/1933)).

On another cluster `init` passes none, and the Mandates get no `publicUrl`; an existing Mandate is kept as it is. Set the portal's with `--param publicUrl=https://portal.example.com` on [`nereus mandate apply nereus-portal`](../specs/cli/core.html#mandate-apply).

A host no route names answers 404 from Envoy, and the portal answers on `localhost`:

```bash
curl --include --header "Host: no-route.example.com" http://localhost:8080/
```

``` { .text .output title="output" }
HTTP/1.1 404 Not Found
server: istio-envoy
content-length: 0
```

## buildkit and forgejo

The profile installs `buildkit` in portable mode, Pod Security privileged, so it builds on any cluster. Where a sandbox runtime is installed, apply it in sandbox mode with `nereus nereid apply buildkit --set BUILD_RUNTIME_CLASS=gvisor` ([#1231](https://github.com/getnereus/nereus/issues/1231)).

`forgejo` mirrors a repository through the scm reef's default Mandate `forgejo` ([Mirror a repository](../guides/reefs/scm-mirror.md)). Forgejo copies from github.com alone until `nereus nereid apply forgejo --set MIRROR_ALLOWED_DOMAINS=git.example.com` names other hosts.

## Apply a profile later

A profile also layers on core after `init` ([#425](https://github.com/getnereus/nereus/issues/425)): [`nereus profile apply internal-developer-platform`](../specs/cli/core.html#profile-apply) runs the same steps thetis runs, from the laptop, one line each, `created` the first time and `unchanged` after.

`--without buildkit` leaves a Nereid out; on a cluster the charts installed, the Profile's `spec.exclude` does the same. `--dry-run` lists the steps and changes nothing. On a cluster `init` has not prepared, it stops and points to `nereus init`.

## Describe a profile

[`nereus profile describe internal-developer-platform`](../specs/cli/core.html#profile-describe) shows its ingress and each Nereid with its reef, Mandate and who requires it, in order.

The order comes from each Nereid's image label `core.getnereus.dev/requires` ([#1368](https://github.com/getnereus/nereus/issues/1368)). With no registry answering, `describe` prints the order from the offline list `cli/src/nereus/requires.yaml`, and its last line says so.

## The proof

`make scene-idp` proves the profile ([#1261](https://github.com/getnereus/nereus/issues/1261)): on a throwaway k3d cluster, every Nereid `Ready`, the portal answering, an app built by `buildkit` and deployed answering, and nothing left behind. It runs only on the owner's word ([#1420](https://github.com/getnereus/nereus/issues/1420)).
