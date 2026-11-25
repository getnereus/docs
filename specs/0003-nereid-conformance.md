# 0003. Nereid conformance

**Status:** Proposed (2026-10-17)

## Intent

A Nereid is an image, and the image carries its own contract: the reef it implements, the reefs it requires (#84), its version and the commands it publishes (ADR 0004). `nereus nereid apply keycloak` then needs only a name (ADR 0011). This spec decides what the image declares, how the platform reads it, and how it checks that a Nereid honours what it declares, in three layers: at install (layer 1, the MVP), at start (layer 2) and before the Nereid registry lists it (layer 3, #22).

The platform checks rather than trusts: images outside the Nereid registry may run, but only conformant ones become Ready and get their commands routed.

## Precedents

- **Crossplane packages.** A `crossplane.yaml` inside the package image declares metadata and `dependsOn` (other packages, with version constraints), and the package manager resolves them. Taken: the image is the unit of distribution and carries its own metadata. Not taken: the file sits in a layer, so it must be pulled to be read, and `dependsOn` names packages, not APIs.
- **OLM ClusterServiceVersion.** An operator declares the CRDs it `owns` and the ones it `requires`; OLM installs it only when every required API is provided, whoever provides it. Taken: dependencies name the API (the reef), never the operator (the Nereid), as #84 asks and ADR 0002 requires.
- **OCI image labels and annotations.** The image spec predefines `org.opencontainers.image.*` keys (`version`, `source`, `title`, `licenses`, ...) and lets anyone add namespaced keys. Labels written by a Dockerfile `LABEL` live in the image config blob, a small JSON document readable from a registry without pulling any layer. Taken: the standard keys where one exists, and the platform's own keys only for what the standard lacks.
- **Kubernetes and Gateway API conformance.** Sonobuoy runs the Kubernetes conformance suite against a cluster; Gateway API ships a suite per feature profile, and each implementation publishes a versioned `ConformanceReport`. Taken for layer 3: a suite per reef, a report per image, the Nereid registry listing only images with a passing report.
- **`terraform-packager`.** A Stack image answers `info` through its entrypoint. Taken for layer 2: the running image answers a cheap call describing itself. The reference Nereid already answers `GET /` with its name and commands.

## The image's metadata

Labels in the image config (`LABEL` in the Dockerfile). The platform's keys use `<API_GROUP>/` as prefix (`core.getnereus.dev`, the core reef's group, ADR 0009; `cli/src/nereus/names.py`), the same key as the Kubernetes labels of the Mandate (ADR 0011), as #99 fixed. OCI recommends reverse-domain keys; the Kubernetes form is kept on purpose, so one key reads the same on the image, the Mandate, the Deployment and the pods.

| Key | Required | Value | Example |
|---|---|---|---|
| `<API_GROUP>/reef` | yes | the reefs it implements, comma-separated | `release`, or `sast,dependency-scan` |
| `<API_GROUP>/requires` | no | the reefs it requires, comma-separated; absent means none | `auth,secrets` |
| `<API_GROUP>/nereid` | yes | the Nereid's name, the default for `nereid apply`'s name | `keycloak` |
| `<API_GROUP>/reference` | no | `true` for a reference Nereid, a test stand-in never next to another kind of Nereid in its reef (#552, #1423) | `true` |
| `org.opencontainers.image.version` | yes | the Nereid's version, shown in `nereus status` | `0.1.0` |
| `org.opencontainers.image.title` | no | the repository's name | `auth-keycloak-controller` |
| `org.opencontainers.image.source` | no | where its code lives | `https://github.com/example/auth-keycloak-controller` |

```dockerfile
LABEL core.getnereus.dev/reef=release \
      core.getnereus.dev/nereid=reference-release \
      core.getnereus.dev/reference=true \
      org.opencontainers.image.version=0.1.0 \
      org.opencontainers.image.title=reference-release-controller
```

- **Several reefs (#72)** share one key, comma-separated (decided by the owner, rather than one key per reef: a Kubernetes label on a Mandate carries one value anyway, and the CLI splits it once). `--reef <reef>` picks one; it must be one of the listed names. An image installed twice, once per reef, is two Nereids (two Mandates, ADR 0011).
- **Required reefs name reefs, never Nereids** (#84, ADR 0002). Contract versions (`auth@v1alpha1`) wait for #18 to version contracts.
- **The commands description stays out of the labels.** It can be long, it changes with the code, and labels would duplicate it. It stays a file in the image (`commands.yaml` today), published by the running Nereid in its `status` (ADR 0004) and returned by the contract call of layer 2.
- **Labels are identical across the platforms of a multi-arch image**, a Good Citizen rule: the platform reads one of them.

## Layer 1: at install, from the labels (MVP)

`nereus nereid apply [<name>] --image <ref> [--reef <reef>]` reads the labels before anything runs in the cluster; the name defaults to the `nereid` label, an explicit one wins, and neither is refused:

1. **From the registry, before any pull or run** (decided by the owner on #85 and #45; #99 implements it). Through the OCI Distribution API: `GET /v2/<name>/manifests/<ref>`; when it returns an index, the manifest of the cluster nodes' platform (`linux/amd64` or `linux/arm64`); then `GET /v2/<name>/blobs/<config digest>`, whose `.config.Labels` holds the labels. Two or three small requests, no layer downloaded, and never `docker image inspect`: the same code serves the CLI, the Platform API and a future operator, none of which can assume a local Docker daemon. The client is a small one of our own, behind one function (decided by the owner): standard library only (token dance, manifest, config blob), no `oras-py`, `crane` or `skopeo`, so the CLI gains no binary dependency and the Platform API can reuse it. Anonymous bearer tokens cover public registries (the Nereid registry is public); private registries and credentials are #87.
2. **Local runs use a registry too.** On k3d the image is pushed to a k3d local registry (`k3d registry create`) instead of `k3d image import`, so a local run reads its labels the same way.
3. **Resolve the reef.** From `--reef` when given, else from the label. Refuse when the label lists several and no `--reef` is given, when `--reef` names one the label does not list, or when there is neither (decided by the owner on #45: no command group named after the Nereid any more).
4. **Check the reef exists** (`nereus reef apply`, #99).
5. **Check every required reef** has an installed Nereid (an active one once #72 brings `spec.active`). Refuse naming each missing one and the command that fixes it. When the required reef has Nereids but none is `Ready` (its Nereid is not healthy), go ahead and warn that the required reef has a problem (decided by the owner on #85).
6. **Record** `spec.image` by digest (ADR 0003): `<repository>@sha256:...`, the digest of the manifest (or index) the labels were read from, so a tag pushed again later never changes what runs (#126); a reference given by digest is kept as is and checked, `spec.reefs`, `spec.requires`, `spec.version` and `spec.controller` (from `org.opencontainers.image.title`), written by the CLI (ADR 0005). `spec.requires` keeps in the cluster, not in local files, what answers "who requires this reef". A Nereid of the local Nereids applied by its name alone records the CLI's version as `spec.version`, as thetis does, not its image's label: `make release` reuses an image whose inputs did not change (#1574), and its label keeps the version it was built at (#2000).
7. **At `nereid delete`,** refuse the last Nereid of a reef that installed Nereids require (read from their `spec.requires`), naming them; `--force` goes ahead (decided by the owner on #85).

The messages:

```text
$ nereus nereid apply my-tool \
  --image example/my-tool:0.1.0
error: example/my-tool:0.1.0 declares no reef (label core.getnereus.dev/reef).
       Add the label to the image, or pass --reef <reef>.

$ nereus nereid apply snyk \
  --image example/snyk-controller:0.1.0
error: example/snyk-controller:0.1.0 implements several reefs: sast, dependency-scan.
       Choose one with --reef sast or --reef dependency-scan.

$ nereus nereid apply snyk \
  --reef iac-scan \
  --image example/snyk-controller:0.1.0
error: example/snyk-controller:0.1.0 does not implement iac-scan; it implements sast, dependency-scan.

$ nereus nereid apply reference-release \
  --reef release \
  --image example/reference-release-controller:0.1.0
error: reference-release implements release, and reef release does not exist.
       Add it first: nereus reef apply release --from-file ./reefs/release/

$ nereus nereid apply inception \
  --image example/inception-controller:0.1.0
error: inception requires reefs with no Nereid installed: auth, exposure.
       Install a Nereid of each first: nereus nereid apply <name> --reef <reef> --image <image>

$ nereus nereid apply inception \
  --image example/inception-controller:0.1.0
warning: inception requires reef auth, which has a problem: keycloak is CrashLoopBackOff.
         See 'nereus nereid list'.

$ nereus nereid delete keycloak
error: keycloak is the last Nereid of reef auth, which installed Nereids require: inception.
       Uninstall them first, or go ahead with: nereus nereid delete keycloak --force

$ nereus nereid apply \
  --image example/my-tool:0.1.0
error: example/my-tool:0.1.0 declares no Nereid name (label core.getnereus.dev/nereid).
       Add the label to the image, or pass the name: nereus nereid apply <name> --reef <reef> --image example/my-tool:0.1.0

$ nereus nereid apply reference-release \
  --reef release \
  --image registry.example.com/reference-release-controller:0.1.0
error: could not read the labels of registry.example.com/reference-release-controller:0.1.0: 401 Unauthorized.
       Private registries are not supported yet (#87): push the image to a public or local registry.
```

## Layer 2: at start, Ready means it honours the contract

**A Nereid is Ready when its readiness and liveness probes pass and its contract call succeeds.** Until then it never becomes the active Nereid of its reef and the CLI routes none of its commands; it keeps running, so its logs explain why.

**The contract call** is `GET /contract` on the Nereid's Service port, reached like every command (the Service proxy today, the Platform API later). It is cheap and side-effect free, so it runs at start and again on every probe period:

```json
{
  "contract": "v1alpha1",
  "implementation": "keycloak",
  "version": "0.1.0",
  "implements": ["auth"],
  "requires": ["secrets"],
  "commands": [{"path": ["user", "list"], "help": "List the users."}]
}
```

The check passes when the answer parses, `implements` contains `spec.reefs`, `implements`, `requires`, `implementation` and `version` match the labels recorded at install, and `commands` is valid against the command schema of ADR 0004. Each failure is a reason: `contract call failed: no 'implements'`, `contract call timed out`, `requires differs from the image label: secrets`.

**`status`, one writer per field (ADR 0005).** The Nereid reports; a checker that is not the Nereid judges:

| Field | Writer | Meaning |
|---|---|---|
| `spec.image`, `spec.reefs`, `spec.params`, `spec.requires`, `spec.version` | the CLI (the API later) | what was asked, and the labels read at install |
| `status.commands` | the Nereid | its commands (ADR 0004), as today |
| `status.conditions[type=Serving]` | the Nereid | it started and serves its endpoint |
| `status.state` | the checker | `Pending`, `Ready` or `NotConformant` |
| `status.reason` | the checker | why, when not `Ready` |
| `status.source` | the checker | `registry` when the digest has a passing report in the Nereid registry (layer 3), else `local` |
| `status.checkedAt`, `status.digest` | the checker | when it last checked, and the digest it checked |

The checker reads the Deployment's availability (the kubelet runs the probes) and makes the contract call. The CLI routes a command only when `status.state` is `Ready`.

### What every Nereid answers

Honouring the contract means more than answering the contract call: a Nereid answers every object of every kind its reef exposes, the same way in every reef (owner, 2026-10-29, #524, #525).

1. **Every verb of every kind.** A Nereid serves `create`, `apply`, `get`, `list` and `delete` (ADR 0013, the command conventions) of every CRD labelled `core.getnereus.dev/reef: <reef>`, even when it does nothing with some of them. A reef that exposes no CRD has no `Ready` Nereid.
2. **The status follows the kind's schema.** What a Nereid writes in `status` follows that kind's CRD: the fields it declares, with the types and values it allows. A `Target` gets `status.ready` even when the Nereid creates no namespace. A reason the contract does not declare is not allowed; when "does not apply" is needed, the contract declares it, for every Nereid of the reef.
3. **The common contract.** Every kind of every reef shares the fields of `cli/src/nereus/interfaces/common.yaml`, which the CLI merges into the `status` of every CRD it applies (a reef's own declarations kept):
   - **The `Ready` condition** in `status.conditions` (`type`, `status`, `reason`, `message`, `lastTransitionTime`), its `lastTransitionTime` moved only when its `status` changes, as the Kubernetes API conventions define it, never when only another field does (#2242: `nereid.operations.ready` keeps it, and `make nereid-check` holds every Nereid to it); with the common reasons `NotApplicable` (the Nereid does nothing with this kind) and `CleanupFailed` (a delete could not remove what was made). A reef declares its own reasons in the annotation `core.getnereus.dev/reasons` of each CRD, comma-separated; the common ones are implied.
   - **`status.observedGeneration`:** the `metadata.generation` the status answers.
   - **`status.steps`**, for a kind whose work has several steps: each with a `name`, a `state` (`Done`, `InProgress`, `Pending` or `Failed`), `startedAt` only once it started, `finishedAt` only once it ended, and a `message`. With one step only, or `NotApplicable`, `steps` may be empty and the `Ready` condition is enough.
   - **One Kubernetes Event per change of a step**, on the object: its reason is the step's state and its message the step's message. That is the history `kubectl describe` shows, kept when the Nereid restarts.
4. **The finalizer `<reef>.getnereus.dev/cleanup`.** The Nereid adds it to every object of every kind of its reef it answers, and removes it only once everything it made for the object is gone; with nothing made (`NotApplicable`), at once. On a failure the object keeps the finalizer, with `Ready=False`, `reason: CleanupFailed` and a message naming what is left: a finalizer is never removed while something it guards still exists. Meanwhile the object shows `Terminating`, kubectl's word for an object with `metadata.deletionTimestamp` set and finalizers left. The finalizer is the one field outside `status` a Nereid writes (ADR 0005 keeps `spec` the CLI's): its Role allows `patch` on its reef's kinds for it, which RBAC cannot narrow to `metadata.finalizers`, so the CLI applies with the Nereid's RBAC a `ValidatingAdmissionPolicy` and its binding (`controller-<nereid>-finalizer-only`), matched on the Nereid's service account and on updates of its reef's kinds (never their `status`). The policy is an allowlist (#552): every root key but `metadata` and `status`, and every `metadata` key but `finalizers` and the ones the API server writes (`resourceVersion`, `generation`, `managedFields`), keeps its old value, present or absent, and no finalizer is added or removed but `<reef>.getnereus.dev/cleanup`. It fails closed: the CLI creates the policy and its binding before the `ClusterRole` that grants `patch`, and on a cluster that does not serve `admissionregistration.k8s.io/v1` `ValidatingAdmissionPolicy` (Kubernetes older than 1.30) it installs nothing and says which version is needed.
5. **A reference Nereid never shares its reef with another kind of Nereid (#552, per reef since #1423).** The reference Nereids (`controllers/reference`: `reference-release` for the release reef, `reference-secrets` for the secrets reef) are test stand-ins: each answers every object of its reef and keeps the reef's one finalizer whatever the Mandate. Their image declares `<API_GROUP>/reference=true`, which `nereid apply` records as the same label on the Nereid. Installing a reference Nereid while one of its reefs has a Nereid without the label is refused, and so is installing a Nereid without the label in a reef a reference one serves; Nereids of other reefs, of either kind, run next to each other, as the catalog Nereid next to the reference ones in `make scene-core` (owner, 2026-11-13); the error names the Nereids in the way and the fix, delete them first. Several reference Nereids run together: the release reef's asks the secrets reef's for its bindings (#533). The other Nereids are multi-Nereid by design: each object goes to the Nereid of its Mandate (`spec.mandate`, else the reef's default Mandate), so two real Nereids never answer the same object, and the finalizer keeps its one name per reef.
6. **A Nereid never acts on a held object (ADR 0031, #2214).** An object the Nereus API wrote under a gate carries the hold, the annotation `authorization.<domain>/approval` naming its Approval, until the API lifts it. Meanwhile only the gate Nereid writes its `status` (`Ready=False`, reason `WaitingApproval`, or `ApprovalMissing` when the Approval is gone); every other Nereid leaves it alone: no `status` and no finalizer. A Nereid lists its objects through `nereid.held.actionable` (nereid-sdk); `make nereid-check` fails on a Nereid of `controllers/` or `templates/nereid` that does not import `nereid.held`, but those of `scripts/nereid/held-allowlist`, a list that only shrinks. #2120's admission policy refuses a write of another Nereid on a held object, so the outcome alone would hide a Nereid that tries: step 0 of the conformance check below proves it, by the object and by the Nereid's log.

```text
$ nereus nereid apply flux --reef release
✗ nereid flux was not installed: its reef has the reference Nereid reference-release, a test stand-in. A reference Nereid never shares its reef with another kind of Nereid (spec 0003).
  Why: it answers every object of its reef and keeps the reef's one finalizer, such as release.getnereus.dev/cleanup, whatever the Mandate, so another Nereid could lose its cleanup to it.
  Check: nereus nereid list
  Fix: delete them first, then apply flux again:
    nereus nereid delete reference-release
    nereus nereid delete reference-secrets
Nothing was installed.
```

**Messages: clarity over brevity.** A message is a full sentence that says what was done, is being done or is left, or why the kind does not apply to this Nereid; never a terse word such as `NoOp`. It is a guideline, not a length a check enforces.

A kind the Nereid does nothing with:

```yaml
conditions:
  - type: Ready
    status: "True"
    reason: NotApplicable
    message: "The openbao Nereid keeps no state for a Target: OpenBao has no namespaces, so nothing is created."
```

A kind whose delete has several steps, half done:

```yaml
steps:
  - name: node-pool
    state: Done
    startedAt: "2026-10-29T21:02:11Z"
    finishedAt: "2026-10-29T21:04:40Z"
    message: "Deleted the node pool demo-pool (3 nodes)."
  - name: aks-cluster
    state: InProgress
    startedAt: "2026-10-29T21:04:41Z"
    message: "Deleting the AKS cluster demo-aks in eastus; Azure reports Deleting."
  - name: resource-group
    state: Pending
    message: "Delete the resource group rg-demo once the cluster is gone."
```

**Implemented (#525): the common contract.** `interfaces/common.yaml` and its merge in `cli/src/nereus/contracts.py`; the release reef's four kinds take it and declare their reasons. Its two Nereids, `flux` and `reference`, keep the finalizer `release.getnereus.dev/cleanup` and write `observedGeneration`: a Release keeps it until its Flux `HelmRelease` is gone, a Repository until its `HelmRepository` is gone, a Source and a Target lose it at once. What the CLI shows while an object is `Terminating` is #526; `NotConformant` for a Nereid that does not answer its reef's kinds is #527; the check, kind by kind, is #528.

**Implemented (#527): `NotConformant` from the reef's kinds.** A Nereid declares the kinds it serves in `status.kinds`, a list of `<plural>.<group>` (for example `targets.release.getnereus.dev`), which it writes (ADR 0005); when the contract call exists, it carries the same list. Until the checker exists, the CLI computes the state, writing no `status` field (`cluster.assess`): a Nereid whose `Ready` condition is `True` is `Unavailable` when its Controller has no pod serving (that wins: with no pod, nothing serves), else `NotConformant` when one of its reefs exposes no kind (no CRD labelled `core.getnereus.dev/reef: <reef>` in the reef's own group) and has none by design (`authentication`, `portal` and `metrics`, #794), or exposes a kind missing from its `status.kinds`, else `Ready`; a Nereid whose condition is not `True` keeps its own reason. The reef's kinds come from one list of the labelled CRDs per command, never one call per row. The reason is a full sentence naming the reef, the kind and the fix: `nereus nereid get` prints it on a `Reason` line, and `nereus status --output json|yaml` as the `reason` field of each row (`null` when there is none). The CLI sends no command to a `NotConformant` Nereid, naming the reason, as it sends none to an `Unavailable` one. `core` is built into the CLI and stays `Ready`. `flux` and `reference` declare the release reef's four kinds; `openbao` and `keycloak` declare none, and are `NotConformant` until their reefs get kinds (#529, #535). `nereus init` waits on the Nereid's own `Ready` condition, so it works while `openbao` is `NotConformant`.

```text
$ nereus nereid get my-auth
...
Status:       NotConformant
Reason:       The auth reef exposes no kind, so my-auth serves no verb: a reef needs at least one CRD labelled core.getnereus.dev/reef=auth.
```

### The conformance check, kind by kind (#528)

The rules above are checked, not trusted: `test/conformance <reef> --nereid <nereid>` drives `nereus` and `kubectl` on a throwaway k3d cluster where the Nereid is installed, `Ready` and named by the reef's default Mandate, and proves every verb of every kind the reef exposes. The reference Nereid passes first; `make scene-release` runs it against the reference Nereid (`reference-release`), then against `flux`.

**A sample per kind**, in the contract the CLI pins: `cli/src/nereus/interfaces/<reef>/samples/<kind>.yaml`, the objects the kind needs first (a `Release`'s `Repository`, `Source` and `Target`), then the kind's object as created, then the same object with a change to its spec, the one `apply` makes. A kind whose CRD keeps every spec field as created (a rule `self == oldSelf` of the field's own, or a rule of `spec` comparing `self.<field>` with `oldSelf.<field>`: the edge reef's `Route` and `Zone`) has no change to make, so its sample holds the object once and step 4 is skipped, said in a line (#2006); a sample holding it once for a kind whose spec can change is refused. `REEF_GROUP` stands for the reef's group, as in the CRDs. The release reef's samples name a chart of `example.com`: the check proves the status a Nereid writes, not that a chart installs, so `flux` answers them as a repository it could not read and a release that failed or is still trying, with reasons the contract declares, and installs nothing.

**For each CRD labelled `core.getnereus.dev/reef: <reef>`** in the reef's own group:

0. **Held:** the sample's needs and the kind's object, the object carrying the hold that names an Approval of the authorization reef, both written as the Nereus API writes them (`kubectl --as system:serviceaccount:<namespace>:nereus-api`). Once the gate Nereid answered it (`Ready` reason `WaitingApproval`) and two passes of the Nereid went by (twice its `RECONCILE_SECONDS`, 5 by default, after that), `python -m nereus.conformance held` finds its `Ready` absent or the gate's and no finalizer `<reef>.getnereus.dev/cleanup`, a line naming the kind; and the Nereid's log since step 0 began holds no refusal of #2120's policy on it (`<plural>/<name> waits for authorization/approvals/<approval>`) and no forbidden write on its path. The API then lifts the hold, the Approval is deleted, the Nereid takes the object (its finalizer), and the object is deleted, so step 1 creates it again.
1. **`create`:** `nereus <reef> apply --from-file` with the sample; `--dry-run` first changes nothing, then the line names the object by its full path (`release/releases/conformance created`).
2. **The status** answers the object's generation (`status.observedGeneration` reaches `metadata.generation`) and follows the CRD read from the cluster, the common fields merged in: every field present is declared, with its type, its enum and its limits; the `Ready` condition is there, its `reason` one the contract declares (the common ones or the CRD's `core.getnereus.dev/reasons`), its `message` not empty; each step has a message, `startedAt` only once it started and `finishedAt` only once it ended. A message's clarity is a guideline, not checked.
3. **The finalizer** `<reef>.getnereus.dev/cleanup` is on the object.
4. **`apply`** of the changed sample says `configured`, raises `metadata.generation`, and the status answers the new one, checked as in 2; skipped for a kind whose spec cannot change.
5. **`get` and `list`** show the object.
6. **`delete`:** `--dry-run` changes nothing; then, the check holding a finalizer of its own so the state is seen whatever the Nereid's pace, `delete --wait=false` says `Terminating` and `list` shows it; the Nereid removes its finalizer once what it made is gone; the check releases its own and the object is gone. The objects it needed are then deleted, each `delete` waiting for its Nereid (#526).

The status is checked by `python -m nereus.conformance status` (`cli/src/nereus/conformance.py`) with the small subset of OpenAPI v3 the contracts use (`type`, `enum`, `properties`, `required`, `items`, `maxItems`, `maxLength`, `pattern`, `format: date-time`, `x-kubernetes-preserve-unknown-fields`), not `jsonschema`: no new dependency, and a contract using another keyword fails the check, naming it, rather than passing unchecked. Each failure names the kind, the object and the field:

```text
FAIL: Target nereus-system/conformance: status.conditions[type=Ready].reason: 'NoOp' is not a reason the contract declares (NotApplicable, CleanupFailed, Reference, InCluster)
FAIL: Target nereus-system/conformance: status.observedGeneration: missing; the Nereid writes the metadata.generation its status answers
FAIL: Target nereus-system/conformance: status.steps[name=quota].finishedAt: set on a Pending step, which has not ended
```

The check refuses any kube context but a k3d one, and `k3d-nereus`, the kept cluster (`docs/agent/rules.md`): it creates and deletes objects. A Nereid that writes no `status.steps` (`flux` today, #567) passes; steps are checked only when present.

```text
$ test/conformance release --nereid reference-release
...
== Release (releases.release.getnereus.dev)
✓ Release nereus-system/conformance: held, its Nereid left it alone (Ready WaitingApproval from the gate, no finalizer release.getnereus.dev/cleanup)
✓ Release nereus-system/conformance: status conforms (generation 1, Ready True, Reference)
✓ Release nereus-system/conformance: status conforms (generation 2, Ready True, Reference)
✓ Release: create, apply, get, list and delete, the status as the contract says
...
✓ reference-release serves every verb of every kind of the release reef and honours its contract: Release Repository Source Target
```

## Layer 3: a conformance suite per reef, gating the Nereid registry (outline)

Layer 3 grows from the check of layer 2: the same steps, the samples the contract ships, and the same validator, run by the CLI against an image rather than by a script against the Nereid installed. #109 builds it.

- **One suite per reef**, versioned with its contract (#18): it installs the image on a throwaway k3d cluster, creates the reef's Instances from the samples of its contract (`interfaces/<reef>/samples/`), runs the check of layer 2 kind by kind, and adds the commands it must publish and the Good Citizen rules below.
- **A report per image digest**, after Gateway API's `ConformanceReport`: Nereid, version, digest, contract version, suite version, the result of each test. Signed later (Sigstore attestations, #22).
- **The Nereid registry (#22) lists only digests with a passing report**, and that is what makes `status.source` read `registry`.
- **Anyone can run the suite locally** (`nereus nereid conformance <reef> --image <ref>`, a provisional shape, replacing `test/conformance`), so the docs and courses (#33) teach building a Nereid that passes before submitting it.

## Good Citizen rules (candidates)

The rules every Nereid follows to run on the platform, checked by the platform rather than trusted. Layer 1 checks the first three, layer 2 the next four, layer 3 all of them.

1. Carries the labels above, well-formed, identical across platforms.
2. Requires reefs, never Nereids.
3. Is installed by digest.
4. Serves readiness and liveness probes.
5. Answers the contract call within two seconds, matching its labels.
6. Writes only its own `status` fields, never `spec` (ADR 0005); checked from the object's `managedFields`.
7. Publishes a command description valid against the schema, every command and argument with help and every command with examples that call it (#676, #132); its output is text (ADR 0004).
8. Runs as non-root, with no privilege escalation (the reference image runs as `65532`).
9. Touches only its own reef's objects; its RBAC is scoped to them.
10. Declares resource requests and limits.
11. Shuts down cleanly on `SIGTERM`.
12. Later: exposes metrics and writes structured logs to stdout (#68).

## `nereus nereid list`

One row per Nereid, with the reason of a `NotConformant` one.

*Illustrative output: the values are examples, replaced by real output when the code prints this table.*

```text
$ nereus nereid list
NEREID             REEFS    IMAGE                                              STATUS         AGE
keycloak           auth     example/auth-keycloak-controller:0.1.0             Ready          3d
auth0              auth     example/auth-auth0-controller:0.1.0                Ready          3d
my-auth            auth     example/my-auth-controller:dev                     NotConformant  2h
                   (contract call failed: no 'implements')
reference-release  release  localhost:5111/reference-release-controller:0.1.0  Pending        5s
```

## `nereus nereid get`

One Nereid in full: its reefs, image and digest, parameters and status, and the image's OCI labels `org.opencontainers.image.title` and `org.opencontainers.image.description`, which `nereid list` leaves out. The title still matters: it names the controller a person sees.

## What the MVP implements

- **Layer 1, all of it:** the labels above on the reference image; reading them from a registry (#99 brings the read of the reef label and the k3d local registry; this spec adds `requires`, `nereid` and the version); resolving the reef; refusing a missing reef or a missing required reef, with the messages above.
- **The list's `STATUS`** from what exists: the Nereid's `Ready` condition as today, computed by the CLI with no new `status` field.
- **Not in the MVP:** the contract call and the checker (layer 2), the suite and the Nereid registry gate (layer 3). The check of a reef's kinds (layer 2, #528) runs from `test/conformance`, in `make scene-release`.

**Implemented (#99, #85, #107): layer 1, all of it.** The name, the reef, `requires`, the version and the title read from the registry; the name argument optional, defaulting to the `nereid` label (an explicit name wins; neither is refused); a missing reef or required reef refused, a required reef with no `Ready` Nereid warned about; `spec.requires`, `spec.version` and `spec.controller` (the title) recorded; the uninstall of the last Nereid of a required reef refused unless `--force`; `nereid list` with the columns above.

**Hostile labels (#134).** Labels are untrusted input: before any is used or shown, `nereid apply` refuses a label it reads that holds a control character or is longer than 128 characters (a Docker tag's limit), naming the label, and writes nothing to the cluster. The scene checks it with a hostile reference image.

**Implemented (#133): the first check of layer 2.** The CLI reads the availability of each Nereid's Deployment: a Nereid with no pod serving shows `Unavailable` in `STATUS` (computed by the CLI, no `status` field written), and its commands are refused with a message and a non-zero exit code instead of reaching a proxy with nowhere to go. The scene kills the pod of a Nereid and scales its Deployment to zero, and checks the message, the exit code and that the commands work again once the pod is back.

## Decisions on the open questions

- **What "has a Nereid" means for a required reef before #72** (decided by the owner on #85): one installed. With none, `nereid apply` is refused; with one that is not `Ready`, `nereid apply` goes ahead and warns that the required reef has a problem. With #72, the active one.
- **Uninstalling the last Nereid of a required reef** (decided by the owner on #85): refused, naming the installed Nereids that require it; `--force` goes ahead.
- **Versions in `requires`** (decided by the owner on #85): names only until #18 versions the contracts, then `auth@v1alpha1`, checked against the contract version the reef serves.

## Open questions

1. **Who runs the checker of layer 2 before the Platform API exists.** The CLI at `nereid apply` and at every `nereid list`, or a system controller that `init` would install (against ADR 0003's "init installs nothing"). Recommendation: the CLI until the Platform API exists, then a controller inside the Platform API.
2. **Should the contract call move into the image as a command,** like `terraform-packager`'s `info`, so layer 1 can run it without a cluster? Recommendation: no for now; labels cover install, and the call is cheap once it runs.

## Learn more

- The precedents above, each with what is taken from it: [Crossplane packages](https://docs.crossplane.io/latest/packages/); [OLM's ClusterServiceVersion](https://olm.operatorframework.io/docs/concepts/crds/clusterserviceversion/); [OCI image annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md); [Sonobuoy](https://github.com/vmware-tanzu/sonobuoy) and [Gateway API conformance](https://gateway-api.sigs.k8s.io/docs/concepts/conformance/).
