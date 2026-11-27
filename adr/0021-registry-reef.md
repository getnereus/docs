# 0021. The registry Reef: a Registry and its Repositories, read with a credential, published through the platform

!!! note "In short"
    A `registry` Reef with `Registry` and `Repository` kinds; images are read with one read-only credential per Registry, over TLS, and published through the platform. Status: Proposed (2026-11-05).

**Status:** Proposed (2026-11-05)

## Context

#844 (prove the nodes pull from a zot inside the cluster) showed that a cluster's nodes can pull from a registry that runs in the cluster, with no cluster recreated. #847 asks for the Reef that makes it a capability, and #848 (the build Reef) needs somewhere to publish. ADR 0017 (resource Reefs) does not list this Reef, so it needs a decision of its own.

## Decision

**A `registry` Reef, `registry.getnereus.dev/v1alpha1`, with two cluster-scoped kinds.** One writer per field (ADR 0005). The commands follow ADR 0013, and the deck is `docs/specs/cli/reefs/registry.yaml`.

| Kind | `spec` (the person) | `status` (the Nereid only) |
|---|---|---|
| `Registry` (default) | `owner`, `mandate` | `observedGeneration`, `conditions`, `steps`, `nereid`, `pullAddress`, `internalAddress`, `namespace`, `readCredential` |
| `Repository` | `registry`, `owner` | the same base fields, `image`, `identity`, `pushIdentity` (#1010; `credentialSecret` before it) |

**No port in `spec`.** Kubernetes allocates the NodePort, and the Nereid copies the result into `status.pullAddress`. A Pod cannot reach `localhost:<port>`, so builds and the delivery Nereid use `status.internalAddress`: a person names the `pullAddress` in `nereus workload deploy`, and the `kubernetes` Nereid finds the Registry that holds it (#1014). It calls the internal address only when it stays in the namespace `registry-<name>`, which an admission policy holds, and only while it looks up an image of that Registry, so an answer from another registry never sends it there.

**A Registry answers only over TLS (#1064)** (owner, 2026-11-06). The platform has one registry CA, made with a new k3d cluster: its name constraints, critical, permit only `localhost` and names under `svc.cluster.local` and exclude every IPv4 and IPv6 address (RFC 5280 checks each name type on its own, and containerd trusts the CA for every registry), so a node that trusts it trusts nothing else on the internet and no IP address. Only its certificate reaches the host, in the CLI's state folder (`~/.local/state/nereus/clusters/<cluster>/registry/ca.crt`), which every node mounts at `/etc/nereus/registry`; the key is made in memory and goes straight into the Secret `registry-ca` in `nereus-system`, of type `kubernetes.io/tls` with `tls.crt` and `tls.key`, the shape cert-manager's CA Issuer reads, so the certificate Reef (#1101, certificates as a Reef) can take it over. A cluster made before keeps what it has until `scripts/cluster/registry-trust` brings it there. containerd trusts the CA for every registry (`registries.yaml`, `configs: {"*": {tls: {ca_file: /etc/nereus/registry/ca.crt}}}`), added to the system's roots, so public images still come over their own https. The zot Nereid reads `registry-ca` by name only and issues each Registry a certificate for `localhost` and `<service>.registry-<name>.svc.cluster.local`, kept in the Secret `zot-tls` of `registry-<name>` and renewed 30 days before its 90 days end; zot reloads it with no restart. It publishes the CA's certificate, never its key, in the ConfigMap `zot-ca` of the same namespace. Every reader trusts only that CA, never the system's roots: the `kubernetes` Nereid calls `https://<internalAddress>` with the CA read from `zot-ca` (RBAC names that ConfigMap; it never reads `zot-tls`) and sends the read credential only there, the zot Nereid checks its users over https, and `nereus registry repository publish` reads the digest over https through its port-forward. Plain HTTP gets no answer as a registry on the pull address nor on the internal address (OWASP A02).

**Reading images takes a credential: one read-only credential per Registry (#1015)** (owner, 2026-11-05). zot answers no anonymous read or write. The Nereid gives each Registry a user `pull`, allowed `read` on every repository, and keeps its password in two places, both written by the Nereid itself at the same moment:

- the Kubernetes Secret `zot-pull` in `registry-<name>` (the `kubernetes` Nereid read it for its lookups until #1187 gave each Registry a read identity, the ServiceAccount `read` of `registry-<name>`, whose ten-minute tokens zot lets read, so that Nereid holds no Secret);
- the secrets Reef's secret `registries/<name>-pull`, key `auth`, the base64 of `pull:<password>` and nothing else, sealed with the public key of the vault's Mandate, in the CLI's envelope (owner, 2026-11-05: deterministic, and a rotation needs no person).

**A Registry is read only by its owner and what is under it (#1075)** (owner, 2026-11-05). The `kubernetes` Nereid gives a Delivery the Registry's read credential only when the Registry's `spec.owner` is the Workload's owner or one of its parents in the tenancy tree, climbed through `spec.parent` of any kind of the group, and is the Environment's owner or one of its parents as well (#1082, owner, 2026-11-06), since the Release puts the credential in the Environment's namespace; an Environment with no `spec.owner` is refused (fail closed); otherwise the Delivery is `Ready False`, reason `RegistryNotOwned`, before any lookup, since a lookup already reads with that credential. A node missing on the way refuses too. The credential stays only while the owner check approves it (#1085, owner, 2026-11-06): a refused Delivery whose Release carries a Registry's credential that the same pass did not approve (refused this way, refused before the check, or now naming an image of no Registry or of another one) loses that Release. Flux uninstalls the chart, the pull Secret goes with it and the app stops, since it ran on a credential it may no longer read; the Target stays. A refusal after the check approved the same credential (an image not found, a registry that does not answer) keeps the last good Release, as does a Release that carries no credential. A Registry with no `spec.owner` stays readable by every Delivery. The gate lives in the Nereid, not in the vault: the vault `registries` stays one, revisited when #990 (who may deliver to which Environment) settles who writes a Delivery.

`status.readCredential` names both. The vault `registries` holds only pull credentials, so allowing an Environment's namespace on the host (`env-<nereid>-<env>`) by name opens nothing else (OWASP A01). `nereus registry create` makes the vault when it is missing. A Delivery of an image from a Registry asks for the key with `secretValues` (#877), at `nereus.pullAuth`: the Release's values hold the `dockerconfigjson` as a template, `{"auths":{"<pullAddress>":{"auth":"{{ .Values.nereus.pullAuth }}"}}}`, which `app-template` renders with `tpl` into its Secret inside the Environment, and `defaultPodOptions.imagePullSecrets` names it. Flux's `targetPath` reads a value with Helm's `--set` parser, so a JSON value breaks; `app-template`'s `tpl` takes the JSON, and the vault keeps only the base64 value, which the parser reads as one string. A credential per Environment goes with #953 (a private image with the platform's registry credential).

**Publishing goes through the platform, and a tag is never overwritten.** Each `Repository` has its own push credential, allowed `read` and `create` only, so a person uses only their own login. `nereus registry repository publish` runs on the kubeconfig, which ADR 0018 (the Nereus API as the one door) allows until the group moves:

1. Apply the `Repository` and wait for Ready.
2. Ask a token of its push identity and open a `port-forward`.
3. Push with crane, the token as a Bearer, from a temporary folder removed on exit.
4. Read the digest back from the registry with the Registry's read credential.

**The push credential expires (#1010, amends the above).** A `Repository`'s push identity is the ServiceAccount `push-<name>` in `builds`, and zot takes its Kubernetes tokens through `http.auth.bearer.oidc`, mapped to a user bound to the ServiceAccount's uid, with the same `read` and `create` only. A token is for one Registry's audience and lasts ten minutes, so no Secret holds a push credential. This is not the token service below: zot's access control decides, so a push still cannot overwrite a tag. Spec 0009 (build security) has the details.

**The first Nereid is `zot`, through its chart, behind the Mandate `zot`.** Harbor stays possible as another Nereid. A token service does not qualify: in zot v2.1.23 a bearer `push` grants `create` and `update` (`pkg/api/bearer.go`), which would allow overwriting a tag.

**A delete is refused while Repositories exist.** A `Repository` name is unique per cluster in this slice.

```console
# Ask for a registry
$ nereus registry create main
registry/registries/main created (mandate: zot, nereid: zot)

Next steps:

  nereus registry get main

# Where to pull from
$ nereus registry get main
NAME  NEREID  PULL-ADDRESS     READY
main  zot     localhost:31874  True

localhost:31874 is a NodePort, for an image reference on this cluster's nodes. Anything that reaches a node's port reaches this registry, over TLS only, and reads nothing with no password.

Next steps:

  nereus registry repository publish hello --registry main --image hello:v1
```

**Stand-ins:** `create`, `apply`, `list`, `get`, `delete`, `purge` and `repository list|get|delete` go through the Nereus API (`/v1/registry/...`, for nereus-admins) once the instance offers sign-in, and through the kubeconfig before (#1324, the two doors of #1322); `repository publish` too since #1328, its image through the API's `/v2` (the amendment below). The API names the person on what it creates (`metadata.annotations[getnereus.dev/created-by]`). Who may create or publish is not enforced: `owner` has nothing behind it until the authorization Reef (#897). The push user lives until rotated, retired by #1010 (the registry Reef's push credential expires). The zot Nereid issues the Registry's certificates from the platform's registry CA until the certificate Reef (#1101, certificates as a Reef) does.

## Prior art

- **Kubernetes, NodePort** ([Service, type NodePort](https://kubernetes.io/docs/concepts/services-networking/service/#type-nodeport)): "the Kubernetes control plane allocates a port from a range", and "Your Service reports the allocated port in its `.spec.ports[*].nodePort` field"; the reason `spec` holds no port and the Nereid copies it.
- **zot, access control** ([Authentication and authorization](https://zotregistry.dev/v2.1.23/articles/authn-authz/)): "With an anonymousPolicy, a repository can allow anonymous actions which do not require user authentication", and "you can choose to allow any combination of read, create, update, or delete actions on specific paths"; anonymous reading and the per-repository `read` and `create` come from these.

## Consequences

- The nodes pull from a registry the platform runs, and #848 has a place to publish.
- Reading needs the Registry's read credential (#1015), but one credential serves every Environment allowed in the vault `registries`, so any of them can read every image of the Registry; the `kubernetes` Nereid gives it only to a Delivery whose Workload's owner (#1075) and Environment's owner (#1082) may both read the Registry, but a namespace allowed in the vault could still name another Registry's secret in a Release written by hand. **Security (OWASP A01, broken access control):** a credential per Environment is #953. The password no longer crosses plain HTTP: a Registry answers only over TLS (#1064, OWASP A02).
- A Registry needs the secrets Reef: without the vault `registries` it is not Ready (`NoVault`).
- `nereus registry` collides with no command; the Nereid registry (#22, #691) stays under `nereus nereid`.
- A person changes a tag's content by publishing a new tag, never by overwriting one.

## Open questions answered

No cluster ran for this design; `test/scene-registry-reef` (#1012) answers the three questions it left open, all yes:

- containerd pulls under mixed policies: a node pulled with no password while another user could write (#1012); since #1015 it pulls only with the read credential, and with none it is refused.
- zot's watcher sees a ConfigMap update: a new user and policy took effect with no restart of the Pod.
- The allocated port survives a Helm upgrade: the NodePort and `status.pullAddress` stayed the same.

*Origin: the owner's decisions of 2026-11-02 in #847 and of 2026-11-05 on its design (#1011 delivers this ADR). Raw data in Drive `#pontos/raw/2026-11-05/`.*

## Amendment (2026-11-13): publish pushes through the Nereus API's /v2 (#1328)

`nereus registry repository publish` no longer needs a kubeconfig (ADR 0018, the Nereus API as the one door). The Repository goes through `/v1/registry`, as since #1324, and the image through the API's `/v2`, which proxies the OCI Distribution API to the Registry's zot. `release source publish` (#1229) pushes the same way, so it now needs `nereus login` too.

- **The person's token, the Repository's push identity behind it.** crane sends the person's Nereus token (`registrytoken` in a temporary Docker configuration); the API checks it and mints, itself, a token of the ServiceAccount `push-<repository>` of `builds`, for the audience `nereus-registry-<registry>`, of at most 600 seconds, cached for half its life. zot still sees only the push identity, with `read` and `create`, so a tag is still never overwritten. The `/v2/` ping answers 401 with a Bearer challenge, as crane expects; `--insecure` is used only for a loopback instance URL.
- **Every `/v2` method needs `nereus-admins`**, reads too: the API would read with the push identity. Pulls by people outside `nereus-admins` are out of scope; nodes and Deliveries keep the read credential and the read identity (#1015, #1187).
- **Only the Distribution grammar passes:** a repository name, then `blobs/<digest>`, `blobs/uploads/[<id>]`, `manifests/<tag or digest>` or `tags/list`; a dot or empty segment, or any `%` in the raw path, is 404 with no call upstream. The upstream URL is built from the checked parts, over TLS that trusts only the Registry's ConfigMap `zot-ca`.
- **The API's grants are Roles the zot Nereid writes, never a ClusterRole** (owner, 2026-11-13). Per Registry, in `registry-<registry>`, `nereus-api-zot-ca` (get of `zot-ca` alone); per Repository, in `builds`, `nereus-api-push-<repository>` (get and token create of `push-<repository>` alone), made and removed with its ServiceAccount; each bound to `nereus-system/nereus-api` alone. The Nereid holds what they grant (RBAC's escalation rule), and its admission policy holds their exact shape. The policy `nereus-api-push-tokens` stays as a second lock: the API asks only tokens of `push-*` in `builds`, for a registry audience, of at most 600 seconds.
- **Open:** the API still holds create and update of ValidatingAdmissionPolicies (#1322), so it could change `nereus-api-push-tokens`; a follow-up issue takes it.

`test/scene-registry-reef` publishes with `KUBECONFIG=/nonexistent`, against a stand-in realm, and the same tag again is refused.
