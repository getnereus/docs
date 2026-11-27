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

Each day reads against its adjusted goal: today's goal as it was fixed at the day's start, what was used then plus what is left to 100% spread over the worked time left.

TOTAL is the share at the day's end (projected for the days ahead, `~`), ADJUSTED that goal (today: the path to it now), GAP the total less the goal, ALLOWED the goal less the day's start, and SPENT what the day used.

```bash
nereus usage get weekly
```

``` { .text .output title="output" }
WINDOW  USED  RESETS           FORECAST  PACE    TODAY  READ
weekly  75%   Mon 16/11 01:00  91%       steady  ≤75%   Sat 19:06

DAY        TOTAL  ADJUSTED  GAP  ALLOWED  SPENT
Mon 09/11  10%    11%       -1   +9%      +10%
Tue 10/11  ~21%   21%       ±0   +11%     ~+11%
Wed 11/11  31%    36%       -5   +15%     +10%
Thu 12/11  41%    42%       -1   +11%     +10%
Fri 13/11  60%    56%       +4   +15%     +19%
Sat 14/11  75%    70%       +5   +15%     +15%   today, goal 75%
Sun 15/11  ~91%   100%      -9   +25%     ~+13%  plan
```

### 3. Cut the days where you live

The days and the times are cut in the time zone of the Reef's Mandate. [`nereus init`](../../specs/cli/core.html#init-profile) sets it on install: the `spec.timeZone` of the `Installation` in `~/.config/nereus/init.yaml` when you set one, else the machine's (`TZ`, then `/etc/localtime`, then `timedatectl`), which it writes back to the file.

It prints the zone and where it came from, and warns when it found none: the days are then cut in UTC.

```text
✓ time zone America/Sao_Paulo (discovered from /etc/localtime; set spec.timeZone of the Installation in ~/.config/nereus/init.yaml to choose it)
```

A Mandate that exists keeps its params, so on an older install set the zone on it by hand. [`nereus mandate apply`](../../specs/cli/core.html#mandate-apply) replaces every param, so name them all.

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

`report` keeps a local cache, one JSON file per window under `~/.local/state/nereus/usage/`, and sends at most every 3 minutes (`nereus config set usage_send_interval <interval>` changes it, at least `1m`), so a status line can run it on every reading and read the figures back with `jq`. Offline, the cache keeps the reading and `get` answers from it, marked `local`.

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

DAY        TOTAL  ADJUSTED  GAP  ALLOWED  SPENT
Mon 09/11  ~18%   13%       +5   +13%     ~+18%
Tue 10/11  ~36%   31%       +5   +13%     ~+18%
Wed 11/11  ~55%   48%       +7   +12%     ~+19%
Thu 12/11  ~73%   66%       +7   +11%     ~+18%
Fri 13/11  91%    81%       +10  +8%      +18%
Sat 14/11  91%    91%       ±0   +1%      +0%    today, goal 92%
Sun 15/11  ~111%  100%      +11  +8%      ~+17%  plan
```

## Next

- [The usage Reef's commands](../../reference/reefs/usage.md), with `apply`, `list` and `delete`.
