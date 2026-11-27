# 0004. Init time SLO: a fitness function caps how long `nereus init` takes

**Status:** Proposed (2026-10-18)

## Intent

`nereus init` brings the platform up, and how long it takes is a quality the project measures and guards (#141): an SLO (service level objective) of 8 minutes on the local k3d undercloud, and 20 minutes on a cloud (Azure first) once the AKS overcloud (#92) and the pivot (#61) exist. A fitness function fails CI when `init` misses its time objective by more than a tolerance, naming the slowest steps; the progress of #88 colours the clock by the share of the time objective used, so a person sees the drift long before CI fails.

Every value is a setting with a default in code. The values a person changes live in one object of the platform's API group in the nereus namespace, so the pivot (#61) moves them to the overcloud with the rest of the platform's state, as Cluster API's `clusterctl move` moves objects, and nothing is reconfigured by hand.

**Provisional.** The word (SLO), the kind (`ServiceLevelObjective`), the `config` group and the shape of the object are chosen for the initial configuration and the tests of this slice. They are expected to change with use: when more objectives arrive (per-step objectives, the first login of `docs/inception.md`, the measurements of #102), a new spec revisits them.

## The scene that ends the slice

```bash
nereus init --yes                                   # the total ends with the SLO: "slo 8m, 3% green"
nereus config slo show
# SETTING    VALUE  SOURCE
# local      8m     default
# ...
nereus config slo set --local 4m --tolerance 5
nereus config slo show                              # local and tolerance now come from the cluster
nereus config slo reset                             # back to the defaults in code
nereus init --yes --check-slo                       # what test/scene and CI run: fails above the SLO + tolerance
```

## The object

One `ServiceLevelObjective` object (short name `slo`), named `default`, in the nereus namespace (`names.NAMESPACE`), of the platform's API group (`names.API_GROUP`, `v1alpha1`); its CRD is `cli/src/nereus/crds/servicelevelobjective.yaml`, applied by `init` with the other kinds.

| Field | Type | Default (constant in `cli/src/nereus/slo.py`) | Meaning |
|---|---|---|---|
| `spec.targets.local` | duration | `8m` (`LOCAL`) | The time objective of `init` on the local target (k3d), from the start of its steps to the end of the last one. |
| `spec.targets.cloud` | duration | `20m` (`CLOUD`) | The time objective on a cloud (Azure first), from `init`'s start until the overcloud is up and has taken over after the pivot. Keyed by the `cloud` Reef, never by a Nereid's name (#313). Recorded, not enforced, until #92 and #61. |
| `spec.bands.yellow` | percent | `50` (`YELLOW`) | From this share of the time objective, the clock is yellow. |
| `spec.bands.orange` | percent | `75` (`ORANGE`) | From this share, orange, and the slowest step so far is shown. |
| `spec.bands.red` | percent | `100` (`RED`) | Above this share, red: the objective is missed, and `init` still finishes. |
| `spec.tolerance` | percent | `20` (`TOLERANCE`) | The fitness function fails above the time objective plus this share of it (120% by default). |

- **A duration** is minutes and seconds, `5m`, `4m30s` or `90s` (pattern `^([0-9]+m)?([0-9]+s)?$`, validated with `re.fullmatch` by the CLI and by the CRD), never zero.
- **The bands** must rise: `yellow < orange <= red`. The CLI refuses a set that breaks the order.
- **Spec only.** The CLI writes `spec` (ADR 0005); there is no Nereid and no `status`. `init`'s timings are printed, not stored: a run's history is #102's.
- **Only the fields set are written.** A field the object leaves out falls back to its default in code, so a change of a default reaches every cluster that did not choose its own value.

## Precedence

Each value, on its own: **the object's field, else the default in code.** `nereus config slo show` prints each value with its source (`cluster` or `default`), as `init` prints its settings.

**The first `init`.** The cluster, and so the object, does not exist when `init` starts. `init` starts with the defaults, and reads the object in its `kinds and namespace` step, once the kinds are applied in the cluster it is preparing; from that step on, the bands and the check use what it read. On a cluster created by that same run, there is no object yet, so the defaults hold for the whole run; on a cluster reused, the object read in the last step decides the total and the check. `init` never writes the object, and the settings file of `init` (`settings.py`) does not carry these values: one place for each value, the cluster, with the defaults in code.

**After the pivot (#61).** The object moves to the overcloud with the rest of the platform's objects, and the CLI reads it there.

## The command

`nereus config` is a new group for the platform's own settings kept in the cluster; `system` stays for Reefs and Nereids (ADR 0011). `nereus config slo`:

- `show`: the six values, each with its source.
- `set --local <duration> --cloud <duration> --yellow <percent> --orange <percent> --red <percent> --tolerance <percent>`: writes the options given, keeps the fields already set, and prints the values as `show` does. At least one option.
- `reset`: deletes the object; every value falls back to its default.

## The bands in the progress

The share is the time since `init`'s steps started over the time objective of its target.

| Band | Share of the time objective | On a terminal (the card of #88) | Anywhere else (plain lines) |
|---|---|---|---|
| green | under `yellow` | the clock next to the objective, `18.7s of ~8m expected` | nothing on the step lines |
| yellow | `yellow` to `orange` | the clock in yellow | `slo 54% yellow` on the line of the step that crossed into it |
| orange | `orange` to `red` | the clock in orange, and the slowest step so far | `slo 82% orange` on the line that crossed |
| red | over `red` | the clock in red, and the slowest step so far | `slo 104% red` on the line that crossed |

The plain total line ends with the time objective and the band reached: `total  18.7s  slo 8m, 3% green`. The share is rounded down, so `99%` is never shown red.

## The fitness function

`nereus init --check-slo` runs `init` as usual, then compares its total with the time objective plus the tolerance. Above it, `init` fails (exit code 1) after the cluster is ready and the config saved, with the total, the limit and the three slowest steps:

```text
✗ init took 9m41s, over its time objective of 8m plus the 20% tolerance (9m36s); slowest steps: cluster nereus-scn-main-a3f9c2 9m12s, kinds and namespace 21.3s, registry localhost:5111 7.1s; shorten them, or raise the objective: nereus config slo set --local 10m
```

Between the objective and the limit, it warns and passes, with the same slowest steps and the same suggestion (#857). Without `--check-slo`, every `init` on the local target warns past the objective and exits 0, since the cluster is ready by then. The scenes that install the profile pass `--check-slo` too. `test/scene` runs `init` with `--check-slo`, so the `scene` job of CI fails when the local objective is missed. The check lives in the CLI, not in the script: the scene does not parse durations, and the output a person reads in the walkthrough stays the same. A CI runner is slower than a laptop: if the first runs show a steady gap, it is recorded on #141 rather than loosening the objective silently.

**The cloud target** is recorded (the default `CLOUD` and the field `spec.targets.cloud`), not enforced: `init` has no target on a cloud yet. When #92 and #61 add it, `init` maps that target to `cloud` as it maps `k3d` to `local`, and the same check applies.

**The former key** (#313). Before #313 the cloud target was keyed `spec.targets.azure`, the name of a Nereid, which the CLI never names (ADR 0002, ADR 0011). For one release the CRD keeps that field, so the API server does not prune it: the CLI reads any key of `spec.targets` that is no target's own as `cloud` when `cloud` is not set, `config slo show` warns with the command that moves it (`nereus config slo set --cloud <duration>`), and any `config slo set` writes it at `cloud` and drops the former key. The release after removes the field from the CRD.

## Security and quality attributes

Under the lens of #28, this slice is **alpha**.

- **Performance, as a fitness function:** the time of `init` is checked on every pull request, against a value in code that a one-line PR changes with its reason.
- **What a person sets is validated** before it reaches the cluster (durations with `re.fullmatch`, percents in range, bands in order), and again by the CRD's schema.
- **Fitness functions of the slice:** unit tests of the bands, the plain and live output, the check and the command; the CRD contract tests; `test/scene` end to end, with `--check-slo`.
- **What beta would need:** per-step objectives from the median of earlier runs (#141), and the history of runs (#102).

## Learn more

- **Service level objectives** (Chris Jones, John Wilkes and Niall Murphy, with Cody Smith, "Service Level Objectives", in Google's *Site Reliability Engineering* book; [sre.google](https://sre.google/sre-book/service-level-objectives/)): a target value for a measured quality; here, the time of `init`.
- **Fitness functions** come from *Building Evolutionary Architectures* (Neal Ford, Rebecca Parsons, Patrick Kua, O'Reilly, 2017; [evolutionaryarchitecture.com](https://evolutionaryarchitecture.com/)): an automated check that a quality of the architecture holds, run on every change. `init --check-slo` is one.
- **Cluster API's `clusterctl move`** ([cluster-api.sigs.k8s.io](https://cluster-api.sigs.k8s.io/clusterctl/commands/move)): the pivot of the objects from the undercloud to the overcloud.
