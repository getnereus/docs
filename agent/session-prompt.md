# Session prompt

A session prompt is the instructions a session leaves so the next one, after `/clear`, resumes the same way of working (#1236, #1239). It carries no memory of what was done: the work itself is in the repository, the issues and the board.

Since #1953 the owner's global tools keep it (smsilva/linux#203): `session-prompt` and its global hook, driven by the global `next` skill; the cycle and the rules are in `~/git/linux/claude/session-prompt/README.md`. Never write its path by hand: `session-prompt path` prints it.

## In Nereus

1. **A session starts:** the global hook (`session-prompt hook`, on every `SessionStart` and `SessionEnd`, in `~/.claude/settings.json`) records its start. This repository's `.claude/settings.json` has no session hook of its own.
2. **Before `/clear`:** the agent rewrites its prompt with `/next save`, without asking the owner to confirm (owner, 2026-11-09, #1284), shows what it saved, and only then tells the owner the session can be cleared. The prompt is `.git/session-prompts/<agent name>.md` in the main clone (inside the git folder, so no clone can bring one), with a `## Board at save` block from `board-queue team`, so who holds what comes from the board, not from memory.
3. **After `/clear`:** the hook puts the prompt in the session's context; one that was not rewritten says **STALE**.
4. **`/next`:** with a prompt, follow it and skip the board; with none, the board (`.claude/next.md`).
5. **A session that ends for good** (`/exit`, a closed window, not `/clear`): the hook archives the prompt to `~/.claude/prompts/nereus/<agent name>-<date>.md`.
6. **`/next clear`:** archives the prompt under a topic and goes back to the board.

## The rules

- **One prompt per agent,** by its name (`AGENT_NAME`, else `agent-name whoami`): every worktree of that agent finds the same file, and two agents never overwrite each other.
- **STALE:** say so to the owner before following it, check its state against the board and the repository, and rewrite it with `/next save` once checked.
- **A peer's item:** the `## Board at save` block is a snapshot; check the board again before acting on an item a peer holds.
- **If the branch or checkout path differs from the prompt's header,** say so and ask before the first commit.
- **Before #1953** the prompts lived in `.claude/prompts/` of the main clone, kept by `scripts/session/prompt`; the switch moved them to `.git/session-prompts/`.
