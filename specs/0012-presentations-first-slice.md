# 0012. The presentations reef, first slice: drive and follow (J1)

The walking skeleton of the presentations reef (ADR 0028, journey #1688): a phone drives a Session's step, another phone and a projector follow it. Crude on purpose: one deck as a blob (a package since #1701), only the talk time, any token with the reef drives (until #1726 made presenting a right of the authorization reef), one API replica.

## The commands

```console
$ nereus presentations presentation create storytelling --from talks/storytelling.yaml
✓ presentations/presentations/storytelling created, revision 1 (sha256:3f9c2a71)

$ nereus presentations session create platform-day --presentation storytelling --talk 30m
✓ presentations/sessions/platform-day created (revision sha256:3f9c2a71)
  follow: https://nereus.example.com/p/K7Q4

$ nereus presentations session get platform-day
NAME           PRESENTATION   STEP   FOLLOWERS   FOLLOW
platform-day   storytelling   0/24   0           https://nereus.example.com/p/K7Q4
```

With the room's pace thermometer on from the start (#1723), `session get` adds its gauge, the taps of the last minute:

```console
$ nereus presentations session create warm-room --presentation storytelling --talk 30m --thermometer
✓ presentations/sessions/warm-room created (revision sha256:3b9880a3)
  follow: https://nereus.example.com/p/M2X9

$ nereus presentations session get warm-room
NAME       PRESENTATION  STEP  FOLLOWERS  FOLLOW
warm-room  storytelling  0/3   0          https://nereus.example.com/p/M2X9

THERMOMETER  TOO SLOW  TOO FAST
on           3         11

$ nereus presentations session get warm-room --output agent > warm-room.yaml
✓ presentations/sessions/warm-room exported (3 slides, 4 questions, 3 feedback answers)
  pace: slide intro 0 slow 1 fast; slide demo 2 slow 14 fast (peak 14:21)
```

`presentation` is the reef's default kind (`nereus presentations create` is the same as `nereus presentations presentation create`). Each kind has `create`, `get`, `list` and `delete`, with `--dry-run` and `--examples` (ADR 0013).

## Who does what

```text
phone / projector / follower
        │  POST step (token)        GET follow stream (no token, by short code)
        ▼
  Nereus API ── finds the reef's Nereid through its Mandate (never by name) ──┐
        │  HTTP, inside the cluster only (NetworkPolicy: the API alone)       │
        ▼                                                                     │
  the reef's Nereid: leagore (#1695); its store is PostgreSQL, or memory in scene-core
        │  every PostgreSQL connection: revisions, the Session's row, LISTEN
        ▼
  PostgreSQL, a Database of the database reef (engine postgres)
```

- **The API holds no database connection** (🟠 decision of #1688, settled with a Fable review): it writes `spec`, and calls the Nereid for everything else. The rule "The API never names a Nereid" keeps the store and its driver behind the Nereid, as the ideas reef does with doris (`api/ideas_notes.py`).
- **The Nereid writes `status`** (ADR 0005) and holds the one `LISTEN` connection; each API replica holds one internal stream to it and fans out to its own followers.
- **The short code is given synchronously** by the Nereid inside the create request, so `session create` prints the follow link at once; its reconciler gives the same code to a Session created any other way.

## The kinds

`Presentation` (`presentations`, default kind):

- `spec`: `description` (optional), `source` (optional, where the YAML came from, informative).
- `status`: `revision` (`sha256:<hex>`), `revisions` (the count), `slides` (the slides of the revision; not `steps`, a name every Nereid's status takes for its own steps), `conditions` (`Ready`), `observedGeneration`.

`Session` (`sessions`):

- `spec`: `presentation` (its name, required), `talk` (a duration such as `30m`, required but for a rehearsal), `rehearsal` (#1710: `true` gives no code, so no public link; fixed at create).
- `status`: `revision` (the digest it shows, fixed at create), `code` (four characters; none for a rehearsal), `step`, `slides`, `times` (#1710: `[{name, seconds}]`, each slide's time on screen, in the deck's order), `ended` (#1710), `conditions` (`Ready`), `observedGeneration`.

## The Nereid's HTTP contract

On the controller port of the Nereid's Service, inside the cluster only. JSON in and out, except the deck. `leagore` serves it over one store interface with two stores: memory (unit tests and `make scene-core`, which installs no real tool) and PostgreSQL (`make scene-presentations` and `k3d-nereus`); one contract test suite runs against both. No reference Nereid: leagore is Nereus's own code, as doris is for the ideas reef (🟠 decision of #1688).

| Method and path | Body | Answer |
|---|---|---|
| `PUT /presentations/{name}/revisions` | the deck's package (`application/x-tar`, #1701), at most 1 MB | `200 {"revision": "sha256:…", "revisions": 1, "steps": 24}`; patches the Presentation's `status` |
| `POST /presentations/{name}/checks` | the deck's package, a dry run (#1702) | `200 {"errors": [...], "warnings": [...], "steps": 24}`: every reason the deck engine refuses it (`steps` null then) and what may not fit the screen; stores nothing |
| `GET /presentations/{name}/deck` | | `200` the latest revision as one self-contained page (`text/html`: style, script and diagrams inline), the speaker's notes included: the offline export (#1703); `404` unknown |
| `PUT /presentations/{name}/link` | `{"expires": "2026-12-16T12:00:00Z" | null}` | `200 {"presentation", "link", "expires"}`: the public link (#1704), made on the first put and kept after, the expiry set; `404` with no deck; `400` an expiry that is not an ISO UTC time |
| `GET /presentations/{name}/link`, `DELETE …` | | `200` the link, `204` removed, `404` none |
| `GET /links` | | `200 {"links": [...]}`, by presentation |
| `GET /links/{link}/deck` | | `200` the latest revision as a follower's page (`--split`, no notes); `410 {"error", "expires"}` once expired; `404` unknown |
| `GET /revisions/{digest}` | | `200` the package (a J1 revision: its YAML, `application/yaml`), or `404` |
| `PUT /sessions/{name}` | `{"presentation": "storytelling"}` | `200` the Session's state (below); idempotent; gives the code, fixes the revision, patches `status` |
| `GET /sessions/{name}` | | `200` the state with `slides`, the slide name, title and message of every step (#1759), and `pace`, the times of the last ended rehearsal of the same revision or `null` (#1711), or `404` |
| `GET /codes/{code}` | | `200` the state, or `404` |
| `POST /sessions/{name}/step` | `{"step": 3}` | `200` the state with the next `sequence`, the time since the previous step added to the slide that was on screen (#1710); `400` outside `0..steps-1`; `409` once ended |
| `POST /sessions/{name}/end` | | `200` the state with `ended` (#1710): the open slide's time closed; ending again answers the same |
| `POST /sessions/{name}/sharing` | `{"on": true}` | `200` the state with `sharing` (#1859), the projector showing the follow QR code on any slide while it is on; the next `sequence` on a change only; `400` anything but a boolean; `404` unknown |
| `POST /sessions/{name}/thermometer` | `{"on": true}` | `200` the state with `thermometer` and `gauge` (#1723): while it is on the followers tap Too slow or Too fast; the next `sequence` on a change only; `400` anything but a boolean; `404` unknown |
| `GET /sessions/{name}/thermometer` | | `200` `{on, slow, fast}`, the taps that count now: each device's latest tap of the last 60 s (#1723); `404` unknown |
| `POST /sessions/{name}/open` | `{"part": "questions"}` | `200` the state with `questions_open` or `rating_open` set once (#1876), the next `sequence` the first time only; `400` a part other than `questions` or `rating`; `404` unknown; `409` the questions of an ended Session. The step that reaches the deck's last step also opens the questions of a Session with a questions' time; a step back keeps them, End closes them |
| `POST /sessions/{name}/polls/{poll}/open` | | `200` the state with the slide's poll opened (#1722), or reopened once closed (#1917, the answers in stay): `poll` `{name, kind, opened, closes, closed, answers, result}`, the next `sequence`; `closes` is only the reference (`opened` plus `seconds`) and closes nothing; `404` a Session or a poll its revision does not have; `409` a poll open now or an ended Session. An answer's count reaches the followers within a second |
| `POST /sessions/{name}/polls/{poll}/close` | | `200` the state with the poll closed by the speaker (#1917), `closed` its time and `result` filled, the next `sequence`; `404` a Session or a poll unknown; `409` a poll not open (never opened, or closed). The end of the Session closes every open poll |
| `POST /codes/{code}/polls/{poll}/answers` | `{"device", "answer"}` | `201` a new answer, `200` one that replaced the device's earlier one, `{at, created}`; `400` no device's id or none of the poll's options (a choice's index from 0, a scale's value, a text of 1 to 280 characters, trimmed); `404` a code or a poll unknown; `409` before it opens, while it is closed, or at its cap |
| `POST /codes/{code}/pace` | `{"device", "vote": "slow"\|"fast"}` | `200` `{vote, at, fades}` (#1723): a device's tap, which replaces its earlier one and restarts its minute; kept per (Session, device, step), so the export has the pace by slide; `400` no device's id or another vote; `404` unknown code; `409` while the thermometer is off, once ended or at 20000 taps |
| `GET /sessions/{name}/polls` | | `200` `{"polls": [...]}`: every poll of the deck in its order, with its question, options and seconds, its count, its result once closed and a text poll's texts once closed (the only place, with the export, that holds them) |
| `GET /sessions/{name}/questions` | | `200` `{"questions": [...]}` in arrival order, each with the full device id and the `step` on screen when it was asked (#1716, #1718; `null` for a question kept before); `404` unknown |
| `GET /sessions/{name}/feedback` | | `200` `{count, average, comments: [{text, at}]}`, the comments in arrival order (a replaced answer keeps its place), no device (#1717); `404` unknown |
| `GET /sessions/{name}/export` | | `200` `{session, slides: [{name, title, text, notes, seconds?}], questions: [{slide, text, at}], feedback}`: the Session for an agent (#1718), each slide of its revision once in the deck's order (its English text and notes), each question under the slide on screen when it was asked, no device and no code; `404` unknown |
| `POST /codes/{code}/questions` | `{"device": "<uuid>", "text": "..."}` | `201` the question `{id, device, text, at, step}` (#1716), checked against the Session in the same step as it is written; `400` a device that is no UUID or a text empty or over 280 characters after the trim; `404` unknown code; `409` once ended or at 500 questions |
| `POST /codes/{code}/feedback` | `{"device": "<uuid>", "rating": 1-5, "comment": "..."}` | `201` a new answer, `200` one that replaced the device's earlier one, `{id, rating, comment, at, created}` (#1717), upserted per (Session, device) in the same step as the Session is checked; `400` a device that is no UUID, a rating that is no whole 1 to 5 or a comment over 280 characters after the trim (empty is none); `404` unknown code; `409` before the end or at 2000 devices |
| `DELETE /sessions/{name}` | | `204`; the code is free again |
| `GET /events` | | `text/event-stream`: one `event: step` per change, `data` the state; a `: hb` comment every 15 s |

The state of a Session:

```json
{"session": "platform-day", "presentation": "storytelling", "revision": "sha256:3f9c…",
 "code": "K7Q4", "step": 3, "steps": 24, "sequence": 7,
 "slide": {"title": "Why a platform", "message": "…"}}
```

`slide` is what a follower draws: the current slide's title and its message, read from the deck by the Nereid, never the deck's code. Since #1709 and #1710 the state also has `talk`, `questions`, `started`, `moved` (when the current slide came up), `ended`, `rehearsal` and `times`, since #1859 `sharing`, since #1723 `thermometer` and `gauge` (`{slow, fast}`, the taps of the last minute; the followers get `thermometer` only, never the counts), and since #1876 `questions_open` and `rating_open` (when the speaker opened the room's questions and rating, `null` before: the turns follow the speaker, never the talk's clock); `GET /codes/{code}` and the events leave `times` out, and the API sends a follower only the public fields.

- **The digest** is `sha256:` and the hex of the package's bytes as sent (a J1 revision: of its YAML).
- **The package** (#1701, `cli/src/nereus/deck_package.py`) is a deterministic tar (USTAR, entries sorted, no times or owners) of the deck's YAML, every file it names (diagrams, code frames, relative links, the `references/*.md` it cites; a link to another deck's `.html` carries that deck's YAML and diagrams) and a `package.json` manifest at the root: `{packageVersion: 1, outlineVersion, deck, files: [{path, sha256, size, origin}]}`, where `origin` is the file's path in its Git repository and its last commit, never a path of the machine. Its root is the closest folder that holds them all, so the YAML travels as written. The Nereid checks every member against the manifest (regular files, relative paths, no `..`), unpacks it in an empty folder, refuses a name that leaves it or a file it does not carry, and renders there. A J1 revision, the YAML alone, still parses, and is refused when it names a file.
- **The steps** are the deck's slides, in order.
- **The offline export** (#1703): the deck engine's own render without `--split`, one page with its style, script and diagrams inline and the speaker's notes, that opens from `file://` with the network off; the portal's CSP does not apply to it. A link to a reference file stays relative, as in the repository's own HTML.
- **The public link** (#1704): 26 characters of the code's alphabet (31^26, about 2^128: no rate limit is needed against guessing, though the follow routes' still applies), one per Presentation. It opens the latest revision, as a follower sees it (no notes), until `expires`; then `410`, and a new one is `link delete` and `link create` again. Deleting the Presentation deletes its link.
- **A dry run** (#1702): the CLI checks the outline's JSON Schema (#1700) before it sends anything, one `✗` line per error with its slide's name; then the Nereid checks what the schema cannot (links, references, the files the package carries, what the engine renders) and gives every reason. A message over 60 characters (docs/agent/decks.md, rule 3) is a warning, `!`, never a refusal: 242 messages of 25 decks of the repository break it.
- **The code** has four characters of `23456789ABCDEFGHJKMNPQRSTUVWXYZ` (no 0/O, 1/I/L), unique among the live Sessions.

## The Nereus API

| Route | Token | What it does |
|---|---|---|
| `POST /v1/presentations/presentations` | the reef | creates the Presentation, then puts the deck in its Nereid; `{"name", "package" | "folder" | "deck", "description"?, "source"?}`: `package` is the tar in base64 (1 MB counted on the tar), `folder` the files of a folder picked in the portal (#1705), `{"deck": its YAML's path, "files": {path: base64}}`, 4 MB at most, which the API packs as the CLI does, refusing a name that leaves the folder, `deck` the YAML as text from a CLI before #1701, which becomes a package of that YAML alone. `?dryRun=true` has the Nereid check the package (`POST /presentations/{name}/checks`) and writes nothing: `200` with `steps` and `warnings`, or `400 Invalid` with `errors`, every reason. A deck the Nereid refuses at create is the same `400`, and the object is deleted again |
| `GET /v1/presentations/presentations[/{name}]`, `DELETE …/{name}` | the reef | list, get, delete |
| `GET /v1/presentations/presentations/{name}/deck` | the reef, asked as an apply (the notes are in it) | the offline export (#1703): `nereus presentations presentation get <name> --output html` writes it as `<name>.html`; served as an attachment, sandboxed, with the follow page's headers |
| `POST /v1/presentations/presentations/{name}/link`, `DELETE …` | the reef, an apply | the public link (#1704): `{"expires": "30d"}` (hours, days or weeks from now, `h`/`d`/`w`, at most 9999) or no body for one that never expires; answers `{name, link, path: "/d/<link>", expires}`; `409 AlreadyExists` when the Presentation has one; `?dryRun=true` writes nothing |
| `GET /v1/presentations/presentations/{name}/link`, `GET /v1/presentations/links` | the reef | get (`404` with the fix `link create`), list |
| `GET /v1/presentations/links/{link}/deck` | none | the shared deck: the page leagore renders for a follower, with the follow page's sandboxed headers; `410 Expired` once expired, `404 not found` for any other link; limited per client as the follow routes |
| `POST /v1/presentations/sessions` | the reef | creates the Session, then `PUT /sessions/{name}` on the Nereid; answers the state and `follow: /p/<code>` |
| `GET /v1/presentations/sessions[/{name}]`, `DELETE …/{name}` | the reef | list, get (with the live step, the followers, the `slides` of every step, #1759, and the last rehearsal's `pace`, #1711), delete |
| `POST /v1/presentations/sessions/{name}/step` | the reef | drives: `{"step": n}`, answers the new state; `400` outside the slides, `404` unknown (#1696), `409 Refused` once ended (#1710) |
| `POST /v1/presentations/sessions/{name}/end` | the reef | the speaker's End (#1710): answers the state with `ended` |
| `POST /v1/presentations/sessions/{name}/sharing` | the reef | drives: `{"on": bool}`, the drive screen's "Show on the projector" in its Share sheet (#1859); answers the state with `sharing`, which the followers get, so the projector shows the follow QR code on any slide; `400 Invalid` anything but a boolean |
| `POST /v1/presentations/sessions/{name}/thermometer` | the reef | drives: `{"on": bool}`, the switch Pace thermometer in the drive screen's Share sheet (#1723), or `session create --thermometer` from the start; answers the state with `thermometer` and `gauge`; `400 Invalid` anything but a boolean |
| `GET /v1/presentations/sessions/{name}/thermometer` | the reef | drives: the gauge `{on, slow, fast}` (#1723), never cached; the drive screen reads it every 1.5 s while the thermometer is on and shows Too slow and Too fast with their counts; the projector shows nothing |
| `POST /v1/presentations/sessions/{name}/open` | the reef | drives: `{"part": "questions" \| "rating"}`, the Questions sheet's "Open questions" and the last step's "Ask the room to rate" (#1876); answers the state, which the followers get; `400 Invalid` another part, `409 Refused` the questions once ended |
| `POST /v1/presentations/sessions/{name}/polls/{poll}/open`, `POST /v1/presentations/sessions/{name}/polls/{poll}/close`, `GET /v1/presentations/sessions/{name}/polls` | the reef | drives: the drive screen's "Open question" on a poll slide (#1722), never by itself, its "Close question" and "Reopen question" (#1917), and the speaker's view of the polls with the texts; `404 NotFound` a poll the deck has not, `409 Refused` an open poll opened again, a poll not open closed, or an ended Session |
| `GET /v1/presentations/sessions/{name}/questions` | the reef | drives: the audience's questions in arrival order, each device by its six-character label only (#1716); the drive screen reads it every 5 s into its Questions sheet |
| `GET /v1/presentations/sessions/{name}/feedback` | the reef | drives: the audience's feedback once the rating opened or the Session ended (#1717, #1876), `{count, average, comments}`, the average to one decimal (`null` with no answer), no device; the drive screen shows it in its Questions sheet and `nereus presentations session get` under the Session |
| `GET /v1/presentations/sessions/{name}/export` | the reef | drives (the notes are in it): the Session for an agent (#1718), `{session: {name, presentation, revision, rehearsal, talkSeconds, questionsSeconds, started, ended}, slides: [{name, title, text, notes, seconds?, questions: [{text, at}]}], questionsWithoutSlide?, feedback, pace}`, `pace` the thermometer's taps by slide, `[{slide, slow, fast, peak}]` with `peak` the last tap of the slide's busiest minute (`null` with no tap), and the session's `thermometer` (#1723), only the contract's fields of the Nereid's answer, so no device id nor label; `nereus presentations session get <name> --output agent` prints it as YAML |
| `GET /v1/presentations/follow/{code}` | none | the SSE stream by short code (#1696): `state` first, then `step` events, `id` the sequence; `retry: 2000` first, an `event: hb` every 15 s with no event (a named event, since `EventSource` hides comments from the page's watchdog), `Last-Event-ID` replays from the last 64 events or sends `state`; the payload is only `code`, `step`, `steps`, `sequence`, `slide`; rate limited per client (`429` with `Retry-After`, also for unknown codes), a cap of followers per process (`503`, `NEREUS_PRESENTATIONS_FOLLOWERS_CAP`, default 2000); `404 not found` for an unknown code; each device's anonymous id (#1714: a random UUID the follow page keeps in `localStorage`, no login) comes in the `nereus_device` cookie, set on `/v1/presentations/follow/` only and never in the URL, and the followers are counted by distinct device; a log holds at most its six-character prefix |
| `POST /v1/presentations/follow/{code}/questions` | none | a follower's question (#1716), shown by the follow page at the questions' turn only, from `questions_open` until the end (#1876): `{"device", "text"}`, the text trimmed; `400 Invalid` empty or over 280 characters or a malformed device id, `413` a body over 4 KB, `404` an unknown code, `409 Refused` before the questions open or once ended; rate limited per client, then per device (`429` with `Retry-After`); a log holds the code and the device's six-character label, never the text |
| `POST /v1/presentations/follow/{code}/feedback` | none | a follower's rating once the speaker asked the room to rate or the Session has ended (#1717, #1876), shown by the follow page from then on: `{"device", "rating", "comment"}`; `201 created`, then `200 configured` when the device answers again (its answer replaced); `400 Invalid`, `413`, `404` as a question; `409 Refused` before either; rate limited per client, then per device, in buckets apart from the questions'; a log holds the code and the device's six-character label, never the comment |
| `POST /v1/presentations/follow/{code}/polls/{poll}/answers` | none | a follower's answer to an open poll (#1722): `{"device", "answer"}`; `201 created`, then `200 configured`; `400 Invalid` none of the options; `404` an unknown code or poll; `409 Refused` before it opens or after it closes; rate limited per client (`polls`, loose for a room behind one address), then per device (`poll`); the followers' state carries the count and, once closed, the result, never a text |
| `POST /v1/presentations/follow/{code}/pace` | none | a follower's tap (#1723): `{"device", "vote": "slow"\|"fast"}`; `200 configured` `{vote, at, fades}`, the follow page marks its own button until `fades`; `400 Invalid` another vote or a malformed device id; `404` an unknown code; `409 Refused` while the thermometer is off or once ended; rate limited per client (`taps`, loose for a room behind one address), then per device (`tap`) |

The follow link the CLI prints joins the installation's address with `/p/<code>`, the portal's public page (#1697). The public link (#1704) joins it with `/d/<link>`: the portal's `shared.html`, where anyone with the link moves through the deck on their own, with every control of the engine.

## The portal's screens (#1697)

Phone first: each screen is designed for 390 × 844, then checked at 1920 × 1080. All of them run under the portal's CSP, unchanged: no inline script or style, no `innerHTML`.

| Screen | Where | Token | What it does |
|---|---|---|---|
| Follow | `GET /p/<code>` on the portal (`follow.html`, `follow.js`, `follow.css`); the code is four characters of `23456789ABCDEFGHJKMNPQRSTUVWXYZ`, any other path under `/p/` is `404` | none | `EventSource` on `/v1/presentations/follow/<code>` (same origin, never through the portal's forward); draws "step n of N", the slide's title and message, only the last event of a burst; a quiet "reconnecting" mark; opens the stream again after 35 s with no event (an `EventSource` does not show the `: hb` comments, so only events reset the watchdog) |
| Projector | `GET /p/<code>?projector` | none | the same page in a large, full-screen layout, with a full-screen button (Fullscreen API, from a click) and, on the title slide and at the turn to the questions, the QR code of `/p/<code>` with the short code in large type (#1715); the deck rendered in the portal mode comes with its own sub-issue |
| Drive | the Sessions tab: leagore's contract publishes `nereus-presentations-drive` (`ui/drive.js`, asset `drive.css`) on `uiPort` 8083 | the person's | lists `GET /v1/presentations/sessions`, opens one (`GET …/sessions/{name}`), big Previous and Next: the screen moves at once and the step is posted to `…/sessions/{name}/step` in the background, in order, a refused one putting the screen back (#1759), the time spent against the Session's talk (a local timer from the first Next; J3 #1707 does it properly), the links `/p/<code>` and `/p/<code>?projector` |
| Decks | the Decks tab (#1705): leagore's contract publishes `nereus-presentations-decks` (`ui/decks.js`, asset `decks.css`) on the same `uiPort` | the person's | lists `GET /v1/presentations/presentations`; imports a deck from a file (a package `.tar`, or a YAML alone) or, where the browser has one, a folder (the chosen deck and the files it seems to name); Check posts `?dryRun=true` and shows the steps and warnings or every reason the Nereid gives; Create, open only after a clean check, posts the same body |

leagore's `uiPort` serves nothing but `ui/`: its Service has a second port and its NetworkPolicy opens it to the portal's pods alone, never the controller's port (decks and Sessions), as doris's.

## Security

- **A01 Broken Access Control:** every write needs a token with the reef, and driving a Session the right `drive` of the authorization reef, held by its speakers (#1726); the follow route is read-only and answers only the state of one Session, by its code; an unknown code says only "not found".
- **A04 Insecure Design:** the Nereid's Service admits only the API's pods; the code space (31⁴, about 923 thousand) is enumerable, so the follow route is rate limited per client and reveals no deck.
- **A05 Security Misconfiguration:** the portal keeps its CSP with no exception (#1693).
- **No personal data:** a follower is anonymous; logs carry the Session's name and code only.

## Stand-ins

- Any token with the reef drives (J6, #1725): retired by #1726, where only a Session's speakers, or a binding that gives `drive` on `presentations/sessions`, drive it.
- One API replica.
- leagore's memory store, for unit tests and scene-core only.
- Until #1695, the API's tests stand a fake Nereid in for leagore.
