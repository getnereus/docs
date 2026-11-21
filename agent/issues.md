# Issues

- **GitHub Issues are the backlog:** what to do now and the next ideas. Nothing is tracked only in a chat, a local file or a Drive dump.
- The order lives on the board (Project v2 #1 of `getnereus`); `docs/agent/queue.md` has the statuses and `scripts/board/queue`.
- An idea that is not ready becomes an `Idea` issue in the `Ideas` column; it moves to `Backlog` only after the owner's triage.
- Each issue carries what an agent needs to deliver it alone: context, decisions and who took them, dependencies, a checkable "Done when".
- **The issue holds the context, not the conversation** (owner, 2026-10-29): before a context compact or a pause, everything the task needs is in its issue (the context, the decisions with who took them, the next step), in its body or a handoff comment. After the compact, the agent resumes by reading the issue (`gh issue view <n> --comments`), never from what it remembers of the conversation. A chain of work is opened as sub-issues first, each complete on its own, and done one at a time (#477, with #479 to #483).
