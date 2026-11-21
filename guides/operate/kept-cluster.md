# Rebuild the kept cluster

Rebuild `k3d-nereus`, the kept cluster used as production, from nothing: the profile `internal-developer-platform` Ready, and Triton, the realm and the portal at their public hostnames.

!!! warning "The owner's job"
    An agent never deletes or recreates this cluster: the guard `.claude/hooks/guard-kept-cluster` refuses it. The rebuild loses OpenBao's secrets, Keycloak's database and the NATS streams of Triton's orders.

## Before you start

- A clone on `main`, and no scene of another session using the registry `localhost:5111`.
- `~/.config/nereus/google-keycloak.env`, exporting `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` of the Google OAuth client.
- The tunnel's credentials, `~/.cloudflared/<UUID>.json` from `cloudflared tunnel create nereus`, mode 0400: the one piece that cannot be made again without Cloudflare's dashboard. On a new machine, copy `~/.cloudflared/` and `~/.config/nereus/`.

## Steps

### 1. Build the CLI and every Nereid from the checkout

`nereus init` installs the images at the version of the `nereus` on the PATH, and `make nereids` tags them with the checkout's version, so build both from the same commit: `make cli`, then `make nereids`.

### 2. Delete and create the cluster

In the owner's terminal (in Claude Code, `!` first): `k3d cluster delete nereus`, then [`nereus init`](../../specs/cli/core.html#init-profile). About 9 minutes; the tenancy tree comes with it.

```bash
nereus init \
  --target k3d \
  --create-cluster \
  --name nereus \
  --profile internal-developer-platform \
  --yes
```

### 3. Log in as the initial admin

The realm answers at `http://auth.localhost:8080` from the start. [`nereus login --initial-admin`](../../specs/cli/reefs/authentication.html#login-initial-admin) reads the admin's password with your kubeconfig.

```bash
nereus login --initial-admin
```

### 4. Bring up the tunnel

Apply the edge reef and its Nereid `cloudflare` ([Publish at a hostname](edge.md)), keep the credentials file as the secret `edge/cloudflare-tunnel`, then create the Mandate with `--param tunnel=nereus --param credentialsSecret=edge/cloudflare-tunnel --default`. Create the three routes at once: until a Route exists, the tunnel answers 404.

```bash
nereus edge route create triton --hostname triton.getnereus.dev
```

Repeat for `auth` and `portal`.

### 5. Trust the tunnel at the ingress gateway

`numTrustedProxies: 1` keeps cloudflared's `X-Forwarded-Proto: https`, so Keycloak's issuer stays `https://`. Write the Release `istio-gateway` with `--values-file deploy/ingress/istio-gateway-values.yaml --dry-run --output yaml`, [`nereus release apply`](../../specs/cli/reefs/release.html#release-apply) it, then `kubectl apply --filename deploy/ingress/gateway.yaml`.

### 6. Put Google in the realm

Only once the tunnel answers. Source the env file, keep the pair as the secret `google-oauth-keycloak`, then apply the Mandate; `mandate apply` replaces every param, so all go together. Then `nereus logout` and `nereus login` at the public realm.

```bash
nereus mandate apply keycloak \
  --reef authentication \
  --nereid keycloak \
  --param publicUrl=https://auth.getnereus.dev \
  --param googleSecret=google-oauth-keycloak \
  --param googleUsers=owner@example.com \
  --param googleAdmins=owner@example.com
```

### 7. Set the portal's address and bring up Triton

[`nereus mandate apply`](../../specs/cli/core.html#mandate-apply) `nereus-portal` with `--param publicUrl=https://portal.getnereus.dev`. Then the Mandate `messaging-nats` with `--param agents=true` holds Triton's account; `nereus nereid apply nats --reef messaging` writes it into NATS, and `nereus nereid apply triton --reef messaging` sets `TRITON_ISSUER`, `TRITON_JWKS_URL` and `TRITON_RESOURCE_URL`.

Every other login is gone with the old realm: the claude.ai connector `Triton` signs in again, and a token saved from the old realm no longer works.

## Check it worked

[`nereus status`](../../specs/cli/core.html#status) shows every reef Ready; `curl` on `https://triton.getnereus.dev/healthz` and `https://portal.getnereus.dev/` answers 200, and the realm `master` answers 404 from outside.

```bash
nereus status
```

``` { .text .output title="output" }
REEF            NEREID           VERSION  STATUS  AGE
authentication  keycloak         0.1.0    Ready   7m
catalog         catalog          0.1.0    Ready   1m
core            built-in         0.1.0    Ready   9m
database        cloudnative-pg   0.1.0    Ready   7m
delivery        kubernetes       0.1.0    Ready   1m
environment     vcluster         0.1.0    Ready   1m
metrics         victoriametrics  0.1.0    Ready   3m
portal          nereus-portal    0.1.0    Ready   3m
registry        zot              0.1.0    Ready   1m
release         flux             0.1.0    Ready   7m
secrets         openbao          0.1.0    Ready   9m
tenancy         -                -        Ready   9m
Registry  localhost:5111
```

## Next

- [Update the kept cluster without a rebuild](kept-cluster-update.md): one Nereid, or the API.
- [Deploy main to the live cluster](deploy-live.md).
