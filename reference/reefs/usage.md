# The usage reef

Every command that reports a coding agent's quota window and shows where it is heading.

## Commands

- [`nereus usage report weekly`](../../specs/cli/reefs/usage.html#usage-report) report sends a reading, read now
- [`nereus usage report weekly`](../../specs/cli/reefs/usage.html#usage-replace) --replace says the share really went down
- [`nereus usage report weekly`](../../specs/cli/reefs/usage.html#usage-offline) offline, report keeps the reading locally and get answers from it
- [`nereus usage apply`](../../specs/cli/reefs/usage.html#usage-apply) apply writes the windows of a file, under the same rules
- [`nereus usage get weekly`](../../specs/cli/reefs/usage.html#usage-get) get shows the forecast at the reset, today's goal and the week day by day
- [`nereus usage list`](../../specs/cli/reefs/usage.html#usage-list-delete) list shows every window, delete forgets one

## Examples

### usage-report

75% used, resetting on Monday at 01:00 in São Paulo.

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

### usage-replace

The usage was reset mid-week: 98% kept, 91% now.

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

### usage-offline

Nereus unreachable: the reading goes to the local cache.

```bash
nereus usage report weekly \
  --used 75 \
  --resets-at 2026-11-16T01:00:00-03:00
```

``` { .text .output title="output" }
✓ usage/windows/weekly kept locally (75% used, resets Mon 16/11 01:00): Nereus unreachable, next try in 5m

Next steps:

  nereus usage get weekly
```

### usage-apply

A file of UsageWindows, or a folder of them.

```bash
nereus usage apply \
  --from-file weekly.yaml
```

``` { .text .output title="output" }
✓ usage/windows/weekly created

Next steps:

  nereus usage list
```

### usage-get

The times in the window's time zone.

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

### usage-list-delete

The same columns as get.

```bash
nereus usage list
```

``` { .text .output title="output" }
WINDOW  USED  RESETS           FORECAST  PACE    TODAY  READ
weekly  75%   Mon 16/11 01:00  91%       steady  ≤79%   Sat 19:06
```
