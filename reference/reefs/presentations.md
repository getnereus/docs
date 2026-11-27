# The presentations Reef

The first slice: a deck kept by the platform, and a Session a phone drives and a room follows.

## Commands

- [`nereus reef apply presentations`](../../specs/cli/reefs/presentations.html#reef-apply) The presentations Reef brings decks and sessions
- [`nereus presentations schema list`](../../specs/cli/reefs/presentations.html#schema) A deck is written anywhere, against a published schema
- [`nereus presentations presentation create storytelling`](../../specs/cli/reefs/presentations.html#presentation-create) A deck travels as a package the platform keeps by its digest
- [`nereus presentations presentation get storytelling`](../../specs/cli/reefs/presentations.html#presentation-export) The deck goes home as one file that opens offline
- [`nereus presentations link create storytelling`](../../specs/cli/reefs/presentations.html#link-create) A public link opens the deck for anyone, until it expires
- [`nereus presentations session create platform-day`](../../specs/cli/reefs/presentations.html#session-create) A Session gives the link a room follows
- [`nereus presentations session get platform-day`](../../specs/cli/reefs/presentations.html#session-get) A Session shows its step and its link
- [`nereus presentations session list`](../../specs/cli/reefs/presentations.html#list-delete) Ending a Session frees its code

## Examples

### reef-apply

The kinds of the Reef; its Nereid, leagore, comes in #1695.

```bash
nereus reef apply presentations
```

``` { .text .output title="output" }
✓ core/reefs/presentations created (presentations.getnereus.dev/v1alpha1: presentations, sessions)

Next steps:

  nereus presentations --help
```

### schema

The outline versions, and where the Nereus API serves each with no token.

```bash
nereus presentations schema list
```

``` { .text .output title="output" }
OUTLINE VERSION  URL
1                https://nereus.example.com/v1/presentations/schemas/outline/1.json
```

### presentation-create

The deck and every file it names, at most 1 MB; the object holds only its digest.

```bash
nereus presentations presentation create storytelling \
  --from talks/storytelling.yaml
```

``` { .text .output title="output" }
✓ presentations/presentations/storytelling created, revision 1 (sha256:3f9c2a71)
  copied 8 references and 1 file from outside the folder, origin recorded

Next steps:

  nereus presentations session create <name> --presentation storytelling --talk 30m
```

### presentation-export

The latest revision, with its notes, as one self-contained HTML file.

```bash
nereus presentations presentation get storytelling \
  --output html
```

``` { .text .output title="output" }
✓ storytelling.html written (revision sha256:3f9c2a71, opens offline)
```

### link-create

A link anyone can open for thirty days, no login.

```bash
nereus presentations link create storytelling \
  --expires 30d
```

``` { .text .output title="output" }
✓ presentations/presentations/storytelling link created
  public: https://nereus.example.com/d/9FK2PQ7XMZ4HR8TV3WKN6PQ2JD (expires 2026-12-17)

Next steps:

  nereus presentations link delete storytelling
```

### session-create

A talk of thirty minutes, on the revision fixed now.

```bash
nereus presentations session create platform-day \
  --presentation storytelling \
  --talk 30m
```

``` { .text .output title="output" }
✓ presentations/sessions/platform-day created (revision sha256:3f9c2a71)
  follow: https://nereus.example.com/p/K7Q4

Next steps:

  nereus presentations session get platform-day
```

### session-get

The step is the Nereid's live one; the followers count arrives with the follow stream (#1696).

```bash
nereus presentations session get platform-day
```

``` { .text .output title="output" }
NAME          PRESENTATION  STEP  FOLLOWERS  FOLLOW
platform-day  storytelling  0/24  0          https://nereus.example.com/p/K7Q4
```

### list-delete

Every Session.

```bash
nereus presentations session list
```

``` { .text .output title="output" }
NAME          PRESENTATION  TALK  CODE  STEP  AGE
platform-day  storytelling  30m   K7Q4  0/24  5m
```
