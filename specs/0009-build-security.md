# 0009. The build reef's security design: what a hostile Dockerfile can reach

**Status:** Accepted (the owner's word, 2026-11-05, #1006), with the decisions below taken by the owner; the code of #848 (the build reef) may start once #847 (the registry reef) is done.

A link is the source of a claim. A sentence marked *(judgement)* is this design's own reading. Nothing here ran: no cluster was used, and every claim about a running cluster goes to [what the scene must prove](#what-the-scene-of-848-must-prove).

## The answer

- **A hostile Dockerfile gets no credential unless it escapes the container.** A fetch Job clones the source into a claim of that Build and runs no user code (#1141); then one Job, three containers in order: `build` runs the Dockerfile on that claim, read-only, and holds nothing secret, `token` and `push` hold a push token of ten minutes and run only after `build` is dead (#1010).
- **It keeps what it needs to build:** its own source, DNS, and the package hosts of an egress proxy's list (#1142): a `RUN` reaches the internet only through Smokescreen, which allows the main package hosts and those the build reef's default Mandate adds, and nothing else. It can send its source to a listed host, as an upload to a package index.
- **NetworkPolicy stops another namespace, Triton's Pods and other nodes, and on k3s the Pod's own node too.** Kubernetes allows a CNI to let that traffic through; k3s's policy controller does not, so the builds' egress policies stop the kube-apiserver, the kubelet and every NodePort, Triton's NATS included, at every address of the node (#1009). On a CNI that lets it through, the buildkit Nereid's probe reaches the kubelet and the Nereid runs no build (#1128).
- **The weak point is the kernel.** With seccomp off, the whole kernel is exposed to hostile code, and nothing here closes an escape. On k3d the kernel is the machine's: an escape reaches Triton, every Secret on the node and the owner's machine.
- **So:** the first slice builds only the scene's own Dockerfiles on a throwaway cluster. That proves the containment; it does not make the kernel safe, since a throwaway k3d cluster shares the same machine. Any other Dockerfile, builds on the kept cluster and #914 (a webhook starts a build) should wait for a kernel of their own, a VM.
- **BuildKit Jobs, not Shipwright, Tekton or Cloud Native Buildpacks:** a Job and its init containers already give the lifecycle, and each of the others adds controllers without removing the exception. Shipwright's split between building and pushing is copied.

## Decided (owner, 2026-11-05)

| # | Decision | Decided | Why |
|---|---|---|---|
| 1 | Where builds run | Throwaway clusters and the scene's own Dockerfiles for #848; anything else, the kept cluster and #914 only on a VM with its own small cluster | [The kernel](#what-the-exception-leaves-open) is the one risk this design cannot contain |
| 2 | `kernel.apparmor_restrict_unprivileged_userns` on the machine | Do not change it on the owner's machine; try an AppArmor profile, then a VM | [BuildKit's fix](#the-exception-itself) weakens the whole machine |
| 3 | Egress during a build | Public internet on 80 and 443 for the first slice; closed behind a mirror later (since #1142, an egress proxy with a host list) | Closed breaks every `RUN apt-get`, and no credential is there to steal |
| 4 | The git credential | A GitHub App's installation token, per build, for one repository with `contents: read`, minted by the github Nereid as the authentication reef's `Token` (ADR 0006, #1274) and asked by the buildkit Nereid, which never holds the App's key (#1070) | It expires in an hour and needs no port 22; a deploy key never expires; the App's key stays with the one Nereid that is the platform's identity towards GitHub |
| 5 | The push credential in #847 (the registry reef) | One per repository, `read` and `create` only | One shared credential would let any build overwrite any image |
| 6 | One Job, or a second Job to publish | One Job, as #848 decided | A second one closes only a bug in the push tool, and costs a volume between Pods |

The two points of #1004's own "To decide" are followed here: the design is the next free spec, and every Dockerfile is hostile, whoever wrote it.

## What runs

```console
$ nereus build create hello-a1b2c3d \
    --workload hello \
    --commit a1b2c3d
build/builds/hello-a1b2c3d created
```

| Order | Container | Runs | Holds | Sees |
|---|---|---|---|---|
| 0 (fetch Job, #1141) | `fetch` | `git`, on the Workload's repository at the commit, in a Pod of its own | nothing secret (a public repository) | writes the claim `source-<build>` |
| 1 (init) | `build` | BuildKit, and every `RUN` of the Dockerfile | nothing secret | the claim `source-<build>` read-only; writes an OCI layout to `image` |
| 2 (init) | `token` | one `printf` in busybox, pinned by digest | the projected push token | writes `config.json` to an in-memory `docker` volume |
| 3 | `push` | a small push tool with no shell | the push token, in `config.json` | `image` and `docker` read-only |

[Each init container must complete before the next starts](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/), and they can hold Secrets other containers cannot. A build's processes die with its container, because containers of a Pod do not share a PID namespace unless asked to *(judgement)*. Shipwright [mounts the push Secret only on its `image-processing` step](https://github.com/shipwright-io/build/blob/main/pkg/reconciler/buildrun/resources/image_processing.go); Cloud Native Buildpacks [keeps its registry phases in separate containers "to avoid exposing sensitive data to buildpacks"](https://buildpacks.io/docs/for-platform-operators/concepts/lifecycle/). This takes the same shape.

## The credentials

The credential cannot sit beside BuildKit. The Kubernetes example runs `--oci-worker-no-process-sandbox`, which [lets a `RUN` `kill`, and depending on seccomp `ptrace`, any process in the daemon's container](https://github.com/moby/buildkit/blob/master/docs/rootless.md). Seccomp is off here, and [a `RUN` as root is the daemon's own UID 1000](https://github.com/moby/buildkit/blob/master/docs/rootless.md#change-uidgid), so a `RUN` can read anything the daemon holds *(judgement)*. That rules out BuildKit's own git and push paths, and [Shipwright's strategy-managed push](https://github.com/shipwright-io/build/blob/main/docs/buildstrategies.md).

| | Git credential | Push credential |
|---|---|---|
| Who holds the long-lived part | the github Nereid: the GitHub App's key is a param of its authentication Mandate, a secret of the secrets reef ([ADR 0006](../adr/0006-authentication-reef.md); [ADR 0002](../adr/0002-conceptual-model.md): credentials live with the Nereid); the buildkit Nereid holds no key | the registry reef's Nereid; the person uses only their own login, as #847 decided |
| What a build receives | a token for one repository, `contents: read` ([GitHub: limits on repositories and permissions](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)): the buildkit Nereid asks a `Token` named after the Build, owned by it, in `builds`, only when an authentication Mandate's `allow` covers `builds` and the Workload's repository; otherwise the fetch is anonymous | a token of the Repository's ServiceAccount `builds/push-<repository>`, for one Registry's audience `nereus-registry-<registry>`; zot maps it to a user bound to the ServiceAccount's uid, `read` and `create` on one repository path ([zot: OIDC bearer and per-user policies](https://zotregistry.dev/v2.1.23/articles/authn-authz/)) |
| Lifetime | [one hour](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app), minted per build | ten minutes, the least kubelet asks for a [projected token](https://kubernetes.io/docs/concepts/storage/projected-volumes/#serviceaccounttoken); kubelet renews it at 80% of that, so a push may start with about two minutes left |
| Where it sits | the Secret `token-<build>` the github Nereid writes in `builds`, which the buildkit Nereid never reads; mounted read-only only in the fetch Pod (#1141), the admission policy of `builds` admits no other Secret; git reads the file through a fixed credential helper, only after GitHub answers 401, so the token reaches no argv, environment or `.git`; the `Token` is deleted once the fetch ends, and its Secret with it | a projected volume mounted only in `token`, which writes it to memory for `push`; no Secret holds it |
| If stolen | reads the repository the build already has | adds new tags to that one repository; cannot move a tag or touch another repository |

**The registry CA, copied, not a credential (#1064):** the Registry answers only over TLS, so `push` checks its certificate. The buildkit Nereid reads the CA's certificate the Registry publishes in its ConfigMap `zot-ca` (get on that name only, cluster-wide), copies it to the ConfigMap `registry-ca-<registry>` in `builds`, one per Registry (#1152), and mounts it read-only in `push` alone at `/etc/nereus/registry`; `SSL_CERT_FILE` points crane there, which in Go replaces the system roots, so `push` trusts that CA and nothing else, and never takes `--insecure`. It holds a certificate, no key: a hostile build that reads it learns nothing secret. The admission policy admits a ConfigMap named `registry-ca-` and a DNS label as a volume, besides `emptyDir` and `secret`. The Nereid's HEAD for the digest trusts the same CA alone.

The repository comes from the Workload and the destination from the registry reef, never from free text on a Build, so a credential goes only where it belongs *(judgement, the same rule as ADR 0020's on server-side request forgery)*. The tag is the Build's name, unique, which is why `update` is not needed. The Nereid reads the digest from the registry, not from anything the Pod wrote.

**What a hostile Dockerfile can read during a build:**

| Thing | Reads it? | What stops it | Left open |
|---|---|---|---|
| The source at that commit | Yes | Nothing; it needs it | It can send it out |
| Git token | No | Only the fetch Pod, another Pod, holds it; the claim it writes holds no `.git` | A copy in `tmpfs` on the node until the fetch Pod goes |
| Push credential | No | Not mounted in `build`, and `push` has not started | The same copy on the node |
| ServiceAccount token | No | `automountServiceAccountToken: false` | None |
| Service addresses in the environment | No | `enableServiceLinks: false` | DNS still answers |
| Other builds | No | One Pod per build, no shared cache | Slower builds |
| BuildKit's process and state | Yes | Nothing | It can alter its own image, which it controls anyway |
| The next container | Indirectly | `image` is read-only in `push`, which refuses anything but regular files and checks digests | A bug in the push tool would run with the credential and the internet |
| Build secrets and SSH agent | Nothing to read | The first slice offers none to `RUN --mount` | None |

The `tmpfs` copy is Kubernetes' behaviour: [a Secret reaches a node only if a Pod there needs it, and the kubelet keeps it in `tmpfs` until the Pod is deleted](https://kubernetes.io/docs/concepts/configuration/secret/#information-security-for-secrets). Mounting it in one container [hides it from the others](https://kubernetes.io/docs/concepts/security/secrets-good-practices/), not from the node. So an escape reads both credentials of its own build.

**The push credential expires (#1010).** zot v2.1.23 takes Kubernetes ServiceAccount tokens through `http.auth.bearer.oidc`, from one issuer: the cluster's own. The Nereid creates the ServiceAccount, records the uid of its own create in its push policy in `zot-config` (copied to `status.pushIdentity.uid`, never trusted from there, #1125), trusts no other of that name, and deletes with that uid as a precondition. The CLI and the buildkit Nereid compute whose token they use and where they push, from the Repository's name and `spec.registry`, and refuse a status that says otherwise.

**Decision, option A over B (owner, 2026-11-06):** zot reads the issuer's discovery and its keys with no credential, and v2.1.23 has no setting for a static key set. A: a new cluster's API server takes an `AuthenticationConfiguration` that lets anonymous requests through only on `/.well-known/openid-configuration` and `/openid/v1/jwks`, and `system:unauthenticated` is bound to `system:service-account-issuer-discovery`. B: `--anonymous-auth=true` opens `/version`, `/healthz` and whatever else anonymous may read. A opens two public documents and nothing else. `nereus doctor` checks it; a cluster made before this needs a recreate. Revisit when zot takes a static key set.

`Stand-in:` who may publish and who may start a build is not enforced. #847's `owner` rule has nothing behind it, since [ADR 0018](../adr/0018-nereus-api.md)'s API has only `/healthz` and `/v1/me`, and `nereus build create` reaches the cluster with the kubeconfig, so anyone holding it can make the Nereid publish to any Workload's repository. Retired by #897 (the authorization reef) and the move of this group behind the API.

**A Build's owner, checked by the Nereid (#1090):** a ValidatingAdmissionPolicy cannot read the Workload, so the buildkit Nereid does: a Build whose `spec.owner` is neither the Workload's owner nor above it in the tenancy tree ([ADR 0015](../adr/0015-tenancy.md)), or whose tree does not lead there, ends `Failed`, reason `OwnerNotWorkloads`, with no Job. A Build with no owner skips that check, which would hold only while RBAC lets the operators alone create Builds: a ValidatingAdmissionPolicy refuses it unless the requester is in the operators group `nereus:operators` or `system:masters`, on create and on an update that drops the owner or changes the spec of a Build with none, while an update that leaves the spec, as the Nereid's finalizer, passes (#1118); the Nereid's early return stays for the operators' Builds. Pinning `spec.commit` to commits reachable from the Workload's ref needs a clone, so it stays a later step. The deadline of a Build's Job is `BUILD_DEADLINE_SECONDS` in the Nereid's environment, 900 by default.

`Stand-in:` a GitHub App's key means one git host. Other hosts wait for #234 (the platform's identity towards external systems) and #279 (the repository reef).

`Stand-in:` a token only for the owners the operator trusts (from the review of #1070, owner, 2026-11-10). An authentication Mandate's `allow` names a namespace, and `builds` is shared by every tenant, while a team writes its own Workload's `spec.source.repository`; the owner check of #1090 ties a Build to its Workload, not the Workload to a repository. So a team could name another team's private repository and have a token minted for it. Until #1331 (a tenant's Build gets a clone token only for a repository its own Organization is allowed), the buildkit Nereid asks a `Token` only when the Workload's owner, and the Build's when it names one, are in `BUILD_TOKEN_OWNERS`, the tenancy nodes the operator trusts (`project/nereids`; empty by default, so no Build gets a token). Otherwise a Build of a repository a Mandate covers stays Pending, `TenantTokenNotSupported`, naming the owner not trusted, with no fetch; one no Mandate covers is fetched anonymously as before. The repository the Token is asked for and the one the fetch clones are read once, from the same Workload, in the same pass.

## The NetworkPolicy

**Does the cluster enforce it?** The documentation says yes; #848's scene must prove it. [K3s includes an embedded controller, built on kube-router's library, off only with `--disable-network-policy`](https://docs.k3s.io/networking/networking-services), and its [hardening guide says it enforces policies "if any are created"](https://docs.k3s.io/security/hardening-guide). `ensure_k3d_cluster` in `cli/src/nereus/cluster.py` passes only `--disable=traefik`. `test/scene-metrics` already proves an ingress denial on k3s, not egress and not the node. [Without such a controller a policy has no effect](https://kubernetes.io/docs/concepts/services-networking/network-policies/), silently, so the Nereid must refuse to be Ready until a probe Pod is really stopped *(judgement)*. **Built in #1090:** after the policies, the Nereid runs a short-lived probe Job in `builds`, in the shape the admission policy admits (the git image, UID 1000, no token). It must reach CoreDNS on 53, which `allow-dns` allows (the positive control: a probe stopped everywhere would pass for a policy enforced), and be stopped, refused or dropped, on the Nereid's own Service in `nereus-system`, by the name and port the API gives it, which nothing allows. A name that does not resolve proves nothing, and a dead target would refuse too: the Nereid checks that the same Service answers it from outside `builds`, before the probe and when reading its verdict, and otherwise stays `Ready=False`, reason `ProbeTargetDown`, with no verdict. **Only the egress policy of `builds` may stop it (#1113):** an ingress policy on the target would stop the probe by itself, so Ready would go `True` even if the egress rules of `builds` were ignored. At the same two moments the Nereid lists the NetworkPolicies of `nereus-system` (its Role there gains `list` on them, nothing else) and gives no verdict, reason `ProbeTargetGuarded`, while one of them [guards ingress (its `policyTypes` name `Ingress`, or are left out)](https://kubernetes.io/docs/concepts/services-networking/network-policies/) and may select the Service's Pods. A policy misses them only by a label of the Service's selector (`matchLabels` with another value, `In` without it, `NotIn` with it, `DoesNotExist` on it), since the Pods may carry labels the Nereid does not know; a Service without a selector is guarded by any ingress policy there. The VMSingle's policy (#744) names another `app.kubernetes.io/name`, so it does not count. Until both hold, the Nereid stays `Ready=False`, reason `NetworkPolicyNotEnforced`, and every Build stays `Pending` with no Job. The probe runs again every `PROBE_SECONDS` (600 by default) and its Job is deleted once read; after no verdict (`ProbeTargetDown`, `ProbeTargetGuarded`) it tries again within seconds, 5 then doubled up to 60, since the target not answering yet is the Nereid's own Pod at start-up. Its name cannot be a Build's (it starts with a digit), and a Job of that name without the probe's label, or with an owner, proves nothing. **The node too (#1128):** last, the probe tries its own node on 10250, the kubelet's port, which every node has, at the address the [downward API's `status.hostIP`](https://kubernetes.io/docs/concepts/workloads/pods/downward-api/) gives it, so it needs no token; 6443 and the NodePorts fall under the same rule, and `make scene-build` keeps proving them. A node that answers keeps the Nereid `Ready=False`, reason `NodeReachableFromBuilds`, and every Build `Pending` with that reason and no Job, whichever CNI the cluster runs. The positive control is the Service's: the Nereid reads the `status.hostIP` of the probe Job's own Pod, by the Job's uid in its label and owner reference, since an earlier probe's Pod may still be terminating on another node (its Role in `builds` gains `list` on Pods, nothing else) and checks the node answers it on 10250 from outside `builds`; a node that does not, or a Pod with no address, gives no verdict (`ProbeTargetDown`). A host firewall for a CNI that fails this check gets its own issue when Nereus first runs on one, together with the build pool of #1121.

**Enforcement can be missing on a k3d cluster (#1113).** During #1090 one throwaway cluster, made by hand with `k3d cluster create <name> --no-lb --k3s-arg --disable=traefik@server:0 --wait` (k3d v5.9.0, its default k3s v1.35.5+k3s1, kube-router's netpol v2.6.3-k3s1), let a Pod of `builds` reach `1.1.1.1:8080` and CoreDNS's 9153 under `deny-all`, although its policy controller had started and written its `KUBE-NWPLCY` chains; `make scene-build`'s clusters, made by `ensure_k3d_cluster`, stopped the same Pod. The flags are not the cause: the same command, run again on the same machine (`br_netfilter` loaded, `bridge-nf-call-iptables` 1, iptables in nf_tables mode), enforced egress at once, also with the old order (the namespace and Pods right after `--wait`, the policies later). One start-up fact did show: `k3d cluster create --wait` returned about ten seconds before k3s's log said `Starting network policy controller`, so a cluster ready for k3d is not yet enforcing any policy; [the controller is on unless `--disable-network-policy` is given](https://docs.k3s.io/networking/networking-services), and no scene passes it. The first cluster's cause stays unknown, so no scene states one; the probe gate is what catches it: on such a cluster the buildkit Nereid stays `NetworkPolicyNotEnforced` and runs no Build *(judgement)*.

**The policy:** deny all ingress and egress for every Pod of the build namespace, then allow only:

| Egress to | Port | For |
|---|---|---|
| CoreDNS in `kube-system` | 53, UDP and TCP | Resolving names |
| Smokescreen in `builds-egress`, by namespace and Pod label (#1142) | 4750 TCP | Packages, through the proxy's host list |
| The registry's Pods, by namespace and Pod label | The registry's | `push` |
| `0.0.0.0/0` except `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `100.64.0.0/10`, `127.0.0.0/8`, for the fetch Pod alone (label `getnereus.dev/step: fetch`, #1141) | 443 TCP | `git` |

[A policy applies to the whole Pod, init containers included](https://kubernetes.io/docs/concepts/services-networking/network-policies/), so `build` and `push` share these rules (the fetch Pod is a Pod of its own, #1141); a `RUN` leaves through the Pod's network, so it does too *(judgement, the scene proves it)*. [It cannot target a name](https://kubernetes.io/docs/concepts/services-networking/network-policies/), so `github.com` alone cannot be allowed. The policy is created with the namespace, before any Job, because [a Pod created before its policy is handled may start unprotected](https://kubernetes.io/docs/concepts/services-networking/network-policies/). That holds for every new Pod too: k3s's policy controller applies the policies to a Pod some seconds after it starts, and the fetch Pod reached the API server's ClusterIP in that window (seen on k3s v1.35, #1141). So no git or BuildKit runs before its Pod is stopped on the API server, whose address kubelet gives every Pod: the fetch script waits for it, and the build Pod's first init container, `contained`, does (`CONTAINED` in `controllers/buildkit/buildkit.py`); a Pod still not stopped after 60 seconds fails, naming the address.

| Threat | What stops it | Left open |
|---|---|---|
| Another namespace, Triton's Pods | The `except` covers k3s's [Pod range `10.42.0.0/16` and Service range `10.43.0.0/16`](https://docs.k3s.io/cli/server) | Their NodePorts, below |
| Another build | No rule allows it, in the same namespace too | None |
| The kube-apiserver | No rule, no token | Stopped on k3s, at its Service and on the node, below |
| k3d's local registry and caches on Docker's network, the owner's machine | The private ranges in `except` | None on k3s, below |
| Cloud metadata | `169.254.0.0/16` in `except`, [as Kubernetes advises](https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/): it can hold node credentials | On k3d nothing answers there, so only a first cloud run proves it |
| Sending the source out | The egress proxy: only its listed hosts, by name, never an address (#1142) | To a listed host, as an upload to a package index |
| Mining, scanning, attacks on others | The proxy's host list, the deadline, the limits | Open within the listed hosts |

**The node, on k3s, is not a hole.** [Kubernetes lets a CNI allow the traffic between a Pod and its own node whatever the policies say](https://kubernetes.io/docs/concepts/services-networking/network-policies/), which would leave a build every port on its node: the [kube-apiserver and K3s supervisor on 6443, the kubelet on 10250](https://docs.k3s.io/installation/requirements), and any NodePort, Triton's NATS on 30422 (`controllers/triton/deploy/nats.yaml`) among them. k3s's policy controller does not allow it: the node's addresses are private, so the `except` of the internet rule leaves them out, and no other rule names them. `make scene-build` proves it from a `RUN` (#1091, #1009): 6443, 10250 and a NodePort refused at the node's address in the Pod network (the `RUN`'s gateway) and at every address of the /24 of k3d's network on Docker that holds the node, with the node answering there from outside `builds`; the owner's machine (`host.k3d.internal`) is refused too. This holds for k3s's network as it ships, not for every CNI *(judgement: Calico and Cilium each have their own rule for traffic to the host, not checked here)*. On a CNI that lets it through, the closing options are a host firewall rule on the build node, or a separate cluster, since a NodePort answers on every node of its cluster *(judgement)*; the buildkit Nereid refuses builds there instead of trusting the CNI (#1128, below).

**DNS:** the policy does not filter what CoreDNS answers. [A Pod resolves Services in any namespace by name, and SRV records give their named ports](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/), so a build can test which names exist, and it can leak data in queries. It learns names, and reaches nothing more. [`dnsPolicy: None` with `dnsConfig`](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/) and a public resolver would remove the names; `push` would then need the registry's address another way, so it waits *(judgement)*.

**Limits:** [`activeDeadlineSeconds` ends a Job](https://kubernetes.io/docs/concepts/workloads/controllers/job/), `backoffLimit: 0` never reruns hostile code, and CPU, memory, a `sizeLimit` on the volumes and a ResourceQuota on the namespace bound the rest. [NetworkPolicy cannot log what it blocks](https://kubernetes.io/docs/concepts/services-networking/network-policies/).

**The egress proxy (#1142):** a `RUN` reaches the internet only through [Smokescreen](https://github.com/stripe/smokescreen) (Stripe, MIT, built to restrict the egress of untrusted code), one Deployment in the namespace `builds-egress` that the CLI installs with `builds`, reached on 4750 and the only Pod there with 80 and 443 to public addresses. BuildKit gives every `RUN` `HTTP_PROXY` and `HTTPS_PROXY` as its predefined proxy build args, kept out of the image's history; a tool that ignores them is stopped by the policy. busybox `wget` sends an `https` URL to `http_proxy` as a plain request, which Smokescreen does not serve (seen in #1142's scene): a `RUN` fetches over `https` with curl or its package manager, which ask for a `CONNECT` tunnel. Smokescreen allows a `CONNECT` only to a host of its ACL, refuses private addresses by itself, and logs every decision. The ACL is the main package hosts, each named with its ecosystem in `EGRESS_DEFAULTS` (`controllers/buildkit/buildkit.py`), and the hosts of the build reef's default Mandate's parameter `egressHosts`, an admin's act, since whoever writes the Dockerfile may be hostile; `github.com` stays off, since it accepts pushes. The buildkit Nereid writes it into a ConfigMap and rolls the Deployment by an annotation holding its hash, since Smokescreen does not reload it. One proxy cannot tell builds apart, so `egressHosts` comes from the default Mandate only, and a Build through another Mandate that sets it is refused (`EgressHostsNotDefault`). A build whose `RUN` was refused fails with reason `EgressRefused`: the Nereid reads the host from the proxy's log, matched by the build Pod's address, and the message gives the `nereus mandate apply` that allows it. buildkitd itself gets no proxy, so a `FROM` that misses the mirror reaches nothing.

`Stand-in:` there is no record of what a build reached beyond the proxy's own log; the record is part of #256 (the platform's audit log). **Built in #1140:** every `FROM` goes through the Registry's zot, which mirrors docker.io, ghcr.io and quay.io on demand. Left open, with DNS: an image's name reaches the remote when zot fetches it, so a `RUN`, which reaches zot as `push` does, can make zot ask Docker Hub for a name it chose, a few bytes the remote sees.

`Stand-in:` NATS has no TLS; Triton's manifest already says it has its own issue. The node's ports, closed on k3s by #1009, are checked by the Nereid's probe on the kubelet's 10250 since #1128; the scene keeps proving 6443 and the NodePorts.

## The exception itself

[BuildKit recommends rootless "to minimize the chance of container breakout attacks"](https://github.com/moby/buildkit/blob/master/examples/kubernetes/README.md). What it needs, from [its rootless page](https://github.com/moby/buildkit/blob/master/docs/rootless.md) and [its Kubernetes Job](https://github.com/moby/buildkit/blob/master/examples/kubernetes/job.rootless.yaml):

| Relaxation | Why, in BuildKit's words | [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) |
|---|---|---|
| `seccompProfile: Unconfined` | "several syscalls such as `unshare` (used by runc) and `mount` (used by snapshotters, etc)" | `baseline` forbids it |
| `appArmorProfile: Unconfined` | "mounting filesystems, etc"; "not needed when the host operating system does not use AppArmor" | `baseline` forbids it |
| `--oci-worker-no-process-sandbox` (a BuildKit flag, not a Pod field) | Docker's `systempaths=unconfined` has no Kubernetes equal; "discouraged", and it allows the `kill` and `ptrace` above | Allowed |
| `allowPrivilegeEscalation` left on | [Shipwright: so setuid binaries can run](https://shipwright.io/docs/build/buildstrategies/) | `baseline` allows it, `restricted` forbids it |

**Not asked for, and refused:** `privileged`, added capabilities, `hostPath`, host namespaces, a device; the Pod runs as UID 1000. [`RUN --network=host` and `RUN --security=insecure` need entitlements](https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/reference.md), which the daemon never receives. A Dockerfile can still name its own frontend with `# syntax=`; it runs under these same limits *(judgement)*.

**Why one namespace, and its weak point.** [Pod Security Admission works per namespace, by level](https://kubernetes.io/docs/concepts/security/pod-security-admission/), and its exemptions skip every check. Since `baseline` forbids both profiles, this namespace must be `privileged`, the level that allows everything, including a Pod the exception never asked for. Any other namespace would inherit that, so it stays in one, holding only short-lived Jobs and no long-lived Secret, while the Environments keep `baseline` (#633, pod security of the vcluster Nereid's environments).

**The label alone is not enough.** A ValidatingAdmissionPolicy, as #633 already uses for Environments, pins the Pods of this namespace to the shape above and to the build's three images by digest (git, BuildKit and the push tool), because [whoever can create a Pod can read the namespace's Secrets](https://kubernetes.io/docs/concepts/configuration/secret/). The Nereid creates Jobs, not Pods, so only its ServiceAccount may create a Job there and only the Job controller a Pod; the shape holds on both, on every update, and no Pod takes an ephemeral container. Built in #1089, by the CLI before the namespace (`builds_policy` in `cli/src/nereus/local_nereids.py`). What is left: a cluster admin, or a stolen Nereid token within that shape *(judgement)*.

**A narrower route to `baseline`, untested.** `baseline` [allows `Localhost` profiles](https://kubernetes.io/docs/concepts/security/pod-security-standards/), and [relaxes `procMount` for a Pod with `hostUsers: false`](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/), which [BuildKit names as the near equal of `systempaths=unconfined`](https://github.com/moby/buildkit/blob/master/docs/rootless.md). Together they could bring back the process sandbox and drop `privileged` from the namespace *(judgement: no source shows BuildKit running this way)*. The cost is profile files on every node.

**The machine may refuse it.** BuildKit's troubleshooting for `fork/exec /proc/self/exe: permission denied` blames `kernel.apparmor_restrict_unprivileged_userns=1`, and its [fix is to set it to `0` on the host](https://github.com/moby/buildkit/blob/master/docs/rootless.md). The owner's machine reads `1` (`sysctl`, 2026-11-05). k3d shares that kernel, so #848's scene may hit this, and the fix relaxes the whole machine, not one namespace *(judgement)*. Decision 2 keeps it at `1`. **It did not:** `make scene-build` (#1067, 2026-11-06) built and pushed with rootless BuildKit on k3d with the sysctl at `1`, with seccomp and AppArmor `Unconfined` on the `build` container.

**In sandbox mode the exception is gone** (#1120, after the spike of #1117, "Without a VM of our own" below). The operator sets the buildkit Nereid's `BUILD_RUNTIME_CLASS` (`nereus nereid apply buildkit --set BUILD_RUNTIME_CLASS=gvisor`): every Pod of `builds` gets that `runtimeClassName`, the `build` container keeps `seccompProfile: RuntimeDefault` and no AppArmor field, the namespace goes to `baseline`, and the admission policy pins that RuntimeClass, with no `Unconfined` profile, on every Pod. It still needs `allowPrivilegeEscalation` for `newuidmap`, so `restricted` stays out. The Nereid is Ready only once a probe Pod under the RuntimeClass reports a kernel that is not its node's (`RuntimeClassMissing`, `SandboxNotEffective`): a RuntimeClass only names a handler, which must be installed on the nodes.

| Mode | `BUILD_RUNTIME_CLASS` | `builds` | Builds |
|---|---|---|---|
| Portable | empty | `privileged`, the exception above | Trusted code only: a Build with `spec.owner` ends `Failed`, `SandboxRequired`; the operators' (no owner, #1118) run |
| Sandbox | `gvisor` (k3d, GKE Sandbox, EKS with runsc on the nodes), Kata on AKS | `baseline`, no exception | Any Dockerfile |

The rest of this section, and "What the exception leaves open", describe portable mode.

### What the exception leaves open

**NetworkPolicy does nothing about a kernel escape.** It filters packets; an escape is a system call. With seccomp off, a `RUN` can call what the default profile refuses, and rootless only means it starts unprivileged. A kernel bug reached from there gives:

- **The node's Secrets and containerd:** Triton's, and any other Pod's on that node, plus the images those Pods run *(judgement, from [what a node holds](https://kubernetes.io/docs/concepts/configuration/secret/#information-security-for-secrets))*.
- **The control plane:** `ensure_k3d_cluster` passes no `--agents`, and [k3d defaults to one server and no agents](https://github.com/k3d-io/k3d/blob/main/cmd/cluster/clusterCreate.go), so every Pod shares a node with the kube-apiserver.
- **The owner's machine:** [k3d's nodes are containers](https://k3d.io/stable/usage/commands/k3d_cluster_create/) that [run privileged](https://github.com/k3d-io/k3d/blob/main/pkg/runtimes/docker/translate.go), on the machine's own kernel.

For comparison, today's `docker build` in `make scene` runs on the same kernel, but keeps Docker's default seccomp and AppArmor *(judgement)*. The exception is a real step down from it, in exchange for builds with no Docker socket.

| What would reduce it | Closes | Leaves | Cost |
|---|---|---|---|
| [`hostUsers: false`](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/) | An escape lands as an unprivileged user; several high and critical CVEs did not apply | A kernel bug that gives root | Low; needs Kubernetes 1.36 for stable, containerd 2.0, Linux 6.3 and idmap mounts, unproven inside k3d |
| `Localhost` seccomp and AppArmor profiles | Much of the kernel surface | Whatever BuildKit needs: `unshare`, `mount` | Writing and keeping the profiles, files on nodes |
| Dedicated node ([taint and selector](https://kubernetes.io/docs/tasks/administer-cluster/securing-a-cluster/)) on a real machine or VM | Other Pods' Secrets, Triton, the control plane, the owner's machine: [Secrets reach only nodes that need them](https://kubernetes.io/docs/concepts/configuration/secret/#information-security-for-secrets) | That node's kubelet identity; the cluster's NodePorts; the builds' own credentials | A VM or a machine, always on or started per need. **On k3d a dedicated node closes nothing:** the same kernel *(judgement)* |
| [gVisor](https://gvisor.dev/docs/) | [The host kernel, behind a per-sandbox kernel](https://gvisor.dev/docs/) | gVisor's own bugs | [Syscall overhead and missing syscalls](https://gvisor.dev/docs/); its [tutorial shows `docker build`](https://gvisor.dev/docs/tutorials/docker-in-gvisor/), not rootless BuildKit; [K3s does not list it](https://docs.k3s.io/advanced), so containerd is set by hand |
| [Kata Containers](https://katacontainers.io/) | The host kernel: "a dedicated kernel" | The hypervisor | Virtualization inside k3d's containers; [K3s does not list it](https://docs.k3s.io/advanced) either. High on k3d *(judgement)* |
| Throwaway [vcluster](https://www.vcluster.com/docs/vcluster/introduction/what-are-virtual-clusters) | API-level reach | **The kernel:** with shared nodes its Pods [run on the host's node pool](https://www.vcluster.com/docs/vcluster/introduction/what-are-virtual-clusters) *(judgement: the page does not mention the kernel)* | Low, the vcluster Nereid exists; it does not answer this threat |
| A VM with its own small cluster | All of the dedicated node's row, plus the NodePorts and the kube-apiserver of the kept cluster | The builds' own credentials; the VM's kernel | RAM and a VM to run, and the registry must be reachable from it, beyond what #844 (a node pulls from a registry inside the cluster) proves |

**Recommendation:** `hostUsers: false` if the scene proves it, on every cluster. On the kept cluster, no build until a VM with its own small cluster runs them, which also keeps decision 2 away from the owner's machine. A VM's boundary is the one here that is both well understood and simple *(judgement)*. [OWASP asks for the same: "pipelines running unreviewed code are executed on isolated nodes"](https://owasp.github.io/www-project-top-10-ci-cd-security-risks/CICD-SEC-04-Poisoned-Pipeline-Execution). Accepting the risk for the owner's own repositories alone would be a choice about the person, which this design was asked not to rely on; a poisoned dependency runs in the owner's own `RUN` too.

`Stand-in:` in portable mode the builds share the node's kernel, which on k3d is the machine's, so only trusted code runs there (`SandboxRequired`). Sandbox mode (#1120) retires it: a hostile `RUN` sees gVisor's kernel. It replaced the VM of #1007.

## The build pool

**Builds run on nodes of their own** (#1121), so an escape, even from the sandbox, lands where no Workload, Nereid or Secret of theirs is. The operator labels and taints those nodes with one key, `build.getnereus.dev/pool`, and sets its value on the Nereid:

```console
$ nereus nereid apply buildkit --set BUILD_NODE_POOL=builds
namespaces/builds applied (Pod Security baseline, every Pod in the RuntimeClass gvisor, every Pod on the nodes labelled build.getnereus.dev/pool=builds, ...)
```

| Cluster | The pool |
|---|---|
| EKS | A node group with the label and the taint `build.getnereus.dev/pool=builds:NoSchedule` |
| AKS, GKE | A node pool with both; on GKE, GKE Sandbox is turned on per pool, on AKS Pod Sandboxing too |
| k3d | An agent node: `NEREUS_K3D_BUILD_POOL=builds` before `nereus init --create-cluster` |

- **Every Pod of `builds`** (fetch, build, both probes) gets the pool's `nodeSelector` and toleration, in portable mode too, and the admission policy of `builds` refuses one without both. Empty, Pods land on any node, so a one-node cluster still builds.
- **No other Pod tolerates the taint.** A second policy, on every namespace but `builds` and those `BUILD_POOL_NAMESPACES` lists (`kube-system` by default, where creating a Pod is already an administrator's act), refuses a toleration of the pool's key or of every taint, and a Pod that names its node, which skips the scheduler and so the taint (kubelet checks only `NoExecute` ones).
- **The cloud metadata endpoint** `169.254.169.254` is stopped by the egress policy of `builds`, which excludes `169.254.0.0/16`. The scene proves it with a listener on the build node, reached from a Pod outside `builds`.
- **The node's cloud identity has no permissions** (an install concern): a node group's or pool's role grants nothing but pulling images. Its ports stay #1009.

Several builds share a node: the sandbox isolates the kernel. One build per node (anti-affinity) is a later setting for clusters without a sandbox.

## The OWASP categories

The lists are OWASP's own, read for names only: the [Kubernetes Top Ten, 2025 edition](https://kubernetes-top10.owasp.org/), and the [Top 10 CI/CD Security Risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/), since #914 makes this reef the CI of Nereus. The mapping is this design's judgement.

| Category | Here | How |
|---|---|---|
| K01 Insecure Workload Configurations | Partly | The exception breaks it on purpose, in one namespace, pinned by admission |
| K02 Overly Permissive Authorization Configurations | Partly | No token in a build, the Nereid's rights limited; people are the Stand-in |
| K03 Secrets Management Failures | Covered | The credentials above; the node's copy stays |
| K04 Lack Of Cluster Level Policy Enforcement | Partly | One policy for one namespace; #898 (the policy reef) is the general answer |
| K05 Missing Network Segmentation Controls | Covered | The node too, on k3s; another CNI fails the Nereid's probe (#1128) |
| K06 Overly Exposed Kubernetes Components | Covered | Stopped from builds on k3s, at the node's every address; another CNI fails the Nereid's probe (#1128) |
| K07 Misconfigured And Vulnerable Cluster Components | Left out | The kernel and containerd are the host's; this is the residual risk |
| K08 Cluster To Cloud Lateral Movement | Covered, unproven | Metadata in `except`; k3d cannot prove it |
| K09 Broken Authentication Mechanisms | Left out | ADR 0018 and #897 |
| K10 Inadequate Logging And Monitoring | Left out | #256; the Job's logs go with its TTL |
| CICD-SEC-1 Insufficient Flow Control Mechanisms | Partly | A build deploys nothing by itself; #914 and #162 (deploy main on every push) must keep that |
| CICD-SEC-2 Inadequate Identity and Access Management | Left out | The Stand-in on who may publish |
| CICD-SEC-3 Dependency Chain Abuse | Left out | A `RUN` installs what it wants; the design assumes it may be hostile |
| CICD-SEC-4 Poisoned Pipeline Execution | Covered by containment | The premise here: contained, not prevented |
| CICD-SEC-5 Insufficient PBAC | Covered | Per-build credentials, network and namespace |
| CICD-SEC-6 Insufficient Credential Hygiene | Covered | The push token lasts ten minutes (#1010) |
| CICD-SEC-7 Insecure System Configuration | Partly | The exception is exactly this; contained |
| CICD-SEC-8 Ungoverned Usage of 3rd Party Services | Left out | The git host's webhook comes with #914 |
| CICD-SEC-9 Improper Artifact Integrity Validation | Left out | A digest says which image, not that it is good; #670 (signed images) |
| CICD-SEC-10 Insufficient Logging and Visibility | Left out | #256 |

## What was evaluated

| Tool | Saves of the Job's lifecycle | Adds to the attack surface | Removes the exception? |
|---|---|---|---|
| **BuildKit Jobs** | Nothing; [the Job has deadline, retries and TTL](https://kubernetes.io/docs/concepts/workloads/controllers/job/), init containers the order | No new controller | No |
| [Shipwright](https://shipwright.io/docs/build/buildstrategies/) | The steps, the managed push, the digest in results | [Tekton is required](https://github.com/shipwright-io/build/blob/main/README.md), plus its own controller and webhook | No: ["requires both AppArmor and SecComp to be disabled"](https://shipwright.io/docs/build/buildstrategies/) |
| [Tekton](https://tekton.dev/docs/pipelines/install/) | Steps and retries | A controller and a webhook; its quick install is "not meant for the production use" | No: the same BuildKit underneath *(judgement)*. Its default makes [credentials "available to all `Steps`"](https://tekton.dev/docs/pipelines/auth/), which must be turned off |
| [Cloud Native Buildpacks](https://buildpacks.io/docs/for-platform-operators/concepts/lifecycle/) | Its lifecycle, inside one Pod or more | Builders to trust | Probably, with [non-root phases](https://buildpacks.io/docs/for-platform-operators/concepts/lifecycle/) and no `RUN`, unproven; **it does not build a Dockerfile**, which is what #848 asks |

**Recommendation: BuildKit Jobs.** None of them saves what a Job plus init containers cannot do in a few lines, and Shipwright would bring two controllers for that. The model leaves Triton open: Shipwright, Tekton or Buildpacks can each be another Nereid of the same reef, and Buildpacks is the one worth trying for a repository with no Dockerfile. [kaniko, which #578 (how the platform builds and publishes a Package) named, is archived](https://github.com/GoogleContainerTools/kaniko) and out.

### Without a VM of our own (#1117)

**Answer:** under a `gvisor` RuntimeClass, rootless BuildKit builds and pushes on k3d in a `baseline` namespace, with no seccomp or AppArmor exception, and a hostile `RUN` sees gVisor's kernel, not the machine's. It replaces the VM of #1007 for the kernel threat; the network threat stays (#1009).

The research (2026-11-06, docs and issue threads):

| Option | Hostile `RUN` vs the host kernel | Verdict |
|---|---|---|
| [Dagger](https://github.com/dagger/dagger/blob/main/helm/dagger/templates/engine-daemonset.yaml) | Its engine DaemonSet is `privileged` with `capabilities.add: [ALL]`; "Dagger doesn't support rootless" ([#9071](https://github.com/dagger/dagger/issues/9071)) | Worse than today |
| [Kaniko](https://github.com/chainguard-forks/kaniko) (Google archived it 2025-06-03; Chainguard fork, security fixes only) | No seccomp or AppArmor exception, but the host kernel; its README: "does not make it safe to run untrusted builds" | Smaller surface |
| [Buildah `--isolation chroot`](https://kubernetes.web.cern.ch/blog/2025/06/19/rootless-container-builds-on-kubernetes/) with `hostUsers: false` | Host kernel, about Docker's default surface; `newuidmap` issues ([#4049](https://github.com/containers/buildah/issues/4049)) | Smaller surface |
| [gVisor](https://gvisor.dev/docs/user_guide/containerd/quick_start/) RuntimeClass | Syscalls go to gVisor's Sentry, not the host; Kaniko under runsc in production ([#13293](https://github.com/google/gvisor/issues/13293)); daemonless BuildKit works but for one emptyDir rename bug ([#14033](https://github.com/google/gvisor/issues/14033)); no KVM needed (systrap) | Removes the exposure, no VM |
| [Kata Containers](https://github.com/kata-containers/kata-containers/blob/main/docs/install/README.md) | A guest kernel per Pod; needs `/dev/kvm` inside k3d's privileged node containers | Removes it, a VM per Pod, fragile on k3d |
| [Sysbox](https://github.com/nestybox/sysbox) | Host kernel; k3s not supported ([#841](https://github.com/nestybox/sysbox/issues/841)) | Sideways |
| ko, Jib, Buildpacks | Do not build Dockerfiles | Not applicable |
| [firecracker-containerd](https://github.com/firecracker-microvm/firecracker-containerd) | Kubernetes and CRI are "longer-term roadmap" | Not usable |

**The spike** (2026-11-06, k3d v5.9.0, k3s v1.35.5, runsc `release-20261102.0`, one throwaway cluster, deleted at the end). gVisor ships one tarball now; `runsc` needs its `gvisor-bin/` sidecars beside it:

```bash
url=https://storage.googleapis.com/gvisor/releases/release/20261102/x86_64
curl -fsSLO "${url}/gvisor.tar.bz2" && curl -fsSLO "${url}/gvisor.tar.bz2.sha512"
sha512sum -c gvisor.tar.bz2.sha512     # gvisor.tar.bz2: OK
tar -xjf gvisor.tar.bz2 -C x           # runsc, containerd-shim-runsc-v1, gvisor-bin/
```

k3s's containerd learns the runtime from a template mounted at `/var/lib/rancher/k3s/agent/etc/containerd/config-v3.toml.tmpl` ([K3s advanced](https://docs.k3s.io/advanced)); the binaries are mounted in `/bin`. No `sudo` on the host:

```toml
{{ template "base" . }}

[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
```

```bash
k3d cluster create nereus-scn-1117-d2c84f --image rancher/k3s:v1.35.5-k3s1 --no-lb \
  -v "${x}/runsc:/bin/runsc@server:0" -v "${x}/containerd-shim-runsc-v1:/bin/containerd-shim-runsc-v1@server:0" \
  -v "${x}/gvisor-bin:/bin/gvisor-bin@server:0" -v "${tmpl}:/var/lib/rancher/k3s/agent/etc/containerd/config-v3.toml.tmpl@server:0"
kubectl apply -f - <<< '{"apiVersion": "node.k8s.io/v1", "kind": "RuntimeClass", "metadata": {"name": "gvisor"}, "handler": "runsc"}'
kubectl logs probe     # a busybox Pod with runtimeClassName: gvisor
# Linux probe 4.19.0-gvisor #1 SMP Sun Jan 10 15:06:54 PST 2016 x86_64 GNU/Linux
# [   0.000000] Starting gVisor...
```

The builds ran as Jobs shaped like `job()` in `controllers/buildkit/buildkit.py` (clone, build, push with crane), the `hello` fixture at the scene's pinned commit, into a `registry:2` Pod, in a namespace labelled `pod-security.kubernetes.io/enforce=baseline`:

| Build under `gvisor` | Result |
|---|---|
| Kaniko, the Chainguard fork (`ghcr.io/kaniko-build/dist/chainguard-forks-kaniko/executor:v1.25.19`, by digest; `cgr.dev/chainguard/kaniko` refuses anonymous pulls) | Built and pushed: `hello@sha256:7cf011e1…`; runs as root inside the sandbox |
| BuildKit as `job()`, both `Unconfined` profiles removed, `seccompProfile: RuntimeDefault` | Built and pushed: `hello@sha256:52f6d6e9…` |
| The same, without `--oci-worker-no-process-sandbox` | Built and pushed: `hello@sha256:d4b7e522…`; the process sandbox comes back |
| The same, with `allowPrivilegeEscalation: false` (`restricted`) | Fails: `newuidmap ... fork/exec /usr/bin/newuidmap: operation not permitted` |
| Control: BuildKit under runc with `RuntimeDefault` | Fails: `[rootlesskit:parent] error: failed to start the child: fork/exec /proc/self/exe: operation not permitted` |

Two findings on k3d. `appArmorProfile: RuntimeDefault` is refused by the kubelet (`Cannot enforce AppArmor: AppArmor is not enabled on the host`), so the field stays unset, which `baseline` allows. runsc ignores the Pod's seccomp profile unless it runs with `--oci-seccomp`; the host is guarded by the Sentry's own filter, not by that field. The rename bug of gVisor #14033 did not show.

The hostile Dockerfile is [`0009-spike/Dockerfile`](0009-spike/Dockerfile). What its `RUN` saw:

| Probe | runc, BuildKit as today | gVisor, BuildKit | gVisor, Kaniko |
|---|---|---|---|
| `uname -a`, `/proc/version` | `7.0.0-42-generic ... Ubuntu`: the machine's kernel | `4.19.0-gvisor` | `4.19.0-gvisor` |
| `dmesg` | `klogctl: Operation not permitted` | `klogctl: Operation not permitted` | `Starting gVisor...` |
| `ls /proc` | The host's: `acpi`, `asound`, `bootconfig`, `buddyinfo`, `diskstats`, `driver`... | gVisor's short list: `cpuinfo`, `meminfo`, `sentry-meminfo`, `sys`... | The same |
| `unshare --user --mount`, `mount -t tmpfs` | `Operation not permitted`; `permission denied` | The same | `unshare` passes, `mount` fails |
| The node on 6443 and 10250, `10.43.0.1:443` | Open | Open | Open |

The node's ports answer in all three: gVisor changes the kernel, not the network. The spike's namespace had no NetworkPolicy, so this does not contradict the scene, where the policies of `builds` stop them (#1009).

**Time**, the build container's seconds (one-second resolution), sequential, images already on the node:

| Build | hello, runs 1, 2, 3 | Job, runs 1, 2, 3 | 20,000 file writes in one `RUN`, once |
|---|---|---|---|
| BuildKit under runc (today) | 3, 3, 3 | 8, 9, 8 | `RUN` step 0.6 s |
| BuildKit under gVisor | 3, 3, 3 | 10, 9, 7 | `RUN` step 4.1 s |
| Kaniko under gVisor | 3, 2, 2 | 7, 7, 6 | about 1 s |

`hello` has no `RUN`, so it costs nothing; a syscall-heavy `RUN` is about seven times slower in BuildKit under gVisor (one run, the project's own observation).

**Recommendation: replace the VM of #1007 with the `gvisor` RuntimeClass, and keep BuildKit.** It removes the machine's kernel from a hostile `RUN` and the seccomp and AppArmor exception with it, with no VM to keep, so the builds namespace goes back to `baseline`. What stays: gVisor's own bugs, `runsc` set up by hand on every node, and a slower `RUN`. Kaniko adds nothing: archived, its Chainguard image is paid, and it runs as root *(judgement)*.

## What triggers a build

**First slice, as #848 decided:** by hand, from a git ref only. Nothing here depends on that for containment.

**#914 (a webhook starts a build) changes:**

- Hostile code runs unattended, on any push, so the kernel risk stops being theoretical: the VM of decision 1 comes first.
- A public address reaches the reef. #914's signature check and its rule of building only refs a Workload names must stay; [a fork's pull request never builds](https://owasp.github.io/www-project-top-10-ci-cd-security-risks/CICD-SEC-04-Poisoned-Pipeline-Execution).
- The quota has to bound builds per repository, since a push can start many.

**A local folder changes:**

- The source arrives through an upload, not a clone: no git credential, a new path through the API (ADR 0018), and a tar a person controls, so size and paths are checked.
- There is no commit, so the image says less about where it came from.
- The `build` and `push` containers stay as they are.

## What the scene of #848 must prove

Each from a hostile `RUN`, on a throwaway cluster, with an allowed probe beside the refused one, as `test/scene-metrics` does. k3s refuses a denied connection rather than dropping it, so the check accepts both.

| Probe | Expected |
|---|---|
| A Pod and a Service in another namespace | Stopped |
| `10.43.0.1`, and the node on 6443 and 10250 | Stopped (#1009); anonymous gets no data. **Observed** (#1091, k3d): all three refused from a `RUN`, at the node's address in the Pod network (`10.42.0.1`, the `RUN`'s gateway) |
| A NodePort on the node | Stopped (#1009). **Observed** (#1091, k3d): refused at the same address, so k3s's policy controller filters the node's ports from `builds`, unlike the [general rule](https://kubernetes.io/docs/concepts/services-networking/network-policies/) above |
| The node and the owner's machine on k3d's network on Docker | Stopped (#1009): 6443, 10250 and the NodePort at every address of the /24 of k3d's registry, which a `RUN` learns by name and which holds the node; the owner's machine (`host.k3d.internal`) on 5111, where k3d's registry was published before #654 and now publishes on the loopback only. The scene checks from outside `builds` that the node is in that range and answers on the three ports, and that the machine does not answer on 5111 there |
| k3d's registry on Docker's network | Stopped; so the scene's pull-through caches are not reachable from a build either |
| A public address on 443; on another port | Reached; stopped |
| `/proc` of every process, the environment, the mounts | No git or push canary found |
| A Pod with `privileged: true` or `hostPath`, or another image, in the namespace | Refused by admission |
| `RUN --network=host`, `RUN --security=insecure` | Fail |
| The push credential on another repository, and on an existing tag | Refused |
| A build past its deadline | Killed; no retry |
| The cloud metadata address `169.254.169.254` on 80 | Stopped (#1121), at a listener the scene puts on the build node, which a Pod outside `builds` reaches |
| The kernel a `RUN` runs on, in sandbox mode | gVisor's, not the node's (#1120), printed by the probes fixture's `PROBE kernel` |
| A Pod outside `builds` that tolerates the build pool's taint, or names a node | Refused by admission (#1121); a build's Pod runs on the build node |
| A `hostUsers: false` variant, and `apparmor_restrict_unprivileged_userns` at `1` | Record whether BuildKit starts. The spike of 2026-11-05 (k3s v1.35.5): it does not (`newuidmap ... Operation not permitted`), so #1067 runs with `hostUsers: true` |

## Stand-ins

Collected from above, for `docs/features.md` when the code arrives. This document creates none in code.

| Stand-in | Retired by |
|---|---|
| Who may publish or build is not enforced | #897, ADR 0018 |
| The push user has no per-build expiry | #1010 |
| One git host | #234, #279 |
| A token only for the owners in `BUILD_TOKEN_OWNERS`: the allowlist names `builds`, shared by every tenant | #1331 |
| No record of what a build reached | #256 |
| A kernel shared with everything else | Portable mode only: sandbox mode (#1120) runs every build in the `gvisor` RuntimeClass the spike of #1117 recommends |

## Learn more

- [BuildKit, rootless mode](https://github.com/moby/buildkit/blob/master/docs/rootless.md) and its [Kubernetes examples](https://github.com/moby/buildkit/tree/master/examples/kubernetes).
- Kubernetes: [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/), [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/), [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/), [User Namespaces](https://kubernetes.io/docs/concepts/workloads/pods/user-namespaces/), [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/).
- OWASP: [Kubernetes Top Ten](https://kubernetes-top10.owasp.org/), [Top 10 CI/CD Security Risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/), [CI/CD Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html).
- gVisor: [its docs](https://gvisor.dev/docs/), [installation](https://gvisor.dev/docs/user_guide/install/), [containerd quick start](https://gvisor.dev/docs/user_guide/containerd/quick_start/).
- K3s: [the network policy controller](https://docs.k3s.io/networking/networking-services). [zot, authentication and authorization](https://zotregistry.dev/v2.1.23/articles/authn-authz/).

*Origin: the owner's condition of 2026-11-02 in the review of #835 (the delivery model of the internal-developer-platform profile), split as #1004 from #848 on 2026-11-05.*
