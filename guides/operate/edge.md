# Publish at a hostname

Publish a reef's endpoint, here Triton, at a hostname of your own domain, while Nereus runs on your machine behind a Cloudflare tunnel.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with the secrets reef: the Nereid `cloudflare` requires it, and makes the vault `edge`.
- A domain, a Cloudflare account on the free plan, and a named tunnel's credentials from `cloudflared tunnel create nereus`, in `~/.cloudflared/<UUID>.json`.

## Steps

### 1. Apply the edge reef

[`nereus reef apply edge`](../../specs/cli/reefs/edge.html#apply-reef) adds the kinds `Zone`, `Domain` and `Route`.

```bash
nereus reef apply edge
```

``` { .text .output title="output" }
✓ core/reefs/edge 0.1.0 created
```

### 2. Apply the Nereid cloudflare

[`nereus nereid apply cloudflare`](../../specs/cli/reefs/edge.html#apply-cloudflare) runs the zone and the tunnel.

```bash
nereus nereid apply cloudflare --reef edge
```

``` { .text .output title="output" }
✓ core/nereids/cloudflare created, Ready
```

### 3. Keep the tunnel's credentials and name the tunnel

Keep the credentials file as the secret `edge/cloudflare-tunnel` with `nereus secrets create edge/cloudflare-tunnel --from-file credentials.json=<file>` ([Keep a secret](../reefs/secrets.md)). Then the Mandate names the tunnel and that secret.

```bash
nereus mandate create cloudflare \
  --reef edge \
  --nereid cloudflare \
  --param tunnel=nereus \
  --param credentialsSecret=edge/cloudflare-tunnel \
  --default
```

``` { .text .output title="output" }
✓ core/mandates/cloudflare created (reef: edge, nereid: cloudflare, default)
```

### 4. Delegate the domain

[`nereus edge zone create`](../../specs/cli/reefs/edge.html#zone-create) makes the zone and prints its nameservers; point your registrar at them.

```bash
nereus edge zone create getnereus.dev --mandate cloudflare
```

``` { .text .output title="output" }
✓ edge/zones/getnereus.dev created, waiting for its delegation
  nameservers: ada.ns.cloudflare.com, bob.ns.cloudflare.com
  point the registrar of getnereus.dev at them; the zone turns Active once Cloudflare sees it
```

Changing the registrar from Nereus waits for the Nereid godaddy [planned] (#475).

### 5. Carry the hostname through the tunnel

[`nereus edge route create`](../../specs/cli/reefs/edge.html#route-hostname) carries a hostname to the ingress gateway. Create the routes right after the Mandate: until one exists, the tunnel answers 404 for every hostname.

```bash
nereus edge route create triton --hostname triton.getnereus.dev
```

``` { .text .output title="output" }
✓ edge/routes/triton created, Ready: https://triton.getnereus.dev
```

A route may also name the endpoint a reef publishes, never a cluster, a namespace, a Service or a port (#1951). [`nereus edge endpoint list`](../../specs/cli/reefs/edge.html#endpoint-list) shows every endpoint the Nereids publish, with the hostnames each one serves; none is published by default. The Nereid's own apply grants one, then the route names it:

```bash
nereus edge endpoint list
nereus nereid apply triton --reef messaging --publish mcp
nereus edge route create triton --hostname triton.getnereus.dev --endpoint messaging/mcp
```

The tunnel carries the hostname only when the endpoint is publishable, granted and served on that hostname; otherwise the route says why (`NotPublished`, `NotServed`, `NoEndpoint`, or `Exposes` when the hostname also serves an endpoint that may not leave the cluster: the tunnel carries the whole hostname). The kept cluster's routes move to endpoints with #2011.

## Check it worked

`nereus edge zone list` shows the zone Active once the delegation arrives, and `nereus edge route list` shows every hostname the platform answers; then `https://triton.getnereus.dev` answers.

```bash
nereus edge route list
```

``` { .text .output title="output" }
NAME     HOSTNAME               ENDPOINT  MANDATE     READY   URL
auth     auth.getnereus.dev     -         cloudflare  True    https://auth.getnereus.dev
portal   portal.getnereus.dev   -         cloudflare  True    https://portal.getnereus.dev
triton   triton.getnereus.dev   -         cloudflare  True    https://triton.getnereus.dev
```

## Next

- [Rebuild the kept cluster](kept-cluster.md), which publishes Triton, the realm and the portal this way.

## Learn more

- With a Cloudflare API token in a secret of the vault `edge` (`--param apiTokenSecret=edge/cloudflare-token` on the Mandate), the Nereid creates or adopts the tunnel itself, with no `cloudflared tunnel create` ([#1961](https://github.com/getnereus/nereus/issues/1961), `deploy/edge/README.md`).
- ADR 0005: Nereids publish their endpoints and commands in `status`.
