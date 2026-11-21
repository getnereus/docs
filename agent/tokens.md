# Saving tokens

The owner's pillar (2026-11-02, #809): the same quality for fewer tokens. Before an activity, weigh whether it can be done as well for less, do the cheaper way, or suggest it when the choice is the owner's. Quality comes first: a saving that brings rework is no saving.

## The practices

1. **One order per session.** Every call reads the whole context again, so a long session is the main cost. Finish an order, then `/clear` or a new session. A `UserPromptSubmit` hook warns the owner and the agent once the context of a call passes 200k tokens, or `CLAUDE_CONTEXT_TOKENS_REFERENCE` when it is set.
2. **Filter tool output.** Use `--quiet`, `--json` with `--jq`, `tail`, or `Read` with `offset` and `limit`: whatever enters the context is read again on every later call. A `PostToolUse` hook on `Bash` and `Read` warns when one output passes 10k characters.
3. **Subagents for mechanical work only**, on a lighter model, with a short brief and a one-line report. What takes a few calls is done directly. A subagent that runs a scene waits for it to end and reports its verdict: its brief says so, since a subagent that stops while its scene still runs leaves the wait, the reading and the commit to the main session (owner, 2026-11-08).
4. **Shorter answers:** the outcome and the next decision, with no recap of what the owner has already seen.

Both hooks are `scripts/metrics/tokens`, set in `.claude/settings.json`. They warn and never block, and whatever goes wrong in them, the session carries on.

## When the context warning fires

| Situation | Do |
|---|---|
| Work finished or at a stopping point | `/wrap-up`, then `/clear` |
| Mid-task with little left (a few calls: a push, a PR, a merge) | Finish it in this session, then `/wrap-up` and `/clear` |
| Mid-task with much left (several steps, files or PRs) and the work has an issue | `/rollover`: the handoff goes on the issue and a new session carries on |
| Mid-task with much left and no issue | `/compact` |
| Nothing pending, all of it in a PR or an issue | `/clear` |

Suggest `/rollover` only when much is left (owner, 2026-11-03): it costs about a dozen calls on the long context plus a new session reading the issue again, so with a few calls left, finishing here is cheaper. `/rollover` is the owner's manual trigger while it is evaluated, compared with `/compact` on cost and rework. No `/compact` before `/wrap-up`: it spends tokens summarizing a conversation about to be cleared, and takes details the wrap-up needs.

## Knowing whether it worked

Compare one week with the one before, at the Friday summary. Figures go to `getnereus/internal`, never here.

```bash
scripts/metrics/order summary --file metrics/orders/2026-W45.csv
scripts/metrics/tokens report --file metrics/orders/2026-W45.csv
```

| Practice | Should go down or hold | Read it in |
|---|---|---|
| All of them, the result | tokens and cost per order | `order summary` |
| 1, one order per session | orders per session (to 1), mean and peak context | `tokens report` |
| 2, filter tool output | big outputs, of all outputs | `tokens report` |
| 3, subagents | tokens per agent in an order | `order summary` |
| 4, shorter answers | output tokens per order | the week's CSV |
| The guard: quality holds | review rounds | `order summary` |

Orders differ in size, so a few of them show a direction, not a proof. A week counts as better only when the cost per order falls and the review rounds hold.
