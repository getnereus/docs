# 0028. The presentations reef: Nereus keeps the deck, a Session is each time it is given

!!! note "In short"
    The `presentations` reef keeps the deck as a `Presentation` and each time it is given as a `Session`. Status: Accepted (2026-11-16).

**Status:** Accepted (2026-11-16)

## Context

Decks live in the repository today: an outline in YAML (`docs/presentations/*.yaml`) rendered by `docs/presentations/render-outline` into one self-contained HTML file. Presenting from a phone while a projector and the room follow, with questions and feedback later, needs a home on the platform. #218 (refine the presentations reef) and its children held only recommendations; on 2026-10-19 the owner decided there that the deck's source lives in Git.

The review of 2026-11-16 (the deck `docs/presentations/presentations-reef.yaml`, PR #1685) took the decisions below and split the work into six journeys under #1687; the first, #1688 (J1, drive and follow), is the walking skeleton. Three measurements came first: #1689 (Server-Sent Events through the Nereus API), #1690 (the renderer under the portal's Content Security Policy) and #1691 (the database).

## Decision

**The reef is `presentations.getnereus.dev/v1alpha1`, with two kinds.**

| Kind | What it answers | What it holds |
|---|---|---|
| `Presentation` | what is shown | the deck and its revisions, each by digest |
| `Session` | each time it is shown, a rehearsal included | the revision it shows, its public link and short code, its step, and later its event, room, speakers, times, staff, questions and feedback |

`Event` (groups Sessions) and `Workshop` (has steps) come later; until then the event's name and venue live on the Session. One writer per field (ADR 0005): the person writes `spec`, the Nereid writes `status`.

**Nereus is the source of the deck; Git is only an optional origin to import from.** A deck is written anywhere, by any agent or editor, against a published JSON Schema versioned by `outlineVersion`, served on a public route and by the CLI, and named by the deck with `$schema`. What the schema cannot say (links, references, fitting the screen) is checked by the Nereid on a dry run. This replaces the owner's decision of 2026-10-19 on #218 (the source in Git), because nobody should need a repository to present.

**One package per revision, never changed afterwards.** The import takes the YAML and everything it points to: its assets, the files it cites from outside its folder and the shared references, each copy with its origin (path and commit), listed in a `package.json` manifest at the root with their hashes and the `outlineVersion`. The package is a deterministic tar whose sha256 is the revision; a Session points to the revision it showed. OCI comes later, only to share a package.

**One database for the revisions and the live state: PostgreSQL through the `Database` kind** (#1691). The reef asks the database reef for one `Database` (`engine: postgres`) per installation; the Nereid of its Mandate (`cloudnative-pg` today, a managed PostgreSQL later) makes it, and the reef's Nereid, `leagore`, reads the connection from the Service Binding Secret. The API holds no database connection: it writes `spec` and calls the Nereid, found through the reef's Mandate, over HTTP inside the cluster, as the ideas reef reads its notes from doris; the store and its driver stay behind the Nereid, so the API never names a tool.

- **Revisions:** a table keyed by digest, behind a small put and get; a put of an existing digest changes nothing, and the API refuses a package over 1 MB.
- **Live state:** a Session's row holds the step and a sequence; a step change is one statement, issued by `leagore`, that updates the row and calls `pg_notify`, so the state and its event commit together.
- **Fan-out:** `leagore` holds the one dedicated `LISTEN` connection and streams each change to the API; each API replica holds one stream to `leagore` and writes each change to its own followers; a notification carries only the Session's name, step and sequence (its payload is at most 8000 bytes).
- **Reversible:** put and get by digest hide the store, so object storage or OCI can take the revisions later without changing the package. NATS JetStream (a KV watch and an Object Store) is the measured alternative.

**The follower is fed by the server and never runs the deck.** The projector and the audience receive only the current state and redraw it. They show the revision as the deck engine renders it, fitted to each screen, with the engine's own font controls (A−, A+) per device; the engine's controls that change the step stay hidden, so the step comes only from the server (owner, 2026-11-16, #1760). A step is the engine's own: a slide and each item it reveals, so the room sees an item when the speaker reveals it (owner, 2026-11-16). The room sees what the speaker sees, animations included; each device can turn its animations off (an older phone), and then sees the same items in the same order, at once (owner, 2026-11-16). leagore renders each revision with the deck engine when it is stored, and refuses a deck that names a file, since a revision carries only its YAML. The speaker presents with the same engine and all its controls, in the Sessions tab; each move of it is the Session's step, the speaker's screen moving before the answer, and the notes and the talk's time are on the speaker's screen only (owner, 2026-11-16, #1761). The channel is Server-Sent Events on the Nereus API (#1689), through the entrance `nereus init` installs, with no change to it:

- each event carries an `id`, the Session's sequence; a reconnect with `Last-Event-ID` gets the events it missed, and an unknown or old id, or a new follower, gets one `state` event with the whole current state first;
- the API sends a heartbeat every 15 s, a fixed server setting, as a named event `hb` rather than a comment, since `EventSource` hides comments from the page, and a `retry:` delay; the page reopens the stream after about 35 s with no event, since neither TCP nor `EventSource` notices a dead network;
- the stream's route has no request timeout, and each follower has a bounded queue, dropped when full, so a slow follower never holds the others back;
- the API raises its open-files limit at start, and a cap of followers per pod answers `503`: with the container's 1024, one pod failed every route at about 1000 followers;
- driving is a plain `POST` that needs a token with the presentations reef in J1 and the right to present from J6 (#1725); following needs no token, only the Session's short code, and is read-only.

WebSocket was not chosen: it would also pass the entrance, but a follower only receives, and the API has no WebSocket library.

**The deck fits the portal's policy with no exception.** The portal keeps `default-src 'self'`; the renderer writes its script and its style as files of their own for the portal, and keeps one self-contained HTML file, everything inline, for the offline export (`nereus presentations presentation get --output html`). #1690 found 6 violations per deck (one inline script, one style block, four style attributes), so the split (#1693) is small.

**The audience is anonymous; sign-up is a choice, later.** A follower is a random id per device, with no login. Signing up (linking the device to a User, e-mails optional, deletion at any time) comes after the six journeys.

**The reef's Nereid is `leagore`**, the Nereid who gathers the people: Nereus's own code, so it takes a sea name, as `doris`, `thetis` and `triton` do. It is born with a new field, `nameOrigin`, that explains its name and is shown by the CLI and the portal; the field for every Nereid is its own issue. The name joins the reserved list, so no agent session gets it.

```text
$ nereus presentations presentation create storytelling \
    --from talks/storytelling.yaml
✓ presentations/presentations/storytelling created, revision 1 (sha256:3f9c2a71)

$ nereus presentations session create platform-day \
    --presentation storytelling \
    --talk 30m
✓ presentations/sessions/platform-day created (revision sha256:3f9c2a71)
  follow: https://nereus.example.com/p/K7Q4
```

The import is `create --from` and the check is `create --dry-run`, the verbs of ADR 0013 (commands), so no new verb is needed.

**Stand-ins, J1 only:** one YAML stored as a blob, with no package (J2, #1699); only the talk time, with no rehearsal (J3, #1707); any token with the presentations reef drives (J6, #1725; retired by #1726, presenting a right of the authorization reef); one API replica.

## Prior art

- Quiz platforms where the audience joins by a short code: a thin page fed by the server that redraws the state it receives.
- Helm charts as packaged archives, with an OCI registry as only one way to move them: the package first, OCI later.
- EPUB 3.3: one archive with a manifest at its root listing its files and the format's version, the idea of `package.json`.
- JSON Schema: a published, versioned schema any editor or agent validates against.
- The HTML `EventSource` and its `Last-Event-ID` reconnect; PostgreSQL `LISTEN`/`NOTIFY` as a fan-out across replicas.

## Consequences

- A speaker needs no repository: any tool writes a deck against the schema, and Nereus keeps its history by digest.
- The Nereus API gains its first long-lived stream: an open-files limit raised at start, a cap of followers per pod, and memory per follower (about 30 KB in the API and 55 KB in the gateway, #1689) to size for.
- The presentations reef depends on the database reef: an installation without a `Database` Mandate cannot run it.
- `leagore` is on the drive and follow path: while it is down, the steps stop and the followers wait; the API reopens its stream to `leagore` and sends each follower the current state.
- The renderer gains a split output for the portal while the offline export stays one file.
- `cloudnative-pg` configures no backup today, so a Session's live state and the revisions are not backed up until it does: a separate issue, outside J1.

## Open questions

- A second API replica or a second `leagore`: `LISTEN`/`NOTIFY` measured with two listeners, but more replicas, the stream relayed from `leagore` to the API, a failover and a pooler in front are not.
- Whether `cloudflared` in front of the kept cluster buffers `text/event-stream`, and how phones behave with the screen locked: the owner's phone test in #1698.
- The credential for a follower when following stops being public (sign-up, rights): `EventSource` sends no `Authorization` header, so a cookie or a short-lived query token, decided with that journey.
- The name of the audience's identifier when sign-up comes, and how deletion keeps the statistics anonymized.

*Origin: the owner's decisions of 2026-11-16 in the review of the presentations reef (the deck `docs/presentations/presentations-reef.yaml`, PR #1685, journeys #1687 and #1688), replacing the decision of 2026-10-19 on #218; the figures of the spikes #1689, #1690 and #1691 of the same day. Raw data in Drive `#pontos/raw/2026-11-16/`.*
