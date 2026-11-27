# 0012. Every error message says what happened and how to fix it

!!! note "In short"
    Every error message, from the CLI or a Nereid, follows eight rules: what happened, the cause, how to check, how to fix, what changed, no traceback, and a fitness function. Status: Proposed (2026-10-19).

**Status:** Proposed (2026-10-19)

## Context

Reviewing #321 (install stops at once when the Controller refuses the cloud Instance) and #327 (the issuer refusal names the undercloud and Kubernetes' default issuer, not k3s), the owner decided on 2026-10-19: "error messages must always be meaningful and, whenever possible, suggest what must be done to fix them".

The rule exists only in pieces today. `platform init` names the setting to fix and says `Nothing was changed.`; spec 0005 asks the plans of a cloud Implementation to be written "in plain words". Nothing asks it of every message, and the cases that triggered the decision show the gap:

- The refusal of the cloud Instance reads "the cluster presents k3s's default issuer ...": it is generic (which cluster?), it names the Kubernetes distribution instead of the object the person knows, and it gives no cause and no way out.
- `make docs` dies with a 40-line traceback when its port is taken (#330): an expected error, shown as if it were a bug.

## Decision

Every error message, from the CLI or from a Nereid, follows eight rules:

1. **What happened**, in the person's words, naming the object: `the undercloud of installation tailwind`, never `the cluster`, never the Kubernetes distribution (such as k3s).
2. **The probable cause**, when it is known.
3. **How to check**: a command the person runs, when there is one.
4. **How to fix**: a command ready to copy, or who has to act (`an admin of the subscription runs ...`).
5. **What changed**: the message says whether anything changed (`Nothing was changed.`).
6. **Never a traceback for an expected error.** Tracebacks are for bugs, and show with `--debug`.
7. **Nereids too.** A refusal in `status` carries the fields `message`, `cause`, `check` and `fix`. The CLI only shows them, cleaned, since what a Nereid publishes is untrusted input, and never names the Nereid (ADR 0002). One line per field, each with its own length limit.
8. **A fitness function guards it.** The CLI's error type requires `fix=`, and each error path has a test that checks its fix line.

The format, on the refusal of #327:

```text
✗ plan     the Controller refused the Instance: IssuerNotPublic
  what     the undercloud of installation tailwind presents Kubernetes' default issuer,
           https://kubernetes.default.svc.cluster.local, which Azure cannot reach
  cause    probably created by nereus init without --target azure (k3d is the default)
  check    kubectl get --raw /.well-known/openid-configuration
  fix      nereus init --target azure --installation-name tailwind
  Nothing was changed.
```

## Prior art

These rules are not new; they gather what these communities already teach:

- **Jakob Nielsen's usability heuristic #9, "Help users recognize, diagnose, and recover from errors" (1994)** ([Nielsen Norman Group](https://www.nngroup.com/articles/ten-usability-heuristics/)): an error in plain language that says what went wrong, why, and suggests the fix (rules 1 to 4).
- **Command Line Interface Guidelines, "Errors"** ([clig.dev](https://clig.dev/#errors)): catch expected errors and rewrite them for humans, keep tracebacks out of them, and suggest the next command (rules 4 and 6).
- **Elm, "Compiler Errors for Humans" (Evan Czaplicki, 2015)** ([elm-lang.org](https://elm-lang.org/news/compiler-errors-for-humans)): errors that teach and point to the fix, shown in the person's terms rather than the tool's (rules 1 and 4).
- **Kubernetes API conventions on conditions, and kstatus's `Stalled`** ([API conventions, "Typical status properties"](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md#typical-status-properties); [kstatus](https://github.com/kubernetes-sigs/cli-utils/blob/master/pkg/kstatus/README.md)): a condition carries a machine-readable `reason` and a human `message`, and `Stalled` says a Controller cannot progress without help; the Controller side of rule 7 builds on both.

Learn more: the four links above, in that order, go from the principle to the CLI and then to the Controller.

## Consequences

- A person reading an error knows what failed, why, how to confirm it and what to run next, without reading the code or asking.
- Existing messages are brought in line as they are touched, not in one sweep.
- Every new error path costs a fix line and its test; an error with no known fix says who has to act instead.
- A Controller's refusal becomes structured data in `status`, with limits the CLI enforces.
- Follow-ups: #327 applies these rules to the issuer refusal and adds the refusal fields to spec 0005's `Stalled` condition; #330 makes `make docs` say its port is taken, and how to pick another, without a traceback.

*Aligned in wording 2026-10-25 from voice session (Reef, Nereid, Mandate, `nereus`); raw data in Drive #pontos/raw/2026-10-25.*
