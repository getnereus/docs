# Update the kept cluster without a rebuild

Move one Nereid, or the Nereus API and its charts, of the kept cluster `k3d-nereus` to a new build, keeping the Installation and every reef, Nereid and secret.

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

```bash
nereus init \
  --target k3d \
  --name nereus \
  --profile internal-developer-platform \
  --yes
```

``` { .text .output title="output" }
✓ kinds               2.4s  release nereus-reefs revision 2, gateway-api/v1.7.0 unchanged (the Gateway API CRDs)
✓ nereus              1.5s  release nereus revision 2, profile internal-developer-platform, images localhost:5111 at 0.1.40
✓ installation        0.2s  kept nereus
```

### 5. Move each Nereid that should change

thetis never changes an image already there, so the Profile stays not Ready, naming the first Nereid whose digest differs. Move each one as in steps 2 and 3.

## Check it worked

[`nereus nereid list`](../../specs/cli/core.html#nereid-list) shows each Nereid Ready with the image you applied, and [`nereus status`](../../specs/cli/core.html#status) shows every reef Ready.

## Next

- [Rebuild the kept cluster](kept-cluster.md) when an in-place update is not enough.
- [Get a reef's commands working again](../troubleshoot/nereid-stops.md) when a Nereid has no pod serving.
