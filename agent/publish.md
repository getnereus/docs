# Publishing on ghcr.io

`make promote` (#850, #1271) copies the seed images and the charts to `ghcr.io/getnereus/nereus` by digest. A package it creates there starts **private**, and only a person can make it public, once, in GitHub's UI (#1338).

```console
$ GHCR_USER=maria GHCR_TOKEN=... make promote
✓ ghcr.io/getnereus/nereus/forgejo-controller@sha256:...
! 1 package(s) answer only with a credential: GHCR creates a new package private, and its API cannot
  make it public (#1338). Once per package, open its settings, Danger Zone, Change visibility, Public (irreversible):
  ghcr.io/getnereus/nereus/forgejo-controller: https://github.com/orgs/getnereus/packages/container/nereus%2Fforgejo-controller/settings
  next: make promote CHECK=1 finds every one with no credential
```

Then check with no credential, as anyone pulling does: a private package fails with its settings link.

```console
$ make promote CHECK=1
✗ ghcr.io/getnereus/nereus/forgejo-controller:0.1.0 is private: make it public at https://github.com/orgs/getnereus/packages/container/nereus%2Fforgejo-controller/settings (Danger Zone, Change visibility, Public)
```

## Publishing a release

A release is published from `main`'s HEAD and tagged there by one command (#1350), with no version-bump commit and no release branch: a merge to `main` is what gets published.

```console
$ git switch main && git pull --ff-only
$ scripts/registry/release publish --dry-run
  would publish 0.1.7 from 3f1c2ab (main, after v0.1.6)
  ...
  flux-controller: :src-a17c9b3e01f2 exists, would reuse sha256:3c1e...
  doris-controller: inputs changed, would build :src-4f1e2d0c9a88
  nereus-api: platform image, would build at 0.1.7
  3 to build, 22 reused
$ GHCR_USER=maria GHCR_TOKEN=... make release
building at 0.1.7 from 3f1c2ab (main)
...
promoted the images and the charts to ghcr.io/getnereus/nereus (cli/src/nereus/charts/nereus/images.lock packaged into the chart nereus)
built 3 image(s), reused 22; tagged and pushed v0.1.7 on 3f1c2ab
ok: promote CHECK=1 finds every package with the same digest
```

- **The version:** the next patch after the highest tag `v*`, reachable from `main` or not (`v0.1.6` sits on its old release branch's commit); `--version` names another.
- **Git keeps no version and no digest** (#186): the CLI reads its version from the tag (hatch-vcs: `0.1.7` on `v0.1.7`, `0.1.8.devN` after it, `nereus --version`), and so do the images, so the publish tags HEAD locally before the build, checks the CLI reads it, and deletes the tag if it fails before the push. The charts say `0.0.0-dev` in git: their version is set in the working tree for the packaging only and put back when it ends.
- **Every image by digest** (#1351): `make promote ONLY=images LOCK=<file>` writes `images.lock` into the chart `nereus`, one line per image, `<name>=<repository>:<tag>@sha256:<digest>`, the digest the target answered after the copy; the release packages it with the chart and removes it at the end (git ignores it). The chart runs the API and thetis as `<repository>@<digest>`, with no tag, and writes each Nereid's image into the Profile the same way, so a tag moved on ghcr.io changes nothing that runs, and an unchanged image keeps its Pod spec (#1574). A chart from git has no lock: it needs `image` and `thetis.image` given, and images built by hand (`nereids.registry=localhost:5111`, or `nereids.tag` given) keep their tag. `make scene-helm-ghcr` fails on any Deployment that runs a `ghcr.io/getnereus/nereus` image with no digest.
- **Only what changed is built** (#1574): one platform version for people, and each image tagged by its inputs too, `:src-<hash>` (`make image-inputs`, `scripts/registry/image-inputs`): a sha256 of `git ls-tree` of its folder (and `lib/nereid/` when built with nereid-sdk) and its build arguments, at the committed tree. An image whose `:src-<hash>` the target already holds is reused: promote tags its digest with the new version too and the lock names that digest, so its Pod spec does not change and its Pod is not restarted. The API and thetis install the CLI at the release's version, so they are built every time. A reused image keeps the version label it was built at: the version in which it last changed. `make release REBUILD=1` builds every one, for a base image's update (#1604).
- **It refuses** another publish holding the lock (a `flock` in the clone's git dir), a working tree with changes, a branch other than `main`, a HEAD that is not the remote's `main`, a version already tagged, a CLI that does not read the new tag, and nothing to publish since the last tag (no change under `api/`, `controllers/`, `lib/`, `cli/src/` or the `Makefile`).
- **The check again, later:** `make promote CHECK=1` on the tagged commit, with the `IMAGES=` and `REUSE=` the release printed (the reused images are not in the local registry), finds the images and the charts published at the tag by the digests the release pushed to the local registry (the charts say `0.0.0-dev` in git, so their files cannot be compared there): a chart changed at the right version answers another digest and fails.
- **Plain git only:** the remote is `NEREUS_RELEASE_REMOTE` (default `origin`) and the destination `NEREUS_PROMOTE_TARGET`; nothing in it calls `gh`.
- The first real publish of each new way of publishing waits for the owner's go (#1559's envelope).

## Publishing the CLI

After `make release`, an optional step publishes the CLI to the public repository `getnereus/install` (#1782), where anyone on Linux installs it with `curl -fsSL https://getnereus.github.io/install/install.sh | sh`: one GitHub Release per version, `v<x.y.z>`, with the wheel, `latest.json` (`version`, `wheel`, `sha256`) and `install.sh`. `make release` does not run it.

```console
$ make cli-publish
built nereus-0.1.22-py3-none-any.whl at v0.1.22 (9d0e886): 222 files, every file of cli/src/nereus/ inside
wrote /tmp/nereus-cli-publish.Ab12Cd/latest.json: {"version": "0.1.22", "wheel": "https://github.com/getnereus/install/releases/download/v0.1.22/nereus-0.1.22-py3-none-any.whl", "sha256": "627c..."}
dry run: nothing changes on GitHub (--publish runs it)
  would run: gh release create v0.1.22 ... --repo getnereus/install --title nereus\ 0.1.22 ... --latest
  would commit install.sh index.html README.md .nojekyll of deploy/install/ to getnereus/install's default branch when they changed, and push
$ make cli-publish PUBLISH=1
```

- **The wheel** is built at the tag (`VERSION=0.1.N`, default the highest tag `v*`) in a throwaway git worktree, so hatch-vcs reads the version from the tag; the script refuses a wheel whose name or `METADATA` says another version, or that misses any file of `cli/src/nereus/` (the charts, CRDs, manifests, assets and the reefs and tree it links).
- **The charts inside the wheel are git's** (`0.0.0-dev`, no `images.lock`): only the charts `make release` pushes to ghcr.io carry the version and the digests.
- **Once, first:** `make cli-publish SETUP=1` says how it would create `getnereus/install` public, push `deploy/install/` (`install.sh`, `index.html`, `README.md`) to its default branch and turn on GitHub Pages from its root; `SETUP=1 PUBLISH=1` does it.
- **It refuses** a tag that does not exist and a release that exists, unless `FORCE=1`, which replaces its files. The credential is the gh CLI's.
- **The check:** `make cli-install-test` (about 30 seconds, docker and the network) builds the wheel from the working tree at a throwaway tag, serves it with `python3 -m http.server`, runs `install.sh` in a clean `ubuntu:24.04` container and requires `nereus --version` to print that version; a wrong sha256 installs nothing.
- The first real publish waits for the owner's go.

## Publishing the docs

The docs site is published to the public repository `getnereus/docs` (#2016), which holds only the built site, and GitHub Pages serves it from the root of its default branch at `https://docs.getnereus.dev/`. CI is off, so it is published from a workstation, the way the CLI is.

```console
$ make docs-publish
built the docs at 879cc0e (240 pages, 632 files, 36M) into /tmp/nereus-docs-publish.Ab12Cd/site
wrote CNAME: docs.getnereus.dev
dry run: nothing changes on GitHub (--publish runs it)
  would commit 37 changed files of the site to getnereus/docs's main, and push
$ make docs-publish PUBLISH=1
pushed 879cc0e to getnereus/docs: https://docs.getnereus.dev/
```

- **The build** is `make docs-build`'s (mkdocs `--strict`, so a warning fails it) into a temporary folder, never `site/` in the checkout; `CNAME` and `.nojekyll` are written into it.
- **It refuses** a working tree with changes on `PUBLISH=1`: each publish is one commit `docs: <commit>` naming the source commit, and the history is kept (a few MB per publish; revisit if the repository passes 1 GB). A page the docs drop leaves the repository too.
- **Once, first:** `make docs-publish SETUP=1` says how it would create `getnereus/docs` public, push the site, turn on GitHub Pages from `main`'s root with the custom domain and enforce HTTPS; `SETUP=1 PUBLISH=1` does it. HTTPS is enforced only once GitHub has issued the domain's certificate, minutes after the DNS record answers: run it again then.
- **The DNS record,** by hand once in the Cloudflare zone of `getnereus.dev`: `docs` `CNAME` `getnereus.github.io`, **DNS only** (no proxy, so GitHub can issue the certificate). Made on 2026-11-21; the cloudflare Nereid takes it over with #577.
- **The check:** `test/docs-publish-test` (in `make test`) runs the script against a fake `gh` and a bare repository; after a real publish, `curl -sS https://docs.getnereus.dev/llms.txt` answers 200.
- `repo_url` and `edit_uri` in `mkdocs.yml` answer 404 to a reader until #9 opens `getnereus/nereus`.

Stand-in: the docs published from a workstation to GitHub Pages, until the platform builds and serves its own docs (#24, #577).

## The gh CLI's token as the credential

`make release` and `make promote` can take the gh CLI's token as `GHCR_TOKEN`, with no separate credential, when it holds the `write:packages` scope. Check it with `gh auth status`, which lists the `Token scopes`; when the scope is missing, add it with `gh auth refresh --scopes write:packages`.

```console
$ GHCR_USER=maria GHCR_TOKEN="$(gh auth token)" make release
```

Never print the token: at most its first 3 characters (`${GHCR_TOKEN:0:3}`). Found while publishing 0.1.14 (#1755).

## The published release's check

Once every package answers with no credential, `make scene-core FROM=ghcr` (#1464) installs what was published, as a person does: a k3d cluster made by hand, the charts `nereus-reefs` and `nereus` from `oci://ghcr.io/getnereus/nereus/charts` at the highest tag's version (`NEREUS_CHART_VERSION` names another) with helm, and thetis pulling the reference Nereids from ghcr.io, then the core's checks of `make scene-core`, in a few minutes.

It is what a release names next, recorded in `docs/checks/scene-core-ghcr.json`. `make scene-helm-ghcr`, with every real tool (about 20 minutes), runs only on the owner's word (#1420's level 4).

## Why a click

- GitHub creates every new package private, and its REST API has no call to change a package's visibility ([Configuring a package's access control and visibility](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility)).
- A package linked to a repository "inherits the access permissions (but not the visibility) of the linked repository" (the same page), and `getnereus/nereus` is private until a first version (#9), so linking cannot make a package public.
- Public is irreversible: "Once you make a package public, you cannot make it private again." Only the owner's go makes a package public.

## The link to the repository

Every published image carries `org.opencontainers.image.source=https://github.com/getnereus/nereus` (the Makefile's `IMAGE_SOURCE_LABEL`), and each chart's `sources` in `Chart.yaml`, which Helm writes as the same OCI annotation. GHCR links the package to the repository, so it shows there and inherits the repository's access, which a publish with the repository's token (#1250) needs.

Stand-in: the click per new package, until GitHub exposes a package's visibility in its API or the repository is public.
