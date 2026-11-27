# Start a new Nereid

Render a new [Nereid](../../concepts/model.md) from the template: a skeleton that already reports `Ready`, serves its metrics and passes its tests, so you only write the Tool's work.

## Before you start

- A checkout of Nereus, with `uv` on the `PATH`: the template runs through [Copier](https://copier.readthedocs.io/), pinned and run by `uvx`, so there is nothing else to install.
- The Reef the Nereid looks after, and the Tool it drives: here the `edge` Reef and Caddy.

## Steps

### 1. Render the skeleton

`scripts/nereid/new` renders `templates/nereid` into `controllers/<tool>/` and refuses a folder that exists.

```bash
scripts/nereid/new --reef edge --tool caddy
```

``` { .text .output title="output" }
✓ controllers/caddy/ created from templates/nereid (copier 9.19.1)
  server.py            the reconcile loop on nereid-sdk, Ready, status.kinds, GET /metrics, the commands' HTTP server
  kube.py              the Kubernetes API, standard library
  requirements.txt     nereid-sdk==0.6.0 (#754), pinned
  Dockerfile           edge-caddy-controller, nereid-sdk from the build context (#741)
  README.md            what the Nereid does, and what every Nereid must do
  test_server.py       the loop's tests, a failing pass counted with its reason
  .copier-answers.yml  the answers, for copier update
Next steps:
  add caddy to NEREIDS in the Makefile, its tests and lint to make test and make lint
  make nereids
  nereus nereid apply caddy --reef edge --image localhost:5111/caddy-controller:0.1.0
```

By default it serves the kind `<reef>s`; `--kinds hostnames,certificates` names the Reef's kinds it serves instead.

### 2. Write the Tool's work

The Tool's work goes in `reconcile()` of `server.py`. The generated `README.md` lists what every Nereid must do: serve every verb of every kind of its Reef, with the status its contract declares.

### 3. Wire it into the build

Add `caddy` to `NEREIDS` in the `Makefile`, and its tests and lint to `make test` and `make lint`, as the skeleton's next steps say.

### 4. Take a later change of the template

From the root of a clean checkout, Copier brings a change of the template as a diff that keeps the Nereid's own changes:

```bash
uvx copier==9.19.1 update \
  --defaults \
  --vcs-ref HEAD \
  controllers/caddy
```

## Check it worked

The skeleton's tests run on the library of the checkout, as the other Nereids' do in `make test`:

```bash
uv run --project cli --with lib/nereid pytest -q controllers/caddy
```

``` { .text .output title="output" }
..............                                                           [100%]
14 passed in 0.18s
```

`make nereid-check`, part of `make test`, fails when a Nereid does not pin `nereid-sdk` at the version of `lib/nereid/pyproject.toml`, in `requirements.txt` and in its `Dockerfile`, or does not import `nereid.held`, or rewrites a `Ready` condition's `lastTransitionTime` (below).

A Nereid lists its objects through `held.actionable(items)`, so it never acts on a held object (ADR 0031: no status, no finalizer while the Nereus API's hold is on, #2214). The skeleton does already; `scripts/nereid/held-allowlist` names the Nereids not adopted yet, a list that only shrinks.

A Nereid sets each object's `Ready` condition through `operations.ready(item, status, ready, reason, message, now)`, which keeps the stored `lastTransitionTime` while `Ready`'s status stays the same, so a pass that changes another field never moves it (#2242).

`make nereid-check` fails on a Nereid that compares statuses without `lastTransitionTime` (the mark of a status built with `now`) and does not import `nereid.operations`; `scripts/nereid/ready-allowlist` names the ones not adopted yet, a list that only shrinks.

## Next

- [Build a Nereid's image](image.md), with the labels that name its Reef, and apply it.
- [Require a Reef](requires.md) when the Nereid needs another Reef's work.
- [Pass the conformance tests](conformance.md): every verb of every kind of its Reef.

## Learn more

- [Reef, Nereid and Mandate](../../concepts/model.md): what a Nereid looks after.
- [Spec 0003](../../specs/0003-nereid-conformance.md): the contract a Nereid honours.
