# Agent guides

One page per topic, read on demand. `CLAUDE.md` stays small and points here, so a session loads only the guide it needs.

- [The CLI design](cli.md): Reef, Nereid, Mandate, the commands, legacy commands mapped.
- [How the owner works](owner.md): voice, pt-BR, spoken summaries, the visual companion, the terminal format.
- [Rules](rules.md): the durable rules and the pillars.
- [The queue](queue.md): the board and how issues are registered.
- [Layout](layout.md): where things live in the repository.
- [Worktrees](worktrees.md): one git worktree per agent run, its name and its cleanup.
- [How we work](how-we-work.md): good enough first, open source first, the languages.
- [Issues](issues.md): GitHub Issues are the backlog.
- [Raw data](raw-data.md): where the recordings and dumps of the sessions live.
- [ADRs](adr.md): how to write a decision.
- [API groups](api-groups.md): every new idea starts as an API group (proposed rule).
- [Decks](decks.md): the rules for a deck or an HTML page, from the deck engine, and for screens used from a phone.
- [Beach](beach.md): Glaucus, the messenger between the voice session and the local agent.
- [Peers](peers.md): the other sessions on this repository, and the resources they share (the protocol and the `room` skill live in the owner's `linux` repository).
- [Saving tokens](tokens.md): the token practices, their hooks and how to tell whether they worked.
- [AI and teams](ai-and-teams.md): the AI accelerates, people set the direction and decide (Paulo Caroli).
- [The session prompt](session-prompt.md): rewritten with `/next save` before every `/clear`, loaded after it, STALE when not rewritten.
- [The status bar](status-bar.md): each piece of the bar under the prompt, and what the forecast asks of the session.
- [Publishing on ghcr.io](publish.md): `make promote`, and the click that makes a new package public.
