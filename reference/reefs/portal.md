# The portal reef

Nereus in the browser: a PWA that signs a person in and shows who they are.

## Commands

- [`nereus reef apply portal`](../../specs/cli/reefs/portal.html#reef-apply) The portal reef, with no kinds
- [`nereus nereid apply nereus-portal`](../../specs/cli/reefs/portal.html#nereid-apply) The nereus-portal Nereid requires the authentication reef
- [`nereus mandate apply nereus-portal`](../../specs/cli/reefs/portal.html#mandate-apply) The publicUrl writes the HTTPRoute
- [`curl https://portal.example.com/healthz`](../../specs/cli/reefs/portal.html#open) The PWA, its config, and the API behind the person's token

## Examples

### reef-apply

The authentication reef and a Nereid of it come first.

```bash
nereus reef apply portal
```

``` { .text .output title="output" }
✓ core/reefs/portal created (portal.getnereus.dev/v1alpha1)

Next steps:

  nereus portal --help
  nereus nereid apply <nereid> --reef portal
```

### nereid-apply

One process, two ports: 8080 the controller's, inside the cluster, 8081 the portal's.

```bash
nereus nereid apply nereus-portal \
  --reef portal
```

``` { .text .output title="output" }
✓ core/nereids/nereus-portal created, Ready, pinned to sha256:b4f9fe726220: see 'nereus portal --help'
  core/mandates/nereus-portal created (reef: portal, nereid: nereus-portal, default)

Next steps:

  nereus mandate apply nereus-portal --reef portal --nereid nereus-portal --param publicUrl=https://portal.example.com
```

### mandate-apply

The gateway parameter takes another Gateway, istio-system/ingress by default (#728).

```bash
nereus mandate apply nereus-portal \
  --reef portal \
  --nereid nereus-portal \
  --param publicUrl=https://portal.example.com
```

``` { .text .output title="output" }
✓ core/mandates/nereus-portal configured (reef: portal, nereid: nereus-portal, default)

Next steps:

  nereus mandate list
```

### open

Open it on a phone and install it; the login is Authorization Code with PKCE.

```bash
curl https://portal.example.com/healthz
```

``` { .text .output title="output" }
ok
```
