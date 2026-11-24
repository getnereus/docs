# 0031. Gates and approvals native to Nereus: a hard gate refuses, a soft gate holds the object Pending until an approver decides

!!! note "In short"
    Any resource created through the Nereus API can be refused (a hard gate, 403 as today) or held: under a soft gate, a person with the right to ask creates the object, which stands visibly `Pending` until an approver approves or rejects it through the API. Two kinds in the `authorization` reef, `Gate` and `Approval`, one hold annotation, one admission policy, and no flow written per kind. Status: Accepted (2026-11-24).

**Status:** Accepted (2026-11-24, by the owner)

## Context

The platform's controls are all or nothing: the Nereus API asks the `authorization` reef before every write (ADR 0027, #1649), and the answer is yes, or a 403. Teams need a middle path, "you may ask, someone decides", and two issues asked for it from two sides: #2102 (hard and soft gates on creating a Room) and #2044 (change classes by blast radius).

If each reef wrote its own approval flow, every kind would grow a different one: its own pending state, its own notification, its own idea of who decides. The owner's requirement (2026-11-22) rules that out: "the Environment was only an example; it should hold for practically any resource created through Nereus, so we do not implement different, custom flows for each resource; this control becomes a native feature of Nereus."

Two more requirements come from the same decision:

- **The object exists while it waits.** The custom resource is created at once and stays `Pending`, "so whoever asked sees that it is pending, can follow it and tell the approvers"; no hold at the door that keeps the object out of the cluster.
- **The requester is told.** When a resource they asked for is approved or rejected, and then when it is provisioned or fails.

What makes it possible without touching each reef: every route of `api/server.py` already declares its `Asks` (reef, kinds, verb, the node it writes under) for the Authorizer of `api/authorization.py`, so the API knows, before any write, which reef, kind and verb a request is about.

## Decision

**Hard and soft, in the owner's sense of #2102.** A **hard gate** refuses: the person has no right to the verb, and the API answers 403, as spec 0011 does today. A **soft gate** lets a person ask: the person has the right to *request* the verb, the API writes the object held, and an approver decides.

**Three answers for one write.** When a write reaches the API, after the Authorizer:

```text
person ── nereus <reef> <kind> create ──▶ Nereus API (the route wrappers of api/server.py)
  ├─ may create?                                  yes ─▶ written as today
  ├─ may request, and a Gate matches reef/kind/verb?
  │    no ─▶ 403, as today (a hard gate)
  │    yes ─▶ the object is written WITH the hold, and an Approval beside it
  │         ├─ the gate Nereid writes the object's status: Pending, Ready=False WaitingApproval
  │         ├─ the messaging reef tells the approvers and the requester
  │         └─ approver ── nereus authorization approval approve|reject ──▶ the API records the decision
  │              ├─ approved: the API lifts the hold ─▶ the kind's own Nereid reconciles as usual
  │              │     └─ the gate Nereid follows Ready until it is provisioned or fails ─▶ notified
  │              └─ rejected: the gate Nereid marks the object Rejected; nothing is provisioned ─▶ notified
  └─ admission (one ValidatingAdmissionPolicy for every reef kind): only the API sets or lifts the hold and
     writes an Approval's spec; while the hold is on, only the gate Nereid writes the object's status or finalizers
```

A person who may `create` is not held: the bindings decide who goes straight through (`create`), who may ask (`request`) and who is refused (neither). A `request` with no `Gate` to match is refused, since nobody would decide it.

### The API group: two kinds in the `authorization` reef

Both live in `authorization.getnereus.dev/v1alpha1`, beside `Role` and `Binding` (ADR 0027), and, like them, are objects the Nereus API keeps.

**`Gate`: which requests wait, and for whom.** Owned by a node of the tenancy tree, as a Binding is, and holding for that node and the nodes under it.

```yaml
apiVersion: authorization.getnereus.dev/v1alpha1
kind: Gate
metadata:
  name: payments-environments
spec:
  owner: {kind: Project, name: payments}
  reef: environment
  kinds: [environments]
  verbs: [create]                       # create only, for now
  approvers:                            # the subjects a Binding takes (ADR 0027)
    - team/payments/tech-lead
  expires: 7d                           # optional; default from the authorization Mandate's approvalExpires
```

**`Approval`: one per held request.** Its `spec` is written only by the Nereus API, its `status` only by the gate Nereid (ADR 0005). It carries an `ownerReference` to the held object, so it goes away with it.

```yaml
apiVersion: authorization.getnereus.dev/v1alpha1
kind: Approval
metadata:
  name: staging-create-7f3a             # <target>-<verb>-<4 hex>
spec:
  gate: payments-environments
  target: {reef: environment, kind: environments, name: staging}
  verb: create
  requestedBy: <User id>                # never an e-mail
  decisions:                            # a list, so a quorum fits later
    - {by: <User id>, decision: approved, at: "2026-11-24T14:02:00Z", reason: "sprint demo"}
status:
  phase: Approved                       # Pending | Approved | Rejected | Expired
  conditions:
    - {type: Provisioned, status: "True", reason: Ready}   # the target's Ready, once approved
```

**The hold** is one annotation on the held object, `authorization.getnereus.dev/approval: <Approval name>`, set by the API when it writes the object and lifted only by the API when the Approval is approved. A rejected or expired object keeps it.

### Who writes what (ADR 0005, one writer per field)

| Field | Writer |
|---|---|
| the held object's `spec`, the hold annotation | the Nereus API |
| an `Approval`'s `spec`, its `decisions[]` included | the Nereus API |
| the held object's `status` and finalizers, while the hold is on | the gate Nereid |
| the held object's `status`, once the hold is lifted | the kind's own Nereid, as usual |
| an `Approval`'s `status` | the gate Nereid |

**The gate Nereid** is the Nereid of the `authorization` reef's default Mandate (the `openfga` Nereid in an install, the reference Nereid in `make scene-core`). While the hold is on it writes the held object's `status.phase: Pending` and the condition `Ready=False`, reason `WaitingApproval`, with a message that names the Approval and who may approve. After a rejection it writes `phase: Rejected`, `Ready=False`, reason `Rejected`; at expiry `phase: Expired`, reason `Expired`. Once the hold is lifted it stops writing the object and follows its `Ready` into the Approval's `Provisioned` condition, which the notifications read.

**A Nereid never acts on a held object.** The Nereid SDK skips any object that carries the hold, every Nereid adopts it, and a conformance test proves it (step 3 of #2117).

**While held, the object does not change.** The API refuses an `apply` on a held object (409, naming its Approval); a `delete` by the requester withdraws the request, and the Approval goes with the object.

**Rejection and expiry keep the history** in ADR 0026's shape: the phase stays until `delete`, and nothing is provisioned. An Approval expires at the Gate's `expires` (the authorization Mandate's parameter `approvalExpires`, `7d` by default).

### The seam in the API

The route wrappers of `api/server.py`, right after the Authorizer of `api/authorization.py`. Every route already declares its `Asks`; the wrapper finds the Gates that match the route's reef, kinds and verb at its node, asks `request` when `create` was refused, and writes the hold and the Approval. No reef's route changes, so a new kind gets approvals by configuration only: a `Gate` naming it.

### The verbs (an amendment to ADR 0013)

- **`request` is a right, not a command.** It appears in a Role's rules (`environment:environments:request`) and in `can-i` (`nereus authorization can-i request environment/environments`). A person who may `request` but not `create` runs the ordinary `create` and gets a held object.
- **`approve` and `reject` are commands of the `approval` kind:** `nereus authorization approval approve <name> --reason <text>` and `reject`, each recording one decision. The API asks `approve` on `authorization/approvals` at the Gate's node, and the answer holds for the Gate's approvers; the `openfga` Nereid's model answers it (step 7 of #2117).
- **`can-i` says when a person may ask:** `no, but may ask: authorization/gates/<name> holds create for <approvers>'s approval`, with exit code 1, since the answer to `create` is still no.

### The CLI

```text
$ nereus environment create staging --owner project/payments
✓ environment/environments/staging created, waiting for approval (authorization/approvals/staging-create-7f3a; approvers: team/payments/tech-lead)

Next steps:

  nereus environment get staging --watch

$ nereus environment get staging
NAME      PHASE     READY   REASON            AGE
staging   Pending   False   WaitingApproval   2m

$ nereus authorization approval list
NAME                  TARGET                             VERB     REQUESTED BY   PHASE     AGE
staging-create-7f3a   environment/environments/staging   create   bruno          Pending   2m

$ nereus authorization approval approve staging-create-7f3a --reason "sprint demo"
✓ authorization/approvals/staging-create-7f3a approved; environment/environments/staging released

$ nereus authorization approval reject staging-create-7f3a --reason "use the shared staging"
✓ authorization/approvals/staging-create-7f3a rejected; environment/environments/staging will not be provisioned

$ nereus authorization can-i create environment/environments --owner project/payments --user bruno
no, but may ask: authorization/gates/payments-environments holds create for team/payments/tech-lead's approval

$ nereus authorization gate create payments-environments \
    --reef environment \
    --kinds environments \
    --verbs create \
    --approvers team/payments/tech-lead \
    --owner project/payments
✓ authorization/gates/payments-environments created
```

### Admission

One ValidatingAdmissionPolicy for every reef kind (the groups `*.getnereus.dev`), built as the existing policies of `cli/src/nereus/cluster.py` are (step 2 of #2117): only the Nereus API's ServiceAccount sets, changes or removes the hold annotation and writes an Approval's `spec`; while the hold is on, only the gate Nereid's ServiceAccount writes the object's `status` or finalizers.

### Notifications

From the conditions, through the messaging reef (ADR 0019, #254): "waiting for approval" to the approvers and the requester when the Approval is written; "approved" or "rejected" on the decision; "provisioned" or "failed" from the Approval's `Provisioned` condition. The first channels are the portal's web push and `--watch` on the CLI; voice and phone come later, with #278.

## Prior art

- **Kubernetes Pod scheduling readiness** ([Pod Scheduling Readiness](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-scheduling-readiness/)): a Pod created with `schedulingGates` exists and is visible, but is not scheduled until every gate is removed; the hold annotation takes the same shape, an object that exists and waits, released by removing a mark.
- **Kubernetes certificate signing requests** ([Certificates and Certificate Signing Requests](https://kubernetes.io/docs/reference/access-authn-authz/certificate-signing-requests/)): a request object that an approver approves or denies with `kubectl certificate approve` and `kubectl certificate deny`, recorded as conditions; `Approval` and the `approve` and `reject` commands follow it.
- **GitHub deployment environments with required reviewers** ([Managing environments for deployment](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment)): a job that targets a protected environment waits until a required reviewer approves or rejects it, and the reviewers are people or teams; the `Gate`'s approvers take teams the same way.
- **Kubernetes ValidatingAdmissionPolicy** ([Validating Admission Policy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)): CEL rules evaluated in the API server; one policy guards the hold for every reef kind.
- **Kaspar von Grünberg and Luca Galante, *Thinking in Platforms*** (2026, `docs/thinking-in-platforms.md`): the owner's proposal that started this ADR, *Hard Gates, Soft Gates and protected approval in Nereus*, was written while reading it; the words hard and soft are used here in the owner's sense of #2102, and the book's own wording on gates is not yet in the notes.

## Consequences

- The `authorization` reef gains `Gate` and `Approval`, and its Nereid gains a second job: the gate Nereid, the first Nereid that writes the status of objects of other reefs, and only while they are held.
- ADR 0005 holds with one handover: while the hold is on, the gate Nereid is the one writer of the held object's `status`; the kind's own Nereid writes it from the moment the hold is lifted.
- ADR 0013 gains the right `request` and the commands `approve` and `reject` of the `approval` kind.
- Every Nereid moves to an SDK that skips held objects (step 3 of #2117); a Nereid outside the SDK that ignores the hold could still act outside the cluster before trying to write. The admission refuses any trace of it in the cluster, step 3's conformance test catches it before install, and #894 and #86 narrow it further.
- The API becomes the one writer of decisions, which raises the weight of #1500 (the API never writes the admission policies that guard it).
- A new kind gets approvals by a `Gate` alone; Room is the proof (#2102, step 10 of #2117).
- The steps of #2117 build it: the walking skeleton on an Environment (#2119), the admission policy (#2120), the SDK filter (#2121), rejection and expiry (#2122), notifications (#2123), `can-i` and `--dry-run` (#2124), the openfga rights (#2125), the portal and MCP (#2126), the metrics (#2127) and Room (#2102).

## Out of scope

A quorum of several approvers (later: `decisions[]` already fits it), change classes by blast radius or cost (#2044, a later extension of `Gate`), the policy reef with kyverno (#898), segregation of duties and an audit log nobody can rewrite (#241), cloud access approvals (#259), contextual conditions by IP or time of day, e-mail or chat pushes, gates on `apply` and `delete`.

## Origin

The owner's proposal of 2026-11-22 (*Hard Gates, Soft Gates and protected approval in Nereus*), analysed by a Fable agent and reshaped into journey #2117 the same day; the design was closed by the owner on 2026-11-22 its verbs approved on 2026-11-24, and this ADR accepted by the owner the same day (#2118, PR #2202). Raw data in `#pontos/raw/2026-11-22/` and `#pontos/raw/2026-11-24/`.

## Open questions

- **A requester who is also an approver:** may they approve their own request? Today nothing refuses it; segregation of duties belongs to #241.
- **A hold whose Approval is missing** (the API wrote the object and failed before the Approval): the gate Nereid's reason for it, and whether the API retries or removes the object; step 1 decides.
