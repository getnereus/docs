# The edge reef

Every command of the edge reef: domains, zones and routes, in the order a person types them.

## Commands

- [`nereus reef apply edge`](../../specs/cli/reefs/edge.html#apply-reef) One command applies the edge reef, with its first kind, Route
- [`nereus nereid apply cloudflare`](../../specs/cli/reefs/edge.html#apply-cloudflare) The cloudflare Nereid runs the tunnel its Mandate names
- [`nereus nereid apply godaddy`](../../specs/cli/reefs/edge.html#apply-godaddy) [planned #475] The godaddy Nereid talks to the registrar, through its Mandate
- [`nereus edge zone create getnereus.dev`](../../specs/cli/reefs/edge.html#zone-create) A zone gives the domain the nameservers that will answer for it
- [`nereus edge domain list`](../../specs/cli/reefs/edge.html#domain-list-registrar) [planned #475] The registrar shows its domains, with the credentials asked for now and never stored
- [`nereus edge domain apply getnereus.dev`](../../specs/cli/reefs/edge.html#domain-apply) [planned #475] Nereus takes the domain and sends it to the zone's nameservers
- [`nereus edge domain list`](../../specs/cli/reefs/edge.html#domain-list) [planned #475] The list shows the domains Nereus looks after
- [`nereus edge domain get getnereus.dev`](../../specs/cli/reefs/edge.html#domain-get) [planned #475] One domain shows every detail, its nameservers one per line
- [`nereus edge route create triton`](../../specs/cli/reefs/edge.html#route-hostname) A route makes a hostname reach the platform
- [`nereus edge endpoint list`](../../specs/cli/reefs/edge.html#endpoint-list) The Nereids say what they serve, never where it runs
- [`nereus edge route create triton`](../../specs/cli/reefs/edge.html#route-create) A route publishes a reef's endpoint at a fixed address

## Examples

### apply-reef

Apply the edge reef.

```bash
nereus reef apply edge
```

``` { .text .output title="output" }
✓ core/reefs/edge 0.1.0 created

Next steps:

  nereus edge --help
  nereus nereid apply <nereid> --reef edge
```

### apply-cloudflare

Apply the cloudflare Nereid to the edge reef.

```bash
nereus nereid apply cloudflare \
  --reef edge
```

``` { .text .output title="output" }
✓ core/nereids/cloudflare created, Ready

Next steps:

  nereus mandate create cloudflare --reef edge --nereid cloudflare --param tunnel=<tunnel> --param credentialsSecret=edge/<secret> --default
  nereus edge route create <name> --hostname <hostname>
```

### apply-godaddy

Apply the godaddy Nereid to the edge reef.

```bash
nereus nereid apply godaddy \
  --reef edge
```

``` { .text .output title="output" }
✓ core/nereids/godaddy created, Ready

Next steps:

  nereus mandate create godaddy --reef edge --nereid godaddy
```

### zone-create

Delegate the domain to the platform.

```bash
nereus edge zone create getnereus.dev \
  --mandate cloudflare
```

``` { .text .output title="output" }
✓ edge/zones/getnereus.dev created, waiting for its delegation
  nameservers: ada.ns.cloudflare.com, bob.ns.cloudflare.com
  point the registrar of getnereus.dev at them; the zone turns Active once Cloudflare sees it

Next steps:

  nereus edge zone get getnereus.dev
```

### domain-list-registrar

What the registrar holds.

```bash
nereus edge domain list \
  --at-registrar \
  --mandate godaddy
```

``` { .text .output title="output" }
GoDaddy API key: ****
GoDaddy API secret: ****
NAME            NAMESERVERS                  EXPIRES      MANAGED
getnereus.dev   ns01.domaincontrol.com (+1)  2029-10-25   no
example.com     ns01.domaincontrol.com (+1)  2029-10-25   no
example.org     ns01.domaincontrol.com (+1)  2028-06-11   no

Next steps:

  nereus edge domain get <name> --at-registrar --mandate godaddy
  nereus edge domain apply <name> --mandate godaddy
```

### domain-apply

Delegate getnereus.dev to the zone.

```bash
nereus edge domain apply getnereus.dev \
  --nameservers-from zone/getnereus.dev \
  --mandate godaddy
```

``` { .text .output title="output" }
✓ domain/getnereus.dev created

Next steps:

  nereus edge domain get getnereus.dev --watch
```

### domain-list

What Nereus looks after.

```bash
nereus edge domain list
```

``` { .text .output title="output" }
NAME            MANDATE  NAMESERVERS                 DELEGATED
getnereus.dev   godaddy  ada.ns.cloudflare.com (+1)  True

Next steps:

  nereus edge domain get getnereus.dev
```

### domain-get

Every detail of one domain.

```bash
nereus edge domain get getnereus.dev
```

``` { .text .output title="output" }
Name:         getnereus.dev
Mandate:      godaddy
Delegated:    True
Expires:      2029-10-25
Nameservers:
  ada.ns.cloudflare.com
  bob.ns.cloudflare.com
  (from zone/getnereus.dev)

Next steps:

  nereus edge domain get getnereus.dev --watch
```

### route-hostname

Carry Triton's hostname through the tunnel.

```bash
nereus edge route create triton \
  --hostname triton.getnereus.dev
```

``` { .text .output title="output" }
✓ edge/routes/triton created, Ready: https://triton.getnereus.dev

Next steps:

  nereus edge route get triton
```

### endpoint-list

What the Nereids serve at the instance's entrance.

```bash
nereus edge endpoint list
```

``` { .text .output title="output" }
REEF       ENDPOINT  NEREID  PROTOCOL  PATHS  HOSTS               PUBLISHABLE  PUBLISHED  ROUTES
messaging  mcp       triton  http      /      triton.example.com  yes          no         -
```

### route-create

Publish Triton's MCP endpoint.

```bash
nereus edge route create triton \
  --hostname triton.example.com \
  --endpoint messaging/mcp
```

``` { .text .output title="output" }
✓ edge/routes/triton created, Ready: https://triton.example.com

Next steps:

  nereus edge route get triton
```
