# Run its commands

Use the `release` group the reference Nereid published: add a Helm repository and list it.

## Run

See the group's commands; the CLI built them from what the Nereid published, with no code downloaded:

```bash
nereus release --help
```

It lists one group per kind of the Reef: `repository`, `source` and `target`, next to the releases themselves.

Add a Helm repository: [`nereus release repository create`](../specs/cli/reefs/release.html#repository-create)

```bash
nereus release repository create codecentric \
  --url https://codecentric.github.io/helm-charts \
  --type http
```

``` { .text .output title="output" }
✓ release/repositories/codecentric created
NAME         TYPE  URL                                        READY
codecentric  http  https://codecentric.github.io/helm-charts  True

Next steps:

  nereus release source create <name> --repository codecentric --chart <chart> --version <version>
```

List the repositories: [`nereus release repository list`](../specs/cli/reefs/release.html#repository-list)

```bash
nereus release repository list
```

``` { .text .output title="output" }
NAME         TYPE  URL                                        READY
codecentric  http  https://codecentric.github.io/helm-charts  True
```

## What you get

- A `Repository` object in the cluster, `Ready`: the reference Nereid answered it with no tool behind it.
- The group is named after the Reef, not the Nereid: another Nereid of `release` would serve the same commands ([Reef, Nereid and Mandate](../concepts/model.md)).

## Next

[Clean up](clean-up.md) when you are done.
