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

In the owner's terminal (in Claude Code, `!` first): `k3d cluster delete nereus`, then [`nereus init`](../../specs/cli/core.html#init-profile), which sets the [time zone](../reefs/usage.md#3-cut-the-days-where-you-live). About 9 minutes; the tenancy tree comes with it.

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

### 4. Bring up the tunnel and trust it at the ingress gateway

Apply the edge Reef and its Nereid `cloudflare` ([Publish at a hostname](edge.md)), keep the credentials file as `edge/cloudflare-tunnel` and an API token (DNS Edit on the zone, Tunnel Read) as `edge/cloudflare-token`, then create the Mandate with `--param tunnel=nereus --param credentialsSecret=edge/cloudflare-tunnel --param apiTokenSecret=edge/cloudflare-token --default`. Create the routes at once.

```bash
nereus edge route create triton --hostname triton.getnereus.dev
```

Repeat for `auth`, `portal` and `api`; the Nereid makes each CNAME. The chart's API route answers only at `localhost`; this one adds `portal` and `api`:

```bash
kubectl apply --filename deploy/ingress/nereus-api-public.yaml
```

Give the Installation its public address (#2291):

```bash
nereus config installation set --public-url https://api.getnereus.dev
```

The CLI and the MCP then use `api.` (#2248).

`numTrustedProxies: 1` keeps cloudflared's `X-Forwarded-Proto: https`, so Keycloak's issuer stays `https://`. Write the Release `istio-gateway` with `--values-file deploy/ingress/istio-gateway-values.yaml --dry-run --output yaml`, [`nereus release apply`](../../specs/cli/reefs/release.html#release-apply) it, then `kubectl apply --filename deploy/ingress/gateway.yaml`.

### 5. Put Google in the realm

Only once the tunnel answers. Source the env file, keep the pair as the secret `google-oauth-keycloak`, then apply the Mandate; `mandate apply` replaces every param, so all go together. Then `nereus logout` and `nereus login` at the public realm.

```bash
nereus mandate apply keycloak \
  --reef authentication \
  --nereid keycloak \
  --param publicUrl=https://auth.getnereus.dev \
  --param googleSecret=google-oauth-keycloak \
  --param googleUsers=owner@example.com \
  --param googleAdmins=owner@example.com \
  --param googleTeam=teammate@example.com
```

`googleTeam` is Triton's team; each person then runs `nereus login https://api.getnereus.dev`.

### 6. Set the portal's address and bring up Triton

[`nereus mandate apply`](../../specs/cli/core.html#mandate-apply) `nereus-portal` with `--param publicUrl=https://portal.getnereus.dev`.

Then the Mandate `messaging-nats` is the messaging Reef's default with no match (`--default`, no `--match`), so it holds the Rooms' Topics, which name no engine (ADR 0030).

A cluster that had `--param agents=true` there keeps the old streams of the account `AGENTS` on the claim, unread, and the Secret `nats-triton` of `nereus-system`: drop the parameter, run `nereus nereid apply nats --reef messaging` again, and delete the Secret by hand.

The rooms Reef needs no parameter and no NATS account of its own (#2078). Triton's issuer is the public realm of step 5, given with `--set` (#2157); without it Triton stops with `--issuer is required`.

```bash
nereus reef apply rooms
nereus nereid apply triton \
  --reef rooms \
  --set TRITON_ISSUER=https://auth.getnereus.dev/realms/nereus \
  --set TRITON_JWKS_URL=http://keycloak-server-http.nereus-system.svc:8180/realms/nereus/protocol/openid-connect/certs \
  --set TRITON_RESOURCE_URL=https://triton.getnereus.dev/mcp
```

`POST https://triton.getnereus.dev/mcp` with no token answers 401.

Every other login is gone with the old realm: the claude.ai connector `Triton` signs in again, and a token saved from the old realm no longer works.

### 7. Make yourself an administrator User

A new instance has no User or binding, so your every call passes through the `nereus-admins` emergency exit (ADR 0027, teams, roles and Users) and `nereus doctor` warns `emergency-exit`. [`nereus user create`](../../specs/cli/reefs/authorization.html#user-create) takes the e-mail of step 5; [`nereus authorization binding create`](../../specs/cli/reefs/authorization.html#binding-create) gives it `administrator` (#2159).

```bash
nereus user create owner --email owner@example.com
nereus authorization binding create owner-admin --role administrator --user owner
nereus authorization can-i create core/users
```

``` { .text .output title="output" }
✓ core/users/owner created
✓ authorization/bindings/owner-admin created
yes: authorization/bindings/owner-admin gives administrator to user/owner at the whole instance
```

From then on your calls take the normal check, and the doctor's count of emergency-exit passes stops growing; its warning goes when the API restarts. You stay in `nereus-admins`, so the exit is still there for an emergency.

## Check it worked

[`nereus status`](../../specs/cli/core.html#status) shows every Reef Ready; `curl` on `https://triton.getnereus.dev/healthz`, `https://portal.getnereus.dev/` and `https://api.getnereus.dev/.well-known/nereus-configuration` answers 200, and the realm `master` answers 404 from outside.

```bash
nereus status
```

``` { .text .output title="output" }
REEF            NEREID           VERSION  STATUS  AGE
authentication  keycloak         0.1.0    Ready   7m
catalog         catalog          0.1.0    Ready   1m
core            nereus-api       0.1.0    Ready   9m
                thetis           0.1.0    Ready   9m
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
