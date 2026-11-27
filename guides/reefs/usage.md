# Follow your agent's quota

Report the share of a coding agent's quota window you read, and see where it is heading: the forecast at the reset, its pace, today's goal and the week day by day.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`: it brings the usage Reef with its Nereid `reference-usage`.
- `nereus login` done: the readings go through the Nereus API.
- The share used and the reset of the window, as your agent's status line shows them.

## Steps

### 1. Report a reading

[`nereus usage report`](../../specs/cli/reefs/usage.html#usage-report) sends the share, read now. Within one window the higher share is kept: an idle session that reports an older, lower share changes nothing.

```bash
nereus usage report weekly \
  --used 75 \
  --resets-at 2026-11-16T01:00:00-03:00
```

``` { .text .output title="output" }
✓ usage/windows/weekly reported (75% used, resets Mon 16/11 01:00)

Next steps:

  nereus usage get weekly
```

### 2. Read where it is heading

[`nereus usage get`](../../specs/cli/reefs/usage.html#usage-get) shows the forecast at the reset and its pace (`push` below 70%, `steady` up to 99%, `slow` above), today's goal, and the week: the days gone (`~` when estimated), today and the plan for the days left.

```bash
nereus usage get weekly
```

``` { .text .output title="output" }
WINDOW  USED  RESETS           FORECAST  PACE    TODAY  READ
weekly  75%   Mon 16/11 01:00  91%       steady  ≤75%   Sat 19:06

DAY        SHARE  TOTAL
Mon 09/11  +10%   10%
Tue 10/11  ~+11%  ~21%
Wed 11/11  +10%   31%
Thu 12/11  +10%   41%
Fri 13/11  +19%   60%
Sat 14/11  +15%   75%    today
Sun 15/11  +25%   100%   plan
```

### 3. Cut the days where you live

The days and the times are cut in the time zone of the Reef's Mandate, UTC until you set one. [`nereus mandate apply`](../../specs/cli/core.html#mandate-apply) replaces every param, so name them all.

```bash
nereus mandate apply reference-usage \
  --reef usage \
  --nereid reference-usage \
  --default \
  --param timeZone=America/Sao_Paulo
```

### 4. Report a reset

When the quota was reset and the share really went down, say so with `--replace`: the lower share wins, and the days gone stay. For an hour, a reading above it but not above the old peak is taken for a stale session's and ignored.

```bash
nereus usage report weekly \
  --used 91 \
  --resets-at 2026-11-16T01:00:00-03:00 \
  --replace
```

``` { .text .output title="output" }
✓ usage/windows/weekly replaced 98% (91% used, resets Mon 16/11 01:00), forecast 110.7% slow

Next steps:

  nereus usage get weekly
```

### 5. Report from the status line

`report` keeps a local cache, one JSON file per window under `~/.local/state/nereus/usage/`, and sends at most every 5 minutes, so a status line can run it on every reading and read the figures back with `jq`. Offline, the cache keeps the reading and `get` answers from it, marked `local`.

```bash
jq '.figures.forecast' ~/.local/state/nereus/usage/weekly.json
```

## Check it worked

`nereus usage get weekly` shows the share you reported, its forecast, and today never below zero after a reset.

```bash
nereus usage get weekly
```

``` { .text .output title="output" }
WINDOW  USED  RESETS           FORECAST  PACE  TODAY  READ
weekly  91%   Mon 16/11 01:00  111%      slow  ≤92%   Sat 19:06

DAY        SHARE  TOTAL
Mon 09/11  ~+18%  ~18%
Tue 10/11  ~+18%  ~36%
Wed 11/11  ~+19%  ~55%
Thu 12/11  ~+18%  ~73%
Fri 13/11  +18%   91%
Sat 14/11  +0%    91%    today
Sun 15/11  +8%    100%   plan
```

## Next

- [The usage Reef's commands](../../reference/reefs/usage.md), with `apply`, `list` and `delete`.
