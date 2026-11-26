# The status bar

The bar under Claude Code's prompt shows, in one line, where the session is working, how full its context is and how much of the plan's quota is left.

![The status bar of a session](../assets/agent/status-bar.png)

```text
nereus  main  ✦ Opus 5.5  40k 13%  4h42m 4% ↻ 17:55  5d10h 16% ↻ Mon 01:00 ▲ 61%
```

## Each piece

| Piece | What it says | Colors |
|-------|--------------|--------|
| `⚠ pontos` | a raw log did not reach Drive (shown only then; run `pontos-save status`) | red |
| `⚠ disk 91%` | the disk passed its warning threshold (shown only then) | amber |
| `nereus` | the repository, and the subfolder when there is one | blue |
| `main` | the branch and the git status | green when clean, gray when dirty |
| `✦ Opus 5.5` | the model | gray |
| `40k 13%` | the session's input tokens, and their share of a 300k reference before a save and `/clear` | green, amber from 60%, salmon from 80% |
| `4h42m 4% ↻ 17:55` | the 5-hour limit: time left, usage, reset, then its verdict and the usage at the reset if this pace goes on | white numbers, the verdict coloured: `•` ok (green), `▼` above 95% (salmon) |
| `5d10h 16% ↻ Mon 01:00 ▲ 61%` | the weekly limit: time left, usage, reset, then the pace and the forecast | white numbers, the pace below |

`/rc`, on the right, is Claude Code's own: Remote Control is on.

## The pace

```text
forecast = weekly usage × 7 days / time gone in the window
```

The week is meant to be used up, so the pace only says hold back past 99%. The same table colours the status bar and the Usage tab of the portal (spec 0015); `controllers/reference/test_usage_palette.py` checks the rule (`cli/src/nereus/usage_rules.py`) and the tab's stylesheet against it.

| Forecast | Word | Icon | Status bar | Dark: pace, container, on | Light: pace, container, on |
|----------|------|------|------------|---------------------------|----------------------------|
| below 70% | `push` | ▲ | 39 (blue) | `#5ec4ff` `#003450` `#cbe8ff` | `#00639b` `#cee5ff` `#001d33` |
| 70% to 99% | `steady` | • | 114 (green) | `#87d787` `#133a1a` `#c6f1c4` | `#2e6b30` `#c4efbf` `#002107` |
| above 99% | `slow` | ▼ | 203 (salmon) | `#ff8a80` `#4d1512` `#ffdad5` | `#b3261e` `#ffdad6` `#410002` |

- `push`: speed up, more subagents and parallel sessions; `steady`: keep the pace; `slow`: hold back, one agent, no subagents, or a day off.
- `final` (no worked time left in the window) is neutral: gray (247) on the status bar, the portal's surface on the tab.
- Nereus computes the word: the status bar reads it from the local cache (`figures.pace` in `~/.local/state/nereus/usage/weekly.json`), and its own rule, with the same thresholds, is only the fallback on a machine without the `nereus` CLI or with a cache of another window.
- The pace stays hidden in the first 6 hours of the window, while the forecast is unstable.

## Today's goal

The goal spreads what was left at the day's first reading evenly up to the reset, so it stays fixed all day. The share passes 100% once the goal is passed. A share above 100% does not mean the week is at risk: the forecast says that.

```console
$ claude-usage-plan
  Weekly quota: 16% used, resets Mon 09/11 01:00, target 100%
```

## Where it lives

The bar is the owner's own tooling, not part of Nereus: `scripts/bin/claude-status-line`, `claude-usage-plan` and `claude-usage-forecast` in the owner's dotfiles repository, set up by its `statusline-setup` skill.

To choose which limits appear:

```console
$ claude-status-line-limits --show weekly
```

`--show` takes `session`, `weekly`, `both` or `none`.
