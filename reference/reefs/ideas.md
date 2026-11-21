# The ideas reef

The owner's classified notes, served inside the cluster for Tide.

## Commands

- [`nereus reef apply ideas`](../../specs/cli/reefs/ideas.html#reef-apply) The ideas reef, with no kinds
- [`nereus nereid apply doris`](../../specs/cli/reefs/ideas.html#nereid-apply) The doris Nereid reads the node's notes folder
- [`nereus mandate apply doris`](../../specs/cli/reefs/ideas.html#mandate-apply) The source and the readers, then the count of notes

## Examples

### reef-apply

No contract to pin: a reef with no kinds is made from its name.

```bash
nereus reef apply ideas
```

``` { .text .output title="output" }
✓ core/reefs/ideas created (ideas.getnereus.dev/v1alpha1)

Next steps:

  nereus ideas --help
  nereus nereid apply <nereid> --reef ideas
```

### nereid-apply

The node's /var/lib/doris/notes, read-only in its Pod.

```bash
nereus nereid apply doris \
  --reef ideas
```

``` { .text .output title="output" }
✓ core/nereids/doris created, Ready, pinned to sha256:3c1d2e4f5a6b: see 'nereus ideas --help'
  core/mandates/doris created (reef: ideas, nereid: doris, default)

Next steps:

  nereus mandate apply doris --reef ideas --nereid doris --param source=/var/lib/doris/notes --param readers=ideas-readers
```

### mandate-apply

readers names the group the Nereus API lets see the notes (#1107).

```bash
nereus mandate apply doris \
  --reef ideas \
  --nereid doris \
  --param source=/var/lib/doris/notes \
  --param readers=ideas-readers
```

``` { .text .output title="output" }
✓ core/mandates/doris configured (reef: ideas, nereid: doris, default)

Next steps:

  nereus mandate list
```
