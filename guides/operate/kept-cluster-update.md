# Update the kept cluster without a rebuild

Move one Nereid, or the Nereus API and its charts, of the kept cluster `k3d-nereus` to a new build, keeping the Installation and every Reef, Nereid and secret.

## Before you start

- The kept cluster of [Rebuild the kept cluster](kept-cluster.md), and a clone on `main`.
- No scene of another session using the registry `localhost:5111`.

## Steps

### 1. Build one Nereid's image

Build it from `main` under the tag the cluster runs, then push it: `make nereid-sdk`, then `docker build --build-arg API_GROUP=core.getnereus.dev --build-context nereid-sdk=lib/nereid/dist --tag localhost:5111/keycloak-controller:0.1.0 controllers/keycloak`, then `docker push` that tag. `make nereids NEREIDS=keycloak` builds the same image but also rebuilds the API and thetis.

### 2. See what changes

[`nereus nereid apply --image`](../../specs/cli/core.html#nereid-apply-image) with `--dry-run` compares the digest the Deployment pins with the new one.

```bash
nereus nereid apply keycloak \
  --image localhost:5111/keycloak-controller:0.1.0 \
  --dry-run
```

``` { .text .output title="output" }
Would configure core/nereids/keycloak for reef authentication: image sha256:7daa642492a8 → sha256:3a50a7f56b45.
Nothing changed (--dry-run).
```

### 3. Apply it in place

The Deployment pins the new digest, and the Nereid's next pass applies what changed. Triton is a Nereid too, so it moves the same way.

```bash
nereus nereid apply keycloak \
  --image localhost:5111/keycloak-controller:0.1.0
```

### 4. Move the API and the charts

Run `make cli`, then `make nereids`, so the CLI and the images share a version. [`nereus init`](../../specs/cli/core.html#init) without `--create-cluster` upgrades the charts `nereus-reefs` and `nereus` in place; the API is ready a few seconds after the `nereus` line.

When the registry lacks an image at the CLI's version (`make cli` ran again after `make nereids`), init stops at its `images` step, before the `nereus` line, and changes nothing:

``` { .text .output title="output" }
✗ images                    0.0s
  total                     0.0s  slo 8m, 0% green
✗ 2 images the release names are not in their registry: nereus-api, thetis
  nereus-api  localhost:5111/nereus-api:0.1.41.dev146
  thetis      localhost:5111/thetis-controller:0.1.41.dev146
  fix         make nereids
```

Run the `fix` line, then init again. A Pod that cannot pull its image anyway (`ImagePullBackOff`) stops the `ready` step at once, naming the Pod, its image and the same `fix`, instead of waiting for the step's timeout of 30 minutes.

```bash
nereus init \
  --target k3d \
  --name nereus \
  --profile internal-developer-platform \
  --yes
```

The output below is what `test/scene-core-upgrade` prints on its cluster, profile `reference`, after one Nereid was applied by hand: only that one stops, and the other six already run their new digests.

``` { .text .output title="output" }
✓ kinds          1.2s  release nereus-reefs revision 2
✓ nereus         3.3s  release nereus revision 2, profile reference, images localhost:5111 at 0.1.41.dev129-nereus-scn-2031-9bab4b-next
✓ installation   0.3s  kept nereus-scn-2031-9bab4b
✗ ready         1m32s
  total         1m37s  slo 8m, 20% green
✗ the cluster's Nereids keep their images: thetis does not change an image that is already there
  reference-secrets  localhost:5111/reference-secrets-controller@sha256:0de294bd2444 → @sha256:780a0ec273e5
  fix                nereus nereid apply reference-secrets --reef secrets --image localhost:5111/reference-secrets-controller@sha256:780a0ec273e5ca09d10175bb3835eb75e899fbc34f2718c5a795bd8e79b71a93
```

thetis moves in place every Nereid whose image it installed itself: it records that image on the Nereid (the annotation `core.getnereus.dev/profile-image`), and while the Nereid still runs it, the new one replaces it. When nothing stops it, init's `ready` line counts them (`7 Nereids ready, 6 moved by thetis`).

A Nereid whose image was applied by hand, as in step 3, keeps it: thetis marks its step `Blocked`, reason `ImageApplied`, and the Profile's Ready condition says `ImageApplied`.

init stops as soon as it reads that, instead of waiting for its timeout, and names only those Nereids; the API, the charts and the Nereids it moved stay as they are. [`nereus doctor`](../../specs/cli/core.html#doctor) shows the same list in its `profile` row.

A Profile that names an image its registry lacks moves nothing either. thetis reads each image before it applies a Nereid: the step is `Blocked`, reason `ImageMissing`, with the image, and the steps after it go on, so a Nereid already there keeps its own. The Profile's Ready condition says `ImageMissing`; init stops at once and adds the fix:

```text
✗ ready          2 Nereids name an image the registry lacks: database, secrets
  database  localhost:5111/database-controller:0.1.41.dev146
  secrets   localhost:5111/secrets-controller:0.1.41.dev146
  fix       make nereids
```

`nereus doctor`'s `profile` row says the same, with the same fix, before any image a Nereid keeps.

A registry that does not answer leaves the step `Waiting` for the next pass.

A Nereid installed before thetis recorded its images has no annotation, so the first update after it lists every such Nereid once; their `fix` lines adopt them, and the next update moves them.

### 5. Move each Nereid applied by hand that should change

Run each `fix` line init printed, as in steps 2 and 3. thetis's next pass finds every image as the Profile names it, records it, and the Profile turns Ready.

## Check it worked

[`nereus nereid list`](../../specs/cli/core.html#nereid-list) shows each Nereid Ready with the image you applied, and [`nereus status`](../../specs/cli/core.html#status) shows every Reef Ready.

## Next

- [Rebuild the kept cluster](kept-cluster.md) when an in-place update is not enough.
- [Get a Reef's commands working again](../troubleshoot/nereid-stops.md) when a Nereid has no pod serving.
