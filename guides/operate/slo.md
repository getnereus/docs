# Meet the time SLO

See and change the time objective `nereus init` is measured against: 8 minutes on k3d, 20 on a cloud, by default ([spec 0004](../../specs/0004-init-time-slo.md)).

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md). The defaults live in the CLI; the cluster may override them in one `ServiceLevelObjective` object in `nereus-system`, whose name and shape are provisional.

## Steps

### 1. See each value and where it came from

[`nereus config slo show`](../../specs/cli/core.html#slo-show) prints the objective of each target (`local`, `cloud`), the shares of it where the clock changes colour (`yellow`, `orange`, `red`), and the `tolerance`. `cloud` is recorded, not checked yet.

```bash
nereus config slo show
```

``` { .text .output title="output" }
SETTING    VALUE  SOURCE
local      8m     default
cloud      20m    default
yellow     50%    default
orange     75%    default
red        100%   default
tolerance  20%    default
```

### 2. Change some

[`nereus config slo set`](../../specs/cli/core.html#slo-set) writes only what you give; the rest keep their defaults.

```bash
nereus config slo set --local 4m --tolerance 5
```

``` { .text .output title="output" }
SETTING    VALUE  SOURCE
local      4m     cluster
cloud      20m    default
yellow     50%    default
orange     75%    default
red        100%   default
tolerance  5%     cluster
```

### 3. Read the bands on the next init

The next [`nereus init`](../../specs/cli/core.html#init) reads them once its kinds are applied: on a cluster it just created, the defaults hold. A step that crossed into a band says so on its line; red reports a miss, and `init` still finishes. With a tight objective (`--local 1s --yellow 10 --orange 20 --red 30`), its last lines read:

```bash
nereus init --yes
```

``` { .text .output title="output" }
✓ prerequisites             0.0s  docker 29.9.1, k3d 5.9.0, helm 4.1.4
✓ registry localhost:5111   0.0s  reused
✓ cluster nereus-local      0.1s  reused
✓ kinds                     0.4s  release nereus-reefs revision 2  slo 47% red
✓ nereus                    1.1s  release nereus revision 2, profile core
✓ installation              0.3s  kept nereus-local
  total                     1.8s  slo 1s, 180% red
```

Past the objective, `init` warns with the slowest steps and the command that raises it. With `--check-slo`, which the scenes that install a profile pass, `init` fails past objective plus tolerance and names the three slowest steps.

## Check it worked

`nereus config slo show` prints `cluster` as the source of each value you set. A cluster set up before #313 may hold the former key `spec.targets.azure`: the table then opens with a warning, and any `nereus config slo set` moves it to `cloud`.

## Clean up

[`nereus config slo reset`](../../specs/cli/core.html#slo-reset) deletes the object, and every value is back to its default.

```bash
nereus config slo reset
```

``` { .text .output title="output" }
✓ SLO reset: every value is back to its default
```

## Next

- [Rebuild the kept cluster](kept-cluster.md), whose `init` the objective measures.
